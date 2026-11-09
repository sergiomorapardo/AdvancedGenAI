# Gotchas: symptom → cause → fix

Observed with `langchain` 1.4, `langchain-anthropic` 1.7 and `claude-haiku-5-5`.

| Symptom | Cause | Fix |
|---|---|---|
| 400 error mentioning `temperature` | Haiku 5.5 rejects it | Remove `temperature` |
| Empty or cut answer with `max_tokens=400` | Default reasoning spends the token budget | `thinking={"type": "disabled"}` |
| 400 error about prefill or the final assistant message | The conversation sent to the model ends in an AI message | Send a list that ends in a human or tool message; keep the reply apart (`conversation = messages + [response]`) |
| The agent stops with a traceback from a tool | An exception inside the tool function is not returned to the model | Return `{"status": "not_found" \| "invalid", "message": ...}` |
| `json.loads` fails on a `ToolMessage` | The tool returned a non-JSON object | Return plain dicts; the `ToolMessage` content is their JSON text |
| `not_found` for "credito libre inversion" | The comparison is case-insensitive but keeps accents | List the accepted values in the docstring, or normalize accents in the tool |
| The agent never answers, keeps calling a tool | A model bound with `tool_choice` was passed to `create_agent` | Force only one standalone call; give `create_agent` the plain model |
| More model calls than expected | The agent retried with other words or called tools in parallel | Normal for agents; state a range, not a fixed number |
| Many LangSmith traces from one run | `ChatPromptTemplate.invoke` and `tool.invoke` each create a trace | Use `format_messages`; keep tracing off unless approved |
| `ValidationError` from the tool before it runs | The model or you passed a value that does not match the schema | Expected: the schema is a guardrail; inside `create_agent` the error goes back to the model |
| `await` fails in a script / `asyncio.run` fails in Jupyter | Different event loops | Top-level `await` in notebooks; `asyncio.run(main())` in scripts |
| The agent hangs on a tool call | The HTTP request has no timeout | `httpx.get(..., timeout=15)` and return `unavailable` on `httpx.HTTPError` |
| A 400 from the API ends the run | `response.raise_for_status()` or `response.json()` on an error body | Check `response.is_error` and return the trimmed `response.text` as data |
| `LangChainBetaWarning` when importing `langchain.mcp` | The integration is in beta | Expected with the locked version; it replaces `langchain-mcp-adapters` |
| `NotImplementedError: StructuredTool does not support sync invocation` | MCP tools are async | `await tool.ainvoke(...)` and `await agent.ainvoke(...)`; `asyncio.run(main())` in scripts |
| "`X` is not a valid tool" | With several servers the names carry the server as prefix (`credits_check_credit`); with one server they do not | Use the names `list_tools()` printed |
| One `INFO … Proxy detected connected client` line per tool call | FastMCP logs at INFO | `logging.getLogger("fastmcp").setLevel(logging.WARNING)` |
| Each document search takes seconds over stdio | The adapter opens a session per call, so a stdio server starts again and rebuilds its index | Expected with stdio; run the server over HTTP to keep one process |
| The agent stops with `__interrupt__` in the state | A server asked the person (elicitation) | Show the question, resume with `Command(resume={"responses": {key: answer}})` and the same `thread_id` |
| `RuntimeError: Cannot use Command(resume=...) without checkpointer` | The agent paused for an elicitation but has nowhere to keep its state | `create_agent(..., checkpointer=InMemorySaver())` and the same `thread_id` on the pause and the resume |
| The tool runs again after the answer | Resuming repeats the tool call from the start | Expected; the server must not act before asking |
| The model API rejects a file block after a tool call | The tool returned a `resource_link`, which the adapter turns into a file with a non-web URL | Use servers whose tools return text or JSON; links belong in prompts |
| The agent answers in English to a Spanish thread without context | The system prompt does not fix the language | Add "answer always in <language>" to the system prompt |
