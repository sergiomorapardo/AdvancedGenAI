"""Piece: serve a LangGraph graph with FastAPI, one thread per chat_id, persistent memory and SSE streaming.

- lifespan opens ONE checkpointer per process: PostgresSaver when DB_URI is set (threads survive restarts),
  InMemorySaver otherwise (local trials only: threads die with the process).
- POST /chat/{chat_id} answers and returns the saved history; POST /chat/{chat_id}/stream sends SSE events.
- Only the "model" node streams to the client: tool results stay inside the graph.
- Each turn logs its model calls and tokens, the minimum to watch cost in production.

Run from the repo root (port 8001 keeps the course API free on 8000):
    uv run uvicorn --app-dir .claude/skills/deploy-app/references/examples api:app --host 127.0.0.1 --port 8001
Cost: 2 model calls per turn that uses the tool, 1 otherwise. LangSmith: 1 trace per turn if tracing is on.
"""

import json
import logging
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, Request
from fastapi.responses import StreamingResponse
from graph import make_graph
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import InMemorySaver
from project import database_uri
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool

logger = logging.getLogger("uvicorn.error")


@asynccontextmanager
async def lifespan(app: FastAPI):
    uri = database_uri()
    if not uri:
        logger.warning("DB_URI is not set: threads live in memory and die with the process.")
        app.state.checkpointer = InMemorySaver()
        yield
        return
    from langgraph.checkpoint.postgres import PostgresSaver

    with PostgresSaver.from_conn_string(uri) as checkpointer:
        await run_in_threadpool(checkpointer.setup)  # creates the checkpoint tables once
        app.state.checkpointer = checkpointer
        try:
            yield
        finally:
            app.state.checkpointer = None


def get_checkpointer(request: Request):
    checkpointer = getattr(request.app.state, "checkpointer", None)
    if checkpointer is None:
        raise RuntimeError("Checkpointer not initialized. Make sure lifespan is running.")
    return checkpointer


Checkpointer = Annotated[object, Depends(get_checkpointer)]
app = FastAPI(lifespan=lifespan)


class Message(BaseModel):
    message: str = Field(min_length=1, max_length=2000)


def turn_usage(messages: list) -> dict:
    """Model calls and tokens of the last turn: the AI messages after the last human message."""
    last_human = max(i for i, message in enumerate(messages) if message.type == "human")
    usage = [message.usage_metadata or {} for message in messages[last_human:] if message.type == "ai"]
    return {"model_calls": len(usage), "input_tokens": sum(u.get("input_tokens", 0) for u in usage),
            "output_tokens": sum(u.get("output_tokens", 0) for u in usage)}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/chat/{chat_id}")
def chat(chat_id: str, item: Message, checkpointer: Checkpointer):
    # A sync route runs in a worker thread, so the sync graph and saver do not block the event loop.
    config = {"configurable": {"thread_id": chat_id}}
    result = make_graph(checkpointer=checkpointer).invoke({"messages": [HumanMessage(item.message)]}, config)
    logger.info("chat %s %s", chat_id, json.dumps(turn_usage(result["messages"])))
    return result["messages"]


@app.post("/chat/{chat_id}/stream")
def stream_chat(chat_id: str, item: Message, checkpointer: Checkpointer):
    def events():
        graph = make_graph(checkpointer=checkpointer)
        for chunk, metadata in graph.stream({"messages": [HumanMessage(item.message)]},
                                            config={"configurable": {"thread_id": chat_id}}, stream_mode="messages"):
            if metadata.get("langgraph_node") != "model" or not chunk.content:
                continue  # tool results and empty chunks stay inside the graph
            yield f"data: {json.dumps({'content': chunk.content}, ensure_ascii=False)}\n\n"

    return StreamingResponse(events(), media_type="text/event-stream")
