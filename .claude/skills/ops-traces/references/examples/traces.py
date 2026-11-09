"""Read every run of a LangSmith project and write a report with tables, charts and links.

Reading creates no traces and calls no model; it does use the LangSmith API, so LANGSMITH_API_KEY must be set.

Run from the repo root:
    uv run python .claude/skills/ops-traces/references/examples/traces.py PROJECT --days 30
Writes results/<timestamp>/ next to this file: runs.jsonl (every run with inputs and outputs: it stays on
the machine), traces.csv (one row per trace), report.md and the charts as PNG.
"""

import argparse
import asyncio
import json
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from langsmith import Client
from project import PRICE_PER_MILLION, configure

RESULTS = Path(__file__).resolve().parent / "results"
FIELDS = [
    "ID", "TRACE_ID", "PARENT_RUN_IDS", "DOTTED_ORDER", "IS_ROOT", "NAME", "RUN_TYPE", "STATUS",
    "START_TIME", "END_TIME", "LATENCY_SECONDS", "PROMPT_TOKENS", "COMPLETION_TOKENS", "TOTAL_TOKENS",
    "TAGS", "METADATA", "INPUTS", "OUTPUTS", "ERROR",
]


def run_async(coroutine):
    """asyncio.run, also from a notebook, whose event loop is already running."""
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coroutine)
    with ThreadPoolExecutor(1) as pool:
        return pool.submit(asyncio.run, coroutine).result()


def read_runs(client: Client, project, since: datetime) -> pd.DataFrame:
    """Every run of the project since a date, one row each, in tree order.

    client.runs.query is async and, without min_start_time, only looks at the most recent runs.
    Client.list_runs and get_run_url are retired after 2027-01-31: the link is built from the project url.
    """

    async def collect():
        return [
            run.model_dump()
            async for run in client.runs.query(
                project_ids=[str(project.id)], min_start_time=since, selects=FIELDS, page_size=100
            )
        ]

    runs = pd.DataFrame(run_async(collect()))
    if runs.empty:
        return runs
    runs = runs.sort_values("dotted_order", ignore_index=True)
    runs["id"] = runs["id"].astype(str)
    runs["depth"] = runs["parent_run_ids"].apply(lambda ids: len(ids or []))
    runs["parent"] = runs["parent_run_ids"].apply(lambda ids: str(ids[-1]) if ids else None)
    runs["url"] = runs["id"].apply(lambda run_id: f"{project.url}/r/{run_id}?poll=true")
    return runs


def label(row) -> str:
    """A readable name for a trace: its first text input, or the run name."""
    for value in (row["inputs"] or {}).values():
        if isinstance(value, str) and value.strip():
            return value.strip()[:80]
    return row["name"]


def summarize_traces(runs: pd.DataFrame) -> pd.DataFrame:
    """One row per trace (root run) with its model calls, tokens and cost summed from its llm runs."""
    llm = runs[runs["run_type"] == "llm"]
    usage = llm.groupby("trace_id")[["prompt_tokens", "completion_tokens"]].sum()
    usage["llm_calls"] = llm.groupby("trace_id").size()
    usage["cost_usd"] = (
        usage["prompt_tokens"] * PRICE_PER_MILLION["input"] + usage["completion_tokens"] * PRICE_PER_MILLION["output"]
    ) / 1e6
    roots = runs[runs["is_root"]].drop(columns=["prompt_tokens", "completion_tokens"])
    traces = roots.join(usage, on="trace_id").fillna({"prompt_tokens": 0, "completion_tokens": 0, "llm_calls": 0, "cost_usd": 0})
    traces["trace"] = traces.apply(label, axis=1)
    traces = traces.astype({"prompt_tokens": int, "completion_tokens": int, "llm_calls": int})
    columns = ["trace", "name", "status", "start_time", "latency_seconds", "llm_calls", "prompt_tokens",
               "completion_tokens", "cost_usd", "url", "trace_id"]
    return traces.sort_values("start_time", ignore_index=True)[columns]


def tree(runs: pd.DataFrame, trace_id) -> list[str]:
    """The runs of one trace, indented under their parent, with seconds and tokens of each model call."""
    lines = []
    for row in runs[runs["trace_id"] == trace_id].itertuples():
        tokens = f" · {row.prompt_tokens:.0f}+{row.completion_tokens:.0f} tokens" if row.run_type == "llm" else ""
        lines.append(f"{'    ' * row.depth}{row.name} [{row.run_type}] {row.latency_seconds:.2f} s{tokens}")
    return lines


def graph_nodes(runs: pd.DataFrame) -> pd.DataFrame:
    """The nodes of each LangGraph run: its direct children, without internal steps such as __start__."""
    graphs = runs[runs["name"] == "LangGraph"]
    return runs[runs["parent"].isin(graphs["id"]) & ~runs["name"].str.startswith("__")].copy()


