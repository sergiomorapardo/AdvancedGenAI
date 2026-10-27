"""Verifica la skill agentic-workflow y el hook de Jinja sin llamar al modelo."""

import ast
import importlib.util
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import httpx
import pytest
from jinja2 import UndefinedError
from langchain_core.documents import Document
from langchain_core.embeddings import DeterministicFakeEmbedding
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.prompts import ChatPromptTemplate

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / ".claude/skills/agentic-workflow"
EXAMPLES = SKILL / "references/examples"
HOOK = ROOT / ".claude/hooks/check_jinja.py"
APP_HOOK = ROOT / ".claude/hooks/check_app.py"
# Lo único que conoce este repositorio; el resto de la skill debe poder copiarse a otro proyecto.
PROJECT_FILES = {"project.md", "project.py"}


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


def run_hook(file_path):
    event = json.dumps({"tool_name": "Write", "tool_input": {"file_path": str(file_path)}})
    return subprocess.run(
        [sys.executable, str(HOOK)], input=event, capture_output=True, text=True, check=False
    )


def test_skill_frontmatter_and_referenced_files_exist():
    text = (SKILL / "SKILL.md").read_text()
    frontmatter = text.split("---")[1]
    assert re.search(r"^name: agentic-workflow$", frontmatter, re.MULTILINE)
    description = re.search(r"^description: (.+)$", frontmatter, re.MULTILINE).group(1)
    assert 100 < len(description) <= 1024  # límite de Agent Skills fuera de Claude Code
    paths = set(re.findall(r"`((?:references|assets)/[\w./-]+)`", text))
    assert paths
    for path in paths:
        assert (SKILL / path).exists(), path


def test_skill_is_portable_outside_the_project_files():
    pattern = re.compile(r"notebooks/|datasets/|agents\.servers|load_dotenv|\d\d_\w+\.py")
    for path in SKILL.rglob("*"):
        if path.is_file() and path.suffix in {".md", ".py", ".jinja", ".json"} and path.name not in PROJECT_FILES:
            assert not pattern.search(path.read_text()), path.relative_to(SKILL)


def test_examples_and_template_compile():
    for path in [*EXAMPLES.glob("*.py"), SKILL / "assets/app.py"]:
        ast.parse(path.read_text(), filename=str(path))


def test_only_the_project_adapter_creates_the_model():
    project = (EXAMPLES / "project.py").read_text()
    assert 'MODEL = "claude-haiku-5-5"' in project and '"type": "disabled"' in project
    for path in [*EXAMPLES.glob("*.py"), SKILL / "assets/app.py"]:
        source = path.read_text()
        assert "temperature=" not in source, path.name
        if path.name != "project.py":
            assert "ChatAnthropic(" not in source and "load_dotenv" not in source, path.name


def test_chain_prompt_keeps_the_question_apart(monkeypatch):
    chain = load_example("chain", monkeypatch)
    messages = chain.PROMPT.format_messages(context=chain.TICKET, question="How much is each charge?")
    assert [m.type for m in messages] == ["system", "human", "human"]
    assert "185,000 COP" in messages[1].content


def test_jinja_example_renders_and_fails_on_missing_data(monkeypatch):
    jinja = load_example("jinja_prompt", monkeypatch)
    prompt = jinja.render_system_prompt(jinja.TICKET, jinja.RULES)
    assert "- Charge date: yesterday" in prompt and "2. Do not convert" in prompt
    assert prompt.count("- Charge: 185000 COP") == 2
    without_customer = {key: value for key, value in jinja.TICKET.items() if key != "customer"}
    with pytest.raises(UndefinedError):
        jinja.render_system_prompt(without_customer, [])


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


def test_rag_example_keeps_pages_cites_and_checks_citations(monkeypatch):
    rag = load_example("rag", monkeypatch)
    pages = rag.load_pages(rag.DOCUMENTS)
    chunks = rag.split(pages)
    assert len(pages) == 8 and len(chunks) == 26
    assert all(set(chunk.metadata) == {"source", "page"} for chunk in chunks)
    ficha = Document("Hasta 3.000.000 COP", metadata={"source": "acme_credit_policy.pdf", "page": 1})
    assert rag.format_context([ficha]) == "[acme_credit_policy.pdf, p. 1]\nHasta 3.000.000 COP"
    assert rag.check_citations("Up to 3,000,000 COP [acme_credit_policy.pdf, p. 1].", [ficha])
    assert not rag.check_citations("Up to 40,000,000 COP [acme_credit_policy.pdf, p. 2].", [ficha])
    assert not rag.check_citations("Up to 3,000,000 COP.", [ficha])
    # Haiku 5.5 agrupó dos fuentes en un corchete en la corrida real.
    guia = Document("Sin efectivo.", metadata={"source": "acme_fees_guide.pdf", "page": 1})
    grouped = "No cash [acme_credit_policy.pdf, p. 1; acme_fees_guide.pdf, p. 1]."
    assert rag.check_citations(grouped, [ficha, guia])
    assert not rag.check_citations(grouped, [ficha])


