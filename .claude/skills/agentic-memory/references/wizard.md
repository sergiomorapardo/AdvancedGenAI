# The wizard, step by step

Run the design as a wizard. In each step use **AskUserQuestion**: one question, two to four options, the recommended one first with "(Recommended)", and a `preview` with an ASCII diagram of how the app looks with that option. Base diagrams are in `references/diagrams.md`: adapt them with the real names of the person's app. Before each question write one or two lines on what is decided and why it matters; after each answer confirm in one line what was settled.

Skip the steps the request already answers. If the person says "you decide", pick the recommended option in every step and continue. If AskUserQuestion is not available, ask the same question in text with numbered options and the diagram in a code block.

| Step | Question | Typical options | Diagram |
|---|---|---|---|
| 0 · Goal | Which conversation must it hold? | 2–3 one-sentence goals with a first question and a follow-up. Recommend the smallest | "conversation" |
| 1 · Memory | Do people ask follow-ups that depend on earlier turns? | Agent with a checkpointer and the search as a tool (Recommended when the agent must decide whether to search) · Fixed rewrite of each follow-up (hand over to llm-rag) · No memory, each question is complete | "conversation" |
| 2 · Thread | What is one conversation, and where does its `thread_id` come from? | The user's session (Recommended) · One per person and case, such as `<user>:<case>` (two people never share a thread) | "conversation" |
| 3 · Checkpointer | Where is the conversation kept? | `InMemorySaver`, dies with the process (Recommended for notebooks and scripts) · A database checkpointer for a service (the repo's API uses PostgreSQL) | "the loop" |
| 4 · Guardrails | What must it never do? (multiSelect) | Search again for data that changes (Recommended) · Never share a thread between people (Recommended) · Trim or summarize long threads (no verified example yet: say so before building it) | "guardrails" |
| 5 · Approval | Does the app act (disburse, write, send)? If so, what does the person see and what may they edit? | No action, it only answers (Recommended when it only reads) · Pause before the action with approve, edit and reject: a graph node with `interrupt` when code decides who needs a person, or `HumanInTheLoopMiddleware` on an agent's tool (Recommended when it writes) · Approve and reject only | "approval" |
| 6 · Observability | How do we see what happened? | Local run log only (Recommended) · Run log + LangSmith traces (counted against the project budget and approved before each run) | "observability" |

Close the wizard with a **blueprint** before writing code: an ASCII diagram of the final app with its tools, the thread and where its id comes from, the checkpointer, the guardrails and, if it acts, the gate and the action node, the list of files to create and the expected cost of one run (model calls and traces). Ask for confirmation with a last AskUserQuestion: "Build it like this (Recommended)" · "Change something".

## Use the diagrams to explain too

When the person asks "why does it forget?", "what is a checkpointer?", "rewrite or let it search?", answer with the matching diagram from `references/diagrams.md` and the table in `references/concepts.md`, and ground it in their app. On delivery, draw the blueprint again with what was actually built.

To measure the app afterwards on a dataset, with code evaluators or a judge, close with a pointer to the eval-experiments skill instead of adding an evaluation step here.
