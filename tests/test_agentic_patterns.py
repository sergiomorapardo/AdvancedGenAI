"""Verifica la skill agentic-patterns sin llamar al modelo: cada patrón con modelos falsos."""

import ast
import importlib.util
import re
import sys
from pathlib import Path

import pytest
from langchain_core.messages import AIMessage
from langgraph.errors import InvalidUpdateError
from langgraph.graph import START, StateGraph

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / ".claude/skills/agentic-patterns"
EXAMPLES = SKILL / "references/examples"
# Lo único que conoce este repositorio; el resto de la skill debe poder copiarse a otro proyecto.
PROJECT_FILES = {"project.md", "project.py"}


def load_example(name, monkeypatch):
    # Los ejemplos se ejecutan como scripts e importan project y run_log desde su carpeta.
    monkeypatch.syspath_prepend(str(EXAMPLES))
    for shared in ("project", "run_log"):
        monkeypatch.delitem(sys.modules, shared, raising=False)
    spec = importlib.util.spec_from_file_location(name, EXAMPLES / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ScriptedModel:
    """Modelo falso: devuelve en orden los objetos de cada esquema y los textos, y cuenta las llamadas."""

    def __init__(self, structured=None, texts=()):
        self.structured = {schema: list(values) for schema, values in (structured or {}).items()}
        self.texts = list(texts)
        self.calls = 0

    def with_structured_output(self, schema, **kwargs):
        model = self

        class Structured:
            def invoke(self, messages, config=None):
                model.calls += 1
                return model.structured[schema].pop(0)

        return Structured()

    def invoke(self, messages, config=None):
        self.calls += 1
        return AIMessage(self.texts.pop(0))

    def model_copy(self, update=None):
        return self


def test_skill_frontmatter_and_referenced_files_exist():
    text = (SKILL / "SKILL.md").read_text()
    frontmatter = text.split("---")[1]
    assert re.search(r"^name: agentic-patterns$", frontmatter, re.MULTILINE)
    description = re.search(r"^description: (.+)$", frontmatter, re.MULTILINE).group(1)
    assert 100 < len(description) <= 1024  # límite de Agent Skills fuera de Claude Code
    paths = set(re.findall(r"`((?:references|assets)/[\w./-]+)`", text))
    assert paths
    for path in paths:
        assert (SKILL / path).exists(), path


def test_skill_is_portable_outside_the_project_files():
    pattern = re.compile(r"notebooks/|datasets/|agents\.servers|load_dotenv|PdfReader")
    for path in SKILL.rglob("*"):
        if path.is_file() and path.suffix in {".md", ".py"} and path.name not in PROJECT_FILES:
            assert not pattern.search(path.read_text()), path.relative_to(SKILL)


def test_examples_compile_and_only_the_adapter_creates_the_model():
    for path in [*EXAMPLES.glob("*.py"), SKILL / "assets/graph.py"]:
        source = path.read_text()
        ast.parse(source, filename=str(path))
        assert "temperature=" not in source, path.name
        if path.name != "project.py":
            assert "ChatAnthropic(" not in source and "load_dotenv" not in source, path.name


def test_run_log_is_the_same_as_in_llm_prompts():
    shared = ROOT / ".claude/skills/llm-prompts/references/examples/run_log.py"
    assert (EXAMPLES / "run_log.py").read_text() == shared.read_text()


def test_policy_text_labels_every_page(monkeypatch):
    project = load_example("project", monkeypatch)
    text = project.policy_text(project.POLICY_FILES["collections"])
    assert "[acme_collections_policy.pdf, p. 1]" in text and "[acme_collections_policy.pdf, p. 2]" in text


def test_chain_gate_stops_early_without_more_calls(monkeypatch):
    chain = load_example("graph_chain", monkeypatch)
    assert chain.gate({"topic": "credit"}) == "extract" and chain.gate({"topic": "other"}) == "out_of_scope"

    data = chain.TicketData(customer="C-3307", question="¿Me reportan?", policy="collections")
    model = ScriptedModel(
        {chain.Classification: [chain.Classification(topic="credit"), chain.Classification(topic="other")],
         chain.TicketData: [data]},
        texts=["Sí, desde 61 días [acme_collections_policy.pdf, p. 1]."],
    )
    graph = chain.build_chain(model)
    long_path = [next(iter(step)) for step in graph.stream({"message": "mora"}, stream_mode="updates")]
    assert long_path == ["classify", "extract", "draft"] and model.calls == 3
    short = graph.invoke({"message": "¿Venden seguros?"})
    assert short["reply"] == chain.OUT_OF_SCOPE and model.calls == 4


def test_router_sends_each_question_to_its_specialist(monkeypatch):
    router = load_example("graph_router", monkeypatch)
    questions = list(router.QUESTIONS)
    assert router.keyword_route(questions[0]) == "credit"  # la regla falla donde el router acierta
    decisions = [router.RouteDecision(route=route) for route in router.QUESTIONS.values()]
    model = ScriptedModel({router.RouteDecision: decisions}, texts=["a", "b", "c"])
    graph = router.build_router(model)
    routes = {question: graph.invoke({"question": question})["route"] for question in questions}
    assert all(router.check_routes(routes, router.QUESTIONS).values()) and model.calls == 6
    assert not router.check_routes({questions[0]: "credit"}, router.QUESTIONS)[questions[0]]


def test_parallel_reviewers_fill_the_reducer_and_the_aggregator_decides(monkeypatch):
    parallel = load_example("graph_parallel", monkeypatch)
    verdicts = [parallel.Review(approved=True, issue=""), parallel.Review(approved=False, issue="6 months, not 3"),
                parallel.Review(approved=True, issue="")]
    model = ScriptedModel({parallel.Review: verdicts})
    result = parallel.build_review(model).invoke({"question": parallel.QUESTION, "draft": parallel.DRAFT})
    assert {review["criterion"] for review in result["reviews"]} == set(parallel.CRITERIA)
    assert result["decision"] == "fix: 6 months, not 3" and model.calls == 3
    assert parallel.aggregate({"reviews": [{"approved": True, "issue": ""}]})["decision"] == "send"


def test_parallel_writes_without_a_reducer_collide():
    from typing import TypedDict

    class Plain(TypedDict, total=False):
        reviews: list[str]

    builder = StateGraph(Plain)
    for name in ("a", "b"):
        builder.add_node(name, lambda state, name=name: {"reviews": [name]})
        builder.add_edge(START, name)
    with pytest.raises(InvalidUpdateError):
        builder.compile().invoke({})


def test_orchestrator_sends_one_worker_per_task_and_handles_an_empty_plan(monkeypatch):
    orchestrator = load_example("orchestrator", monkeypatch)
    tasks = [orchestrator.Task(question="¿Cuánto amplían?", policy="collections"),
             orchestrator.Task(question="¿Pago por PSE?", policy="fees")]
    model = ScriptedModel({orchestrator.Plan: [orchestrator.Plan(tasks=tasks), orchestrator.Plan(tasks=[])]},
                          texts=["24 meses.", "Sí, por PSE.", "Respuesta unida.", "Sin tareas."])
    graph = orchestrator.build_orchestrator(model)
    result = graph.invoke({"message": orchestrator.MESSAGE})
    assert len(result["answers"]) == 2 and result["reply"] == "Respuesta unida." and model.calls == 4
    assert orchestrator.check_plan(result["tasks"], orchestrator.EXPECTED_POLICIES) == {"missing": [], "unexpected": []}
    assert orchestrator.check_plan([{"policy": "credit"}], {"collections"}) == {"missing": ["collections"],
                                                                                "unexpected": ["credit"]}
    empty = graph.invoke({"message": "hola"})
    assert empty["reply"] == "Sin tareas." and not empty.get("answers")


def test_evaluator_loop_stops_at_the_cap_and_counts_words_in_code(monkeypatch):
    loop = load_example("evaluator_loop", monkeypatch)
    never = [loop.Feedback(grade="fix", feedback="falta una cita")] * loop.MAX_ATTEMPTS
    model = ScriptedModel({loop.Feedback: never}, texts=["corta"] * loop.MAX_ATTEMPTS)
    result = loop.build_loop(model).invoke({"question": loop.QUESTION})
    assert result["attempts"] == loop.MAX_ATTEMPTS and len(result["history"]) == loop.MAX_ATTEMPTS
    assert model.calls == 2 * loop.MAX_ATTEMPTS

    long_draft = "palabra " * (loop.MAX_WORDS + 1)
    model = ScriptedModel({loop.Feedback: [loop.Feedback(grade="approved", feedback="")]}, texts=[long_draft, "corta"])
    result = loop.build_loop(model).invoke({"question": loop.QUESTION})
    first, second = result["history"]
    assert first["grade"] == "fix" and "words" in first["feedback"]  # el juez no se llamó
    assert second["grade"] == "approved" and model.calls == 3

    cited = "palabra " * loop.MAX_WORDS + "[acme_collections_policy.pdf, p. 2] " * 5  # las citas no cuentan
    model = ScriptedModel({loop.Feedback: [loop.Feedback(grade="approved", feedback="")]}, texts=[cited])
    result = loop.build_loop(model).invoke({"question": loop.QUESTION})
    assert result["history"][0]["words"] == loop.MAX_WORDS and result["grade"] == "approved"
