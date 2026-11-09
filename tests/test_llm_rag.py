"""Verifica los ejemplos de la skill llm-rag sin llamar al modelo."""

import importlib.util
import sys
from pathlib import Path

from langchain_core.documents import Document
from langchain_core.embeddings import DeterministicFakeEmbedding
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage, HumanMessage

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / ".claude/skills/llm-rag"
EXAMPLES = SKILL / "references/examples"


def load_example(name, monkeypatch):
    # Los ejemplos se ejecutan como scripts e importan run_log desde su carpeta.
    monkeypatch.syspath_prepend(str(EXAMPLES))
    # Cada skill tiene su project.py: se descarta el que haya cargado otra prueba.
    for shared in ("project", "run_log"):
        monkeypatch.delitem(sys.modules, shared, raising=False)
    spec = importlib.util.spec_from_file_location(name, EXAMPLES / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def record_retriever(docs, queries):
    # Retriever falso: guarda cada consulta y devuelve siempre los mismos fragmentos.
    from langchain_core.runnables import RunnableLambda

    return RunnableLambda(lambda query: queries.append(query) or docs)


POLICY = Document("Una sola reestructuración por año.", metadata={"source": "acme_collections_policy.pdf", "page": 2})


def test_rag_example_keeps_pages_cites_and_checks_citations(monkeypatch):
    rag = load_example("rag", monkeypatch)
    pages = rag.load_pages(rag.DOCUMENTS)
    chunks = rag.split(pages)
    assert len(pages) == 8 and len(chunks) == 26
    assert all(set(chunk.metadata) == {"source", "page"} for chunk in chunks)
    ficha = Document("Hasta 3.000.000 COP", metadata={"source": "acme_credit_policy.pdf", "page": 1})
    assert rag.format_context([ficha]) == "[acme_credit_policy.pdf, p. 1]\nHasta 3.000.000 COP"
    assert rag.check_citations("Up to 3,000,000 COP [acme_credit_policy.pdf, p. 1].", [ficha])
    assert not rag.check_citations("Up to 40,000,000 COP [acme_credit_policy.pdf, p. 2].", [ficha])
    assert not rag.check_citations("Up to 3,000,000 COP.", [ficha])
    # Haiku 5.5 agrupó dos fuentes en un corchete en la corrida real.
    guia = Document("Sin efectivo.", metadata={"source": "acme_fees_guide.pdf", "page": 1})
    grouped = "No cash [acme_credit_policy.pdf, p. 1; acme_fees_guide.pdf, p. 1]."
    assert rag.check_citations(grouped, [ficha, guia])
    assert not rag.check_citations(grouped, [ficha])


def test_rag_chain_returns_answer_and_docs_without_the_model(monkeypatch):
    rag = load_example("rag", monkeypatch)
    from langchain_core.vectorstores import InMemoryVectorStore

    chunks = rag.split(rag.load_pages(rag.DOCUMENTS))
    store = InMemoryVectorStore.from_documents(chunks, DeterministicFakeEmbedding(size=16))
    model = GenericFakeChatModel(messages=iter([AIMessage("Not in the documents.")]))
    result = rag.build_rag(store.as_retriever(search_kwargs={"k": 3}), model).invoke("Price?")
    assert result["answer"] == "Not in the documents." and len(result["docs"]) == 3
    assert "[file, p. N]" in rag.SYSTEM_PROMPT and "not in the documents" in rag.SYSTEM_PROMPT


def test_vector_store_example_persists_faiss_and_chroma(monkeypatch, tmp_path):
    stores = load_example("vector_store", monkeypatch)
    embeddings = DeterministicFakeEmbedding(size=16)
    chunks = stores.load_chunks(stores.DOCUMENTS)
    question = "restructuring"

    built = stores.build_faiss(chunks, embeddings, tmp_path / "faiss")
    assert {p.name for p in (tmp_path / "faiss").iterdir()} == {"index.faiss", "index.pkl"}
    loaded = stores.load_faiss(tmp_path / "faiss", embeddings)
    assert stores.pages_of(loaded.similarity_search(question, k=3)) == stores.pages_of(
        built.similarity_search(question, k=3)
    )

    stores.build_chroma(chunks, embeddings, tmp_path / "chroma")
    chroma = stores.build_chroma(chunks, embeddings, tmp_path / "chroma")  # rerun: no duplicates
    assert len(chroma.get()["ids"]) == len(chunks) == 26
    assert chroma._collection.metadata["hnsw:space"] == "cosine"
    filtered = chroma.similarity_search(question, k=3, filter={"source": "acme_collections_policy.pdf"})
    assert {source for source, _ in stores.pages_of(filtered)} == {"acme_collections_policy.pdf"}


def test_conversational_rag_rewrites_only_follow_ups(monkeypatch):
    rag = load_example("conversational_rag", monkeypatch)
    queries = []
    model = GenericFakeChatModel(messages=iter([
        AIMessage("Yes, up to 90 days [acme_collections_policy.pdf, p. 2]."),
        AIMessage("How many times can customer C-1042 restructure a Crédito Libre Inversión?"),
        AIMessage("Once a year [acme_collections_policy.pdf, p. 2]."),
    ]))
    chain = rag.build_conversational_rag(record_retriever([POLICY], queries), model)

    first = chain.invoke({"question": "Can C-1042 restructure?", "history": []})
    assert first["standalone_question"] == "Can C-1042 restructure?"
    history = [HumanMessage("Can C-1042 restructure?"), first["answer"]]
    follow_up = chain.invoke({"question": "And how many times can I do it?", "history": history})
    # Se recupera con la pregunta reescrita, no con la de seguimiento.
    assert queries == ["Can C-1042 restructure?", follow_up["standalone_question"]]
    assert "C-1042" in follow_up["standalone_question"]
    assert rag.check_citations(follow_up["answer"].text, follow_up["docs"])
    rewrite = rag.REWRITE.format_messages(conversation=rag.format_history(history), question="And?")
    assert [m.type for m in rewrite] == ["system", "human"] and "human: Can" in rewrite[1].content


def test_multi_query_keeps_each_fragment_once(monkeypatch):
    rag = load_example("conversational_rag", monkeypatch)
    other = Document("Periodo de gracia.", metadata={"source": "acme_collections_policy.pdf", "page": 1})
    assert rag.unique_docs([[POLICY, other], [other], [POLICY]]) == [POLICY, other]
