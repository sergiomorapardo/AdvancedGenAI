# ASCII diagrams for the wizard

Use them in the `preview` field of AskUserQuestion and in explanations. Adapt them to the concrete app: change the tool names and the goal. At most ~16 lines and ~60 columns per preview.

## Contents

- Conversation
- The loop
- Guardrails
- Approval
- Observability

## Conversation

```
NO HISTORY            REWRITE (chain)             AGENT + MEMORY
one complete          history + follow-up         thread_id ─▶ checkpointer
question per run      ─▶ model: standalone q      messages of the thread
                      ─▶ retriever ─▶ answer      ─▶ agent decides whether
1 call                2 calls per follow-up          and what to search
                      the rewrite is printed      1-2+ calls per turn
```

## The loop

```
question ─▶ ┌──────────── create_agent ─────────────┐
            │ context: system prompt + messages     │
            │      │                                │
            │      ▼          tool call             │
            │   ┌─────┐ ─────────────▶ your tool    │
            │   │ LLM │ ◀───────────── ToolMessage  │
            │   └─────┘  (repeats until it answers) │
            └─────│─────────────────────────────────┘
                  ▼
              answer  +  runs/<timestamp>/transcript.md
```

## Guardrails

```
Who decides whether it happens?
  the model asks   (may or may not happen) ─▶ tool call · prompt rule
  the code enforces (always happens)       ─▶ read-only tool · argument
                                              schema · errors as data ·
                                              tool_choice · answer check
```

## Approval

```
propose ──▶ approve ⏸ interrupt(proposal) ──▶ person
              │   ▲                              │
              │   └── Command(resume=answer) ◀───┘
              ├─ approve · edit ──▶ action node (once, idempotent)
              └─ reject ───────────▶ END (reason kept in the state)
before the answer: 0 actions · on resume approve runs again
```

## Observability

```
RUN LOG (always)                LANGSMITH (optional)
runs/<ts>/events.jsonl          one trace per top-level invoke
runs/<ts>/transcript.md         shared monthly trace budget
stays on your machine           count traces, ask before running
```
