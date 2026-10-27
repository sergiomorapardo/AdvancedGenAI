"""Piece: a document-search MCP server that returns fragments with their [file, p. N] citation.

It only retrieves; it never calls a generative model. The client's model writes the answer, so every
app gets the same citations without building its own RAG. It offers the three primitives:
- tool search_documents(query): the 3 closest fragments, each with its citation;
- resource docs://{name}: the full text of one document of the folder, nothing outside it;
- prompt summarize_document(name): a template that links the document with a resource_link.

A client starts it; no model calls, embeddings run locally:
    uv run python .claude/skills/mcp-server/references/examples/docs_server.py          # stdio
    uv run python .claude/skills/mcp-server/references/examples/docs_server.py --http   # http://127.0.0.1:8002/mcp
DOCUMENTS_DIR points to another folder of PDFs.
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

# Library warnings and progress bars go to stderr and reach the client as noise.
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", module="huggingface_hub")
os.environ.setdefault("HF_HUB_VERBOSITY", "error")

from langchain_community.embeddings import FastEmbedEmbeddings
from langchain_core.documents import Document
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter
from project import EMBEDDINGS_MODEL, SAMPLE_DOCUMENTS
from pypdf import PdfReader

DOCUMENTS = Path(os.getenv("DOCUMENTS_DIR", SAMPLE_DOCUMENTS))

mcp = MCPServer("documents", instructions="Data sheets, guides and policies. Read only.", log_level="WARNING")
READ_ONLY = ToolAnnotations(read_only_hint=True, open_world_hint=False)


def read_pages(path: Path) -> list[Document]:
    return [
        Document(page.extract_text(), metadata={"source": path.name, "page": number})
        for number, page in enumerate(PdfReader(path).pages, 1)
    ]


def allowed_documents() -> dict[str, Path]:
    """Only file names of the folder: '../.env' or an absolute path never match."""
    return {path.name: path for path in DOCUMENTS.glob("*.pdf")}


@cache
def retriever():
    """Built on the first search and kept while the process lives: over HTTP, once for every client."""
    pages = [page for path in sorted(DOCUMENTS.glob("*.pdf")) for page in read_pages(path)]
    chunks = RecursiveCharacterTextSplitter(chunk_size=400, chunk_overlap=60).split_documents(pages)
    embeddings = FastEmbedEmbeddings(model_name=EMBEDDINGS_MODEL)
    return InMemoryVectorStore.from_documents(chunks, embeddings).as_retriever(search_kwargs={"k": 3})


@mcp.tool(annotations=READ_ONLY)
def search_documents(
    query: Annotated[str, Field(description="Complete question with the product, the customer situation and the topic; no pronouns.")],
) -> str:
    """Search the policies and guides.

    Returns the 3 closest fragments, each one with its citation [file, p. N].
    """
    if not query.strip() or len(query) > 500:
        raise ToolError("Write a question of 1 to 500 characters.")
    # Text only: some clients turn a resource_link inside a tool result into a file to download.
    return "\n\n".join(
        f"[{doc.metadata['source']}, p. {doc.metadata['page']}]\n{doc.page_content}"
        for doc in retriever().invoke(query)
    )


@mcp.resource("docs://{name}", mime_type="text/plain")
def read_document(name: str) -> str:
    """Full text of one document, by file name."""
    allowed = allowed_documents()
    if name not in allowed:
        raise ResourceError(f"Unknown document. Available: {', '.join(sorted(allowed))}")
    return "\n\n".join(f"[{name}, p. {d.metadata['page']}]\n{d.page_content}" for d in read_pages(allowed[name]))


@mcp.prompt(title="Summarize a document")
def summarize_document(name: Annotated[str, Field(description="File name, as listed by docs://.")]) -> list[UserMessage]:
    """Prepare a summary of one document, linked instead of copied."""
    if name not in allowed_documents():
        raise ValueError(f"Unknown document: {name}")
    # resource_link: the prompt points to the document by its URI; the client decides whether to read it.
    link = ResourceLink(type="resource_link", uri=f"docs://{name}", name=name, mime_type="text/plain")
    return [UserMessage(f"Summarize {name} in five points. Cite each one as [file, p. N]."), UserMessage(link)]


if __name__ == "__main__":
    if "--http" in sys.argv:
        mcp.run("streamable-http", port=8002)
    else:
        mcp.run()
