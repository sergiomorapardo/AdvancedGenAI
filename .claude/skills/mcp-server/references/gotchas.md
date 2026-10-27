# Gotchas: symptom → cause → fix

Observed with the official SDK `mcp` 2.3 and protocol 2026-07-28.

| Symptom | Cause | Fix |
|---|---|---|
| `ModuleNotFoundError: mcp.server.fastmcp` | Version 1 import in an example from the internet | `from mcp.server import MCPServer`; the client is `from mcp import Client` |
| `AttributeError` on `isError`, `structuredContent` or `inputSchema` | Version 2 uses snake_case | `is_error`, `structured_content`, `input_schema`, `output_schema`, `read_only_hint` |
| The model sees no description for an argument | The SDK does not read the docstring `Args:` section | `Annotated[str, Field(description="...")]` |
| The client gets "Error executing tool" without the reason | The tool raised `ValueError` or another exception | `raise ToolError("...")`; a resource raises `ResourceError` |
| The stdio client hangs or fails to parse a message | Something wrote to stdout: a `print()`, a progress bar, a banner | Remove the `print()`; send logs to stderr; silence library output before importing it |
| `SQLite objects created in a thread can only be used in that same thread` | Sync tools run in a worker thread; the connection was created at import | Open the connection inside each call, or pass `check_same_thread=False` for a read-only one |
| `attempt to write a readonly database` | Expected: `mode=ro` | That is the control working; a seed must be created before opening read only |
| `unable to open database file` with `mode=ro` | The database does not exist yet; read-only mode cannot create it | Create it from the seed SQL on first use, then open it read only |
| Tool works from the repo root but not from Claude Code or another folder | A default path is relative to the working directory | Resolve from `Path(__file__).resolve()` |
| "credito" finds nothing | `LIKE` keeps accents | Normalize both sides (`unaccent`) |
| Elicitation never asks | The client did not declare the capability, or only one item matched | Expected: the resolver returns every match; test with an `elicitation_callback` |
| `ctx.elicit()` fails with a new client | It only works with clients of the older protocol (2025-11-25) | Use a resolver with `Resolve(...)` and `Elicit(...)`; it works with both |
| The tool runs twice when the person answers | With 2026-07-28 the client repeats the call with the answer | Expected: do nothing irreversible before the question |
| A resource template returns "resource not found" | The URI argument name differs from the function argument | `@mcp.resource("docs://{name}")` with `def read(name: str)` |
| A LangChain agent fails after a tool returns a `resource_link` | `langchain.mcp` turns it into a file block with a URL that the model API tries to download; `docs://` is not a web URL. `audience` does not avoid it | Return text from tools an agent uses; put links in prompts |
| `address already in use` on `--http` | A previous HTTP server is still running on the port | Stop it (`terminate()`), or use another port |
| The first search takes seconds; next ones are fast | The index is built lazily and kept in the process | Expected; over stdio each new process builds it again |
| The first search hangs | The embeddings model is downloading (~220 MB) | Run it once with network before a demo |
| `npx @modelcontextprotocol/inspector` fails | Node is missing or older than 22.19 | Install Node, or use `inspect_server.py`, which needs only Python |
| The hook says the server does not load | An import fails or setup runs at import time | Fix the import; move slow setup into a `@cache` function |
