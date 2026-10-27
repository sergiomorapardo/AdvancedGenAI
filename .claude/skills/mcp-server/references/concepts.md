# Concepts and diagrams

Use the diagrams in the `preview` of AskUserQuestion and in explanations; change the names to the person's server. At most ~16 lines and ~60 columns per preview. Show a round trip with two arrows, one each way, never a double-headed one.

## Contents

- Which piece for which need
- Who does what
- Primitives
- Data and control
- Output
- Elicitation
- Transport
- Registration
- Guardrails
- Protocol and SDK versions

## Which piece for which need

| Need | Piece | Why |
|---|---|---|
| One app calls one function | `@tool` in the app | No process, no protocol; MCP adds nothing yet |
| Several apps need the same capability | MCP server | One implementation, one contract that every MCP client discovers |
| A system already has an API | MCP server in front of it, or no server | MCP standardizes discovery and use for models; the server can call the API |
| The model must run an operation with arguments | Tool | The model proposes the call; the client and the server execute it |
| The app must read content by name (a schema, a document) | Resource with a URI | The app decides what enters the context; the model does not ask for it |
| The person picks a ready-made task ("prepare a dispute") | Prompt | A template with arguments; getting it does not call a model |
| An app reads fields of the result | Typed output → `outputSchema` | The client can validate and render rows without parsing text |
| Point to a large document without copying it | `resource_link` in a prompt | The client decides whether to read it |
| Only the person knows which item they meant | Elicitation | The server asks the person through the client, in the middle of the call |
| Many servers and tools | Connect only what the task needs; tool search in the client | Every definition is sent to the model on every call |

## Who does what

```
HOST (Claude Code, a LangChain app)
  model ── proposes check_credit(...) ──▶ app (permissions)
  app ── one MCP client per server ──▶ client
client ── tools/call ──────────────────▶ SERVER
client ◀── result or is_error ───────── SERVER
                                         │ parameterized query
                                         ▼
                                     data (read only)
```

The model never opens the database; the server does. A server is a role, not a machine: it can run on the same laptop.

## Primitives

```
TOOL               RESOURCE              PROMPT
model proposes     app reads by URI      person picks
check_credit(...)  schema://credits      /summarize_document
runs an operation  returns content       returns messages
```

## Data and control

```
tool ──▶ find_credits(customer, product)
           │ SQL with ? parameters, limits
           ▼
         connect(mode=ro) ──▶ credits.db
           a DELETE fails here, whatever was asked
read_only_hint=True ─ tells the client; enforces nothing
```

## Output

```
-> list[CreditRow]                -> str
outputSchema published            text for the model
structured_content: rows          content[0].text: fragments
an app renders a table            with [file, p. N]
```

## Elicitation

```
client ── check_credit("C-1042") ──────▶ server
client ◀── input required: which credit? ─ server
person ◀── form: CEX / CLI
person ── CLI ──▶ client
client ── same call + answer ──────────▶ server
client ◀── row of CLI ────────────────── server
client without elicitation: every matching row
```

The answer is `accept` with the data, `decline` or `cancel`. In a LangChain agent the question pauses the graph with an interrupt; in Claude Code a dialog opens.

## Transport

```
STDIO                              STREAMABLE HTTP
client ── starts ──▶ server.py     agent ──────┐
one process per client             Claude Code ┼──▶ :8001/mcp
stdout = protocol, logs = stderr   other app ──┘    one process
nothing listens on the network     needs auth beyond localhost
```

The contract is the same; only how messages travel changes. HTTP does not cache by itself: an index built once per process is the server's own code (`@cache`).

## Registration

```
.mcp.json (repo, shared)           local scope (one person)
{"mcpServers": {                   claude mcp add --scope local
  "credits": {"command": "uv",       credits -- uv run python ...
    "args": ["run", "python",
             "servers/credits.py"]}}}
Claude Code asks to approve it; /mcp lists servers and tools
```

The same `mcpServers` shape is what LangChain's `MCPAdapter` reads.

## Guardrails

```
model asks ──▶ client: approval for tools with effects
           ──▶ schema: rejects bad types before the function
           ──▶ tool: validates, ToolError with the reason
           ──▶ query: parameters, LIMIT
           ──▶ connection: read only   ◀── the real control
```

## Protocol and SDK versions

- The protocol has dated versions. With 2026-07-28 there is no session or `initialize`: each request carries what it needs, and elicitation travels as an "input required" answer that the client repeats with the response (multi round-trip). Older clients (2025-11-25) still connect; the SDK serves both. Sampling, roots and server logging are deprecated: do not design around them.
- SDK 2 renamed `FastMCP` to `MCPServer` and has a single `Client` that connects to a server object (in memory), a stdio command or a URL. Examples on the internet with `mcp.server.fastmcp` are version 1.
