---
name: ops-traces
description: Reads what an LLM app left in LangSmith, read only: how many traces and model calls a run made, how long each trace and node took, what it cost, which branch a graph took, whether two branches ran in parallel and what failed, with a link to every trace. Downloads the runs of a project with client.runs.query, rebuilds each tree, writes a report with tables and charts, and checks a traced run before it is repeated. Use it for "what did this run leave in LangSmith?", "how many traces", "why is it slow", "runs.query", "get_run_stats", "¿cuántas trazas quedaron?", "revisar las trazas", "¿por qué tarda?", "cuánto costó la corrida", /ops-traces. Not for comparing experiments of a dataset (use eval-experiments), turning tracing on in an app (the skill that builds it) or deleting traces, which needs the person's approval.
---

# Read traces in LangSmith

A traced run leaves a **trace** per top-level `invoke`: a tree of runs whose root is the app or the graph, with its nodes and, inside them, the model calls, parsers and retrievers. Reading that tree from Python answers with data what the LangSmith UI shows one trace at a time. Reading is free: no model calls, no new traces, only the LangSmith API.

## Flow

Copy this checklist into your answer and tick it as you go:

```
- [ ] 0. Project            → read references/project.md (key, project names, price, budget)
- [ ] 1. Scope: which project, since when, and what question the reading must answer
- [ ] 2. Read               → read references/reading.md; run references/examples/traces.py or reuse its functions
- [ ] 3. Check the reading: trace and call counts against what the run should have made
- [ ] 4. If something is off → references/gotchas.md
- [ ] 5. Delivery: report path, the table, the charts, the links and the answer to the question
```

## What to open and when

| Phase or question | Open |
|---|---|
| Credentials, how projects are named here, price and trace budget | `references/project.md` |
| How to query runs, rebuild a tree, read graph nodes, prove parallelism, find errors, and what to conclude | `references/reading.md` |
| An empty result, a missing trace, a deprecation warning, a delete that does not happen | `references/gotchas.md` |

## Verified example

| Piece | Example |
|---|---|
| Read every run of a project since a date, one row per trace with model calls, tokens, cost and link, the tree of a trace, the path of nodes of each graph run, overlap of two branches, errors, `report.md` and charts | `references/examples/traces.py` |
| The only file that knows this project: credentials and model price | `references/examples/project.py` |

From the repo root: `uv run python .claude/skills/ops-traces/references/examples/traces.py <project> --days 30`. In a notebook, import its functions and `await` nothing: `read_runs` already handles the running event loop.

## What is never skipped

1. **Read only.** This skill never creates traces, calls a model or writes to LangSmith. Deleting traces or projects is a separate action that needs the person's explicit "yes" for that exact deletion.
2. **Count before a repeat.** Before a traced run is repeated, read what the previous one left and say whether the new run would duplicate it.
3. **Always a time window.** `runs.query` without `min_start_time` returns only the most recent runs; pass the window explicitly and say which one you used.
4. **Links, not screenshots.** Every trace and error in the report carries its URL (`{project.url}/r/{run_id}?poll=true`), so the person can open it.
5. **The raw runs stay on the machine.** `runs.jsonl` holds inputs and outputs: it lives in `results/`, which is ignored by Git, and is never pasted whole into a chat or a PR.
6. **Compare with what was expected.** A count of traces and model calls means something only next to what the run should have made; say both.
