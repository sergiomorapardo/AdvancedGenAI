# Build: pieces, files and rules

## Contents

- Which piece to use
- Files to generate
- Rules that are not negotiable
- Project specifics

## Which piece to use

- **RAG** (`rag.py`): one `Document` per PDF page with `{"source", "page"}`; `RecursiveCharacterTextSplitter(chunk_size=400, chunk_overlap=60)`; `FastEmbedEmbeddings` with the open multilingual model; `InMemoryVectorStore.from_documents`; `as_retriever(search_kwargs={"k": 3})`. The context puts `[file, p. N]` before each fragment; the system prompt asks to cite and to say when the answer is not there. Wrap retrieve → context → model in a `@chain` that returns the answer and the docs, so the citation check can run.
- **Persistent index** (`vector_store.py`): FAISS with `normalize_L2=True`, `save_local` and `load_local(..., allow_dangerous_deserialization=True)`; or Chroma with stable `ids`, `collection_metadata={"hnsw:space": "cosine"}` and `filter={"source": ...}`. Same chunks, same embeddings model for indexing and asking.
- **Follow-up questions, fixed steps** (`conversational_rag.py`): a `@chain` that rewrites the question with the history (as text in one human message), retrieves with the rewrite and answers with `MessagesPlaceholder("history")`. Skip the rewrite on the first question. Return the rewrite with the answer and the docs so it can be checked.
- **Multi-query** (`conversational_rag.py`): `with_structured_output(SearchQueries)` writes 3 versions; `retriever.batch([question, *versions])`; keep each fragment once. More fragments, not a guaranteed better one: measure it.
- **Run log** (`run_log.py`): copy it as is next to the app and pass `config={"callbacks": [run_log]}` on the top-level `invoke`. Print `run_log.receipt()` at the end.

## Files to generate

Copy `assets/app.py`, fill the `TODO` marks and delete what the blueprint does not use. Output structure, in a new folder named after the app:

```
labs/<app-name>/
  README.md                 # problem, success criteria, how to run, cost of one run
  app.py                    # from assets/app.py
  project.py                # copied as is from references/examples/project.py
  run_log.py                # copied as is from references/examples/run_log.py
  rag.py                    # copied as is from references/examples/rag.py; adapt SYSTEM_PROMPT
  documents/                # synthetic or authorized PDFs
  indexes/                  # only with FAISS or Chroma; in .gitignore
  .gitignore                # runs/ and indexes/
  runs/<timestamp>/         # events.jsonl + transcript.md, one folder per run
```

The `README.md` states the problem in one sentence, two or three success criteria the person can check (for example "says it is not in the documents when asked for a price"), the command, and the cost of one run in model calls and traces.

## Rules that are not negotiable

1. **Model**: `build_model(max_tokens=...)` from `project.py`, nothing else creates a chat model. Its settings and why are in `references/project.md`. Do not switch to a bigger model on your own.
2. **Credentials**: `build_model()` loads them the way the project decides. Never write a key, never print `.env`.
3. **Run log always**; never filter events before saving them and never remove it to "simplify".
4. **Tracing off by default.** With LangSmith, every top-level `invoke`, `batch` or `stream` is one trace, including `ChatPromptTemplate.invoke`; fill templates with `format_messages` when the trace is not needed.
5. **RAG cites and checks.** Every answer from documents cites `[file, p. N]`, and `check_citations` confirms each citation was retrieved. Embeddings are local unless the person has a provider key and a reason.
6. **Never load an index you did not build.** `allow_dangerous_deserialization=True` runs `pickle`; indexes are rebuilt from the documents, never downloaded or committed.
7. **Synthetic or authorized documents** only, anonymized when they come from the person's area.
8. **Names in English** for files, functions, classes and variables.
9. **Keep it simple**: the smallest code that meets the goal, no helpers the blueprint does not need.

## Project specifics

Where apps live, which packages are allowed, the branch convention, the repository tools and the hooks that check what you write are in `references/project.md`. Read it before generating files.
