# ASCII diagrams for the wizard

Use them in the `preview` field of AskUserQuestion and in explanations. Adapt them to the concrete app: change the tool names and the goal. At most ~16 lines and ~60 columns per preview.

## Contents

- The loop
- Chain or agent
- Prompt
- Output
- Observability
- Shapes

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

## Chain or agent

```
CHAIN                           AGENT
fixed steps, you decide them    the model decides the next step
prompt ─▶ model ─▶ parser       model ⇄ tools, until it answers
1 model call per run            2+ model calls per run
predictable cost                cost depends on the question
```

## Prompt

```
INLINE                          JINJA FILE
ChatPromptTemplate              prompts/ticket.jinja, versioned
"Context: {context}"            {% if charge_date %}…{% else %}…
fixed holes                     {% for rule in rules %}…
                                StrictUndefined: missing data fails loudly
```

## Output

```
FREE TEXT                       STRUCTURED (Pydantic)
response.text                   with_structured_output(TicketReview)
a person reads it               code reads review.disputed_charges
nothing to validate             the shape is validated; the content
                                still has to be checked against data
```

## Observability

```
RUN LOG (always)                LANGSMITH (optional)
runs/<ts>/events.jsonl          one trace per top-level invoke
runs/<ts>/transcript.md         shared monthly trace budget
stays on your machine           count traces, ask before running
```

## Shapes

```
COLLECTIONS     "How much is overdue on this credit?" agent + credits tool
COMPLIANCE      "Is this dispute ticket complete?"   chain + Jinja + schema
SALES           "Summarize this customer request"    chain + schema
RISK            "Which customers are past 60 days?"  agent + 2 tools
OPERATIONS      "When is this credit disbursed?"     RAG over policies
CUSTOMER CARE   "And how many times can I do it?"    RAG + rewrite or memory
```
