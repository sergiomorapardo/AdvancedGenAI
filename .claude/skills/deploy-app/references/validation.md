# Check, run and deliver

## 1. Offline checks (no model, no database)

With FastAPI's `TestClient`, a fake model (`GenericFakeChatModel` with `bind_tools` returning itself) and no `DB_URI`, so the lifespan opens an `InMemorySaver` (see `tests/test_deploy_app.py`):

1. `GET /health` answers without building the graph.
2. `POST /chat/{chat_id}` twice on the same id: the second history contains the first turn. Another id starts empty.
3. `POST /chat/{chat_id}/stream` with a fake graph whose `stream` yields chunks from the `tools` and `model` nodes (a fake chat model drops `tool_calls` when it streams): every frame is `data: {...}`, only non-empty `model` chunks arrive, content blocks pass as they are.
4. An empty message gets 422 and makes no model call.
5. `turn_usage` counts only the last turn.
6. If the graph is registered for Studio: the project's startup check (`references/project.md`), which loads every graph without model calls.

## 2. The live run

Before running, tell the person: the commands, the turns of the smoke client and their model calls (1 per turn, 2 when the tool is used: about 5 in `client.py`), the traces (0 with tracing off) and that the first run may download models. Wait for an explicit "yes".

```
docker compose up -d postgres            # with DB_URI; for in-memory threads start the API with DB_URI= instead
uv run uvicorn --app-dir labs/<app-name> api:app --host 127.0.0.1 --port 8001
uv run python labs/<app-name>/client.py http://127.0.0.1:8001
```

Check, in this order:

1. The API log says which checkpointer it opened (PostgreSQL, or the in-memory warning).
2. The client prints "Memory per thread: True".
3. Restart the API and send one more turn on the same `chat_id`: with PostgreSQL the history is still there.
4. The log shows the model calls and tokens of every turn.
5. The checkpoint query of `references/project.md`, with the thread id, lists its checkpoints (PostgreSQL only).

Stop the API at the end. Leave the database running or stop it with `docker compose down`, which keeps the volume.

## 3. Delivery

The commands, the endpoints with one example each, what survives a restart, the limits (no authentication, loopback only, sequential turns per thread), the cost of a typical turn from the log, and one next step: evaluate the app before release (evaluate-app) or register it in Studio.
