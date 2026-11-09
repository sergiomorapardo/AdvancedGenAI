"""TODO: one sentence with the goal of this app.

Run from the repo root:
    uv run python labs/TODO-app-name/app.py
Cost: 1 model call per question to the project model (2 with the rewrite of a follow-up, 1 more with
multi-query). Embeddings run locally. LangSmith: 1 trace per question only if LANGSMITH_TRACING=true.

project.py, run_log.py and rag.py are copied as is next to this file; adapt SYSTEM_PROMPT in rag.py.
Evaluating the app is another skill.
"""

from pathlib import Path

from langchain_community.embeddings import FastEmbedEmbeddings
from langchain_core.vectorstores import InMemoryVectorStore
from project import build_model
from rag import (  # rag.py copied as is from references/examples/
    build_rag,
    check_citations,
    load_pages,
    split,
)
from run_log import RunLog

# --- RAG: answers from documents with [file, p. N] citations -------------------------------
# For FAISS or Chroma, add the builder from vector_store.py; for follow-up questions, use
# build_conversational_rag or build_multi_query_rag from conversational_rag.py instead of build_rag.
DOCUMENTS = Path(__file__).resolve().parent / "documents"  # TODO: synthetic or authorized PDFs
EMBEDDINGS_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


def main():
    model = build_model(max_tokens=500)
    run_log = RunLog(Path(__file__).resolve().parent / "runs")
    embeddings = FastEmbedEmbeddings(model_name=EMBEDDINGS_MODEL)
    store = InMemoryVectorStore.from_documents(split(load_pages(DOCUMENTS)), embeddings)
    rag = build_rag(store.as_retriever(search_kwargs={"k": 3}), model)
    result = rag.invoke("TODO", config={"callbacks": [run_log]})
    print(result["answer"])
    print("Every citation was retrieved:", check_citations(result["answer"], result["docs"]))
    print(run_log.receipt())


if __name__ == "__main__":
    main()
