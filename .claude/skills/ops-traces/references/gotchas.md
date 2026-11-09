# Gotchas: symptom → cause → fix

Observed with `langsmith` 0.14.

| Symptom | Cause | Fix |
|---|---|---|
| `client.runs.query` returns nothing for a project that has traces | Without `min_start_time` it only looks at the most recent runs | Pass `min_start_time`, for example the project's `start_time` or a window in days |
| `asyncio.run` fails inside a notebook | `client.runs.query` is async and the notebook's loop is already running | `run_async` from `traces.py`, or `async for` directly in the cell |
| Deprecation warning for `list_runs` or `get_run_url` | Both are retired after 2027-01-31 | `client.runs.query`; link `f"{project.url}/r/{run_id}?poll=true"` |
| An id does not match a feedback or example id | `runs.query` returns ids as text | Convert with `UUID(str(value))` |
| A trace that just ran is missing | LangSmith indexes new traces after a few seconds | Wait and read again; call `client.flush()` first when the run happened in the same process |
| A traced run printed that tracing is on but the project is empty | `.env` has the old `LANGCHAIN_TRACING_V2=false`, which wins over `LANGSMITH_TRACING=true` | The app must trace with `tracing_context(enabled=True, project_name=...)`; in `.env`, change both lines together |
| Some traces of a run are in the `.env` default project | A traced call ran outside `tracing_context(project_name=...)` | Fix the call in the app; read both projects to count the run |
| Two traces have the same label in a chart | Two invokes had the same input | Labels are numbered in `plot`; tell them apart by start time |
| A graph's path starts with `__start__` | LangGraph runs the edge function of a routing that starts at `START` as its own step | `graph_nodes` skips names that start with `__` |
| Runs deleted by id still appear hours later | `runs/delete` is queued | Expected; `delete_project` is immediate. Both only after an explicit "yes" |
| The cost column is 0 for every trace | The project has no `llm` runs (a graph without model calls) or tokens were not recorded | Check `run_type` in the tree; price only model calls |
