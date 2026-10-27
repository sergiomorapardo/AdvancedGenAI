"""Piece: RAG over PDFs with file and page citations, "not in the documents" and a citation check.

Run from the repo root:
    uv run python .claude/skills/agentic-workflow/references/examples/rag.py
Cost: 2 model calls to the project model (one per question). Embeddings run locally, at no cost;
the first run downloads the open model (~220 MB) from Hugging Face.
LangSmith: 2 traces only if LANGSMITH_TRACING=true; each groups the retriever and the model.
"""

import re
from pathlib import Path

from langchain_community.embeddings import FastEmbedEmbeddings
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import chain
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter
from project import SAMPLE_DOCUMENTS, build_model
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
PROMPT = ChatPromptTemplate.from_messages(
    [("system", SYSTEM_PROMPT), ("human", "Fragments:\n\n{context}\n\nQuestion: {question}")]
)
# One bracket may hold several sources: [a.pdf, p. 1; b.pdf, p. 2].
BRACKET = re.compile(r"\[([^\]]+)\]")
SOURCE = re.compile(r"^\s*([\w.-]+\.pdf), p\. (\d+)\s*$")


def load_pages(folder: Path) -> list[Document]:
    """One Document per PDF page; file and page in the metadata are what makes citing possible."""
    pages = []
    for path in sorted(folder.glob("*.pdf")):
        for number, page in enumerate(PdfReader(path).pages, 1):
            pages.append(Document(page.extract_text(), metadata={"source": path.name, "page": number}))
    return pages


def split(pages: list[Document]) -> list[Document]:
    """Fragments keep the metadata of their page."""
    return RecursiveCharacterTextSplitter(chunk_size=400, chunk_overlap=60).split_documents(pages)


def format_context(docs: list[Document]) -> str:
    return "\n\n".join(
        f"[{doc.metadata['source']}, p. {doc.metadata['page']}]\n{doc.page_content}" for doc in docs
    )


def build_rag(retriever, model):
    """retriever → context with sources → model, as one runnable (one trace)."""

    @chain
    def rag(question: str) -> dict:
        docs = retriever.invoke(question)
        answer = model.invoke(PROMPT.format_messages(context=format_context(docs), question=question))
        return {"answer": answer.text, "docs": docs}

    return rag


def check_citations(answer: str, docs: list[Document]) -> bool:
    """Deterministic check: there are citations and every one points to a retrieved page."""
    parts = [part for group in BRACKET.findall(answer) for part in group.split(";")]
    cited = {match.groups() for match in map(SOURCE.match, parts) if match}
    retrieved = {(doc.metadata["source"], str(doc.metadata["page"])) for doc in docs}
    return bool(cited) and cited <= retrieved


def main():
    model = build_model(max_tokens=500)
    embeddings = FastEmbedEmbeddings(model_name=EMBEDDINGS_MODEL)
    vector_store = InMemoryVectorStore.from_documents(split(load_pages(DOCUMENTS)), embeddings)
    rag = build_rag(vector_store.as_retriever(search_kwargs={"k": 3}), model)
    run_log = RunLog()

    result = rag.invoke(
        "I signed a Crédito Libre Inversión on Friday at 5 p.m. When is it disbursed?",
        config={"callbacks": [run_log]},
    )
    print(result["answer"])
    print("Every citation was retrieved:", check_citations(result["answer"], result["docs"]))

    # The retriever always returns k fragments: only the prompt rule stops made-up benefits.
    missing = rag.invoke("What are the benefits of the ACME credit card?", config={"callbacks": [run_log]})
    print(missing["answer"])
    print(run_log.receipt())


if __name__ == "__main__":
    main()
