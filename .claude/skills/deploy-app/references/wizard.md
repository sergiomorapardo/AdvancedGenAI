# Decisions, one at a time

Use **AskUserQuestion** for each decision: one question, two to four options, the recommended one first with "(Recommended)", and a `preview` with an ASCII sketch. Skip what the request already answers. With "you decide", take the recommended options.

| Step | Question | Typical options |
|---|---|---|
| 1 · What is served | Which app, and does it expose a factory `make_graph(*, checkpointer=None)`? | Wrap the existing graph in a factory (Recommended) · The app is a plain chain: serve it without a checkpointer (no memory between requests) |
| 2 · Where state lives | Must a conversation survive a restart of the API? | PostgreSQL with `PostgresSaver` (Recommended for anything people use) · In memory, for a local trial only |
| 3 · Thread identity | Where does the `thread_id` come from? | The client's `chat_id` in the URL (Recommended) · A session id the server issues · Never a customer code shared by several conversations |
| 4 · Answers | Does the person need to see the answer as it is written? | Both endpoints: complete and SSE stream (Recommended) · Only complete answers |
| 5 · What the client sees | Which node writes to the person? | Only the `model` node; tool results stay inside (Recommended) · Also tool calls, for an internal debugging screen |
| 6 · Exposure | Who calls it? | Only this machine, `127.0.0.1` (Recommended for the course) · A private network, behind authentication and a per-user rate limit (needs work this skill does not generate) |
| 7 · Observability | How is it watched? | Token log per turn (Recommended) · Plus LangSmith traces in a project for this environment (approved, against the budget) |
| 8 · Studio and CI | Should the graph appear in Studio and be checked in CI? | Register it in `langgraph.json` and run the startup check (Recommended) · Not now |

```
client ──POST /chat/{chat_id}──► FastAPI ──thread_id──► graph ⇄ checkpointer (PostgreSQL)
       ◄──── JSON history ─────
       ──POST …/stream────────► FastAPI ──► graph.stream(messages) ──► only "model" chunks
       ◄──── SSE data: {...} ──
```

Close with a plan before writing code: the endpoints, where state lives, what is hidden, the exposure, the commands and the cost of one turn and of the smoke test. Confirm with a last AskUserQuestion: "Build it like this (Recommended)" · "Change something".
