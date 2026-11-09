# ASCII diagrams for the wizard

Use them in the `preview` field of AskUserQuestion and in explanations. Adapt them to the concrete app: change the tool names and the goal. At most ~16 lines and ~60 columns per preview.

## Contents

- Tool or documents
- RAG
- Where the index lives
- Conversation
- Guardrails
- Observability

## Tool or documents

```
TOOL                            DOCUMENTS / RAG
"how much is overdue?"          "can I restructure?"
structured data that changes    text someone wrote
lookup_credit() ─▶ figures      retriever ─▶ fragments + page
check: figure in the answer     check: every [file, p. N] retrieved
```

## RAG

```
INDEX (once per document version)
PDFs ─▶ pages ─▶ fragments ─▶ embeddings ─▶ index
        source + page kept on every fragment

ASK (every question)
question ─▶ retriever (k=3) ─▶ context with [file, p. N]
                                   │
                                   ▼
                     model ─▶ answer with citations
                              or "not in the documents"
```

## Where the index lives

```
IN MEMORY             FAISS                  CHROMA
InMemoryVectorStore   indexes/faiss/         indexes/chroma/
rebuilt every run     index.faiss + .pkl     sqlite + vectors
no files              load without re-       stable ids, filters
                      computing; pickle!     by source or page
smallest              fast, file based       closest to a database
```

## Conversation

```
NO HISTORY            REWRITE (chain)             AGENT + MEMORY
one complete          history + follow-up         thread_id ─▶ checkpointer
question per run      ─▶ model: standalone q      messages of the thread
                      ─▶ retriever ─▶ answer      ─▶ agent decides whether
1 call                2 calls per follow-up          and what to search
                      the rewrite is printed      1-2+ calls per turn
```

## Guardrails

```
Who decides whether it happens?
  the model asks   (may or may not happen) ─▶ tool call · prompt rule
  the code enforces (always happens)       ─▶ read-only tool · argument
                                              schema · errors as data ·
                                              tool_choice · answer check
```

## Observability

```
RUN LOG (always)                LANGSMITH (optional)
runs/<ts>/events.jsonl          one trace per top-level invoke
runs/<ts>/transcript.md         shared monthly trace budget
stays on your machine           count traces, ask before running
```
