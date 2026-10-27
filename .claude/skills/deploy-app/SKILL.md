---
name: deploy-app
description: Serves a LangChain or LangGraph app as an API and prepares it to run for other people: FastAPI with one thread per chat_id, a PostgreSQL checkpointer so conversations survive restarts, SSE streaming that hides tool output, Docker Compose for the database, registration in langgraph.json for LangGraph Studio, a startup check for CI, and the LLMOps basics (cost per turn, traces, evaluation before release, security limits). Asks one decision at a time, checks everything with fake models and an in-memory checkpointer, and runs the live API only after approval. Use when someone asks to deploy, serve, expose or productionize an agent ("make it an API", "FastAPI", "streaming", "SSE", "PostgresSaver", "persistent memory", "docker compose", "langgraph dev", "Studio", "LLMOps", "monitor cost", /deploy-app). Not for designing the app (agentic-workflow, agent-patterns) or for measuring its quality (evaluate-app).
---

# Deploy an LLM app

You and the person decide **what is served** (a graph factory), **where state lives** (a checkpointer and one thread per conversation), **how answers reach the client** (complete or streamed, and what is hidden), **who can call it** (network exposure and limits) and **how it is watched** (cost, traces, evaluation). The app itself was built before: this skill wraps it, it does not redesign it.

This file is the map. Open each reference when you reach its phase, in full, and not before.

## Flow

Copy this checklist into your answer and tick it as you go:

```
- [ ] 0. Project            → read references/project.md (model, database, ports, existing API)
- [ ] 1. Decisions           → read references/wizard.md (one decision per question)
- [ ] 2. Plan confirmed: endpoints, persistence, streaming, exposure, cost per turn
- [ ] 3. Build               → read references/build.md + examples/api.py and examples/graph.py
- [ ] 4. Offline checks      → read references/validation.md (fake model, in-memory threads)
- [ ] 5. Live run, only after an explicit "yes": database up, API up, smoke client
- [ ] 6. Operations          → read references/operations.md (cost, traces, evaluation, security)
- [ ] 7. If something fails  → references/gotchas.md, fix only that, back to step 4
- [ ] 8. Delivery: commands, endpoints, what survives a restart, limits, next step
```

## What to open and when

| Phase or question | Open |
|---|---|
| Model, credentials, the course API, database, ports, Studio, CI | `references/project.md` |
| What to decide: persistence, endpoints, streaming, exposure, observability | `references/wizard.md` |
| Which pieces to write and the rules that are not negotiable | `references/build.md` |
| Offline checks and the live run | `references/validation.md` |
| Cost per turn, traces, evaluation before release, monitoring, security | `references/operations.md` |
| An error symptom | `references/gotchas.md` |

## Examples

| File | What it gives |
|---|---|
| `references/examples/api.py` | FastAPI with a lifespan that opens one checkpointer (PostgreSQL or memory), `/health`, `/chat/{chat_id}`, `/chat/{chat_id}/stream` with SSE from the `model` node only, and the tokens of each turn in the log |
| `references/examples/graph.py` | The graph factory the API calls: `make_graph(*, checkpointer=None, model=None)` |
| `references/examples/client.py` | Smoke test of a running API: two turns on one thread, a stream and a second thread that must not remember |
| `references/examples/project.py` | The only file that knows the project: model, credentials, `DB_URI` |

## What is never skipped

1. **One checkpointer per process**, opened in the lifespan, passed to the graph factory. Never a new saver per request.
2. **One thread per conversation**: the `thread_id` comes from the client's `chat_id`, never shared between people.
3. **Tool output stays inside**: stream only the node that writes to the person.
4. **No public exposure without access control.** The examples listen on `127.0.0.1` and have no authentication: say so in the delivery.
5. **No live run without an explicit "yes"**: state the model calls per turn, the turns of the smoke test and the traces.
6. **Credentials and `DB_URI` from `.env`** through `project.py`; never in code, logs or responses.
7. **Measure before release**: an evaluation of the app (evaluate-app) and the cost of a typical turn, reported with the deployment.
8. **Never delete the database volume** to fix a problem: it holds the saved conversations.