def test_rag_chain_returns_answer_and_docs_without_the_model(monkeypatch):
    rag = load_example("rag", monkeypatch)
    from langchain_core.vectorstores import InMemoryVectorStore

    chunks = rag.split(rag.load_pages(rag.DOCUMENTS))
    store = InMemoryVectorStore.from_documents(chunks, DeterministicFakeEmbedding(size=16))
    model = GenericFakeChatModel(messages=iter([AIMessage("Not in the documents.")]))
    result = rag.build_rag(store.as_retriever(search_kwargs={"k": 3}), model).invoke("Price?")
    assert result["answer"] == "Not in the documents." and len(result["docs"]) == 3
    assert "[file, p. N]" in rag.SYSTEM_PROMPT and "not in the documents" in rag.SYSTEM_PROMPT


def test_vector_store_example_persists_faiss_and_chroma(monkeypatch, tmp_path):
    stores = load_example("vector_store", monkeypatch)
    embeddings = DeterministicFakeEmbedding(size=16)
    chunks = stores.load_chunks(stores.DOCUMENTS)
    question = "restructuring"

    built = stores.build_faiss(chunks, embeddings, tmp_path / "faiss")
    assert {p.name for p in (tmp_path / "faiss").iterdir()} == {"index.faiss", "index.pkl"}
    loaded = stores.load_faiss(tmp_path / "faiss", embeddings)
    assert stores.pages_of(loaded.similarity_search(question, k=3)) == stores.pages_of(
        built.similarity_search(question, k=3)
    )

    stores.build_chroma(chunks, embeddings, tmp_path / "chroma")
    chroma = stores.build_chroma(chunks, embeddings, tmp_path / "chroma")  # rerun: no duplicates
    assert len(chroma.get()["ids"]) == len(chunks) == 26
    assert chroma._collection.metadata["hnsw:space"] == "cosine"
    filtered = chroma.similarity_search(question, k=3, filter={"source": "acme_collections_policy.pdf"})
    assert {source for source, _ in stores.pages_of(filtered)} == {"acme_collections_policy.pdf"}


def test_run_log_writes_events_and_transcript(monkeypatch, tmp_path):
    run_log_module = load_example("run_log", monkeypatch)
    run_log = run_log_module.RunLog(tmp_path / "runs")
    model = GenericFakeChatModel(messages=iter([AIMessage("185,000 COP.")]))
    chain = ChatPromptTemplate.from_messages([("human", "{question}")]) | model
    chain.invoke({"question": "How much is each charge?"}, config={"callbacks": [run_log]})
    events = [json.loads(line) for line in (run_log.path / "events.jsonl").read_text().splitlines()]
    assert [event["event"] for event in events] == ["model_start", "model_end"]
    transcript = (run_log.path / "transcript.md").read_text()
    assert "Model call 1" in transcript and "185,000 COP." in transcript
    assert run_log.model_calls == 1


def test_hook_accepts_the_example_template_and_ignores_other_files(tmp_path):
    assert run_hook(EXAMPLES / "prompts/ticket.jinja").returncode == 0
    assert run_hook(ROOT / "datasets/acme_ticket.jinja").returncode == 0
    assert run_hook(tmp_path / "notes.md").returncode == 0


def test_hook_rejects_syntax_errors_and_missing_variables(tmp_path):
    broken = tmp_path / "broken.jinja"
    broken.write_text("{% if ticket %}Ticket {{ ticket.code }}")
    result = run_hook(broken)
    assert result.returncode == 2 and "TemplateSyntaxError" in result.stderr

    template = tmp_path / "ticket.jinja"
    template.write_text("Customer: {{ ticket.customer }}")
    (tmp_path / "ticket.example.json").write_text(json.dumps({"ticket": {"code": "T-1"}}))
    result = run_hook(template)
    assert result.returncode == 2 and "UndefinedError" in result.stderr


