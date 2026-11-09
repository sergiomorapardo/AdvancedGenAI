# The wizard, step by step

Run the design as a wizard. In each step use **AskUserQuestion**: one question, two to four options, the recommended one first with "(Recommended)", and a `preview` with an ASCII diagram of how the app looks with that option. Base diagrams are in `references/diagrams.md`: adapt them with the real names of the person's app. Before each question write one or two lines on what is decided and why it matters; after each answer confirm in one line what was settled.

Skip the steps the request already answers. If the person says "you decide", pick the recommended option in every step and continue. If AskUserQuestion is not available, ask the same question in text with numbered options and the diagram in a code block.

| Step | Question | Typical options | Diagram |
|---|---|---|---|
| 0 · Goal | Which question must the documents answer? | 2–3 one-sentence goals, from smallest to most ambitious. Recommend the smallest | "tool or documents" |
| 1 · Documents | Which documents, and are they allowed? | Synthetic PDFs of the course (Recommended for a first app) · Authorized and anonymized documents of the person | "RAG" |
| 2 · Index | Where does the index live? | In memory, rebuilt each run (Recommended for a first app and small corpora) · FAISS files, loaded without recomputing · Chroma collection, with metadata filters (`vector_store.py`) | "where the index lives" |
| 3 · Embeddings | Which embeddings model? | Open multilingual model, local (Recommended: no key, no cost, documents stay on the machine; the project's model is in `references/project.md`) · A provider (needs its own key and budget; Anthropic has none) | "RAG" |
| 4 · Conversation | Will people ask follow-up questions ("and after that?")? | One question per run, no history (Recommended if each question is complete) · Rewrite the follow-up with the history before retrieving (`conversational_rag.py`; 2 calls per follow-up) · Add multi-query for colloquial questions (one more call, more fragments) · An agent that remembers the thread and decides whether to search (hand over to agentic-memory) | "conversation" |
| 5 · Guardrails | What must it never do? (multiSelect) | Answer only from the fragments (Recommended) · Say it is not in the documents (Recommended) · Citation check in code (Recommended) | "guardrails" |
| 6 · Observability | How do we see what happened? | Local run log only (Recommended) · Run log + LangSmith traces (counted against the project budget and approved before each run) | "observability" |

Close the wizard with a **blueprint** before writing code: an ASCII diagram of the final app with its documents, index, embeddings, conversation handling and the citation check, the list of files to create and the expected cost of one run (model calls and traces). Ask for confirmation with a last AskUserQuestion: "Build it like this (Recommended)" · "Change something".

## Use the diagrams to explain too

When the person asks "what is RAG?", "what is an embedding?", "tool or documents?", answer with the matching diagram from `references/diagrams.md` and the table in `references/concepts.md`, and ground it in their app. On delivery, draw the blueprint again with what was actually built.

To measure the app afterwards on a dataset, with code evaluators or a judge, close with a pointer to the eval-experiments skill instead of adding an evaluation step here.
