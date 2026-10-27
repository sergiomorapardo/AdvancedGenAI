import json

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field

from agents.acme import make_graph
from api.db import CheckpointerDep, lifespan

app = FastAPI(lifespan=lifespan)


@app.get("/health")
def health():
    return {"status": "ok"}


class Message(BaseModel):
    message: str = Field(min_length=1)


@app.post("/chat/{chat_id}")
def chat(chat_id: str, item: Message, checkpointer: CheckpointerDep):
    config = {"configurable": {"thread_id": chat_id}}
    agent = make_graph(checkpointer=checkpointer)
    response = agent.invoke({"messages": [HumanMessage(content=item.message)]}, config)
    return response["messages"]


@app.post("/chat/{chat_id}/stream")
def stream_chat(chat_id: str, message: Message, checkpointer: CheckpointerDep):
    human_message = HumanMessage(content=message.message)

    # A sync iterator runs in Starlette's thread pool, like the nonstreaming route.
    def generate_response():
        agent = make_graph(checkpointer=checkpointer)
        for message_chunk, metadata in agent.stream(
            {"messages": [human_message]},
            config={"configurable": {"thread_id": chat_id}},
            stream_mode="messages",
        ):
            # Only the agent's "model" node writes to the customer; tool results stay internal.
            if metadata.get("langgraph_node") != "model":
                continue
            if message_chunk.content:
                payload = json.dumps({"content": message_chunk.content}, ensure_ascii=False)
                yield f"data: {payload}\n\n"

    return StreamingResponse(generate_response(), media_type="text/event-stream")
