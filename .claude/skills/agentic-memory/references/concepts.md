# Concepts: which piece for which need

| Need | Piece | Why |
|---|---|---|
| Remember a conversation between invokes | `create_agent(..., checkpointer=...)` + `thread_id` | Each `invoke` starts empty; the checkpointer saves and reloads the messages of a thread |
| A follow-up question has no product or topic ("and how many times can I do it?") | Rewrite it with the history, then retrieve | Passing the history to the model does not fix retrieval: the retriever only sees the question |
| Human approval before acting | `interrupt()` in a node + `Command(resume=...)` on the same thread (`approval.py`) | The checkpoint keeps the paused state; the answer comes back as the value of `interrupt()` |
| The approval belongs to an agent's tool | `HumanInTheLoopMiddleware(interrupt_on={...})` (`approval.py`) | The tool does not run until a person approves, edits or rejects the call |
| One question per run, or a fixed rewrite of each follow-up | A chain, no memory | The llm-rag skill builds it |
| Explicit state, routing, parallel branches | LangGraph `StateGraph` | The agentic-patterns skill builds it |

## Rewrite or let the agent search

- **Rewrite in a chain**: you decide that every follow-up is rewritten and searched. Predictable: 2 calls per follow-up, and the rewrite can be printed and checked.
- **Agent with a checkpointer**: the agent decides **whether** to search and **what** to search, guided by the system prompt and the tool docstring. It may answer from fragments already in the thread, which saves a call or reuses stale fragments.
- The history grows with every turn: each call reads all previous questions, fragments and answers. Long conversations cost more and need trimming or a summary.

## Where the person approves

- **Gate the writes, not the reads.** Looking up a balance or a policy changes nothing; disbursing, sending or writing does. Asking for every step tires the reviewer into approving without reading.
- **Show the exact action and its evidence** in the value passed to `interrupt()`: what, how much, where, the figure that justifies it and the options. A vague "approve?" gets approved blind.
- **Decide with data, not with the model's wording.** Whether there is anything to approve (the amount against the limits) is a comparison in code; the model's review informs the person.
- **Edit in the answer or in the state.** `Command(resume={"decision": "edit", ...})` lets the node that asked validate the edit (recommended). `update_state(config, {...})` changes the paused state from outside, without that validation; the pause stays where it was.
- **The paused node runs again on resume**, from its first line. Anything before `interrupt()` happens twice, so the action lives in its own node after the approval and is idempotent.
- **Only an answer counts.** A cancelled stream, a timeout, a new `invoke` without `Command` or a scheduled prompt are not an approval: the thread stays paused. `Command(resume={})` is read as "no interrupt answered" and pauses again.
- **Where the pause lives.** `InMemorySaver` dies with the process; an approval that may come hours later needs a database checkpointer or a server that keeps threads (the local LangGraph server does, so a graph for it compiles without a checkpointer).
