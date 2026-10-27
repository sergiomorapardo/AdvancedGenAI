"""Agente de soporte de ACME: políticas con citas, cartera de créditos y memoria por conversación.

Junta las piezas del curso: el RAG de L4 sobre las políticas sintéticas de `datasets/`, la
consulta de solo lectura del servidor MCP de créditos (L20) y la memoria por `thread_id` (L9).
La API de `src/api` lo sirve con PostgreSQL como checkpointer; LangGraph Studio lo abre como `acme`.
"""

from functools import cache
from pathlib import Path

from dotenv import find_dotenv, load_dotenv
from langchain.agents import create_agent
from langchain_anthropic import ChatAnthropic
from langchain_community.embeddings import FastEmbedEmbeddings
from langchain_core.documents import Document
from langchain_core.tools import tool
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langgraph.checkpoint.base import BaseCheckpointSaver
from mcp.server.mcpserver.exceptions import ToolError
from pypdf import PdfReader

from agents.servers.credits import find_credits

# find_dotenv sube por las carpetas hasta encontrar el .env de la raíz
load_dotenv(find_dotenv())

DATASETS = Path(__file__).resolve().parents[2] / "datasets"
EMBEDDINGS_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

SYSTEM_PROMPT = (
    "Eres el asistente de soporte de ACME, una fintech. Responde siempre en español. "
    "Para saldos, montos vencidos y días de mora, consulta la cartera con check_credit y da el producto y la cifra en pesos. "
    "Para requisitos, plazos o políticas, busca con search_policies escribiendo una pregunta completa, "
    "aunque el cliente se refiera a mensajes anteriores, y cita cada dato con el formato [archivo, p. N]. "
    "Si las herramientas no devuelven el dato, dilo y no lo inventes. No prometas aprobaciones."
)


@cache
def retriever():
    """El índice de L4: se construye en la primera búsqueda y se reutiliza mientras viva el proceso."""
    pages = [
        Document(page.extract_text(), metadata={"source": path.name, "page": number})
        for path in sorted(DATASETS.glob("acme_*.pdf"))
        for number, page in enumerate(PdfReader(path).pages, 1)
    ]
    chunks = RecursiveCharacterTextSplitter(chunk_size=400, chunk_overlap=60).split_documents(pages)
    store = InMemoryVectorStore.from_documents(chunks, FastEmbedEmbeddings(model_name=EMBEDDINGS_MODEL))
    return store.as_retriever(search_kwargs={"k": 3})


@tool(parse_docstring=True)
def search_policies(query: str) -> str:
    """Busca en las políticas de ACME: crédito, desembolsos, costos y pagos, y cobranza. Solo lectura.

    Args:
        query: pregunta completa, con el producto, la situación del cliente y el tema; sin pronombres como «eso».
    """
    return "\n\n".join(
        f"[{doc.metadata['source']}, p. {doc.metadata['page']}]\n{doc.page_content}"
        for doc in retriever().invoke(query)
    )


@tool(parse_docstring=True)
def check_credit(customer: str, product: str = "") -> dict:
    """Consulta los créditos de un cliente de ACME: saldo, monto vencido y días de mora, en pesos. Solo lectura.

    Args:
        customer: código del cliente, por ejemplo C-1042.
        product: código (CLI, CEX) o nombre del producto; vacío para todos sus créditos.
    """
    try:
        return {"status": "ok", "credits": find_credits(customer, product)}
    except ToolError as error:  # una entrada inválida vuelve como dato: el agente puede corregirla
        return {"status": "invalid", "message": str(error)}


def build_model() -> ChatAnthropic:
    return ChatAnthropic(
        model="claude-haiku-5-5",
        max_tokens=500,
        thinking={"type": "disabled"},
        timeout=60,
        max_retries=2,
    )


def make_graph(*, checkpointer: BaseCheckpointSaver | None = None):
    """Con un checkpointer, el agente recuerda cada conversación por su thread_id."""
    return create_agent(
        build_model(),
        tools=[search_policies, check_credit],
        system_prompt=SYSTEM_PROMPT,
        checkpointer=checkpointer,
    )


# Studio supplies its own persistence; the API injects the PostgreSQL checkpointer.
agent = make_graph()
