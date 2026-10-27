"""Download the runs, traces and scores of LangSmith experiments and write a comparison report.

Reading from LangSmith creates no traces and calls no model. The report gives the figures and
the signals; the conclusion is written by a person (or by Claude following references/results.md).

Run from the repo root, with the experiment names printed by evaluate():
    uv run python .claude/skills/evaluate-app/references/examples/results.py EXP_A EXP_B --scores 5
--scores is the number of evaluators: feedback is stored late, so it waits until every row has them.
Writes results/<timestamp>/ next to this file: traces.jsonl (every run of every trace),
rows.json (one row per example) and report.md.
"""

import argparse
import json
import time
from collections import defaultdict
from datetime import datetime
from math import comb
from pathlib import Path
from statistics import mean, median

from langsmith import Client
from project import PRICE_PER_MILLION, configure

RESULTS = Path(__file__).resolve().parent / "results"
SMALL_SAMPLE = 20  # below this, a difference is a signal to read the cases, not evidence


# --- Download ---------------------------------------------------------------------------
def fetch_experiment(client: Client, name: str) -> tuple[list[dict], list[dict]]:
    """One row per example (root run + its feedback) and every run of its traces."""
    runs = list(client.list_runs(project_name=name))
    roots = [run for run in runs if run.parent_run_id is None]
    feedback = defaultdict(dict)
    # Without roots, list_feedback(run_ids=[]) would not filter: an empty experiment reads nothing.
    for item in client.list_feedback(run_ids=[run.id for run in roots]) if roots else []:
        feedback[item.run_id][item.key] = {"score": item.score, "comment": item.comment or ""}
    steps = defaultdict(list)
    for run in runs:
        if run.parent_run_id is not None:
            steps[run.trace_id].append(run)
    examples = {}
    if roots and roots[0].reference_example_id:  # the dataset gives each row its id and reference
        dataset_id = client.read_example(roots[0].reference_example_id).dataset_id
        examples = {example.id: example for example in client.list_examples(dataset_id=dataset_id)}
    rows = [
        _row(name, run, feedback[run.id], steps[run.trace_id], examples.get(run.reference_example_id))
        for run in roots
    ]
    return rows, [_trace_record(name, run) for run in runs]


def _seconds(run) -> float | None:
    return (run.end_time - run.start_time).total_seconds() if run.end_time and run.start_time else None


def _row(experiment: str, run, scores: dict, steps: list, example) -> dict:
    outputs = run.outputs or {}
    inputs = run.inputs or {}
    inputs = inputs.get("inputs", inputs)  # a @traceable target logs its argument by name
    return {
        "experiment": experiment,
        "example_id": str(run.reference_example_id),
        "id": (example.metadata or {}).get("id") if example else None,
        "question": inputs.get("question") or json.dumps(inputs, ensure_ascii=False),
        "answer": outputs.get("answer"),
        "reference": (example.outputs or {}).get("reference") if example else None,
        "error": run.error,
        "seconds": _seconds(run),
        "input_tokens": run.prompt_tokens or outputs.get("input_tokens") or 0,
        "output_tokens": run.completion_tokens or outputs.get("output_tokens") or 0,
        "scores": {key: value["score"] for key, value in scores.items()},
        "comments": {key: value["comment"] for key, value in scores.items()},
        "steps": {step.name: _seconds(step) for step in sorted(steps, key=lambda s: s.start_time)},
        "trace_id": str(run.trace_id),
    }


def _trace_record(experiment: str, run) -> dict:
    return {
        "experiment": experiment,
        "trace_id": str(run.trace_id),
        "run_id": str(run.id),
        "parent_run_id": str(run.parent_run_id) if run.parent_run_id else None,
        "name": run.name,
        "run_type": run.run_type,
        "inputs": run.inputs,
        "outputs": run.outputs,
        "error": run.error,
        "seconds": _seconds(run),
    }


# --- Figures ----------------------------------------------------------------------------
def summarize(rows: list[dict]) -> dict:
    """Mean of each evaluator over the rows that have a score, with how many rows that is."""
    keys = sorted({key for row in rows for key in row["scores"]})
    ok = [row for row in rows if not row["error"]]
    seconds = [row["seconds"] for row in ok if row["seconds"] is not None]
    cost = sum(
        row["input_tokens"] * PRICE_PER_MILLION["input"] + row["output_tokens"] * PRICE_PER_MILLION["output"]
        for row in ok
    ) / 1e6
    metrics = {}
    for key in keys:
        values = [float(row["scores"][key]) for row in ok if row["scores"].get(key) is not None]
        failures = sum(row["comments"].get(key, "").startswith("Invalid format") for row in ok)
        metrics[key] = {"mean": mean(values) if values else None, "n": len(values), "format_failures": failures}
    return {
        "rows": len(rows),
        "repeated": len(rows) - len({row["example_id"] for row in rows}),  # num_repetitions > 1
        "errors": len(rows) - len(ok),
        "metrics": metrics,
        "latency_median_s": median(seconds) if seconds else None,
        "latency_max_s": max(seconds) if seconds else None,
        "cost_usd": cost,
    }


