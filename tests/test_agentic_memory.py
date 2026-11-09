"""Verifica los ejemplos de la skill agentic-memory sin llamar al modelo: hilos y aprobación humana."""

import importlib.util
import sys
from pathlib import Path

from langchain_core.documents import Document
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.types import Command

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / ".claude/skills/agentic-memory"
EXAMPLES = SKILL / "references/examples"


def load_example(name, monkeypatch):
    # Los ejemplos se ejecutan como scripts e importan run_log desde su carpeta.
    monkeypatch.syspath_prepend(str(EXAMPLES))
    # Cada skill tiene su project.py: se descarta el que haya cargado otra prueba.
    for shared in ("project", "run_log"):
        monkeypatch.delitem(sys.modules, shared, raising=False)
    spec = importlib.util.spec_from_file_location(name, EXAMPLES / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ToolCallingFakeModel(GenericFakeChatModel):
    """Modelo falso que acepta herramientas, como lo exige create_agent."""

    def bind_tools(self, tools, **kwargs):
        return self


POLICY = Document("Una sola reestructuración por año.", metadata={"source": "acme_collections_policy.pdf", "page": 2})


def record_retriever(docs, queries):
    # Retriever falso: guarda cada consulta y devuelve siempre los mismos fragmentos.
    from langchain_core.runnables import RunnableLambda

    return RunnableLambda(lambda query: queries.append(query) or docs)


def test_memory_agent_remembers_each_thread_apart(monkeypatch):
    memory = load_example("memory_agent", monkeypatch)
    from langgraph.checkpoint.memory import InMemorySaver

    queries = []
    call = {"name": "search_documents", "args": {"query": "Restructuring rules for C-1042"}, "id": "c1"}
    model = ToolCallingFakeModel(messages=iter([
        AIMessage("", tool_calls=[call]),
        AIMessage("Up to 90 days [acme_collections_policy.pdf, p. 2]."),
        AIMessage("Quality decides."),
        AIMessage("Which credit do you mean?"),
    ]))
    agent = memory.build_agent(model, record_retriever([POLICY], queries), checkpointer=InMemorySaver())
    order, other = memory.thread("c-1042-arrears"), memory.thread("c-2210-new")

    agent.invoke({"messages": [HumanMessage("Can C-1042 restructure?")]}, order)
    state = agent.invoke({"messages": [HumanMessage("And how many times can I do it?")]}, order)
    assert queries == ["Restructuring rules for C-1042"]
    assert memory.searches(state["messages"]) == ["Restructuring rules for C-1042"]
    assert "[acme_collections_policy.pdf, p. 2]" in state["messages"][2].content  # el ToolMessage

    agent.invoke({"messages": [HumanMessage("And how many times can I do it?")]}, other)

    def humans(config):
        return [m.text for m in agent.get_state(config).values["messages"] if m.type == "human"]

    assert humans(order) == ["Can C-1042 restructure?", "And how many times can I do it?"]
    assert humans(other) == ["And how many times can I do it?"]


def test_approval_graph_pauses_and_resumes_each_way(monkeypatch):
    approval = load_example("approval", monkeypatch)
    graph = approval.build_graph()

    small = graph.invoke({"customer": "C-2210", "amount_cop": 1_200_000}, {"configurable": {"thread_id": "t1"}})
    assert "__interrupt__" not in small and small["status"].startswith("disbursed 1,200,000")
    too_big = graph.invoke({"customer": "C-2210", "amount_cop": 45_000_000}, {"configurable": {"thread_id": "t2"}})
    assert too_big["status"].startswith("rejected: over the daily limit")

    for thread, answer, expected in [
        ("t3", {"type": "approve"}, "disbursed 25,000,000"),
        ("t4", {"type": "reject", "note": "missing income statement"}, "rejected: missing income statement"),
        ("t5", {"type": "edit", "amount_cop": 20_000_000}, "disbursed 20,000,000"),
    ]:
        config = {"configurable": {"thread_id": thread}}
        paused = graph.invoke({"customer": "C-4415", "amount_cop": 25_000_000}, config)
        assert paused["__interrupt__"][0].value["amount_cop"] == 25_000_000
        assert graph.get_state(config).next == ("approval",)
        assert graph.invoke(Command(resume=answer), config)["status"].startswith(expected)


def test_approval_agent_never_runs_a_rejected_tool(monkeypatch):
    approval = load_example("approval", monkeypatch)
    call = {"name": "request_disbursement", "args": {"customer": "C-3307", "amount_cop": 35_000_000},
            "id": "call-1", "type": "tool_call"}
    model = ToolCallingFakeModel(messages=iter([AIMessage("", tool_calls=[call]), AIMessage("No se desembolsó.")]))
    agent = approval.build_agent(model)
    config = {"configurable": {"thread_id": "a1"}}
    paused = agent.invoke({"messages": [HumanMessage("Desembolsa 35.000.000 COP a C-3307.")]}, config)
    [action] = paused["__interrupt__"][0].value["action_requests"]
    assert action["name"] == "request_disbursement"
    result = agent.invoke(Command(resume={"decisions": [{"type": "reject", "message": "75 días de mora"}]}), config)
    assert not approval.tool_executed(result["messages"])
