# Gotchas: symptom → cause → fix

Observed with `fastapi`, `langgraph` 1.2, `langgraph-checkpoint-postgres` 3 and PostgreSQL 15.

| Symptom | Cause | Fix |
|---|---|---|
| `RuntimeError: Set DB_URI before starting the API` (course API) | `.env` has no `DB_URI` | Copy it from `.env.example`; the skill's example falls back to memory instead |
| Connection refused on startup | PostgreSQL is not up yet | `docker compose up -d --wait postgres`, then start the API |
| Permission error while creating the checkpoint tables | `setup()` needs schema privileges | Use a user that can create tables, or run `setup()` once with one |
| The API still connects to PostgreSQL after `env -u DB_URI` | The project adapter loads `.env`, which sets it again | Start it with `DB_URI=` (empty): loading `.env` does not override a variable that already exists |
| The conversation is lost after a restart | The API is running with `InMemorySaver` | Set `DB_URI`; check the startup log |
| Two conversations share history | The same `thread_id` for both, such as a customer code | One `chat_id` per conversation |
| `RuntimeError: Checkpointer not initialized` in a test | The test client was created without running the lifespan | Use `with TestClient(app) as client:`, or override the dependency |
| The event loop blocks during a turn | An `async def` route calls the synchronous graph | Use `def` routes (worker threads) or the async graph and saver throughout |
| Tool results appear in the stream | The generator does not filter by node | Keep only `metadata["langgraph_node"] == "model"` |
| Some frames carry a list instead of text | The provider sends content blocks | Send them as is; the client joins the `text` of each block |
| Empty `data:` frames | Chunks with no content (tool-call deltas) | Skip chunks whose `content` is empty |
| Two simultaneous turns on one thread interleave | The demo does not serialize turns per thread | Send turns sequentially per `chat_id`, or add a lock per thread |
| Port 5432 already in use | Another PostgreSQL on the machine | Stop it, or map another port in Compose and in `DB_URI` |
| Studio does not show the new graph | It is not in `langgraph.json`, or the module fails at import | Register `module.py:agent` and run the startup check |
| Studio's threads are not the API's threads | Studio has its own persistence | Expected; test memory through the API |
| The first answer takes much longer | The local embeddings model downloads on first use (~220 MB) | Run one turn before class or warm it at startup |
