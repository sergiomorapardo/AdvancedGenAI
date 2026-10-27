"""Verifica la skill deploy-app sin modelo ni base de datos: API con modelo falso e hilos en memoria."""

import ast
import importlib.util
import json
import re
import sys
from pathlib import Path

from fastapi.testclient import TestClient
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage, AIMessageChunk, HumanMessage

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / ".claude/skills/deploy-app"
EXAMPLES = SKILL / "references/examples"
PROJECT_FILES = {"project.md", "project.py"}


class ToolCallingFakeModel(GenericFakeChatModel):
    """Modelo falso que acepta herramientas, como lo exige create_agent."""

    def bind_tools(self, tools, **kwargs):
        return self


def load_examples(monkeypatch):
    monkeypatch.syspath_prepend(str(EXAMPLES))
    monkeypatch.delenv("DB_URI", raising=False)
    for shared in ("project", "graph", "api"):
        monkeypatch.delitem(sys.modules, shared, raising=False)
    modules = {}
    for name in ("project", "graph", "api"):
        spec = importlib.util.spec_from_file_location(name, EXAMPLES / f"{name}.py")
        modules[name] = importlib.util.module_from_spec(spec)
        sys.modules[name] = modules[name]
        spec.loader.exec_module(modules[name])
    # project.py carga el .env al importarse: se vuelve a quitar DB_URI para usar hilos en memoria.
    monkeypatch.delenv("DB_URI", raising=False)
    return modules["graph"], modules["api"]


def fake_api(monkeypatch, replies):
    graph, api = load_examples(monkeypatch)
    model = ToolCallingFakeModel(messages=iter(replies))
    monkeypatch.setattr(api, "make_graph", lambda checkpointer: graph.make_graph(checkpointer=checkpointer, model=model))
    return api


def test_skill_frontmatter_and_referenced_files_exist():
    text = (SKILL / "SKILL.md").read_text()
    frontmatter = text.split("---")[1]
    assert re.search(r"^name: deploy-app$", frontmatter, re.MULTILINE)
    description = re.search(r"^description: (.+)$", frontmatter, re.MULTILINE).group(1)
    assert 100 < len(description) <= 1024
    for path in set(re.findall(r"`((?:references|assets)/[\w./-]+)`", text)):
        assert (SKILL / path).exists(), path


def test_skill_is_portable_outside_the_project_files():
    pattern = re.compile(r"src/api|docs/sql|\.github/scripts|datasets/|load_dotenv")
    for path in SKILL.rglob("*"):
        if path.is_file() and path.suffix in {".md", ".py"} and path.name not in PROJECT_FILES:
            assert not pattern.search(path.read_text()), path.relative_to(SKILL)


def test_examples_compile_and_only_the_adapter_creates_the_model():
    for path in EXAMPLES.glob("*.py"):
        source = path.read_text()
        ast.parse(source, filename=str(path))
        assert "temperature=" not in source and "sk-ant-" not in source, path.name
        if path.name != "project.py":
            assert "ChatAnthropic(" not in source, path.name


def test_health_and_memory_per_thread(monkeypatch):
    api = fake_api(monkeypatch, [AIMessage("Hola."), AIMessage("Seguimos."), AIMessage("Nuevo hilo.")])
    with TestClient(api.app) as client:
        assert client.get("/health").json() == {"status": "ok"}
        first = client.post("/chat/t-1", json={"message": "Hola"}).json()
        second = client.post("/chat/t-1", json={"message": "¿Sigues ahí?"}).json()
        other = client.post("/chat/t-2", json={"message": "Hola"}).json()
    assert [m["content"] for m in first] == ["Hola", "Hola."]
    assert [m["content"] for m in second] == ["Hola", "Hola.", "¿Sigues ahí?", "Seguimos."]
    assert len(other) == 2


def test_stream_hides_tool_results(monkeypatch):
    _, api = load_examples(monkeypatch)
    blocks = [{"type": "text", "text": "COP vencidos."}]

    class FakeGraph:
        # Como en el agente real: trozos del nodo tools y del nodo model, algunos vacíos o en bloques.
        def stream(self, state, config, stream_mode):
            assert config["configurable"]["thread_id"] == "t-3" and stream_mode == "messages"
            yield AIMessageChunk(content='{"overdue_cop": 2070000}'), {"langgraph_node": "tools"}
            yield AIMessageChunk(content=""), {"langgraph_node": "model"}
            yield AIMessageChunk(content="Tienes 2.070.000 "), {"langgraph_node": "model"}
            yield AIMessageChunk(content=blocks), {"langgraph_node": "model"}

    monkeypatch.setattr(api, "make_graph", lambda checkpointer: FakeGraph())
    with TestClient(api.app) as client:
        response = client.post("/chat/t-3/stream", json={"message": "¿Cuánto debo? Soy C-3307"})
    assert response.status_code == 200 and "text/event-stream" in response.headers["content-type"]
    frames = [json.loads(frame.removeprefix("data: ")) for frame in response.text.strip().split("\n\n")]
    assert frames == [{"content": "Tienes 2.070.000 "}, {"content": blocks}]  # sin la herramienta ni vacíos


def test_empty_message_is_rejected_before_the_model(monkeypatch):
    api = fake_api(monkeypatch, [])
    with TestClient(api.app) as client:
        assert client.post("/chat/t-4", json={"message": ""}).status_code == 422


def test_turn_usage_counts_only_the_last_turn(monkeypatch):
    _, api = load_examples(monkeypatch)
    usage = {"input_tokens": 10, "output_tokens": 5, "total_tokens": 15}
    messages = [HumanMessage("a"), AIMessage("b", usage_metadata=usage), HumanMessage("c"),
                AIMessage("", usage_metadata=usage), AIMessage("d", usage_metadata=usage)]
    assert api.turn_usage(messages) == {"model_calls": 2, "input_tokens": 20, "output_tokens": 10}
