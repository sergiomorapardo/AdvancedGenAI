# Build: pieces, files and rules

## Contents

- Which piece to use
- Files to generate
- Rules that are not negotiable
- Project specifics

## Which piece to use

- **Tool** (`tools_agent.py`): `@tool(parse_docstring=True)` with Google-style `Args:`. The docstring is all the model knows: list the accepted values. Return a dict with `status` (`ok`, `not_found`, `invalid`) instead of raising. Read only.
- **API tool** (`api_tool.py`): `httpx.get(..., timeout=15)` inside `try/except httpx.HTTPError`; an HTTP error returns `{"status": "unavailable", "message": response.text[:300]}`. Return only the fields the model needs and a `source`. Public APIs without a key only; never put keys in the tool or the prompt.
- **Agent** (`tools_agent.py`): `create_agent(model, tools=[...], system_prompt=...)`. The system prompt says to look up before answering and to use only figures from the tools.
- **Forced first lookup**: `model.bind_tools(tools, tool_choice="<tool name>")` for one call only. Do not pass a forced model to `create_agent`: it would never answer.
- **Tools from MCP servers** (`mcp_agent.py`): `async with MCPAdapter({"mcpServers": {...}}) as adapter: tools = await adapter.list_tools()`, with the same entries as `.mcp.json` (`command`/`args` for stdio, `url` for HTTP). With several servers, tools are named `<server>_<tool>` (with one, just `<tool>`); they are async: call the agent with `await agent.ainvoke(...)` and, in a script, `asyncio.run(main())`. If a server asks the person, `create_agent(..., checkpointer=...)` pauses with `state["__interrupt__"]`; show `message` and the options of `requested_schema` to the person and resume with `Command(resume={"responses": {key: {"action": "accept", "content": {...}}}})`, or `{"action": "decline"}`. The model never answers for the person. Connect only the servers the task needs: every definition goes to the model on every call.
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

The `README.md` states the problem in one sentence, two or three success criteria the person can check (for example "reports the missing amount when a payment does not cover the overdue balance"), the command, and the cost of one run in model calls and traces.

## Rules that are not negotiable

1. **Model**: `build_model(max_tokens=...)` from `project.py`, nothing else creates a chat model. Its settings and why are in `references/project.md`. Do not switch to a bigger model on your own.
2. **Credentials**: `build_model()` loads them the way the project decides. Never write a key, never print `.env`.
3. **Run log always**; never filter events before saving them and never remove it to "simplify".
4. **Tracing off by default.** With LangSmith, every top-level `invoke`, `batch` or `stream` is one trace, including `ChatPromptTemplate.invoke`; fill templates with `format_messages` when the trace is not needed.
5. **Synthetic data** in the code (8–12 rows with one or two traps that force the agent to read, such as zero availability or a missing product). Real data only if it is authorized and anonymized.
6. **Read-only tools.** Writing, sending or reserving requires human approval with interrupts, which the agentic-memory skill builds: hand the action over to it instead of giving the agent a tool that writes.
7. **MCP tools stay where they are.** The agent never copies a server's query or index; it connects to the server. Review a server you did not write with the mcp-server skill before connecting it.
8. **Names in English** for files, functions, classes and variables.
9. **Keep it simple**: the smallest code that meets the goal, no helpers the blueprint does not need.

## Project specifics

Where apps live, which packages are allowed, the branch convention, the repository tools and the hooks that check what you write are in `references/project.md`. Read it before generating files.
