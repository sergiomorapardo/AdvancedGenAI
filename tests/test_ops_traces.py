"""Verifica la skill ops-traces sin LangSmith: corridas simuladas con la forma de client.runs.query."""

import importlib.util
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / ".claude/skills/ops-traces/references/examples"
START = datetime(2026, 10, 29, 15, tzinfo=UTC)


def load_example(name, monkeypatch):
    monkeypatch.syspath_prepend(str(EXAMPLES))
    monkeypatch.delitem(sys.modules, "project", raising=False)
    spec = importlib.util.spec_from_file_location(name, EXAMPLES / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run(run_id, name, run_type, parents, order, start, seconds, **extra):
    data = {
        "id": run_id, "trace_id": "t1", "parent_run_ids": parents, "dotted_order": order, "is_root": not parents,
        "name": name, "run_type": run_type, "status": "success", "start_time": START + timedelta(seconds=start),
        "end_time": START + timedelta(seconds=start + seconds), "latency_seconds": seconds,
        "prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0, "tags": [], "metadata": {},
        "inputs": {}, "outputs": {}, "error": None,
    }
    return SimpleNamespace(model_dump=lambda: data | extra)


# Un ticket de ACME: read_ticket, dos revisiones en paralelo y aggregate, con dos llamadas al modelo.
RUNS = [
    run("r", "LangGraph", "chain", [], "1", 0, 3.0, inputs={"request": "T-1043: cobro duplicado"}),
    run("a", "read_ticket", "chain", ["r"], "1.1", 0, 1.0),
    run("a1", "ChatAnthropic", "llm", ["r", "a"], "1.1.1", 0, 1.0, prompt_tokens=600, completion_tokens=80),
    run("b", "compliance", "chain", ["r"], "1.2", 1.0, 0.1),
    run("c", "accuracy", "chain", ["r"], "1.3", 1.0, 0.4),
    run("d", "aggregate", "chain", ["r"], "1.4", 1.5, 1.5, status="error", error="InvalidUpdateError: x\nmore"),
    run("d1", "ChatAnthropic", "llm", ["r", "d"], "1.4.1", 1.5, 1.4, prompt_tokens=400, completion_tokens=120),
]


class FakeClient:
    def __init__(self):
        self.queries = []
        self.runs = self

    def query(self, **kwargs):
        self.queries.append(kwargs)

        async def rows():
            for item in RUNS:
                yield item

        return rows()


def read(monkeypatch):
    traces = load_example("traces", monkeypatch)
    client = FakeClient()
    project = SimpleNamespace(id="p1", url="https://smith/p1")
    return traces, client, traces.read_runs(client, project, START), project


def test_read_runs_queries_from_a_date_and_builds_links(monkeypatch):
    _, client, runs, _ = read(monkeypatch)
    # Sin min_start_time la consulta solo mira lo más reciente.
    assert client.queries[0]["min_start_time"] == START and client.queries[0]["project_ids"] == ["p1"]
    assert list(runs["name"])[:3] == ["LangGraph", "read_ticket", "ChatAnthropic"]
    assert runs.loc[runs["id"] == "a1", "depth"].item() == 2
    assert runs.loc[runs["id"] == "r", "url"].item() == "https://smith/p1/r/r?poll=true"


def test_traces_sum_model_calls_tokens_and_cost(monkeypatch):
    traces, _, runs, _ = read(monkeypatch)
    [row] = traces.summarize_traces(runs).to_dict("records")
    assert row["trace"] == "T-1043: cobro duplicado" and row["llm_calls"] == 2
    assert (row["prompt_tokens"], row["completion_tokens"]) == (1000, 200)
    assert round(row["cost_usd"], 6) == round((1000 * 0.10 + 200 * 0.50) / 1e6, 6)


def test_tree_paths_overlap_and_errors(monkeypatch):
    traces, _, runs, _ = read(monkeypatch)
    lines = traces.tree(runs, "t1")
    assert lines[0].startswith("LangGraph [chain]") and lines[2] == "        ChatAnthropic [llm] 1.00 s · 600+80 tokens"
    assert traces.paths(runs)["t1"] == "read_ticket → compliance → accuracy → aggregate"
    assert traces.overlap(runs, "t1", "compliance", "accuracy")
    assert not traces.overlap(runs, "t1", "read_ticket", "aggregate")
    assert traces.errors(runs)["message"].tolist() == ["InvalidUpdateError: x"]


def test_report_and_charts_are_written(monkeypatch, tmp_path):
    traces, _, runs, project = read(monkeypatch)
    table = traces.summarize_traces(runs)
    report = traces.render_report("advancedgenai-l19", project.url, runs, table)
    assert "7 runs in 1 traces · 2 model calls" in report and "[T-1043: cobro duplicado](https://smith/p1/r/r?poll=true)" in report
    assert "## Errors" in report
    charts = traces.plot(table, traces.graph_nodes(runs), tmp_path)
    assert [chart.name for chart in charts] == ["traces.png", "nodes.png"] and all(c.exists() for c in charts)
