# Build: pieces and rules

## Pieces

- **Graph factory** (`examples/graph.py`): `make_graph(*, checkpointer=None, model=None)` returns a compiled graph. The API passes its checkpointer; tests pass a fake model. Compiling per request is cheap; the state lives in the checkpointer, not in the graph object.
- **Lifespan** (`examples/api.py`): opens the checkpointer once. `PostgresSaver.from_conn_string(uri)` as a context manager, `checkpointer.setup()` once (it creates the tables, so the database user needs schema privileges), and the saver in `app.state`. Without `DB_URI`, `InMemorySaver()` with a warning: threads die with the process.
- **Dependency**: `get_checkpointer(request)` reads `app.state` and fails loudly if the lifespan did not run; routes receive it as a parameter, so tests can override it.
- **Request model**: `Message(message: str = Field(min_length=1, max_length=...))`: an empty or huge message is rejected with 422 before any model call.
- **Complete answer**: `POST /chat/{chat_id}` → `graph.invoke({"messages": [HumanMessage(...)]}, {"configurable": {"thread_id": chat_id}})` → the saved history. A `def` route (not `async def`) runs in a worker thread, so the synchronous graph and saver never block the event loop.
- **Streaming**: `POST /chat/{chat_id}/stream` → `StreamingResponse(generator, media_type="text/event-stream")`; the generator iterates `graph.stream(..., stream_mode="messages")`, keeps only `metadata["langgraph_node"] == "model"` and non-empty `chunk.content`, and yields `data: {json}\n\n`. Content can be a string or a list of content blocks: send it as is and let the client join the text.
- **Health**: `GET /health` returns without building the graph or touching the model.
- **Cost per turn**: `turn_usage(messages)` sums `usage_metadata` of the AI messages after the last human message; log it with the `chat_id`.
- **Studio**: add `"<name>": "./path/to/module.py:agent"` to `langgraph.json`, where `agent = make_graph()` is a module-level compiled graph (it builds the model at import, so the module needs the key in `.env`). Then run the startup check.
- **Smoke client** (`examples/client.py`): health, two turns on a new thread, a stream on the same thread, and another thread that must not remember.

## Files

```
labs/<app-name>/
  README.md        # endpoints, how to run, what survives a restart, limits, cost per turn
  api.py           # from examples/api.py
  graph.py         # the app's factory (or an import of it)
  project.py       # copied from examples/project.py
  client.py        # from examples/client.py
```

## Rules that are not negotiable

1. One checkpointer per process, from the lifespan; never per request.
2. `thread_id` from the conversation, never from the customer or a constant.
3. Stream only the node that writes to the person.
4. Listen on `127.0.0.1` unless the person adds authentication and rate limits; say so in the README.
5. Credentials and `DB_URI` only through `project.py` and `.env`; never in responses or logs.
6. Do not remove the database volume, drop tables or reset threads to fix an error.
7. Names in English for files, functions and routes.
