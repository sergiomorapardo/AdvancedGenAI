---
name: llm-rag
description: Designs and builds a RAG app on Claude with LangChain that answers from documents citing [file, p. N]: PDF pages with metadata, fragments, local embeddings, an in-memory, FAISS or Chroma index, a citation check, and for follow-ups a rewrite with the history or multi-query. One decision at a time with ASCII diagrams, a blueprint, a run log, offline checks and one paid run after approval. Use it whenever the answer lives in PDFs, manuals or policies: "RAG", "retriever", "embeddings", "FAISS", "Chroma", "vector store", "query rewriting", "multi-query", "responder con los documentos", "que cite la fuente", "buscar en las políticas", "preguntas de seguimiento", /llm-rag. Not for an agent that remembers each conversation (use agentic-memory), tools over tables or APIs (use llm-tools) or measuring retrieval on a dataset (use eval-experiments).
---

# RAG with LangChain

You and the person decide four things and write them down: the **documents** (which PDFs, synthetic or authorized), the **index** (where it lives and which embeddings), the **answer** (only from the fragments, citing `[file, p. N]`, saying when it is not there) and the **conversation** (one question per run, or a rewrite of each follow-up). The retriever always returns `k` fragments: the prompt rule and a citation check keep the answer honest.

This file is the map. Each phase lives in `references/`: open the file of the phase when you reach it, in full, and not before.

## Flow

Copy this checklist into your answer and tick it as you go:

```
- [ ] 0. Project            → read references/project.md (model, credentials, paths, budget)
- [ ] 1. Wizard              → read references/wizard.md and references/diagrams.md
- [ ] 2. Blueprint confirmed by the person
- [ ] 3. Build               → read references/build.md + the example of each chosen piece
- [ ] 4. Offline checks      → read references/validation.md (no model calls)
- [ ] 5. One paid run, only after an explicit "yes" with the call and trace count
- [ ] 6. If something fails  → references/gotchas.md, fix only that, back to step 4
- [ ] 7. Delivery with paths, command, receipt and final blueprint
```

## What to open and when

| Phase or question | Open |
|---|---|
| Model, credentials, where apps live, budget, controls this project enforces | `references/project.md` |
| Running the wizard: what to ask, which options | `references/wizard.md` |
| ASCII diagrams for the `preview` fields and for explaining concepts | `references/diagrams.md` |
| "Tool or documents?", "which index?", "why local embeddings?", "rewrite or let an agent search?" | `references/concepts.md` |
| Which piece to use, which files to generate, rules that are not negotiable | `references/build.md` |
| Offline checks, the paid run and the delivery | `references/validation.md` |
| An error symptom | `references/gotchas.md` |

Template to copy and fill (`TODO` marks): `assets/app.py`. Two files are copied as is next to every app: `references/examples/project.py` (the only code that knows the project: credentials, model, sample data) and `references/examples/run_log.py`.

## Verified examples

Read in full the example of the piece you are about to write. Copy the shape, change the content. Every example runs on its own from the repo root and imports its model from `project.py`; `references/project.md` says how they were verified.

| Piece | Example |
|---|---|
| RAG: PDF pages with file and page, fragments, local embeddings, `@chain` with `[file, p. N]` citations, "not in the documents" and a citation check | `references/examples/rag.py` |
| A persistent index: FAISS (`save_local`/`load_local`) or Chroma (stable ids, metadata filter, cosine) | `references/examples/vector_store.py` |
| Conversational RAG: rewrite the follow-up with the history before retrieving, history in the answer, multi-query with a union of fragments | `references/examples/conversational_rag.py` |
| Local run log: `runs/<timestamp>/events.jsonl` + `transcript.md` | `references/examples/run_log.py` |

For an agent that keeps each conversation by `thread_id` and decides when to search, hand over to the agentic-memory skill; for tools over tables or APIs, to llm-tools; to expose the documents to several apps, to mcp-server. Measuring retrieval over a question set belongs to eval-experiments.

## What is never skipped

1. **One decision per question**, with AskUserQuestion and an ASCII diagram in the `preview`. With "you decide" or no human: the recommended options.
2. **Smallest shape that works.** An in-memory index rebuilt each run and one question per run, until the person needs more.
3. **Run log always.** Every run writes `runs/<timestamp>/events.jsonl` and `transcript.md`. Tracing services are optional and spend a shared budget.
4. **No paid call without an explicit "yes".** Before running, state how many model calls and traces the run makes, and wait.
5. **The model comes from `project.py`.** Never write a key in code; never switch to a bigger model on your own.
6. **Answers from documents cite file and page**, and `check_citations` confirms every citation was retrieved.
7. **Embeddings stay local** by default, so documents do not leave the machine to be indexed.
8. **Synthetic or anonymized data** only. No real customer data, PII or raw extracts.
9. **Not done without a successful run** and the transcript read, or an explicit note that it could not run and the exact command to run it.
