import os
from functools import lru_cache
from pathlib import Path
from typing import Any

from dotenv import find_dotenv, load_dotenv
from langchain_chroma import Chroma
from langchain_community.document_loaders import DirectoryLoader, PyPDFLoader
from langchain_core.documents import Document
from langchain_core.tools import tool
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

load_dotenv(find_dotenv())

ROOT_DIR = Path(__file__).resolve().parents[5]
DATA_DIR = Path(os.getenv("RAG_DATA_DIR", ROOT_DIR / "data" / "pdfs"))
CHROMA_DIR = Path(os.getenv("RAG_CHROMA_DIR", ROOT_DIR / "data" / "chroma"))
COLLECTION_NAME = "advancedgenai-course-rag"


@lru_cache(maxsize=1)
def _get_retriever() -> Any:
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    vector_store = Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=OpenAIEmbeddings(model="text-embedding-3-small"),
        persist_directory=str(CHROMA_DIR),
    )
    if not vector_store.get(limit=1)["ids"]:
        if not DATA_DIR.exists() or not any(DATA_DIR.glob("*.pdf")):
            raise FileNotFoundError(
                f"No se encontraron PDFs locales en {DATA_DIR}. "
                "Agrega al menos un archivo .pdf antes de ejecutar el RAG."
            )
        documents = DirectoryLoader(
            str(DATA_DIR),
            glob="**/*.pdf",
            loader_cls=PyPDFLoader,
        ).load()
        chunks = RecursiveCharacterTextSplitter(
            chunk_size=800,
            chunk_overlap=100,
        ).split_documents(documents)
        vector_store.add_documents(chunks)
    return vector_store.as_retriever(search_kwargs={"k": 4})


def _format_documents(documents: list[Document]) -> str:
    return "\n\n".join(
        f"[{Path(document.metadata.get('source', 'documento')).name} "
        f"p.{document.metadata.get('page', 0) + 1}]\n{document.page_content}"
        for document in documents
    )


@tool
def search_docs(query: str) -> str:
    """Consulta los PDFs disponibles, incluido un recetario de cocina saludable.
    Úsala cuando el usuario pida recetas, ideas para comer o recomendaciones
    de comida, incluso si solo expresa que tiene hambre.
    También permite consultar los demás documentos disponibles.
    """
    return _format_documents(_get_retriever().invoke(query))
