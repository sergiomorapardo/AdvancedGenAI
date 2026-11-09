# This project: AdvancedGenAI course repository

Everything that ties the skill to this repository lives here and in `examples/project.py`. To reuse the skill elsewhere, rewrite these two files; the rest of the skill stays as is.

## Model, credentials and database

- `examples/project.py` builds `ChatAnthropic(model="claude-haiku-5-5", thinking={"type": "disabled"}, timeout=60, max_retries=2)` and reads `DB_URI`. No `temperature`: Haiku 5.5 rejects it. Do not switch to a bigger model on your own.
- Credentials and `DB_URI` come from the repository `.env`, with the variables and order of `.env.example`. Never write them in code, never print `.env`.
- Database: `docker compose up -d postgres` starts PostgreSQL 15 on `127.0.0.1:5432` with demo-only credentials and the `postgres_data` volume. `docker compose down` keeps the volume; removing it deletes every saved conversation and needs the person's approval.

## The course API

- `src/api/main.py` and `src/api/db.py` serve the ACME agent (`src/agents/acme.py`: cited policy search, the read-only credit portfolio and memory) with `PostgresSaver`. It is the reference implementation of this skill; `examples/api.py` is the same shape, self-contained, with an in-memory fallback and token logging.
- Run it: `uv sync --locked --no-dev`, `docker compose up -d postgres`, `uv run --no-sync uvicorn api.main:app --host 127.0.0.1 --port 8000`. Endpoint schemas at `http://127.0.0.1:8000/docs`.
- `docs/sql/checkpoints.sql` lists the checkpoints of one thread.
- Its offline tests: `tests/test_api.py` (fake graph, fake checkpointer).

## Studio and CI

- `langgraph.json` registers the graphs that `uv run langgraph dev` opens in LangGraph Studio; each entry points to a module-level compiled graph (`"acme": "./src/agents/acme.py:agent"`). Studio manages its own persistence, apart from the API's database.
- CI (`.github/workflows/ci.yml`): `unit-tests` runs the offline tests; `langgraph-startup` starts the real `langgraph dev` with placeholder credentials and checks that every graph in `langgraph.json` loads, without calling a model. Both are required to merge into `main`. Run it locally with `uv run --no-sync python .github/scripts/check_langgraph_startup.py`.

## Budget and tracing

- Every turn calls a paid model: 1 call, or 2 when the agent uses a tool. The first policy search of the ACME agent downloads the local embeddings model (~220 MB).
- LangSmith is off by default (`LANGSMITH_TRACING=false`); with it on, every turn is one trace against a monthly limit. Use one project per environment (`tracing_context(project_name=...)` or `LANGSMITH_PROJECT` before start), never the course's evaluation projects.

## Controls the repository enforces

- Permissions in `.claude/settings.json` ask before running the skill examples: that is the "explicit yes" of a live run, enforced by the harness.
- Offline tests of the examples: `uv run --group quality python -m pytest -q tests/test_deploy_app.py`.

## The course behind this skill

Week 12 (LLMOps and deployment): the "Local support chat API" section of the README and the W12 presentation. `examples/api.py` and `client.py` were run once on 2026-10-27 with in-memory threads: two turns on one thread (6 messages, the second turn remembered the first), a stream, and a second thread that started empty; 2, 1 and 1 model calls per turn in the log.
