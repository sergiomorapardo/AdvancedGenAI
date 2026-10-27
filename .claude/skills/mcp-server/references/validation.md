# Check, register and deliver

Nothing here calls a model, so no step needs a paid-run approval. Running the server does execute its code: for a server you did not write, read `references/security.md` first.

## 1. Checks with real clients

Run them in a short `uv run python` snippet from the repo root, with `from mcp import Client, StdioServerParameters`. Print what you check; do not only assert it.

1. **In memory**: import the module and use `async with Client(module.mcp) as client:`. `list_tools()` shows each name, description, `input_schema` (every property with a description) and `output_schema` when the output is typed.
2. **Calls**: `call_tool(name, args)` for a found case (check the figure against the seed), a not-found case (empty result, not an error), an invalid argument (`is_error=True` with the `ToolError` message) and an injection attempt such as `"x' OR '1'='1"` (no rows).
3. **Read only**: with the server's own `connect()`, a `DELETE` raises `sqlite3.OperationalError` (or the database's permission error).
4. **Resources and prompts**: `read_resource(uri)` returns the content; a name outside the allow list, such as `docs://../.env`, is rejected. `get_prompt(name, args)` returns the messages, and a `resource_link` points to a URI that `read_resource` can open.
5. **Elicitation**: an `elicitation_callback` that prints `params.message` and the options and returns `ElicitResult(action="accept", content={...})` gets the chosen rows; one that returns `action="decline"` gets every match; a client without callback gets every match.
6. **stdio**: `Client(StdioServerParameters(command=sys.executable, args=["<path>/server.py"]))` from the repo root and from another folder (`cwd=...`): the same tools, and the call works. This proves paths resolve from the script and that nothing writes to stdout.
7. **HTTP**, if chosen: start `subprocess.Popen([sys.executable, "<path>/server.py", "--http"])`, wait until the port accepts connections, connect with `Client("http://127.0.0.1:<port>/mcp")`, call one tool, then `terminate()` and `wait()`. A second start on a busy port fails: stop the first one.
8. **Review**: `uv run python <skill>/references/examples/inspect_server.py -- python <path>/server.py` ends with "No flags". With `--snapshot`, save the approved definitions next to the server's README.

The project's hooks run part of this after every edit (`references/project.md`); they do not replace these checks.

## 2. Register

Only where the person chose in the wizard:

- **Project**: add an entry to `.mcp.json` at the repo root with `{"command": "uv", "args": ["run", "python", "<path>/server.py"]}` (or `{"type": "http", "url": "..."}`). Validate the JSON. Claude Code asks every person to approve project servers; `/mcp` shows their status and tools.
- **Local**: give the person the `claude mcp add --scope local <name> -- uv run python <path>/server.py` command to run themselves.
- **An agent**: hand over to agentic-workflow with the `mcpServers` entry.

Optional, if Node 22.19 or newer is installed: `npx @modelcontextprotocol/inspector --cli --config .mcp.json --server <name> --method tools/list` lists the tools from the terminal, and without `--cli` it opens the web view to try each tool and answer elicitations by hand.

## 3. Delivery

Answer with: the file paths, the list of tools, resources and prompts with one real result each, the review report, the commands for stdio and HTTP, where it was registered and how to see it (`/mcp`), and the final blueprint. State that the server makes no model calls and that an agent using it does. Suggest a single next step: connecting it to an agent with agentic-workflow, or a second client.