def test_project_settings_register_the_hooks_and_ask_before_paid_runs():
    settings = json.loads((ROOT / ".claude/settings.json").read_text())
    hook = settings["hooks"]["PostToolUse"][0]
    assert {"Write", "Edit"} <= set(hook["matcher"].split("|"))
    commands = " ".join(entry["command"] for entry in hook["hooks"])
    assert "check_jinja.py" in commands and "check_app.py" in commands
    assert "Bash(uv run python labs/*)" in settings["permissions"]["ask"]


def run_app_hook(file_path, root):
    event = json.dumps({"tool_name": "Write", "tool_input": {"file_path": str(file_path)}})
    return subprocess.run(
        [sys.executable, str(APP_HOOK)], input=event, capture_output=True, text=True, check=False,
        env={**os.environ, "CLAUDE_PROJECT_DIR": str(root)}, cwd=ROOT,
    )


def test_app_hook_accepts_an_example_and_ignores_files_outside_labs(tmp_path):
    app = tmp_path / "labs/ticket-check/app.py"
    app.parent.mkdir(parents=True)
    app.write_text((EXAMPLES / "chain.py").read_text())
    assert run_app_hook(app, tmp_path).returncode == 0
    outside = tmp_path / "notes.py"
    outside.write_text("this is not python")
    assert run_app_hook(outside, tmp_path).returncode == 0


def test_app_hook_rejects_temperature_keys_and_lint_errors(tmp_path):
    app = tmp_path / "labs/bad/app.py"
    app.parent.mkdir(parents=True)
    app.write_text('from langchain_anthropic import ChatAnthropic\n\nKEY = "sk-ant-0123456789"\n'
                   'model = ChatAnthropic(model="x", temperature=0)\n')
    result = run_app_hook(app, tmp_path)
    assert result.returncode == 2
    assert "temperature" in result.stderr and "literal API key" in result.stderr
    app.write_text("import os\n")
    result = run_app_hook(app, tmp_path)
    assert result.returncode == 2 and "F401" in result.stderr
    app.write_text("def broken(:\n")
    assert "SyntaxError" in run_app_hook(app, tmp_path).stderr


class ToolCallingFakeModel(GenericFakeChatModel):
    """Modelo falso que acepta herramientas, como lo exige create_agent."""

    def bind_tools(self, tools, **kwargs):
        return self


def record_retriever(docs, queries):
    # Retriever falso: guarda cada consulta y devuelve siempre los mismos fragmentos.
    from langchain_core.runnables import RunnableLambda

    return RunnableLambda(lambda query: queries.append(query) or docs)


POLICY = Document("Una sola reestructuración por año.", metadata={"source": "acme_collections_policy.pdf", "page": 2})


def test_conversational_rag_rewrites_only_follow_ups(monkeypatch):
    rag = load_example("conversational_rag", monkeypatch)
    queries = []
    model = GenericFakeChatModel(messages=iter([
        AIMessage("Yes, up to 90 days [acme_collections_policy.pdf, p. 2]."),
        AIMessage("How many times can customer C-1042 restructure a Crédito Libre Inversión?"),
        AIMessage("Once a year [acme_collections_policy.pdf, p. 2]."),
    ]))
    chain = rag.build_conversational_rag(record_retriever([POLICY], queries), model)

    first = chain.invoke({"question": "Can C-1042 restructure?", "history": []})
    assert first["standalone_question"] == "Can C-1042 restructure?"
    history = [HumanMessage("Can C-1042 restructure?"), first["answer"]]
    follow_up = chain.invoke({"question": "And how many times can I do it?", "history": history})
    # Se recupera con la pregunta reescrita, no con la de seguimiento.
    assert queries == ["Can C-1042 restructure?", follow_up["standalone_question"]]
    assert "C-1042" in follow_up["standalone_question"]
    assert rag.check_citations(follow_up["answer"].text, follow_up["docs"])
    rewrite = rag.REWRITE.format_messages(conversation=rag.format_history(history), question="And?")
    assert [m.type for m in rewrite] == ["system", "human"] and "human: Can" in rewrite[1].content


def test_multi_query_keeps_each_fragment_once(monkeypatch):
    rag = load_example("conversational_rag", monkeypatch)
    other = Document("Periodo de gracia.", metadata={"source": "acme_collections_policy.pdf", "page": 1})
    assert rag.unique_docs([[POLICY, other], [other], [POLICY]]) == [POLICY, other]


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


def test_mcp_agent_loads_prefixed_tools_and_pauses_for_the_person(monkeypatch):
    # Servidores reales por stdio y un modelo falso: ninguna llamada a la API.
    import asyncio

    from langgraph.checkpoint.memory import InMemorySaver
    from langgraph.types import Command

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
