"""Piece: an agent that searches the documents and remembers each conversation by thread_id.

The retriever becomes a @tool whose docstring asks for a complete query: the agent decides whether
to search and writes the standalone question itself. A checkpointer keeps the messages of each
thread; another thread_id starts empty.

Run from the repo root:
    uv run python .claude/skills/agentic-workflow/references/examples/memory_agent.py
Cost: about 5 model calls to the project model (2 per turn that searches, 1 if the agent answers
with the fragments it already has); state a range, the agent decides. Embeddings run locally.
LangSmith: 3 traces only if LANGSMITH_TRACING=true; turns of one thread share its thread_id.
"""

from pathlib import Path

from langchain.agents import create_agent
from langchain_community.embeddings import FastEmbedEmbeddings
from langchain_core.documents import Document
from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langgraph.checkpoint.memory import InMemorySaver
from project import SAMPLE_DOCUMENTS, build_model
from pypdf import PdfReader
from run_log import RunLog

DOCUMENTS = SAMPLE_DOCUMENTS
EMBEDDINGS_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

SYSTEM_PROMPT = (
    "You are the support assistant of ACME, a fintech. "
    "To answer about credits, disbursements, payments or collections, always search the policies with the tool. "
    "Write the search as a complete question, with the product, the customer's situation and the topic, even when "
    "the user refers to earlier messages. Answer only with the fragments the tool returns and cite "
    "each fact as [file, p. N]. If they do not contain the answer, say it is not in the documents."
)


def load_chunks(folder: Path) -> list[Document]:
    pages = []
    for path in sorted(folder.glob("*.pdf")):
        for number, page in enumerate(PdfReader(path).pages, 1):
            pages.append(Document(page.extract_text(), metadata={"source": path.name, "page": number}))
    return RecursiveCharacterTextSplitter(chunk_size=400, chunk_overlap=60).split_documents(pages)


def format_context(docs: list[Document]) -> str:
    return "\n\n".join(
        f"[{doc.metadata['source']}, p. {doc.metadata['page']}]\n{doc.page_content}" for doc in docs
    )


def build_search_tool(retriever):
    @tool(parse_docstring=True)
    def search_documents(query: str) -> str:
        """Search the ACME policies: credit, disbursements, fees and payments, and collections. Read only.

        Args:
            query: complete question with the product, the customer's situation and the topic; no pronouns like "that".
        """
        return format_context(retriever.invoke(query))

    return search_documents


def build_agent(model, retriever, checkpointer=None):
    """Without a checkpointer every invoke starts from scratch; with one, each thread_id remembers."""
    return create_agent(
        model, tools=[build_search_tool(retriever)], system_prompt=SYSTEM_PROMPT, checkpointer=checkpointer
    )


def thread(thread_id: str) -> dict:
    # In an app, the thread_id comes from the user's session: two people must never share one.
    return {"configurable": {"thread_id": thread_id}}


def searches(messages: list) -> list[str]:
    """The queries the agent wrote for the tool: check that follow-ups became complete questions."""
    return [call["args"]["query"] for m in messages if m.type == "ai" for call in m.tool_calls]


def main():
    model = build_model(max_tokens=500)
    embeddings = FastEmbedEmbeddings(model_name=EMBEDDINGS_MODEL)
    retriever = InMemoryVectorStore.from_documents(load_chunks(DOCUMENTS), embeddings).as_retriever(
        search_kwargs={"k": 3}
    )
    # InMemorySaver lives in this process; production uses a database checkpointer (PostgresSaver).
    agent = build_agent(model, retriever, checkpointer=InMemorySaver())
    run_log = RunLog()
    conversation = thread("c-1042-arrears")

    for question in [
        "I am 45 days past due on my Crédito Libre Inversión. Can I restructure it?",
        "And meanwhile, will I be reported to the credit bureaus?",
    ]:
        state = agent.invoke({"messages": [HumanMessage(question)]}, conversation | {"callbacks": [run_log]})
        print(state["messages"][-1].text)
    print("Searches in the thread:", searches(state["messages"]))

    # Another thread does not know that customer: the checkpointer isolates conversations.
    other = agent.invoke(
        {"messages": [HumanMessage("And how many times can I do it?")]},
        thread("c-2210-new") | {"callbacks": [run_log]},
    )
    print(other["messages"][-1].text)
    for config in (conversation, thread("c-2210-new")):
        print(config["configurable"]["thread_id"], len(agent.get_state(config).values["messages"]), "messages")
    print(run_log.receipt())


if __name__ == "__main__":
    main()
