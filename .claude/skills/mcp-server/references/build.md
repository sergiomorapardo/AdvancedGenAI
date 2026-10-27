# Build: pieces, files and rules

## Contents

- Which piece to use
- Files to generate
- Rules that are not negotiable
- Project specifics

## Which piece to use

- **Server** (`credits_server.py`): `mcp = MCPServer("<name>", instructions="<what it holds, read only>", log_level="WARNING")`. The name becomes the tool prefix in some clients (`credits_check_credit`): short, lowercase, no spaces.
- **Tool**: `@mcp.tool(annotations=ToolAnnotations(read_only_hint=True, open_world_hint=False))`. The function name, its docstring and its types are what the model reads. Describe each argument with `Annotated[str, Field(description="...")]` and list accepted values there: the SDK does **not** read a docstring `Args:` section. A tool with effects declares `destructive_hint` and `idempotent_hint` instead, and the client must ask for approval.
- **Errors**: `raise ToolError("message the model can act on")` (`mcp.server.mcpserver.exceptions`). The client gets `is_error=True` and the text. Any other exception arrives as a generic error without details, which is right for unexpected failures.
- **Read-only data**: open SQLite with `sqlite3.connect(f"{path.resolve().as_uri()}?mode=ro", uri=True)`; another database with a read-only user. Values go as `?` parameters; when the number of terms varies, repeat only the placeholder. Put a `LIMIT`.
- **Accents and case**: register a function in SQLite (`create_function("unaccent", 1, ...)`) so "credito" finds "Crédito"; PostgreSQL has `unaccent` and `ILIKE`.
- **Typed output**: return a Pydantic model or `list[Model]` with a `Field(description=...)` per field. The SDK publishes the `outputSchema` and fills `structured_content` (a list arrives as `{"result": [...]}`); the model receives the same data as JSON.
- **Elicitation** (`credits_server.py`): a resolver `async def choose(..., ctx: Context) -> Choice | Elicit[Choice]` returns the data when it already knows it, or `Elicit(message, Model)` to ask. The tool receives it as `choice: Annotated[ElicitationResult[Choice], Resolve(choose)]` and checks `isinstance(choice, AcceptedElicitation)`. Ask only when `ctx.client_capabilities.elicitation` exists and there is a real choice; otherwise return every match. For a closed list of options, build the model with `create_model` and a `Literal[...]` of the values. Ask for choices, never for passwords or keys.
- **Fixed resource**: `@mcp.resource("schema://<name>", mime_type="text/plain")`.
- **Resource template** (`docs_server.py`): `@mcp.resource("docs://{name}")` with a function argument of the same name. Check the name against an allow list built from the folder, and raise `ResourceError` with the valid names.
- **Prompt** (`docs_server.py`): `@mcp.prompt(title="...")` returns `list[UserMessage]`. A `UserMessage(ResourceLink(type="resource_link", uri=..., name=..., mime_type=...))` points to a resource without copying it. Keep `resource_link` out of tool results that a LangChain agent will use (see `references/gotchas.md`).
- **Slow setup** (an index, a client): build it lazily with `@cache` on first use, never at import, so `list_tools` stays fast and the hook can load the server.
- **Transport**: end with `mcp.run("streamable-http", port=<port>)` when `--http` is in `sys.argv`, otherwise `mcp.run()` (stdio). Use one port per server.
- **Configuration**: paths and connection strings from environment variables with a safe default (`CREDITS_DB`, `DOCUMENTS_DIR`). Resolve default paths from `Path(__file__)`, never from the working directory: clients start the script from anywhere.
- **Noisy libraries**: filter their warnings and progress bars before importing them (`warnings.filterwarnings`, `HF_HUB_VERBOSITY=error`); they write to stderr and reach the client as noise.

## Files to generate

Copy the closest example, change the content and delete the pieces the blueprint does not use. In a new folder named after the server:

```
<servers folder>/<server-name>/
  README.md        # what it shares, tools/resources/prompts, how to run and register it, controls
  server.py        # from the closest example
  project.py       # only if it needs project settings; copied from references/examples/project.py
  data/<name>.sql  # synthetic seed; the .db it creates goes in .gitignore
  documents/       # only for document search: synthetic or authorized PDFs
  .gitignore
```

`references/project.md` says where the servers folder is in this project. The `README.md` lists each tool with its arguments and one example result, the command for stdio and HTTP, the registration snippet and the controls (what stops a write, which files can be read).

## Rules that are not negotiable

1. **No model inside the server.** Retrieval with local embeddings is fine; generating text is the client's job.
2. **No `print()`** anywhere in a stdio server. The repository hook rejects it.
3. **Read only** below the server (connection, file, user). Writing needs a separate tool with `destructive_hint=True`, approval in the client and a decision by the person; this skill does not build it.
4. **Parameters, validation and limits** on every input; never SQL, paths or shell commands from the model.
5. **Every tool and argument described**; descriptions describe the tool, they never address the model about other tools, hidden steps or what not to tell. The hook flags those phrases.
6. **Resources limited** to an allow list; never open a path that came from the client.
7. **No secrets** in code, descriptions or results; credentials from environment variables, never echoed in errors.
8. **Synthetic or authorized data** only, 8–12 rows with one or two traps (zero availability, an ambiguous name).
9. **Names in English** for files, functions, classes and variables.
10. **Keep it simple**: the smallest server that meets the blueprint.

## Project specifics

Where servers live, the SDK version, how they are registered and the hooks that check what you write are in `references/project.md`. Read it before generating files.
