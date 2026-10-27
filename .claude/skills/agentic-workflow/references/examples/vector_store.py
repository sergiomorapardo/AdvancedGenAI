"""Piece: a persistent index in FAISS (files) or Chroma (a collection with metadata filters).

Run from the repo root:
    uv run python .claude/skills/agentic-workflow/references/examples/vector_store.py
Cost: 0 model calls and 0 traces. Embeddings run locally; the first run downloads the open model.
Writes indexes/ next to this file (ignored by Git). Plug either retriever into build_rag from rag.py.
"""

from pathlib import Path

from langchain_chroma import Chroma
from langchain_community.embeddings import FastEmbedEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from project import SAMPLE_DOCUMENTS
from pypdf import PdfReader

DOCUMENTS = SAMPLE_DOCUMENTS
INDEXES = Path(__file__).resolve().parent / "indexes"
EMBEDDINGS_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


def load_chunks(folder: Path) -> list[Document]:
    pages = []
    for path in sorted(folder.glob("*.pdf")):
        for number, page in enumerate(PdfReader(path).pages, 1):
            pages.append(Document(page.extract_text(), metadata={"source": path.name, "page": number}))
    return RecursiveCharacterTextSplitter(chunk_size=400, chunk_overlap=60).split_documents(pages)


def build_faiss(chunks: list[Document], embeddings, folder: Path) -> FAISS:
    """Writes index.faiss (vectors) and index.pkl (texts and metadata, with pickle)."""
    # This model's vectors do not have length 1: without normalizing, L2 ranks by length too.
    store = FAISS.from_documents(chunks, embeddings, normalize_L2=True)
    store.save_local(str(folder))
    return store


def load_faiss(folder: Path, embeddings) -> FAISS:
    # pickle can run code: load only indexes you built yourself.
    return FAISS.load_local(str(folder), embeddings, allow_dangerous_deserialization=True)


def build_chroma(chunks: list[Document], embeddings, folder: Path) -> Chroma:
    """Stable ids make a rerun replace fragments instead of duplicating them."""
    ids = [f"{c.metadata['source']}-p{c.metadata['page']}-{i}" for i, c in enumerate(chunks)]
    return Chroma.from_documents(
        chunks,
        embeddings,
        ids=ids,
        collection_name="documents",
        # The metric is fixed when the collection is created; an old L2 collection keeps L2.
        collection_metadata={"hnsw:space": "cosine"},
        persist_directory=str(folder),
    )


def pages_of(docs: list[Document]) -> list[tuple[str, int]]:
    return [(doc.metadata["source"], doc.metadata["page"]) for doc in docs]


def main():
    embeddings = FastEmbedEmbeddings(model_name=EMBEDDINGS_MODEL)
    chunks = load_chunks(DOCUMENTS)
    question = "I signed a Crédito Libre Inversión on Friday at 5 p.m. When is it disbursed?"

    build_faiss(chunks, embeddings, INDEXES / "faiss")
    faiss = load_faiss(INDEXES / "faiss", embeddings)  # no embedding is computed again
    print("FAISS :", pages_of(faiss.similarity_search(question, k=3)))

    chroma = build_chroma(chunks, embeddings, INDEXES / "chroma")
    print("Chroma:", pages_of(chroma.similarity_search(question, k=3)))
    print("Chroma fragments (no duplicates on rerun):", len(chroma.get()["ids"]), "of", len(chunks))

    arrears_question = "I am 45 days past due: can I restructure my credit?"
    policy_only = {"source": "acme_collections_policy.pdf"}
    print("Filtered:", pages_of(chroma.similarity_search(arrears_question, k=3, filter=policy_only)))

    # Either one becomes the retriever of rag.build_rag:
    # chroma.as_retriever(search_kwargs={"k": 3, "filter": policy_only})


if __name__ == "__main__":
    main()
