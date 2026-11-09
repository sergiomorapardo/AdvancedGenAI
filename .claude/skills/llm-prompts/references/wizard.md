# The wizard, step by step

Run the design as a wizard. In each step use **AskUserQuestion**: one question, two to four options, the recommended one first with "(Recommended)", and a `preview` with an ASCII diagram of how the app looks with that option. Base diagrams are in `references/diagrams.md`: adapt them with the real names of the person's app. Before each question write one or two lines on what is decided and why it matters; after each answer confirm in one line what was settled.

Skip the steps the request already answers. If the person says "you decide", pick the recommended option in every step and continue. If AskUserQuestion is not available, ask the same question in text with numbered options and the diagram in a code block.

| Step | Question | Typical options | Diagram |
|---|---|---|---|
| 0 · Idea | What do you want to build? Only if the request is vague ("something for sales") | Option 1: a small first app for the person's area (customer care, collections, risk, compliance, operations, analytics) built on a question they ask every week. Options 2–3: a smaller and a slightly bigger variant | "shapes" |
| 1 · Goal | Which sentence describes what it must solve? | 2–3 one-sentence goals, from smallest to most ambitious. Recommend the smallest | "the loop" |
| 2 · Shape | Are the steps fixed, or do they depend on data the model must fetch? | Chain, fixed steps (Recommended when the input has everything) · Agent with tools (hand over to llm-tools) · Answers from documents (hand over to llm-rag) | "chain or agent" |
| 3 · Prompt | Does the prompt change with the data? | Inline `ChatPromptTemplate` · Jinja template in `prompts/` with `StrictUndefined` (recommended when fields are optional or lists vary) | "prompt" |
| 4 · Output | Does someone or some code read fields from the answer? | Structured output with Pydantic (Recommended) · Free text | "output" |
| 5 · Observability | How do we see what happened? | Local run log only (Recommended) · Run log + LangSmith traces (counted against the project budget and approved before each run) | "observability" |

If the goal is solved by fixed, known steps, say it in step 1 or 2: that is a chain, and an agent is more expensive and less predictable.

Close the wizard with a **blueprint** before writing code: an ASCII diagram of the final app with its prompt or template, the input it fills and the output schema, the list of files to create and the expected cost of one run (model calls and traces). Ask for confirmation with a last AskUserQuestion: "Build it like this (Recommended)" · "Change something".

## Use the diagrams to explain too

When the person asks "what is a chain?", "chain or agent?", "why Jinja?", answer with the matching diagram from `references/diagrams.md` and the table in `references/concepts.md`, and ground it in their app. On delivery, draw the blueprint again with what was actually built.

To measure the app afterwards on a dataset, with code evaluators or a judge, close with a pointer to the eval-experiments skill instead of adding an evaluation step here.
