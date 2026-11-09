# Concepts: which piece for which need

| Need | Piece | Why |
|---|---|---|
| Same steps every time | Chain: `prompt \| model \| parser` | One call, predictable cost, easy to test |
| Fill holes in a fixed message | `ChatPromptTemplate` | Separates instructions from data |
| Code must read fields from the answer | `with_structured_output(Model)` | The shape is validated; a `ValidationError` names the field |
| The prompt changes with the data (optional fields, lists) | Jinja template in `prompts/` | `if` and `for` instead of string concatenation; versioned and reviewed like code |
| Fail when a variable is missing | `Environment(undefined=StrictUndefined)` | LangChain's Jinja is lenient and renders an empty string |
| Compare two prompt variants | Same input, two templates, compare field by field | One run proves nothing; to decide, a dataset and two experiments (eval-experiments) |
| The next step depends on data the model must fetch | A tool and an agent | The llm-tools skill builds it |
| The answer lives in documents | RAG | The llm-rag skill builds it |
| Explicit state, routing, parallel branches | LangGraph `StateGraph` | The agentic-patterns skill builds it |

## Who controls what

- **The prompt suggests.** The model may ignore a rule in the system prompt.
- **The code enforces.** A read-only tool cannot write, whatever the model asks. An argument schema rejects `"forty"` before the function runs. A tool that returns `{"status": "not_found"}` lets the agent explain the gap instead of crashing.
- When a rule must always hold, implement it in code. A rule in a prompt or a `SKILL.md` is a request, not a control.

## Chain first

Start with the smallest shape. Move from a chain to an agent only when the person can name the data the model must fetch and why the steps cannot be fixed in advance.
