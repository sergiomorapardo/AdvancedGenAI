# Concepts: which piece for which need

| Need | Piece | Why |
|---|---|---|
| Same steps every time | Chain: `prompt \| model \| parser` | One call, predictable cost, easy to test |
| Fill holes in a fixed message | `ChatPromptTemplate` | Separates instructions from data |
| Code must read fields from the answer | `with_structured_output(Model)` | The shape is validated; a `ValidationError` names the field |
| The prompt changes with the data (optional fields, lists) | Jinja template in `prompts/` | `if` and `for` instead of string concatenation; versioned and reviewed like code |
| Fail when a variable is missing | `Environment(undefined=StrictUndefined)` | LangChain's Jinja is lenient and renders an empty string |
| Compare two prompt variants | Same input, two templates, compare field by field | One run proves nothing; to decide, a dataset and two experiments (evaluate-app) |
| A fact lives in another system | `@tool` | The model asks; your code executes and controls what is possible |
| The next step depends on what a tool returns | `create_agent` | Runs model → tool → model until the model answers in text |
| The first step must always be a lookup | `bind_tools(..., tool_choice=name)` | Forces that call; forcing it on every turn would never let the model answer |
| The answer must use the tool's figure | Deterministic check over the `ToolMessage` | A convincing answer is not evidence |
| The answer lives in documents (manuals, policies, data sheets), not in a table | RAG: retrieve fragments, answer only with them | The model does not know your documents and they do not fit in every prompt |
| Cite where each fact comes from | `source` and `page` in the metadata, `[file, p. N]` in the context | Without metadata there is no citation; a regex can check it |
| Find by meaning, not by words | Embeddings + cosine similarity | "when does the money arrive?" is close to "disbursed the same business day" |
| Keep the index between runs | FAISS (files) or Chroma (collection with filters) | Recomputing embeddings costs time, or money with a provider |
| Codes, product names, exact figures | Keyword search (BM25), alone or fused with embeddings | Embeddings blur exact terms; measure before choosing (evaluate-app) |
| A follow-up question has no product or topic ("and after that?") | Rewrite it with the history, then retrieve | Passing the history to the model does not fix retrieval: the retriever only sees the question |
| Colloquial questions miss the right fragment | Multi-query: several versions, union of fragments | Compensates the limits of similarity search; costs one call and adds fragments |
| Remember a conversation between invokes | `create_agent(..., checkpointer=...)` + `thread_id` | Each `invoke` starts empty; the checkpointer saves and reloads the messages of a thread |
| Several apps need the same tools or documents | Tools of an MCP server, loaded with `MCPAdapter` | One implementation, discovered by every client; the agent does not change when the server does, if the contract holds |
| Only the person knows which item they meant | Elicitation from the server: the agent pauses and resumes | The model must not guess for the person |
| Explicit state, routing, parallel branches | LangGraph `StateGraph` | Not yet in this skill |
| Human approval before acting | LangGraph interrupts | Not yet in this skill |

## Who controls what

- **The prompt suggests.** The model may ignore a rule in the system prompt.
- **The code enforces.** A read-only tool cannot write, whatever the model asks. An argument schema rejects `"forty"` before the function runs. A tool that returns `{"status": "not_found"}` lets the agent explain the gap instead of crashing.
- When a rule must always hold, implement it in code. A rule in a prompt or a `SKILL.md` is a request, not a control.

## Tool or documents

- A **tool** answers from structured data that changes: balances, overdue amounts, an exchange rate. It returns figures.
- **RAG** answers from text that someone wrote: rules, procedures, policies. It returns fragments to quote.
- Many apps need both: the overdue amount with a tool and the restructuring rule from a policy.
- The retriever always returns `k` fragments, even when none helps. What prevents a made-up answer is the prompt rule "say it is not in the documents" plus a citation check, just as `not_found` does for tools.

## Rewrite or let the agent search

- **Rewrite in a chain**: you decide that every follow-up is rewritten and searched. Predictable: 2 calls per follow-up, and the rewrite can be printed and checked.
- **Agent with a checkpointer**: the agent decides **whether** to search and **what** to search, guided by the system prompt and the tool docstring. It may answer from fragments already in the thread, which saves a call or reuses stale fragments.
- The history grows with every turn: each call reads all previous questions, fragments and answers. Long conversations cost more and need trimming or a summary.

## Chain first

Start with the smallest shape. Move from a chain to an agent only when the person can name the data the model must fetch and why the steps cannot be fixed in advance.
