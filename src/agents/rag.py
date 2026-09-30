import os
from functools import lru_cache
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen

from dotenv import find_dotenv, load_dotenv
from langchain.chat_models import init_chat_model
from langchain_chroma import Chroma
from langchain_community.document_loaders import DirectoryLoader, PyPDFLoader
from langchain_core.documents import Document
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langgraph.graph import END, START, MessagesState, StateGraph

load_dotenv(find_dotenv())

ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = Path(os.getenv("RAG_DATA_DIR", ROOT_DIR / "data" / "pdfs"))
CHROMA_DIR = Path(os.getenv("RAG_CHROMA_DIR", ROOT_DIR / "data" / "chroma"))
COLLECTION_NAME = "advancedgenai-course-rag"

PDF_URLS = {
    "informe_analisis_ventas_tienda_abc": "https://static.platzi.com/media/public/uploads/informe_analisis_ventas_tienda_abc_78f886d7-831a-496c-ac41-082a322ea23c.pdf",
    "recetario_cocina_saludable": "https://static.platzi.com/media/public/uploads/recetario_cocina_saludable_e1e8fca6-168b-4c9c-bf47-74e8b97ea02f.pdf",
    "guia_viaje_descubre_paris": "https://static.platzi.com/media/public/uploads/guia_viaje_descubre_paris_78441010-4be3-4f9a-80b3-7093a3acabf7.pdf",
    "investigacion_ia_medicina": "https://static.platzi.com/media/public/uploads/investigacion_ia_medicina_a3889b2c-cb97-4b29-ac95-bd9c9d49c6b7.pdf",
}

llm = init_chat_model(
    "anthropic:claude-haiku-4-5",
    temperature=0,
    max_tokens=400,
)

contextualize_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "Dado el historial y la última pregunta, devuelve solamente una pregunta "
            "autónoma que se entienda sin el historial. No respondas la pregunta.",
        ),
        MessagesPlaceholder("history"),
        ("human", "{question}"),
    ]
)

answer_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "Eres un asistente que responde sobre múltiples PDFs. Responde únicamente "
            "con la información del contexto, incluye emojis y cita las fuentes usando "
            "las etiquetas entre corchetes. Si la respuesta no está en el contexto, dilo."
            "\n\nContexto:\n{context}",
        ),
        MessagesPlaceholder("messages"),
    ]
)


class State(MessagesState):
    query: str
    documents: list[Document]


def _download_pdfs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    for name, url in PDF_URLS.items():
        destination = DATA_DIR / f"{name}.pdf"
        if destination.exists():
            continue
        request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urlopen(request, timeout=30) as response:
            destination.write_bytes(response.read())


@lru_cache(maxsize=1)
def _get_retriever() -> Any:
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    vector_store = Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=OpenAIEmbeddings(model="text-embedding-3-small"),
        persist_directory=str(CHROMA_DIR),
    )
    if not vector_store.get(limit=1)["ids"]:
        _download_pdfs()
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


def _latest_question(messages: list[BaseMessage]) -> tuple[str, list[BaseMessage]]:
    for index in range(len(messages) - 1, -1, -1):
        message = messages[index]
        if isinstance(message, HumanMessage):
            return str(message.content), messages[:index]
    raise ValueError("El estado debe incluir al menos un mensaje del usuario")


def retrieve(state: State) -> dict[str, Any]:
    question, history = _latest_question(state["messages"])
    query = question
    if history:
        standalone_question = (contextualize_prompt | llm).invoke(
            {"history": history, "question": question}
        )
        query = str(standalone_question.content)

    documents = _get_retriever().invoke(query)
    return {"query": query, "documents": documents}


def _format_documents(documents: list[Document]) -> str:
    return "\n\n".join(
        f"[{Path(document.metadata.get('source', 'documento')).name} "
        f"p.{document.metadata.get('page', 0) + 1}]\n{document.page_content}"
        for document in documents
    )


def answer(state: State) -> dict[str, list[AIMessage]]:
    response = (answer_prompt | llm).invoke(
        {
            "context": _format_documents(state["documents"]),
            "messages": state["messages"],
        }
    )
    return {"messages": [response]}


builder = StateGraph(State)
builder.add_node("retrieve", retrieve)
builder.add_node("answer", answer)
builder.add_edge(START, "retrieve")
builder.add_edge("retrieve", "answer")
builder.add_edge("answer", END)

agent = builder.compile()
