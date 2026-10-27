# The wizard, step by step

Run the design as a wizard. In each step use **AskUserQuestion**: one question, two to four options, the recommended one first with "(Recommended)", and a `preview` with an ASCII diagram of how the app looks with that option. Base diagrams are in `references/diagrams.md`: adapt them with the real names of the person's app. Before each question write one or two lines on what is decided and why it matters; after each answer confirm in one line what was settled.

Skip the steps the request already answers. If the person says "you decide", pick the recommended option in every step and continue. If AskUserQuestion is not available, ask the same question in text with numbered options and the diagram in a code block.

| Step | Question | Typical options | Diagram |
|---|---|---|---|
| 0 · Idea | What do you want to build? Only if the request is vague ("something for sales") | Option 1: a small first app for the person's area (customer care, collections, risk, compliance, operations, analytics) built on a question they ask every week. Options 2–3: a smaller and a slightly bigger variant | "shapes" |
| 1 · Goal | Which sentence describes what it must solve? | 2–3 one-sentence goals, from smallest to most ambitious. Recommend the smallest | "the loop" |
| 2 · Shape | Are the steps fixed, or do they depend on data the model must fetch? | Chain, fixed steps · Agent with tools · Graph with explicit state (not yet in this skill) | "chain or agent" |
| 3 · Prompt | Does the prompt change with the data? | Inline `ChatPromptTemplate` · Jinja template in `prompts/` with `StrictUndefined` (recommended when fields are optional or lists vary) | "prompt" |
| 4 · Output | Does someone or some code read fields from the answer? | Structured output with Pydantic (Recommended) · Free text | "output" |
| 5 · Data and tools | Where does the data come from? (multiSelect) | One read-only tool over synthetic data (Recommended for tables) · Several tools, the agent picks · A public HTTP API without a key (`api_tool.py`) · A system of the project (see `references/project.md`) · Documents: answer from PDFs with citations (RAG, `rag.py`) · Tools of MCP servers that the team already shares (`mcp_agent.py`; to build a server, the mcp-server skill) | "data", "tool or documents" |
| 5b · Documents | Only with documents. Where does the index live? | In memory, rebuilt each run (Recommended for a first app and small corpora) · FAISS files, loaded without recomputing · Chroma collection, with metadata filters (`vector_store.py`) | "where the index lives" |
| 5c · Embeddings | Only with documents. Which embeddings model? | Open multilingual model, local (Recommended: no key, no cost, documents stay on the machine; the project's model is in `references/project.md`) · A provider (needs its own key and budget; Anthropic has none) | "RAG" |
| 5d · Conversation | Will people ask follow-up questions ("and after that?")? | One question per run, no history (Recommended if each question is complete) · Chain: rewrite the follow-up with the history before retrieving (`conversational_rag.py`; fixed steps, 2 calls per follow-up) · Agent with the retriever as a tool and a checkpointer per `thread_id` (`memory_agent.py`; the agent decides whether to search) · Add multi-query for colloquial questions (one more call, more fragments) | "conversation" |
| 5e · MCP servers | Only with MCP servers. How does the agent reach them, and what happens when a server asks the person? | stdio, the agent starts each server (Recommended on one machine) · HTTP URL of a running server · If a server uses elicitation: checkpointer and a pause for the person (Recommended; without a checkpointer the agent pauses but cannot resume) | "MCP" |
| 6 · Guardrails | What must it never do? (multiSelect) | Read-only tools (Recommended) · Errors returned as data (Recommended) · Outward actions only as drafts · Force a first lookup with `tool_choice` · Deterministic answer check | "guardrails" |
| 7 · Observability | How do we see what happened? | Local run log only (Recommended) · Run log + LangSmith traces (counted against the project budget and approved before each run) | "observability" |

Close the wizard with a **blueprint** before writing code: an ASCII diagram of the final app with its prompt, tools or documents and index, conversation handling, output schema and guardrails, the list of files to create and the expected cost of one run (model calls and traces). Ask for confirmation with a last AskUserQuestion: "Build it like this (Recommended)" · "Change something".

If the goal is solved by fixed, known steps, say it in step 1 or 2: that is a chain or a script, and an agent is more expensive and less predictable. Continue with an agent only if the person confirms.

## Use the diagrams to explain too

When the person asks "what is a tool?", "chain or agent?", "why Jinja?", answer with the matching diagram from `references/diagrams.md` and the table in `references/concepts.md`, and ground it in their app. On delivery, draw the blueprint again with what was actually built.

To measure the app afterwards on a dataset, with code evaluators or a judge, close with a pointer to the evaluate-app skill instead of adding an evaluation step here.
