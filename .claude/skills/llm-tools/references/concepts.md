# Concepts: which piece for which need

| Need | Piece | Why |
|---|---|---|
| A fact lives in another system | `@tool` | The model asks; your code executes and controls what is possible |
| The next step depends on what a tool returns | `create_agent` | Runs model → tool → model until the model answers in text |
| The first step must always be a lookup | `bind_tools(..., tool_choice=name)` | Forces that call; forcing it on every turn would never let the model answer |
| The answer must use the tool's figure | Deterministic check over the `ToolMessage` | A convincing answer is not evidence |
| Several apps need the same tools or documents | Tools of an MCP server, loaded with `MCPAdapter` | One implementation, discovered by every client; the agent does not change when the server does, if the contract holds |
| Only the person knows which item they meant | Elicitation from the server: the agent pauses and resumes | The model must not guess for the person |
| Fixed, known steps | A chain | Cheaper and predictable: the llm-prompts skill builds it |
| The answer lives in documents, not in a table | RAG | The llm-rag skill builds it |
| Remember a conversation between invokes | A checkpointer and a `thread_id` | The agentic-memory skill builds it |
| Explicit state, routing, parallel branches | LangGraph `StateGraph` | The agentic-patterns skill builds it |

## Who controls what

- **The prompt suggests.** The model may ignore a rule in the system prompt.
- **The code enforces.** A read-only tool cannot write, whatever the model asks. An argument schema rejects `"forty"` before the function runs. A tool that returns `{"status": "not_found"}` lets the agent explain the gap instead of crashing.
- When a rule must always hold, implement it in code. A rule in a prompt or a `SKILL.md` is a request, not a control.

## Tool or documents

- A **tool** answers from structured data that changes: balances, overdue amounts, an exchange rate. It returns figures.
- **RAG** answers from text that someone wrote: rules, procedures, policies. It returns fragments to quote.
- Many apps need both: the overdue amount with a tool and the restructuring rule from a policy.
- The retriever always returns `k` fragments, even when none helps. What prevents a made-up answer is the prompt rule "say it is not in the documents" plus a citation check, just as `not_found` does for tools.

## Chain first

Start with the smallest shape. Move from a chain to an agent only when the person can name the data the model must fetch and why the steps cannot be fixed in advance.
