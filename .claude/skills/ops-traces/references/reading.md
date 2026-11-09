# Read a project and conclude

## Contents

- Query the runs
- One row per trace
- The tree of a trace
- Graph nodes, paths and parallel branches
- Errors
- What to conclude

## Query the runs

`client.runs.query(project_ids=[str(project.id)], min_start_time=since, selects=FIELDS, page_size=100)` returns every run of the project since `since`, with the fields listed in `selects`. It is async: `read_runs` in `traces.py` collects it with `run_async`, which also works inside a notebook. `Client.list_runs` and `get_run_url` stop working after 2027-01-31; do not use them.

- Ids come back as text. Convert them with `UUID(...)` before comparing them with other SDK objects (feedback, examples).
- Sort by `dotted_order`: runs then appear in the order they started, each under its parent. `parent_run_ids` lists the ancestors from the root down; its length is the depth.
- A run's link is `f"{project.url}/r/{run_id}?poll=true"`.
- `client.get_run_stats(project_ids=[project.id])` gives the totals of the project in one call (run count, p50 and p99 latency, tokens, error rate). It counts **every run**, not only traces.

## One row per trace

Roots (`is_root`) are traces: one `invoke` of an app or a graph, or a group opened with `trace(...)`. `summarize_traces` sums tokens over the model calls of each trace (`run_type == "llm"`) and prices them with `PRICE_PER_MILLION`, because LangSmith may not know the model's price. A trace without model calls costs 0 and takes milliseconds.

## The tree of a trace

`tree(runs, trace_id)` prints each run indented under its parent with its seconds and, for model calls, input and output tokens. Read it to see which steps ran and where the time went.

## Graph nodes, paths and parallel branches

- A compiled LangGraph names its root `LangGraph`; its direct children are the nodes. `graph_nodes` skips internal steps such as `__start__`, which runs the edge function when routing starts at `START`.
- `paths(runs)` gives the path of each graph run, such as `classify → look_up_stock → answer`: the branch the router took.
- The input and output of a deciding node (for example `classify`) are in its `inputs` and `outputs`: they show what it decided and why.
- `overlap(runs, trace_id, "verify_stock", "verify_documents")` is `True` when the two runs share time: the evidence that fan-out branches ran in parallel. With slow sources, the wait is the slowest branch, not the sum.

## Errors

`errors(runs)` lists the runs with `status == "error"`, their depth and the first line of the message. The root and the run that raised it both carry the error; open the deepest one first.

## What to conclude

- **Counts against expectations.** Traces = top-level invokes the run should have made; model calls = what the app's docstring or README states. A larger count means a retry, an extra branch or a trace that escaped its project; a smaller one, a run that did not trace.
- **Latency.** Name the slowest traces and nodes, and whether the time is in model calls, retrieval (local embeddings) or the network.
- **Cost.** Total and per trace, with the price used. Say it is an estimate from tokens.
- **Duplicates.** If the project already has the traces of the same run, a repeat duplicates them: say it before the person approves the next traced run.
- **Read two traces by hand** before concluding from averages: the table says where to look, the tree says what happened.

Deliver the path of `report.md`, the trace table, the charts, the links of the traces that answer the question, and the answer itself in two or three sentences.
