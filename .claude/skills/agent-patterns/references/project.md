# This project: AdvancedGenAI course repository

Everything that ties the skill to this repository lives here and in `examples/project.py`. To reuse the skill elsewhere, rewrite these two files; the rest of the skill stays as is.

## Model and credentials

- `examples/project.py` builds `ChatAnthropic(model="claude-haiku-5-5", thinking={"type": "disabled"}, timeout=60, max_retries=2)`; `build_model(max_tokens=...)` sets the budget (500 for graph steps, 400 for the approval agent). No `temperature`: Haiku 5.5 rejects it. Do not switch to Sonnet or Opus on your own.
- A judge inside a loop gets `model.model_copy(update={"max_tokens": 1000})` and `with_structured_output(..., method="json_schema")`: it reasons before grading.
- Credentials: `load_dotenv(find_dotenv())` reads the repository `.env` (`ANTHROPIC_API_KEY`). Never write a key, never print `.env`.

## Where things live

- Generated graphs: `labs/<graph-name>/`, in a feature branch and its sibling worktree (`feature/<graph-name>`), never on `main`; see `AGENTS.md`.
- Sample documents: the synthetic ACME policies in `datasets/acme_*.pdf`, two pages each, read whole with `policy_text(name)`; `POLICY_FILES` maps credit, disbursement, fees and collections to their files. ACME is a fictional fintech; every figure is made up.
- To show a graph to the class, `uv run langgraph dev` serves the graphs listed in `langgraph.json` in LangGraph Studio. Registering a new graph there is the deploy-app skill's job.
- Install nothing outside uv. Everything the examples use is in `pyproject.toml`; if a package is really needed, propose `uv add` and wait.

## Budget and tracing

- LangSmith is off by default (`LANGSMITH_TRACING=false`) and the free tier has a monthly trace limit. Every top-level `invoke` or `stream` is one trace; a pause and its resume are two.
- `langsmith` reads `LANGSMITH_TRACING` and `LANGSMITH_PROJECT` once: switch them with `tracing_context(enabled=True, project_name=...)`, not `os.environ`.

## Controls the repository enforces

- Hook `.claude/hooks/check_app.py`: after every edit of a Python file under `labs/`, checks syntax, `ruff`, no `temperature=` and no literal API key. If it fails, the message comes back to you: fix that and continue.
- Permissions in `.claude/settings.json` ask before running `labs/` and the skill examples: that is the "explicit yes" of a paid run, enforced by the harness.
- Offline tests of every example, with fake models: `uv run --group quality python -m pytest -q tests/test_agent_patterns.py`.

## The course behind each pattern

The examples follow the course notebooks, which use the same ACME case and model. All six were run once on 2026-10-27 with tracing off: the chain took 4 calls (the gate stopped the out-of-scope message after 1); the router chose the 3 expected routes where the keyword rule sent all of them to `credit`; the three reviewers rejected the bad draft in 2.0 s of wall time, and `tone` judged the content although its prompt says not to; the approval graph followed each decision and the rejected agent call never ran; the plan split the ticket into the expected collections and fees tasks; the evaluator loop ended at its cap in three runs: the generator stayed a few words over the 90-word limit (best case 96, citations not counted) although the feedback gave it the exact count, so the judge was never reached. Haiku does not count words reliably: the count belongs in code, and the limit should leave room or be checked with the person.

| Example | Week · notebook |
|---|---|
| State, nodes, edges, reducers, `MessagesState` | 8 · L15, L16 (concepts; no example needed) |
| `graph_chain.py` | 8 · L17 |
| `graph_router.py` | 8 · L18 |
| `graph_parallel.py` | 8 · L19 |
| `approval.py` | 9 · L20 |
| `orchestrator.py` | 10 · L21 |
| `evaluator_loop.py` | 11 · L22 |
