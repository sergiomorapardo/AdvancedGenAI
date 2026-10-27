"""Verifica la skill evaluate-app sin llamar al modelo ni a LangSmith."""

import importlib.util
import json
import re
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pytest
from langchain_core.runnables import RunnableLambda

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / ".claude/skills/evaluate-app"
EXAMPLES = SKILL / "references/examples"
# Lo único que conoce este repositorio; el resto de la skill debe poder copiarse a otro proyecto.
PROJECT_FILES = {"project.md", "project.py"}


def load_example(name, monkeypatch):
    monkeypatch.syspath_prepend(str(EXAMPLES))
    # Cada skill tiene su project.py: se descarta el que haya cargado otra prueba.
    for shared in ("project", "evaluators", "results"):
        monkeypatch.delitem(sys.modules, shared, raising=False)
    spec = importlib.util.spec_from_file_location(name, EXAMPLES / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_skill_frontmatter_and_referenced_files_exist():
    text = (SKILL / "SKILL.md").read_text()
    frontmatter = text.split("---")[1]
    assert re.search(r"^name: evaluate-app$", frontmatter, re.MULTILINE)
    description = re.search(r"^description: (.+)$", frontmatter, re.MULTILINE).group(1)
    assert 100 < len(description) <= 1024
    paths = set(re.findall(r"`((?:references|assets)/[\w./-]+)`", text))
    assert paths
    for path in paths:
        assert (SKILL / path).exists(), path


def test_skill_is_portable_outside_the_project_files():
    pattern = re.compile(r"notebooks/|datasets/|agents\.servers|load_dotenv|\d\d_\w+\.py")
    for path in SKILL.rglob("*"):
        if path.is_file() and path.suffix in {".md", ".py"} and path.name not in PROJECT_FILES:
            assert not pattern.search(path.read_text()), path.relative_to(SKILL)


def test_only_the_project_adapter_creates_the_model():
    assert 'MODEL = "claude-haiku-5-5"' in (EXAMPLES / "project.py").read_text()
    for name in ("evaluation", "evaluators", "results"):
        source = (EXAMPLES / f"{name}.py").read_text()
        assert "ChatAnthropic(" not in source and "temperature=" not in source, name


REFERENCE = {"reference": "Hasta 90 días de mora.", "source": "acme_collections_policy.pdf", "page": 2}
NO_ANSWER = {"reference": "No está en los documentos.", "source": None, "page": None}


def test_code_evaluators_pass_fail_and_do_not_apply(monkeypatch):
    evaluators = load_example("evaluators", monkeypatch)
    good = {"answer": "90 días [acme_collections_policy.pdf, p. 2].", "sources": [["acme_collections_policy.pdf", 2]]}
    bad = {"answer": "60 días [acme_collections_policy.pdf, p. 1].", "sources": [["acme_fees_guide.pdf", 1]]}
    for evaluator in (evaluators.retrieval_hit, evaluators.citations_ok, evaluators.figures_match):
        assert evaluator(good, REFERENCE)["score"] is True, evaluator.__name__
        assert evaluator(bad, REFERENCE)["score"] is False, evaluator.__name__
    assert "('acme_collections_policy.pdf', 1)" in evaluators.citations_ok(bad, REFERENCE)["comment"]
    assert evaluators.figures_match(bad, REFERENCE)["comment"] == "Missing: ['90']"
    # El número de página de la cita no cuenta como cifra de la respuesta.
    only_page = {"answer": "Ver [acme_collections_policy.pdf, p. 90].", "sources": [["acme_collections_policy.pdf", 90]]}
    assert evaluators.figures_match(only_page, REFERENCE)["score"] is False
    assert evaluators.retrieval_hit(good, NO_ANSWER)["score"] is None
    assert evaluators.figures_match(good, NO_ANSWER)["score"] is None
    assert evaluators.citations_ok({"answer": "No está.", "sources": []}, NO_ANSWER)["score"] is True


def test_make_judge_fills_only_its_placeholders_and_counts_failures_apart(monkeypatch):
    evaluators = load_example("evaluators", monkeypatch)
    prompts = []

    def fake_judge(messages):
        prompts.append(messages[0].content)
        if "60 días" in messages[0].content:
            raise ValueError("no score")
        return evaluators.Judgement(reasoning="Coincide con la referencia.", score=" A 90 días" in messages[0].content)

    judge = RunnableLambda(fake_judge)
    correctness = evaluators.make_judge(judge, "correctness", "Q {inputs} A {outputs} R {reference_outputs}")
    grounded = evaluators.make_judge(judge, "groundedness", "C {context} A {outputs}")
    inputs, outputs = {"question": "¿Con cuántos días de mora?"}, {"answer": "90 días", "context": "Hasta 90 días."}
    assert correctness(inputs, outputs, REFERENCE) == {
        "key": "correctness", "score": True, "comment": "Coincide con la referencia.",
    }
    assert prompts[-1] == "Q ¿Con cuántos días de mora? A 90 días R Hasta 90 días de mora."
    assert grounded(inputs, outputs, None)["score"] is True  # sin referencia: no la necesita
    failed = correctness(inputs, {"answer": "60 días"}, REFERENCE)
    assert failed["score"] is None and failed["comment"].startswith("Invalid format")
    with pytest.raises(ValueError, match="unknown placeholders"):
        evaluators.make_judge(judge, "bad", "Use {answer}")

    labeled = [
        {"inputs": inputs, "outputs": {"answer": "90 días"}, "reference_outputs": REFERENCE, "human": True, "note": "ok"},
        {"inputs": inputs, "outputs": {"answer": "75 días"}, "reference_outputs": REFERENCE, "human": True, "note": "?"},
        {"inputs": inputs, "outputs": {"answer": "60 días"}, "reference_outputs": REFERENCE, "human": False, "note": "x"},
    ]
    calibration = evaluators.calibrate(correctness, labeled)
    assert calibration["agreement"] == 0.5 and calibration["scored"] == 2
    assert calibration["format_failures"] == 1 and [r["note"] for r in calibration["disagreements"]] == ["?"]


def row(experiment, example_id, scores, error=None, seconds=2.0, comments=None):
    return {
        "experiment": experiment, "example_id": example_id, "id": example_id, "question": f"¿{example_id}?",
        "answer": f"respuesta {example_id}", "reference": "ref", "error": error, "seconds": seconds,
        "input_tokens": 1000, "output_tokens": 100, "scores": scores, "comments": comments or {},
        "steps": {}, "trace_id": example_id,
    }


def test_results_summarize_compare_and_diagnose(monkeypatch):
    results = load_example("results", monkeypatch)
    a = [row("A", "q1", {"retrieval_hit": False, "correctness": False}),
         row("A", "q2", {"retrieval_hit": True, "correctness": False}),
         row("A", "q3", {"retrieval_hit": True, "correctness": True}),
         row("A", "q4", {"correctness": None}, comments={"correctness": "Invalid format: x"})]
    b = [row("B", "q1", {"retrieval_hit": True, "correctness": True}),
         row("B", "q2", {"retrieval_hit": True, "correctness": True}),
         row("B", "q3", {"retrieval_hit": True, "correctness": True}),
         row("B", "q4", {}, error="boom")]
    summary = results.summarize(a)
    assert summary["metrics"]["correctness"] == {"mean": 1 / 3, "n": 3, "format_failures": 1}
    assert summary["errors"] == 0 and summary["latency_median_s"] == 2.0
    assert round(summary["cost_usd"], 6) == round(4 * (1000 * 0.10 + 100 * 0.50) / 1e6, 6)
    assert results.summarize(b)["errors"] == 1

    comparison = results.compare(a, b, "correctness")
    assert (comparison["paired"], comparison["b_better"], comparison["b_worse"], comparison["ties"]) == (3, 2, 0, 1)
    assert comparison["p_value"] == 0.5
    assert results.sign_test(6, 0) == pytest.approx(0.03125) and results.sign_test(0, 0) == 1.0
    assert [results.diagnose(r) for r in a] == ["retrieval", "generation", "ok", "not scored"]
    assert results.diagnose(b[3]) == "app error"

    report = results.render_report({"A": a, "B": b})
    assert "| correctness | 0.33 (n=3) | 1.00 (n=3) |" in report
    assert "| correctness | 3 | 2 | 0 | 1 | 0.50 |" in report
    assert "| A | 1 | 1 | 1 | 1 |" in report  # ok, retrieval, generation, other
    assert "### q3" not in report  # los dos aciertan con las mismas puntuaciones: no hay que leerla
    assert "B: 1 examples ended with an error" in report and "A: 1 judgements of correctness failed" in report
    assert "no difference demonstrated" in report and "A signal, not evidence" in report


def test_results_downloads_runs_feedback_and_traces(monkeypatch, tmp_path):
    results = load_example("results", monkeypatch)
    start = datetime(2026, 10, 22, tzinfo=UTC)
    example_id, trace_id = uuid4(), uuid4()
    root = SimpleNamespace(
        id=trace_id, trace_id=trace_id, parent_run_id=None, name="RAG · k=3", run_type="chain",
        inputs={"question": "¿Cuánto debo?"}, outputs={"answer": "824.000 pesos", "input_tokens": 900, "output_tokens": 80},
        error=None, start_time=start, end_time=start + timedelta(seconds=2), reference_example_id=example_id,
        prompt_tokens=None, completion_tokens=None,
    )
    step = SimpleNamespace(
        id=uuid4(), trace_id=trace_id, parent_run_id=trace_id, name="retrieve · k=3", run_type="retriever",
        inputs={"question": "¿Cuánto debo?"}, outputs={"output": []}, error=None,
        start_time=start, end_time=start + timedelta(seconds=0.1),
    )
    example = SimpleNamespace(id=example_id, dataset_id="ds", metadata={"id": "q02"}, outputs=REFERENCE)

    class FakeClient:
        def list_runs(self, project_name):
            assert project_name == "exp-a"
            return iter([root, step])

        def list_feedback(self, run_ids):
            assert run_ids == [trace_id]
            return iter([SimpleNamespace(run_id=trace_id, key="correctness", score=1.0, comment="ok")])

        def read_example(self, example_id):
            return example

        def list_examples(self, dataset_id):
            return iter([example])

    rows, traces = results.fetch_experiment(FakeClient(), "exp-a")
    assert rows[0]["id"] == "q02" and rows[0]["reference"] == REFERENCE["reference"]
    assert rows[0]["scores"] == {"correctness": 1.0} and rows[0]["input_tokens"] == 900
    assert rows[0]["steps"] == {"retrieve · k=3": 0.1} and len(traces) == 2

    out = results.write_results({"exp-a": rows}, traces, folder=tmp_path)
    assert {path.name for path in out.iterdir()} == {"traces.jsonl", "rows.json", "report.md"}
    assert len((out / "traces.jsonl").read_text().splitlines()) == 2
    assert json.loads((out / "rows.json").read_text())["exp-a"][0]["id"] == "q02"


def test_results_read_langsmith_shapes_and_wait_for_late_feedback(monkeypatch):
    """Lo que devolvió LangSmith real: scores 1.0/0.0, inputs anidados y feedback que llega tarde."""
    results = load_example("results", monkeypatch)
    monkeypatch.setattr(results.time, "sleep", lambda seconds: None)
    retrieval_failed = row("A", "q05", {"retrieval_hit": 0.0, "correctness": 0.0, "citations_ok": 1.0},
                           comments={"correctness": "Falta separar el lote."})
    assert results.diagnose(retrieval_failed) == "retrieval"
    assert results.diagnose(row("A", "q1", {"retrieval_hit": 1.0, "correctness": 0.0})) == "generation"
    report = results.render_report({"A": [retrieval_failed]})
    assert "correctness: Falta separar el lote." in report and "citations_ok:" not in report

    trace_id = uuid4()
    root = SimpleNamespace(
        id=trace_id, trace_id=trace_id, parent_run_id=None, inputs={"inputs": {"question": "¿Cuánto debo?"}},
        outputs={"answer": "6"}, error=None, start_time=None, end_time=None, reference_example_id=None,
        prompt_tokens=10, completion_tokens=2, name="RAG", run_type="chain",
    )
    reads = []

    class LateFeedbackClient:
        def list_runs(self, project_name):
            return iter([root])

        def list_feedback(self, run_ids):
            reads.append(1)
            keys = ["correctness"] if len(reads) == 1 else ["correctness", "groundedness"]
            return iter([SimpleNamespace(run_id=trace_id, key=key, score=1.0, comment="") for key in keys])

    experiments, _ = results.download(LateFeedbackClient(), ["exp-a"], scores_per_row=2)
    assert len(reads) == 2 and set(experiments["exp-a"][0]["scores"]) == {"correctness", "groundedness"}
    assert experiments["exp-a"][0]["question"] == "¿Cuánto debo?"


def test_results_flags_empty_experiments_and_repetitions(monkeypatch):
    """Hallazgos de la revisión de @claude en el PR #41: experimento vacío y num_repetitions."""
    results = load_example("results", monkeypatch)

    class EmptyClient:
        def list_runs(self, project_name):
            return iter([])

        def list_feedback(self, run_ids):
            raise AssertionError("list_feedback(run_ids=[]) no filtra: no debe llamarse")

    assert results.fetch_experiment(EmptyClient(), "nombre-mal-escrito") == ([], [])
    repeated = [row("A", "q1", {"correctness": True}), row("A", "q1", {"correctness": False}),
                row("A", "q2", {"correctness": True})]
    notes = results.signals({"A": results.summarize(repeated), "B": results.summarize([])}, [])
    assert any("A: 1 repeated rows" in note for note in notes)
    assert any("B: no rows" in note for note in notes)


def test_results_cli_requires_experiments_and_accepts_scores():
    """Sin nombres, la CLI muestra el uso en vez de un reporte vacío; --scores llega a download()."""
    script = EXAMPLES / "results.py"
    empty = subprocess.run([sys.executable, script], capture_output=True, text=True, cwd=ROOT, check=False)
    assert empty.returncode == 2 and "usage:" in empty.stderr and "--scores" in empty.stderr
    source = script.read_text(encoding="utf-8")
    assert "report(Client(), args.experiments, scores_per_row=args.scores)" in source


def test_evaluation_example_prepares_data_without_the_model(monkeypatch):
    evaluation = load_example("evaluation", monkeypatch)
    questions = evaluation.load_questions()
    assert len(questions) == 22 and all(row["reference"] for row in questions)
    assert set(evaluation.QUESTION_IDS) <= {row["id"] for row in questions}
    labeled = evaluation.labeled_answers(questions)
    assert len(labeled) == 8 and {row["human"] for row in labeled} == {True, False}
    assert set(labeled[0]) == {"inputs", "outputs", "reference_outputs", "human", "note"}
    assert 0 < evaluation.MIN_AGREEMENT <= 1


def test_agent_evaluators_read_the_trajectory(monkeypatch):
    from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

    agents = load_example("agent_evaluators", monkeypatch)
    call = {"name": "check_credit", "args": {"customer": "C-3307", "product": "CLI"}, "id": "c1", "type": "tool_call"}
    messages = [HumanMessage("¿Cuánto debo?"), AIMessage("", tool_calls=[call]),
                ToolMessage('{"overdue": 2070000}', tool_call_id="c1", name="check_credit"),
                AIMessage("Tienes 2.070.000 COP vencidos.")]
    outputs = agents.agent_outputs(messages, route="collections")
    assert outputs["tool_calls"] == [{"name": "check_credit", "args": call["args"]}]
    assert outputs["executed_tools"] == ["check_credit"] and outputs["model_calls"] == 2

    reference = {"tools": ["check_credit"], "calls": [{"name": "check_credit", "args": {"customer": "c-3307"}}],
                 "forbidden_tools": ["request_disbursement"], "route": "collections", "max_model_calls": 3}
    scores = {e(outputs, reference)["key"]: e(outputs, reference)["score"] for e in agents.AGENT_EVALUATORS}
    assert scores == {"tools_called": True, "tool_args_match": True, "no_forbidden_tool": True,
                      "route_correct": True, "plan_covers": None, "calls_within": True}

    wrong = {"tools": ["search_documents"], "calls": [{"name": "check_credit", "args": {"customer": "C-1042"}}],
             "forbidden_tools": ["check_credit"], "route": "credit", "max_model_calls": 1}
    failed = {e(outputs, wrong)["key"]: e(outputs, wrong) for e in agents.AGENT_EVALUATORS}
    assert all(failed[key]["score"] is False for key in
               ("tools_called", "tool_args_match", "no_forbidden_tool", "route_correct", "calls_within"))
    assert "Missing: ['search_documents']" in failed["tools_called"]["comment"]
    assert failed["no_forbidden_tool"]["comment"] == "Executed: ['check_credit']"


def test_agent_evaluators_handle_rejected_calls_and_plans(monkeypatch):
    from langchain_core.messages import AIMessage, HumanMessage

    agents = load_example("agent_evaluators", monkeypatch)
    call = {"name": "request_disbursement", "args": {"amount_cop": 35_000_000}, "id": "c1", "type": "tool_call"}
    # Rechazada por la persona: hubo llamada, pero ninguna herramienta se ejecutó.
    outputs = agents.agent_outputs([HumanMessage("Desembolsa"), AIMessage("", tool_calls=[call]), AIMessage("No.")])
    assert agents.no_forbidden_tool(outputs, {"forbidden_tools": ["request_disbursement"]})["score"] is True
    plan = {"tasks": [{"policy": "collections"}, {"policy": "credit"}]}
    result = agents.plan_covers(plan, {"plan_sources": ["collections", "fees"]})
    assert result["score"] is False and result["comment"] == "Missing: ['fees']; Unexpected: ['credit']"