def sign_test(wins: int, losses: int) -> float:
    """Two-sided exact sign test over the questions where the two experiments differ."""
    n = wins + losses
    if n == 0:
        return 1.0
    tail = sum(comb(n, k) for k in range(min(wins, losses) + 1)) / 2**n
    return min(1.0, 2 * tail)


def compare(rows_a: list[dict], rows_b: list[dict], key: str) -> dict:
    """Question by question: where B is better, worse or equal to A on one evaluator."""
    a = {row["example_id"]: row["scores"].get(key) for row in rows_a}
    b = {row["example_id"]: row["scores"].get(key) for row in rows_b}
    paired = [(a[i], b[i]) for i in a.keys() & b.keys() if a[i] is not None and b[i] is not None]
    wins = sum(float(y) > float(x) for x, y in paired)
    losses = sum(float(y) < float(x) for x, y in paired)
    return {"key": key, "paired": len(paired), "b_better": wins, "b_worse": losses,
            "ties": len(paired) - wins - losses, "p_value": sign_test(wins, losses)}


def diagnose(row: dict, retrieval_key: str = "retrieval_hit", answer_key: str = "correctness") -> str:
    """Where a wrong answer failed: retrieval (the page never arrived) or generation.

    LangSmith returns boolean scores as 1.0/0.0: compare with None, never with `is False`.
    """
    if row["error"]:
        return "app error"
    answer, retrieval = row["scores"].get(answer_key), row["scores"].get(retrieval_key)
    if answer is None:
        return "not scored"
    if answer:
        return "ok"
    if retrieval is None:
        return "wrong, no retrieval check"
    return "generation" if retrieval else "retrieval"


def signals(summaries: dict, comparisons: list[dict]) -> list[str]:
    """Facts the conclusion must take into account. They are rules, not a verdict."""
    notes = []
    for name, summary in summaries.items():
        if not summary["rows"]:
            notes.append(f"{name}: no rows; check the experiment name.")
        if summary["repeated"]:
            notes.append(f"{name}: {summary['repeated']} repeated rows (num_repetitions); the means use every "
                         "row, but the question-by-question comparison keeps one per question.")
        if summary["errors"]:
            notes.append(f"{name}: {summary['errors']} examples ended with an error; the experiment is incomplete.")
        for key, metric in summary["metrics"].items():
            if metric["format_failures"]:
                notes.append(f"{name}: {metric['format_failures']} judgements of {key} failed; read them by hand.")
    for item in comparisons:
        if item["paired"] < SMALL_SAMPLE:
            notes.append(f"{item['key']}: only {item['paired']} paired questions; one answer moves "
                         f"{100 / max(item['paired'], 1):.0f} points. A signal, not evidence.")
        if item["b_better"] + item["b_worse"] and item["p_value"] >= 0.05:
            notes.append(f"{item['key']}: B better in {item['b_better']} and worse in {item['b_worse']} "
                         f"(sign test p={item['p_value']:.2f}): no difference demonstrated.")
    return notes


# --- Report -----------------------------------------------------------------------------
def _fmt(value, digits=2):
    return "—" if value is None else f"{value:.{digits}f}"


