# Concepts: which piece for which need

| Need | Piece | Why |
|---|---|---|
| The answer lives in documents (manuals, policies, data sheets), not in a table | RAG: retrieve fragments, answer only with them | The model does not know your documents and they do not fit in every prompt |
| Cite where each fact comes from | `source` and `page` in the metadata, `[file, p. N]` in the context | Without metadata there is no citation; a regex can check it |
| Find by meaning, not by words | Embeddings + cosine similarity | "when does the money arrive?" is close to "disbursed the same business day" |
| Keep the index between runs | FAISS (files) or Chroma (collection with filters) | Recomputing embeddings costs time, or money with a provider |
| Codes, product names, exact figures | Keyword search (BM25), alone or fused with embeddings | Embeddings blur exact terms; measure before choosing (eval-experiments) |
| A follow-up question has no product or topic ("and after that?") | Rewrite it with the history, then retrieve | Passing the history to the model does not fix retrieval: the retriever only sees the question |
| Colloquial questions miss the right fragment | Multi-query: several versions, union of fragments | Compensates the limits of similarity search; costs one call and adds fragments |
| Data that changes: balances, overdue amounts | A tool | The llm-tools skill builds it |
| An agent that remembers the thread and decides whether to search | A checkpointer and the retriever as a tool | The agentic-memory skill builds it |
| Explicit state, routing, parallel branches | LangGraph `StateGraph` | The agentic-patterns skill builds it |

## Tool or documents

- A **tool** answers from structured data that changes: balances, overdue amounts, an exchange rate. It returns figures.
- **RAG** answers from text that someone wrote: rules, procedures, policies. It returns fragments to quote.
- Many apps need both: the overdue amount with a tool and the restructuring rule from a policy.
- The retriever always returns `k` fragments, even when none helps. What prevents a made-up answer is the prompt rule "say it is not in the documents" plus a citation check, just as `not_found` does for tools.

## Rewrite or let the agent search

- **Rewrite in a chain**: you decide that every follow-up is rewritten and searched. Predictable: 2 calls per follow-up, and the rewrite can be printed and checked.
- **Agent with a checkpointer**: the agent decides **whether** to search and **what** to search, guided by the system prompt and the tool docstring. It may answer from fragments already in the thread, which saves a call or reuses stale fragments.
- The history grows with every turn: each call reads all previous questions, fragments and answers. Long conversations cost more and need trimming or a summary.
