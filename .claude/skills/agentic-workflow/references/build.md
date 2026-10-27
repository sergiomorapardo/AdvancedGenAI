# Build: pieces, files and rules

## Contents

- Which piece to use
- Files to generate
- Rules that are not negotiable
- Project specifics

## Which piece to use

- **Chain** (`chain.py`): `PROMPT | model.with_structured_output(Schema)`. Use it when the steps are fixed.
- **Jinja template** (`jinja_prompt.py`): `prompts/<name>.jinja` loaded from the script's folder with `FileSystemLoader(Path(__file__).resolve().parent / "prompts")` and `StrictUndefined`. Render the system prompt with Jinja; pass the user message as data in a separate human message, never through Jinja. Next to each template, write `<name>.example.json` with a realistic context: the repo's Jinja hook renders it with `StrictUndefined` after every edit.
- **Structured output**: a Pydantic model with a docstring and a `Field(description=...)` per field. Optional fields are `X | None`. Validate the shape with the schema and the content with a check against the input or the tool.
- **Tool** (`tools_agent.py`): `@tool(parse_docstring=True)` with Google-style `Args:`. The docstring is all the model knows: list the accepted values. Return a dict with `status` (`ok`, `not_found`, `invalid`) instead of raising. Read only.
- **API tool** (`api_tool.py`): `httpx.get(..., timeout=15)` inside `try/except httpx.HTTPError`; an HTTP error returns `{"status": "unavailable", "message": response.text[:300]}`. Return only the fields the model needs and a `source`. Public APIs without a key only; never put keys in the tool or the prompt.
- **Agent** (`tools_agent.py`): `create_agent(model, tools=[...], system_prompt=...)`. The system prompt says to look up before answering and to use only figures from the tools.
- **Forced first lookup**: `model.bind_tools(tools, tool_choice="<tool name>")` for one call only. Do not pass a forced model to `create_agent`: it would never answer.
- **RAG** (`rag.py`): one `Document` per PDF page with `{"source", "page"}`; `RecursiveCharacterTextSplitter(chunk_size=400, chunk_overlap=60)`; `FastEmbedEmbeddings` with the open multilingual model; `InMemoryVectorStore.from_documents`; `as_retriever(search_kwargs={"k": 3})`. The context puts `[file, p. N]` before each fragment; the system prompt asks to cite and to say when the answer is not there. Wrap retrieve → context → model in a `@chain` that returns the answer and the docs, so the citation check can run.
- **Persistent index** (`vector_store.py`): FAISS with `normalize_L2=True`, `save_local` and `load_local(..., allow_dangerous_deserialization=True)`; or Chroma with stable `ids`, `collection_metadata={"hnsw:space": "cosine"}` and `filter={"source": ...}`. Same chunks, same embeddings model for indexing and asking.
- **Follow-up questions, fixed steps** (`conversational_rag.py`): a `@chain` that rewrites the question with the history (as text in one human message), retrieves with the rewrite and answers with `MessagesPlaceholder("history")`. Skip the rewrite on the first question. Return the rewrite with the answer and the docs so it can be checked.
- **Multi-query** (`conversational_rag.py`): `with_structured_output(SearchQueries)` writes 3 versions; `retriever.batch([question, *versions])`; keep each fragment once. More fragments, not a guaranteed better one: measure it.
- **Memory per conversation** (`memory_agent.py`): the retriever as a `@tool(parse_docstring=True)` whose docstring asks for a complete query; `create_agent(..., checkpointer=InMemorySaver())` and `config={"configurable": {"thread_id": ...}}`. The `thread_id` comes from the user's session; one per conversation. `InMemorySaver` dies with the process: for a service, use a database checkpointer (the repo's API in `src/api/` uses PostgreSQL).
- **Tools from MCP servers** (`mcp_agent.py`): `async with MCPAdapter({"mcpServers": {...}}) as adapter: tools = await adapter.list_tools()`, with the same entries as `.mcp.json` (`command`/`args` for stdio, `url` for HTTP). With several servers, tools are named `<server>_<tool>` (with one, just `<tool>`); they are async: call the agent with `await agent.ainvoke(...)` and, in a script, `asyncio.run(main())`. If a server asks the person, `create_agent(..., checkpointer=...)` pauses with `state["__interrupt__"]`; show `message` and the options of `requested_schema` to the person and resume with `Command(resume={"responses": {key: {"action": "accept", "content": {...}}}})`, or `{"action": "decline"}`. The model never answers for the person. Connect only the servers the task needs: every definition goes to the model on every call.
- **Run log** (`run_log.py`): copy it as is next to the app and pass `config={"callbacks": [run_log]}` on the top-level `invoke`. Print `run_log.receipt()` at the end.

## Files to generate

Copy `assets/app.py`, fill the `TODO` marks and delete the pieces the blueprint does not use. Output structure, in a new folder named after the app:

```
labs/<app-name>/
  README.md                 # problem, success criteria, how to run, cost of one run
  app.py                    # from assets/app.py
  project.py                # copied as is from references/examples/project.py
  run_log.py                # copied as is from references/examples/run_log.py
  prompts/<name>.jinja      # only with a Jinja prompt
  prompts/<name>.example.json
  documents/                # only with RAG: synthetic or authorized PDFs
  indexes/                  # only with FAISS or Chroma; in .gitignore
  .gitignore                # runs/ and indexes/
  runs/<timestamp>/         # events.jsonl + transcript.md, one folder per run
```

The `README.md` states the problem in one sentence, two or three success criteria the person can check (for example "reports the missing amount when a payment does not cover the overdue balance"), the command, and the cost of one run in model calls and traces.

## Rules that are not negotiable

1. **Model**: `build_model(max_tokens=...)` from `project.py`, nothing else creates a chat model. Its settings and why are in `references/project.md`. Do not switch to a bigger model on your own.
2. **Credentials**: `build_model()` loads them the way the project decides. Never write a key, never print `.env`.
3. **Run log always**; never filter events before saving them and never remove it to "simplify".
4. **Tracing off by default.** With LangSmith, every top-level `invoke`, `batch` or `stream` is one trace, including `ChatPromptTemplate.invoke`; fill templates with `format_messages` when the trace is not needed.
5. **Synthetic data** in the code (8–12 rows with one or two traps that force the agent to read, such as zero availability or a missing product). Real data only if it is authorized and anonymized.
6. **Read-only tools.** Writing, sending or reserving requires human approval, which is not in this skill yet: generate a draft and say so.
7. **Names in English** for files, functions, classes and variables.
8. **Keep it simple**: the smallest code that meets the goal, no helpers the blueprint does not need.
9. **RAG cites and checks.** Every answer from documents cites `[file, p. N]`, and `check_citations` confirms each citation was retrieved. Embeddings are local unless the person has a provider key and a reason.
10. **Never load an index you did not build.** `allow_dangerous_deserialization=True` runs `pickle`; indexes are rebuilt from the documents, never downloaded or committed.
11. **MCP tools stay where they are.** The agent never copies a server's query or index; it connects to the server. Review a server you did not write with the mcp-server skill before connecting it.
12. **Conversations are isolated.** One `thread_id` per conversation, taken from the session, never shared between people. Memory does not replace a fresh lookup of data that changes, such as a balance.

## Project specifics

Where apps live, which packages are allowed, the branch convention, the repository tools and the hooks that check what you write are in `references/project.md`. Read it before generating files.