def render_report(experiments: dict[str, list[dict]]) -> str:
    names = list(experiments)
    summaries = {name: summarize(rows) for name, rows in experiments.items()}
    keys = sorted({key for summary in summaries.values() for key in summary["metrics"]})
    lines = ["# Experiment report", "", f"Generated {datetime.now().astimezone():%Y-%m-%d %H:%M}.", "",
             "## Summary", "", "| Metric | " + " | ".join(names) + " |", "|---|" + "---|" * len(names)]
    for key in keys:
        metrics = [summaries[name]["metrics"].get(key, {}) for name in names]
        cells = [f"{_fmt(metric.get('mean'))} (n={metric.get('n', 0)})" for metric in metrics]
        lines.append(f"| {key} | " + " | ".join(cells) + " |")
    for label, field, digits in [("median latency (s)", "latency_median_s", 2), ("max latency (s)", "latency_max_s", 2),
                                 ("cost of the answers (USD)", "cost_usd", 4), ("errors", "errors", 0)]:
        lines.append(f"| {label} | " + " | ".join(_fmt(summaries[n][field], digits) for n in names) + " |")

    comparisons = []
    if len(names) == 2:
        a, b = names
        comparisons = [compare(experiments[a], experiments[b], key) for key in keys]
        lines += ["", f"## {b} against {a}, question by question", "",
                  "| Metric | paired | B better | B worse | ties | sign test p |", "|---|---|---|---|---|---|"]
        lines += [f"| {c['key']} | {c['paired']} | {c['b_better']} | {c['b_worse']} | {c['ties']} | {c['p_value']:.2f} |" for c in comparisons]

    lines += ["", "## Where the answers fail", "", "| Experiment | ok | retrieval | generation | other |", "|---|---|---|---|---|"]
    for name, rows in experiments.items():
        kinds = [diagnose(row) for row in rows]
        other = sum(kind not in {"ok", "retrieval", "generation"} for kind in kinds)
        lines.append(f"| {name} | {kinds.count('ok')} | {kinds.count('retrieval')} | {kinds.count('generation')} | {other} |")

    lines += ["", "## Questions to read", ""]
    by_example = defaultdict(dict)
    for name, rows in experiments.items():
        for row in rows:
            by_example[row["example_id"]][name] = row
    for cases in by_example.values():
        same_scores = len({json.dumps(row["scores"], sort_keys=True) for row in cases.values()}) == 1
        if same_scores and all(diagnose(row) == "ok" for row in cases.values()):
            continue  # nothing to learn from a question every experiment got right
        first = next(iter(cases.values()))
        lines += [f"### {first['id'] or first['example_id']}: {first['question']}", "", f"Reference: {first['reference']}", ""]
        for name, row in cases.items():
            failed = {key: row["comments"].get(key, "") for key, score in row["scores"].items()
                      if score is not None and not score}
            lines.append(f"- **{name}** ({diagnose(row)}): {row['answer'] or row['error']}")
            lines += [f"  - {key}: {comment[:300]}" for key, comment in failed.items() if comment]
        lines.append("")

    lines += ["## Signals for the conclusion", ""] + [f"- {note}" for note in signals(summaries, comparisons) or ["None."]]
    return "\n".join(lines) + "\n"


def write_results(experiments: dict[str, list[dict]], traces: list[dict], folder: Path = RESULTS) -> Path:
    out = folder / datetime.now().astimezone().strftime("%Y%m%d-%H%M%S")
    out.mkdir(parents=True, exist_ok=True)
    with (out / "traces.jsonl").open("w", encoding="utf-8") as file:
        for record in traces:
            file.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")
    (out / "rows.json").write_text(json.dumps(experiments, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    (out / "report.md").write_text(render_report(experiments), encoding="utf-8")
    return out


def download(client: Client, names: list[str], scores_per_row: int = 0, timeout: float = 120) -> tuple[dict, list]:
    """Download every experiment; wait until each row has its scores.

    LangSmith stores feedback asynchronously: read right after evaluate(), the last experiment
    may come back with rows still unscored, and the report would compare incomplete data.
    """
    deadline = time.monotonic() + timeout
    while True:
        experiments, traces = {}, []
        for name in names:
            experiments[name], records = fetch_experiment(client, name)
            traces += records
        pending = sum(len(row["scores"]) < scores_per_row for rows in experiments.values() for row in rows)
        if not pending:
            return experiments, traces
        if time.monotonic() > deadline:
            print(f"Warning: {pending} rows still without all their scores after {timeout:.0f} s.")
            return experiments, traces
        time.sleep(5)


def report(client: Client, names: list[str], scores_per_row: int = 0) -> Path:
    """Download the experiments, save their traces and print the report."""
    experiments, traces = download(client, names, scores_per_row)
    out = write_results(experiments, traces)
    print((out / "report.md").read_text(encoding="utf-8"))
    print("Saved in", out)
    return out


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download LangSmith experiments and write a report.")
    parser.add_argument("experiments", nargs="+", help="experiment names printed by evaluate()")
    parser.add_argument("--scores", type=int, default=0,
                        help="evaluators per row: wait until every row has them (right after evaluate)")
    args = parser.parse_args()
    configure()
    report(Client(), args.experiments, scores_per_row=args.scores)
