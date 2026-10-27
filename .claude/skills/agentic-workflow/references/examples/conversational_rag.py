"""Piece: conversational RAG. Rewrite the follow-up into a standalone question, then retrieve.

A follow-up such as "And after that, who decides?" has no product or topic: retrieving with it
brings the wrong fragments. The chain rewrites it with the history (prompt chaining: rewrite →
retrieve → answer) and, for colloquial questions, multi-query searches with several versions.

Run from the repo root:
    uv run python .claude/skills/agentic-workflow/references/examples/conversational_rag.py
Cost: 5 model calls to the project model: 1 answer, 2 for the follow-up (rewrite + answer) and
2 for multi-query (versions + answer). Embeddings run locally, at no cost.
LangSmith: 3 traces only if LANGSMITH_TRACING=true (one per top-level invoke).
"""

import re
from pathlib import Path

from langchain_community.embeddings import FastEmbedEmbeddings
from langchain_core.documents import Document
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import chain
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter
from project import SAMPLE_DOCUMENTS, build_model
from pydantic import BaseModel, Field
from pypdf import PdfReader
from run_log import RunLog

DOCUMENTS = SAMPLE_DOCUMENTS
EMBEDDINGS_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

SYSTEM_PROMPT = (
    "You are the support assistant of ACME, a fintech. "
    "Answer only with the information in the document fragments you receive. "
    "After each fact, cite its source as [file, p. N], exactly as it appears in the fragment. "
    "If the fragments do not contain the answer, say it is not in the documents and do not make it up."
)
REWRITE_PROMPT = (
    "Rewrite the user's last question as a complete question that can be understood without the "
    "conversation. It will be used to search the ACME policies. Include the product, the customer's "
    "situation, the amounts and the deadlines the question refers to. "
    "Do not answer the question. Return only the rewritten question."
)
MULTI_QUERY_PROMPT = (
    "Write 3 different versions of the user's question to search the ACME policies. "
    "Each version is a short question with a single idea and other words: the formal term of the "
    "situation (arrears, unemployment, prepayment) or the action (restructure, pause, report)."
)
# The history goes as text in one message: sent as messages, the model answered instead of rewriting.
REWRITE = ChatPromptTemplate.from_messages(
    [("system", REWRITE_PROMPT), ("human", "Conversation:\n{conversation}\n\nLast question: {question}")]
)
ANSWER = ChatPromptTemplate.from_messages(
    [
        ("system", SYSTEM_PROMPT),
        MessagesPlaceholder("history"),
        ("human", "Fragments:\n\n{context}\n\nQuestion: {question}"),
    ]
)
BRACKET = re.compile(r"\[([^\]]+)\]")
SOURCE = re.compile(r"^\s*([\w.-]+\.pdf), p\. (\d+)\s*$")


class SearchQueries(BaseModel):
    """Versions of one question to search the documents."""

    queries: list[str] = Field(description="Three different versions of the question.")


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


def format_history(history: list[BaseMessage]) -> str:
    return "\n".join(f"{message.type}: {message.text}" for message in history)


def build_conversational_rag(retriever, model):
    """rewrite → retrieve → answer, as one runnable (one trace). Returns the rewrite to inspect it."""

    @chain
    def conversational_rag(inputs: dict) -> dict:
        question, history = inputs["question"], inputs["history"]
        standalone = question
        if history:  # the first question needs no rewrite: one call saved
            messages = REWRITE.format_messages(conversation=format_history(history), question=question)
            standalone = model.invoke(messages).text
        docs = retriever.invoke(standalone)
        answer = model.invoke(
            ANSWER.format_messages(history=history, context=format_context(docs), question=question)
        )
        return {"standalone_question": standalone, "docs": docs, "answer": answer}

    return conversational_rag


def unique_docs(document_lists: list[list[Document]]) -> list[Document]:
    """The same fragment may come from several queries: keep it once, in arrival order."""
    return list({doc.page_content: doc for docs in document_lists for doc in docs}.values())


def build_multi_query_rag(retriever, model):
    """Original question + 3 versions → union of fragments → one answer."""
    query_model = model.with_structured_output(SearchQueries)

    @chain
    def multi_query_rag(question: str) -> dict:
        versions = query_model.invoke([SystemMessage(MULTI_QUERY_PROMPT), HumanMessage(question)]).queries
        docs = unique_docs(retriever.batch([question, *versions]))
        answer = model.invoke(ANSWER.format_messages(history=[], context=format_context(docs), question=question))
        return {"queries": versions, "docs": docs, "answer": answer}

    return multi_query_rag


def check_citations(answer: str, docs: list[Document]) -> bool:
    """Deterministic check: there are citations and every one points to a retrieved page."""
    parts = [part for group in BRACKET.findall(answer) for part in group.split(";")]
    cited = {match.groups() for match in map(SOURCE.match, parts) if match}
    retrieved = {(doc.metadata["source"], str(doc.metadata["page"])) for doc in docs}
    return bool(cited) and cited <= retrieved


def main():
    model = build_model(max_tokens=500)
    embeddings = FastEmbedEmbeddings(model_name=EMBEDDINGS_MODEL)
    retriever = InMemoryVectorStore.from_documents(load_chunks(DOCUMENTS), embeddings).as_retriever(
        search_kwargs={"k": 3}
    )
    rag = build_conversational_rag(retriever, model)
    run_log = RunLog()

    history = []
    for question in [
        "I am 45 days past due on my Crédito Libre Inversión. Can I restructure it?",
        "And how many times can I do it?",
    ]:
        result = rag.invoke({"question": question, "history": history}, config={"callbacks": [run_log]})
        print("Search:", result["standalone_question"])
        print(result["answer"].text)
        print("Every citation was retrieved:", check_citations(result["answer"].text, result["docs"]))
        history += [HumanMessage(question), result["answer"]]

    multi = build_multi_query_rag(retriever, model).invoke(
        "I got fired, what happens with my installments?", config={"callbacks": [run_log]}
    )
    print("Versions:", multi["queries"], "·", len(multi["docs"]), "unique fragments")
    print(multi["answer"].text)
    print(run_log.receipt())


if __name__ == "__main__":
    main()
