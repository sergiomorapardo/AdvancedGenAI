"""Verifica los ejemplos de la skill llm-tools sin llamar al modelo."""

import importlib.util
import json
import sys
from pathlib import Path

import httpx
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langgraph.types import Command

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / ".claude/skills/llm-tools"
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


def test_tools_example_returns_errors_as_data_and_checks_answers(monkeypatch):
    agent = load_example("tools_agent", monkeypatch)
    lookup = agent.lookup_credit
    assert lookup.invoke({"customer": "C-1042", "product": "libre inversión", "payment": 500_000}) == {
        "status": "ok", "customer": "C-1042", "code": "CLI", "overdue_cop": 824_000, "days_past_due": 45,
        "covers_overdue": False, "missing_cop": 324_000,
    }
    assert lookup.invoke({"customer": "C-1042", "product": "credit card"})["status"] == "not_found"
    tool_message = lookup.invoke({
        "type": "tool_call", "id": "call-1", "name": "lookup_credit",
        "args": {"customer": "C-1042", "product": "CLI"},
    })
    assert agent.check_answer([tool_message, AIMessage("You have $824.000 overdue.")])
    assert not agent.check_answer([tool_message, AIMessage("You have $412.000 overdue.")])


def test_api_tool_returns_every_failure_as_data(monkeypatch):
    api = load_example("api_tool", monkeypatch)
    row = {"valor": "4000.00", "unidad": "COP", "vigenciadesde": "2026-10-26T00:00:00.000",
           "vigenciahasta": "2026-10-26T00:00:00.000"}
    responses = iter([
        httpx.Response(200, json=[row]),
        httpx.Response(400, text='{"message": "query.soql.type-mismatch"}'),
        httpx.Response(200, json=[]),
    ])
    monkeypatch.setattr(api.httpx, "get", lambda *args, **kwargs: next(responses))

    ok = api.get_exchange_rate.invoke({"day": "2026-10-26"})
    assert ok["status"] == "ok" and ok["cop_per_usd"] == 4000.0
    assert api.get_exchange_rate.invoke({"day": "tomorrow"})["status"] == "unavailable"
    assert api.get_exchange_rate.invoke({"day": "2099-01-01"})["status"] == "not_found"

    def timeout(*args, **kwargs):
        raise httpx.ConnectTimeout("timed out")

    monkeypatch.setattr(api.httpx, "get", timeout)
    assert api.get_exchange_rate.invoke({"day": "2026-10-26"})["status"] == "unavailable"

    tool_message = ToolMessage(json.dumps(ok), tool_call_id="call-1")
    assert api.check_answer([tool_message, AIMessage("300 USD × 4.000 = $1.200.000 COP.")], usd=300)
    assert not api.check_answer([tool_message, AIMessage("About one million pesos.")], usd=300)


def test_mcp_agent_loads_prefixed_tools_and_pauses_for_the_person(monkeypatch):
    # Servidores reales por stdio y un modelo falso: ninguna llamada a la API.
    import asyncio

    from langgraph.checkpoint.memory import InMemorySaver

    mcp_agent = load_example("mcp_agent", monkeypatch)
    from project import SAMPLE_MCP_SERVERS

    call = {"name": "credits_check_credit", "args": {"customer": "C-1042"}, "id": "c1"}
    model = ToolCallingFakeModel(messages=iter([AIMessage("", tool_calls=[call]), AIMessage("824.000 pesos.")]))

    async def conversation():
        tools = await mcp_agent.load_tools(mcp_agent.server_config(SAMPLE_MCP_SERVERS))
        agent = mcp_agent.build_agent(model, tools, checkpointer=InMemorySaver())
        config = {"configurable": {"thread_id": "ambiguous-credit"}}
        paused = await agent.ainvoke({"messages": [HumanMessage(mcp_agent.AMBIGUOUS)]}, config)
        request = mcp_agent.pending_question(paused)
        answer = {"action": "accept", "content": {"code": "CLI"}}
        resumed = await agent.ainvoke(Command(resume={"responses": {request["key"]: answer}}), config)
        return [tool.name for tool in tools], request, resumed

    names, request, resumed = asyncio.run(conversation())
    assert names == ["credits_check_credit", "credits_list_products", "documents_search_documents"]
    assert request["requested_schema"]["properties"]["code"]["enum"] == ["CEX", "CLI"]
    rows = json.loads(resumed["messages"][-2].content[0]["text"])
    assert rows["code"] == "CLI" and rows["overdue"] == 824_000
    assert mcp_agent.pending_question(resumed) is None
    assert mcp_agent.tools_used(resumed["messages"]) == ["credits_check_credit"]


def test_mcp_agent_asks_the_person_and_declines_unknown_answers(monkeypatch):
    mcp_agent = load_example("mcp_agent", monkeypatch)
    request = {"message": "Which credit?", "requested_schema": {"properties": {"code": {"enum": ["CEX", "CLI"]}}}}
    answers = iter(["CLI", "card", ""])
    monkeypatch.setattr("builtins.input", lambda prompt: next(answers))
    assert mcp_agent.answer_from_person(request) == {"action": "accept", "content": {"code": "CLI"}}
    assert mcp_agent.answer_from_person(request) == {"action": "decline"}
    assert mcp_agent.answer_from_person(request) == {"action": "decline"}
