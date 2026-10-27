# ASCII diagrams for the wizard

Use them in the `preview` field of AskUserQuestion and in explanations. Adapt them to the concrete app: change the tool names and the goal. At most ~16 lines and ~60 columns per preview.

## Contents

- The loop
- Chain or agent
- Prompt
- Output
- Data
- Guardrails
- Observability
- Tool or documents
- RAG
- Where the index lives
- Conversation
- MCP
- Shapes (for the idea step)

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

## Data

```
ONE TOOL                SEVERAL TOOLS            PROJECT SYSTEM
lookup_credit()         lookup_credit()          its own tool
synthetic dict          check_restructuring()    read-only access
┌───────┐               ┌───────┐                needs its service
│ agent │─▶ tool        │ agent │─▶ picks by     see project.md
└───────┘               └───────┘   description
simplest                more calls               closest to production
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

## MCP

```
mcpServers (same shape as .mcp.json)
  credits: command python credits_server.py (stdio)
  documents: url http://127.0.0.1:8002/mcp (HTTP)
        │ MCPAdapter.list_tools()
        ▼
create_agent ── credits_check_credit ──▶ server
create_agent ◀── rows ─────────────────── server
server asks "which credit?" ─▶ interrupt ─▶ person
person ─▶ Command(resume=...) ─▶ same tool call again
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
