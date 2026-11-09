# The wizard, step by step

Run the design as a wizard. In each step use **AskUserQuestion**: one question, two to four options, the recommended one first with "(Recommended)", and a `preview` with an ASCII diagram of how the app looks with that option. Base diagrams are in `references/diagrams.md`: adapt them with the real names of the person's app. Before each question write one or two lines on what is decided and why it matters; after each answer confirm in one line what was settled.

Skip the steps the request already answers. If the person says "you decide", pick the recommended option in every step and continue. If AskUserQuestion is not available, ask the same question in text with numbered options and the diagram in a code block.

| Step | Question | Typical options | Diagram |
|---|---|---|---|
| 0 · Idea | What do you want to build? Only if the request is vague ("something for sales") | Option 1: a small first agent for the person's area built on a question they ask every week. Options 2–3: a smaller and a slightly bigger variant | "shapes" |
| 1 · Goal | Which sentence describes what it must solve? | 2–3 one-sentence goals, from smallest to most ambitious. Recommend the smallest | "the loop" |
| 2 · Shape | Are the steps fixed, or do they depend on data the model must fetch? | Agent with tools · Chain, fixed steps (hand over to llm-prompts) · Graph with explicit state, routing or parallel branches (hand over to agentic-patterns) | "chain or agent" |
| 3 · Data and tools | Where does the data come from? (multiSelect) | One read-only tool over synthetic data (Recommended for tables) · Several tools, the agent picks · A public HTTP API without a key (`api_tool.py`) · A system of the project (see `references/project.md`) · Tools of MCP servers that the team already shares (`mcp_agent.py`; to build a server, the mcp-server skill) · Documents (hand over to llm-rag) | "data", "tool or documents" |
| 3b · MCP servers | Only with MCP servers. How does the agent reach them, and what happens when a server asks the person? | stdio, the agent starts each server (Recommended on one machine) · HTTP URL of a running server · If a server uses elicitation: checkpointer and a pause for the person (Recommended; without a checkpointer the agent pauses but cannot resume) | "MCP" |
| 4 · Guardrails | What must it never do? (multiSelect) | Read-only tools (Recommended) · Errors returned as data (Recommended) · Outward actions only as drafts · Force a first lookup with `tool_choice` · Deterministic answer check | "guardrails" |
| 5 · Observability | How do we see what happened? | Local run log only (Recommended) · Run log + LangSmith traces (counted against the project budget and approved before each run) | "observability" |

If the goal is solved by fixed, known steps, say it in step 1 or 2: that is a chain or a script (llm-prompts), and an agent is more expensive and less predictable. Continue with an agent only if the person confirms.

Close the wizard with a **blueprint** before writing code: an ASCII diagram of the final app with its tools or MCP servers, the system prompt, the answer check and the guardrails, the list of files to create and the expected cost of one run (model calls and traces). Ask for confirmation with a last AskUserQuestion: "Build it like this (Recommended)" · "Change something".

## Use the diagrams to explain too

When the person asks "what is a tool?", "chain or agent?", "why MCP?", answer with the matching diagram from `references/diagrams.md` and the table in `references/concepts.md`, and ground it in their app. On delivery, draw the blueprint again with what was actually built.

To measure the app afterwards on a dataset, with code evaluators or a judge, close with a pointer to the eval-experiments skill instead of adding an evaluation step here.