def paths(runs: pd.DataFrame) -> pd.Series:
    """The path of nodes each graph run took, such as classify → look_up_stock → answer."""
    return graph_nodes(runs).groupby("trace_id")["name"].apply(" → ".join).rename("path")


def overlap(runs: pd.DataFrame, trace_id, first: str, second: str) -> bool:
    """Whether two runs of one trace ran at the same time: the proof that two branches were parallel."""
    trace = runs[runs["trace_id"] == trace_id]
    a, b = (trace[trace["name"] == name].iloc[0] for name in (first, second))
    return min(a["end_time"], b["end_time"]) > max(a["start_time"], b["start_time"])


def errors(runs: pd.DataFrame) -> pd.DataFrame:
    failed = runs[runs["status"] == "error"].copy()
    failed["message"] = failed["error"].apply(lambda text: str(text).strip().splitlines()[0][:160] if text else "")
    return failed[["name", "run_type", "depth", "message", "url"]]


def plot(traces: pd.DataFrame, nodes: pd.DataFrame, folder: Path) -> list[Path]:
    """Latency and tokens per trace, and mean latency per node. Labels are numbered: inputs may repeat."""
    charts = []
    labels = [f"{number}. {text[:40]}" for number, text in enumerate(traces["trace"], 1)]
    fig, (left, right) = plt.subplots(1, 2, figsize=(13, max(3, 0.4 * len(traces))), sharey=True)
    left.barh(labels, traces["latency_seconds"], color="#5c6bc0")
    left.set_xlabel("seconds")
    left.set_title("Latency per trace")
    right.barh(labels, traces["prompt_tokens"], color="#ffab91", label="input")
    right.barh(labels, traces["completion_tokens"], left=traces["prompt_tokens"], color="#bf360c", label="output")
    right.set_xlabel("tokens")
    right.set_title("Tokens per trace")
    right.legend()
    left.invert_yaxis()
    fig.tight_layout()
    charts.append(folder / "traces.png")
    fig.savefig(charts[-1])
    plt.close(fig)
    if not nodes.empty:
        latency = nodes.groupby("name")["latency_seconds"].mean().sort_values()
        ax = latency.plot.barh(figsize=(8, max(3, 0.4 * len(latency))), color="#2e7d32")
        ax.set_xlabel("seconds, mean")
        ax.set_title("Latency per node")
        ax.figure.tight_layout()
        charts.append(folder / "nodes.png")
        ax.figure.savefig(charts[-1])
        plt.close(ax.figure)
    return charts


def render_report(project_name: str, project_url: str, runs: pd.DataFrame, traces: pd.DataFrame) -> str:
    failed = errors(runs)
    totals = traces[["llm_calls", "prompt_tokens", "completion_tokens", "cost_usd"]].sum()
    lines = [
        f"# Traces of {project_name}", "",
        (
            f"[Open the project]({project_url}) · {len(runs)} runs in {len(traces)} traces · "
            f"{int(totals['llm_calls'])} model calls · {int(totals['prompt_tokens'])} input and "
            f"{int(totals['completion_tokens'])} output tokens · US${totals['cost_usd']:.4f} · {len(failed)} runs with errors"
        ),
        "",
        "| # | Trace | Status | Seconds | Model calls | Tokens in/out | USD |", "|---|---|---|---|---|---|---|",
    ]
    for number, row in enumerate(traces.itertuples(), 1):
        lines.append(f"| {number} | [{row.trace}]({row.url}) | {row.status} | {row.latency_seconds:.1f} | {row.llm_calls} | "
                     f"{row.prompt_tokens}/{row.completion_tokens} | {row.cost_usd:.4f} |")
    if not failed.empty:
        lines += ["", "## Errors", ""] + [f"- [{row.name}]({row.url}): {row.message}" for row in failed.itertuples()]
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("project")
    parser.add_argument("--days", type=int, default=30)
    args = parser.parse_args()

    configure()
    client = Client()
    project = client.read_project(project_name=args.project)
    runs = read_runs(client, project, datetime.now(UTC) - timedelta(days=args.days))
    if runs.empty:
        print(f"No runs in {args.project} in the last {args.days} days.")
        return
    traces = summarize_traces(runs)
    folder = RESULTS / datetime.now(UTC).astimezone().strftime("%Y%m%d-%H%M%S")
    folder.mkdir(parents=True)
    runs.to_json(folder / "runs.jsonl", orient="records", lines=True, date_format="iso", default_handler=str)
    traces.to_csv(folder / "traces.csv", index=False)
    report = render_report(args.project, project.url, runs, traces)
    (folder / "report.md").write_text(report)
    charts = plot(traces, graph_nodes(runs), folder)
    print(report)
    print("Written:", folder, *[chart.name for chart in charts])
    print(json.dumps({"traces": len(traces), "runs": len(runs)}))


if __name__ == "__main__":
    main()
