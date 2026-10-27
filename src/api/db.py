import os
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, Request
from langgraph.checkpoint.postgres import PostgresSaver
from starlette.concurrency import run_in_threadpool


@asynccontextmanager
async def lifespan(app: FastAPI):
    db_uri = os.getenv("DB_URI")
    if not db_uri:
        raise RuntimeError("Set DB_URI before starting the API.")
    with PostgresSaver.from_conn_string(db_uri) as checkpointer:
        await run_in_threadpool(checkpointer.setup)
        app.state.checkpointer = checkpointer
        try:
            yield
        finally:
            app.state.checkpointer = None


def get_checkpointer(request: Request) -> PostgresSaver:
    checkpointer = getattr(request.app.state, "checkpointer", None)
    if checkpointer is None:
        raise RuntimeError("Checkpointer not initialized. Make sure lifespan is running.")
    return checkpointer


CheckpointerDep = Annotated[PostgresSaver, Depends(get_checkpointer)]
