"""Servidor MCP de documentos: búsqueda en las políticas de ACME, con cita de archivo y página.

Usa embeddings locales para recuperar fragmentos, sin llamar a un modelo generativo.
El LLM de la aplicación escribe la respuesta, así que cualquier agente obtiene las mismas citas
sin construir su propio RAG.

Lo arranca el cliente, desde cualquier carpeta del proyecto:
    python -m agents.servers.documents          # stdio: el cliente lo abre como subproceso
    python -m agents.servers.documents --http   # streamable HTTP en http://127.0.0.1:8002/mcp

DOCUMENTS_DIR apunta a otra carpeta con PDFs acme_*.pdf; por defecto, datasets/.
"""

import os
import sys
import warnings
from functools import cache
from pathlib import Path
from typing import Annotated

from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ResourceError, ToolError
from mcp.server.mcpserver.prompts.base import UserMessage
from mcp.types import ResourceLink, ToolAnnotations
from pydantic import Field

# Los avisos y barras de progreso de las librerías van a stderr y llegan al cliente como ruido.
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", module="huggingface_hub")
os.environ.setdefault("HF_HUB_VERBOSITY", "error")
os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")

from langchain_community.embeddings import FastEmbedEmbeddings  # noqa: E402
from langchain_core.documents import Document  # noqa: E402
from langchain_core.vectorstores import InMemoryVectorStore  # noqa: E402
from langchain_text_splitters import RecursiveCharacterTextSplitter  # noqa: E402
from langsmith import tracing_context  # noqa: E402
from pypdf import PdfReader  # noqa: E402

DOCUMENTS = Path(os.getenv("DOCUMENTS_DIR", Path(__file__).resolve().parents[3] / "datasets"))
EMBEDDINGS_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

mcp = MCPServer(
    "documentos",
    instructions="Políticas de crédito, desembolsos, costos y cobranza de ACME. Solo lectura.",
    log_level="WARNING",
)
READ_ONLY = ToolAnnotations(read_only_hint=True, open_world_hint=False)


def policy_files() -> dict[str, Path]:
    return {path.name: path for path in sorted(DOCUMENTS.glob("acme_*.pdf"))}


def read_pages(path: Path) -> list[Document]:
    return [
        Document(page.extract_text(), metadata={"source": path.name, "page": number})
        for number, page in enumerate(PdfReader(path).pages, 1)
    ]


def embeddings():
    return FastEmbedEmbeddings(model_name=EMBEDDINGS_MODEL)


@cache
def retriever():
    """El índice de L4: se construye la primera vez que se busca y sigue vivo mientras viva el proceso."""
    pages = [page for path in policy_files().values() for page in read_pages(path)]
    chunks = RecursiveCharacterTextSplitter(chunk_size=400, chunk_overlap=60).split_documents(pages)
    return InMemoryVectorStore.from_documents(chunks, embeddings()).as_retriever(search_kwargs={"k": 3})


@mcp.tool(annotations=READ_ONLY)
def search_documents(
    query: Annotated[str, Field(description="Pregunta completa, con el producto, la situación del cliente y el tema; sin pronombres como «eso».")],
) -> str:
    """Busca en las políticas de ACME: crédito, desembolsos, costos y pagos, y cobranza.

    Devuelve los 3 fragmentos más parecidos, cada uno con su cita [archivo, p. N].
    """
    if not query.strip() or len(query) > 500:
        raise ToolError("Escribe una pregunta de 1 a 500 caracteres.")
    # La traza de la tool pertenece al agente; el servidor no crea otra traza de recuperación.
    with tracing_context(enabled=False):
        documents = retriever().invoke(query)
    return "\n\n".join(
        f"[{doc.metadata['source']}, p. {doc.metadata['page']}]\n{doc.page_content}"
        for doc in documents
    )


@mcp.prompt(title="Solicitud de reestructuración")
def restructuring_request(customer: Annotated[str, Field(description="Código del cliente, por ejemplo C-1042.")]) -> list[UserMessage]:
    """Prepara la solicitud de reestructuración de un cliente, con la política de cobranza enlazada."""
    # resource_link: el prompt enlaza el documento por su URI; el cliente decide si lo lee completo.
    # Va en un prompt y no en search_documents: langchain.mcp convierte el enlace en un archivo
    # que la API del modelo intentaría descargar, y docs:// no es una URL de internet.
    policy = ResourceLink(
        type="resource_link", uri="docs://acme_collections_policy.pdf", name="acme_collections_policy.pdf",
        mime_type="text/plain",
    )
    return [
        UserMessage(f"Prepara la solicitud de reestructuración del cliente {customer}: requisitos, cuánto se puede "
                    "ampliar el plazo y cuántas veces se puede pedir. Cita cada dato con [archivo, p. N]."),
        UserMessage(policy),
    ]


@mcp.resource("docs://{name}", mime_type="text/plain")
def read_document(name: str) -> str:
    """El texto completo de una política, por su nombre de archivo (por ejemplo, acme_collections_policy.pdf)."""
    # Solo nombres de la carpeta: «../.env» o una ruta absoluta no se leen.
    allowed = policy_files()
    if name not in allowed:
        raise ResourceError(f"Documento desconocido. Disponibles: {', '.join(allowed)}")
    return "\n\n".join(f"[{name}, p. {d.metadata['page']}]\n{d.page_content}" for d in read_pages(allowed[name]))


if __name__ == "__main__":
    if "--http" in sys.argv:
        mcp.run("streamable-http", port=8002)
    else:
        mcp.run()
