# Build: pieces, files and rules

## Contents

- Which piece to use
- Files to generate
- Rules that are not negotiable
- Project specifics

## Which piece to use

- **Memory per conversation** (`memory_agent.py`): the retriever as a `@tool(parse_docstring=True)` whose docstring asks for a complete query; `create_agent(..., checkpointer=InMemorySaver())` and `config={"configurable": {"thread_id": ...}}`. The `thread_id` comes from the user's session; one per conversation. `InMemorySaver` dies with the process: for a service, use a database checkpointer (the repo's API in `src/api/` uses PostgreSQL; the ops-deploy skill serves it).
- **What the thread kept**: `agent.get_state(config).values["messages"]` shows the messages of one thread; the queries the agent wrote are the `args` of its tool calls (`searches` in `memory_agent.py`).
- **Approval in a graph** (`approval.py`): a `StateGraph` with a checkpointer; limits in code decide which requests need a person, the `approval` node calls `interrupt({...})` with exactly what the person must see and returns `Command(goto=..., update=...)`: approve and edit go to the action node, reject to its own node. Resume with `graph.invoke(Command(resume={"type": ...}), config)` on the same `thread_id`. The action is its own node after the approval, never code before the `interrupt` in the same node (it would run again on resume). In a real system the action is idempotent, keyed by the request id. For a graph served by the local LangGraph server, compile without a checkpointer: the server keeps the threads.
- **Approval on an agent's tool** (`approval.py`): `create_agent(..., middleware=[HumanInTheLoopMiddleware(interrupt_on={"tool_name": True})], checkpointer=...)`; the agent pauses with `__interrupt__` and the proposed call in `action_requests`, and resumes with `Command(resume={"decisions": [{"type": "approve" | "edit" | "reject", ...}]})`. A check over the `ToolMessage`s (`tool_executed`) confirms whether the tool ran.
- **Run log** (`run_log.py`): copy it as is next to the app and pass `config={"callbacks": [run_log]}` on the top-level `invoke`. Print `run_log.receipt()` at the end.

## Files to generate

Copy `assets/app.py`, fill the `TODO` marks and delete what the blueprint does not use. Output structure, in a new folder named after the app:

```
labs/<app-name>/
  README.md                 # problem, success criteria, how to run, cost of one run
  app.py                    # from assets/app.py
  project.py                # copied as is from references/examples/project.py
  run_log.py                # copied as is from references/examples/run_log.py
  .gitignore                # runs/
  runs/<timestamp>/         # events.jsonl + transcript.md, one folder per run
```

The `README.md` states the problem in one sentence, two or three success criteria the person can check (for example "answers the follow-up of the same thread and does not know it in another thread"), the command, and the cost of one run in model calls and traces.

## Rules that are not negotiable

1. **Model**: `build_model(max_tokens=...)` from `project.py`, nothing else creates a chat model. Its settings and why are in `references/project.md`. Do not switch to a bigger model on your own.
2. **Credentials**: `build_model()` loads them the way the project decides. Never write a key, never print `.env`.
3. **Run log always**; never filter events before saving them and never remove it to "simplify".
4. **Tracing off by default.** With LangSmith, every top-level `invoke`, `batch` or `stream` is one trace, including `ChatPromptTemplate.invoke`; fill templates with `format_messages` when the trace is not needed.
5. **Synthetic data** in the code and in the conversations. Real data only if it is authorized and anonymized.
6. **Conversations are isolated.** One `thread_id` per conversation, taken from the session, never shared between people. Memory does not replace a fresh lookup of data that changes, such as a balance.
7. **Read-only tools; writes behind a gate.** Tools only read. Disbursing, writing or sending goes in its own node after an `interrupt()`, or in a tool guarded by `HumanInTheLoopMiddleware`, and runs only with an explicit approve or edit, as in `approval.py`.
8. **Names in English** for files, functions, classes and variables.
9. **Keep it simple**: the smallest code that meets the goal, no helpers the blueprint does not need.

## Project specifics

Where apps live, which packages are allowed, the branch convention, the repository tools and the hooks that check what you write are in `references/project.md`. Read it before generating files.
