# Gotchas: symptom → cause → fix

Observed with `langchain` 1.4, `langchain-anthropic` 1.7 and `claude-haiku-5-5`.

| Symptom | Cause | Fix |
|---|---|---|
| 400 error mentioning `temperature` | Haiku 5.5 rejects it | Remove `temperature` |
| Empty or cut answer with `max_tokens=400` | Default reasoning spends the token budget | `thinking={"type": "disabled"}` |
| Many LangSmith traces from one run | `ChatPromptTemplate.invoke` and `tool.invoke` each create a trace | Use `format_messages`; keep tracing off unless approved |
| FAISS or Chroma ranks a long, generic fragment first; the in-memory store does not | The open model's vectors do not have length 1 and the store measures L2 distance | FAISS: `normalize_L2=True`; Chroma: `collection_metadata={"hnsw:space": "cosine"}` |
| Chroma keeps ranking as before after adding the cosine metric | The collection already existed with L2; the metric is fixed at creation | Delete `indexes/chroma` and build it again |
| Chroma returns each fragment twice | The cell or script ran again without `ids` | Pass stable `ids` (file, page, position) |
| `ValueError` about `allow_dangerous_deserialization` | `FAISS.load_local` reads `index.pkl` with `pickle` | Pass it only for indexes you built yourself |
| The citation check misses `[a.pdf, p. 1; a.pdf, p. 2]` | The model grouped several sources in one bracket (seen with `claude-haiku-5-5`) | Split each bracket on `;` before matching, as `check_citations` in `rag.py` does |
| The answer cites "page 2" and the citation check says `False` | The model did not follow the `[file, p. N]` format | Show the exact format in the context labels and the system prompt |
| The answer invents a price that no document has | The retriever always returns `k` fragments | Keep the "say it is not in the documents" rule; check citations |
| `DeprecationWarning` from `langchain-community` | The package was archived in June 2026; FAISS and FastEmbed still live there | Expected with the locked version; Chroma has its own package (`langchain-chroma`) |
| The first run hangs or fails while creating the embeddings | It downloads the open model (~220 MB) from Hugging Face | Run it once with network before class; later runs use the cache |
| The PDF footer appears in every fragment | `pypdf` extracts all the text on the page | Expected; clean it before indexing if it hurts retrieval |
| The rewrite step answers the question instead of rewriting it | The history went as messages (`MessagesPlaceholder`) to the rewrite prompt | Send the history as text in one human message; keep `MessagesPlaceholder` for the answer |
| A follow-up retrieves unrelated pages | The retriever only sees "and after that, who decides?" | Rewrite with the history, or let an agent write the query (docstring asks for a complete question) |
| The follow-up answer cites a page that is not in the current fragments, and the citation check fails | The page came from an earlier turn in the history | Expected with history; check groundedness against the fragments of this turn |
| The turns of a conversation show up as separate traces, not in the LangSmith Threads tab | The history is a list handled by hand: no checkpointer copies a `thread_id` to the metadata | Pass `{"metadata": {"thread_id": "<person>-<case>"}}` in the config of every turn, as `conversational_rag.py` does |
| The agent answers in English to a Spanish thread without context | The system prompt does not fix the language | Add "answer always in <language>" to the system prompt |
