"""TODO: one sentence with the goal of this app.

Run from the repo root:
    uv run python labs/TODO-app-name/app.py
Cost: TODO model calls to the project model. LangSmith: TODO traces only if LANGSMITH_TRACING=true.

Delete the blocks the blueprint does not use (CHAIN or AGENT, JINJA, TOOLS, RAG, CONVERSATION).
project.py and run_log.py are copied as is next to this file. Evaluating the app is another skill.
"""

import json
from datetime import datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined
from langchain.agents import create_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from project import build_model
from pydantic import BaseModel, Field
from run_log import RunLog

# --- JINJA: versioned templates next to this file, strict about missing data -------------
TEMPLATES = Environment(
    loader=FileSystemLoader(Path(__file__).resolve().parent / "prompts"),
    undefined=StrictUndefined,
    trim_blocks=True,
    lstrip_blocks=True,
)

MESSAGES = ChatPromptTemplate.from_messages([
    ("system", "{system_prompt}"),
    ("human", "{user_message}"),  # the user message is data, never rendered with Jinja
])


# --- OUTPUT: the fields that people or code will read ------------------------------------
class Result(BaseModel):
    """TODO: what this result describes."""

    answer: str = Field(description="TODO")
    issues: list[str] = Field(description="Missing or ambiguous data. Empty if none.")


# --- TOOLS: read only, errors returned as data --------------------------------------------
DATA = [
    # TODO: 8-12 synthetic rows, with one or two traps (a zero balance, a missing customer).
]


@tool(parse_docstring=True)
def lookup_data(key: str) -> dict:
    """TODO: what it looks up. Read only.

    Args:
        key: TODO accepted values, listed explicitly.
    """
    for row in DATA:
        if row["key"].lower() == key.lower():
            return {"status": "ok", **row}
    return {"status": "not_found", "message": f"No record of '{key}'."}


# --- RAG: answers from documents with [file, p. N] citations -------------------------------
# Copy load_pages, split, format_context, PROMPT, build_rag and check_citations from
# references/examples/rag.py; for FAISS or Chroma, the builder from vector_store.py.
DOCUMENTS = Path(__file__).resolve().parent / "documents"  # TODO: synthetic or authorized PDFs


SYSTEM_PROMPT = (
    "TODO: role. Always look up the data with the tools before answering. "
    "Use only the figures the tools return. If they do not find the data, say so."
)


def check_answer(messages: list) -> bool:
    """TODO: deterministic check that the answer uses the tool's data."""
    results = [json.loads(m.content) for m in messages if m.type == "tool"]
    return any(r["status"] == "ok" for r in results)


def main():
    model = build_model()
    run_log = RunLog(Path(__file__).resolve().parent / "runs")

    # --- CHAIN: fixed steps --------------------------------------------------------------
    messages = MESSAGES.format_messages(
        system_prompt=TEMPLATES.get_template("TODO.jinja").render(today=datetime.now().astimezone().date().isoformat()),
        user_message="TODO",
    )
    result = model.with_structured_output(Result).invoke(messages, config={"callbacks": [run_log]})
    print(result.model_dump_json(indent=2))

    # --- AGENT: the model decides which tool to call -------------------------------------
    agent = create_agent(model, tools=[lookup_data], system_prompt=SYSTEM_PROMPT)
    state = agent.invoke(
        {"messages": [{"role": "user", "content": "TODO"}]},
        config={"callbacks": [run_log]},
    )
    print(state["messages"][-1].text)
    print("Answer matches the tool:", check_answer(state["messages"]))

    # --- RAG: retrieve, answer only with the fragments, check every citation -------------
    # embeddings = FastEmbedEmbeddings(model_name=EMBEDDINGS_MODEL)
    # store = InMemoryVectorStore.from_documents(split(load_pages(DOCUMENTS)), embeddings)
    # rag = build_rag(store.as_retriever(search_kwargs={"k": 3}), model)
    # result = rag.invoke("TODO", config={"callbacks": [run_log]})
    # print(result["answer"], "\nEvery citation was retrieved:", check_citations(result["answer"], result["docs"]))

    # --- CONVERSATION: follow-up questions -----------------------------------------------
    # Fixed steps: build_conversational_rag from conversational_rag.py, history kept by you.
    # Agent: build_agent from memory_agent.py with InMemorySaver() and one thread_id per conversation:
    # state = agent.invoke({"messages": [HumanMessage("TODO")]}, {"configurable": {"thread_id": "TODO"}, "callbacks": [run_log]})

    print(run_log.receipt())


if __name__ == "__main__":
    main()
