# The wizard, step by step

Run the design as a wizard. In each step use **AskUserQuestion**: one question, two to four options, the recommended one first with "(Recommended)", and a `preview` with an ASCII diagram of the server with that option. Base diagrams are in `references/concepts.md`: adapt them with the real names. Before each question write one or two lines on what is decided and why it matters; after each answer confirm in one line what was settled.

Skip the steps the request already answers. If the person says "you decide", pick the recommended option in every step and continue. If AskUserQuestion is not available, ask the same question in text with numbered options and the diagram in a code block.

| Step | Question | Typical options | Diagram |
|---|---|---|---|
| 0 · Need | What should several apps share? Who will use it? | An existing `@tool` or query · A table or database · A folder of documents (search with citations) · A public HTTP API without a key. If only one app needs it, recommend keeping a `@tool` and stop unless the person confirms | "who does what" |
| 1 · Primitives | What does each app need from it? (multiSelect) | Tools the model calls (Recommended) · Resources the app reads by URI (a schema, a document) · Prompts the person picks as commands | "primitives" |
| 2 · Data | Where does the data come from, and what stops a write? | SQLite file opened with `mode=ro` (Recommended for synthetic data) · Another database with a read-only user, credentials from environment variables · PDFs with local embeddings · Public API with timeout and errors as data | "data and control" |
| 3 · Output | Does an app read fields from the result? | Typed output with a Pydantic model: the SDK publishes the `outputSchema` (Recommended for rows and figures) · Text (Recommended for fragments with citations) | "output" |
| 4 · Ambiguity | What happens when the input matches several items? | Ask the person with elicitation; clients that cannot ask get every match (Recommended when the person knows the answer) · Return every match and let the model ask · Fail with `ToolError` and the options | "elicitation" |
| 5 · Transport | How do clients reach it? | stdio: each client starts the script (Recommended on one machine) · stdio and `--http`: also one shared process on a port (index built once) · HTTP only, on an internal server (needs authentication; see `references/security.md`) | "transport" |
| 6 · Registration | Where is it registered? | Project `.mcp.json`, versioned with the repo (Recommended for a team server) · Only for this person (`claude mcp add --scope local`) · Not registered: only an agent uses it (then hand over to agentic-workflow) | "registration" |
| 7 · Guardrails | What must it never do? (multiSelect) | Read-only connection (Recommended) · Validated inputs and parameters (Recommended) · Resources limited to an allow list (Recommended) · Limit rows and text sizes · Approval in the client before any tool with effects | "guardrails" |

Close the wizard with a **blueprint** before writing code: an ASCII diagram of the server with its tools, resources and prompts (name, arguments, output), the data source and its control, the transport, where it is registered, the files to create and the checks that will prove it works. The server costs nothing to run; say so, and say that an agent using it does spend model calls. Ask for confirmation with a last AskUserQuestion: "Build it like this (Recommended)" · "Change something".

## Use the diagrams to explain too

When the person asks "what is MCP?", "why not an API?", "tool or resource?", answer with the matching diagram and table in `references/concepts.md`, grounded in their server. On delivery, draw the blueprint again with what was actually built.

To build the agent that uses the server, close with a pointer to the agentic-workflow skill. To review a server from someone else, go to `references/security.md`.
