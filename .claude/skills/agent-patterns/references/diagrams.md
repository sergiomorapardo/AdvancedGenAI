# ASCII diagrams for the wizard

Use them in the `preview` of each AskUserQuestion option and when explaining a pattern. Replace the sample names with the person's nodes.

## Decision tree

```
Can one call do it? ──yes──► one call (agentic-workflow)
        │ no
Are the steps known in advance?
   ├─ yes, in order ............ prompt chaining
   ├─ yes, by type of input .... routing
   ├─ yes, independent ......... parallelization
   └─ no
       ├─ depend on the input .. orchestrator-workers
       ├─ must pass criteria ... evaluator-optimizer
       └─ model picks tools .... agent (agentic-workflow)
Acts outside the graph? → add human approval to any of them
```

## Chaining with a gate

```
START → classify ─(gate in code)─┬─ credit ─► extract → draft → END
                                 └─ other ──► out_of_scope ───► END
calls: 3 on the long path, 1 on the short one
```

## Routing

```
START → router (Literal route) ─┬─► credit       ─┐
                                ├─► disbursement ─┤
                                ├─► fees         ─┼─► END
                                └─► collections  ─┘
calls: 1 route + 1 answer
```

## Parallelization

```
        ┌─► compliance ─┐
START ──┼─► accuracy   ─┼─► aggregate (code) → END
        └─► tone       ─┘
reviews: Annotated[list, operator.add]   wall time ≈ slowest branch
```

## Human approval

```
START → validate ─┬─ ≤ 20 M ──────────────────► disburse → END
                  ├─ 20–40 M ─► approval ⏸ interrupt
                  │               approve/edit ─► disburse
                  │               reject ───────► reject → END
                  └─ > 40 M ──────────────────► reject
checkpointer + thread_id keep the pause; Command(resume=...) continues
```

## Orchestrator-workers

```
START → orchestrator (Plan) ─Send─┬─► worker(task 1) ─┐
                                   ├─► worker(task 2) ─┼─► synthesize → END
                                   └─► worker(task n) ─┘
empty plan ───────────────────────────────────────────► synthesize
calls: 1 + N + 1      worker = subgraph(load_policy → answer)
```

## Evaluator-optimizer

```
START → generate → evaluate ─┬─ approved or attempts ≥ cap ─► END
            ▲                └─ fix ─┐
            └──── feedback ──────────┘
calls: 2 per attempt; code checks length before the judge
```

## State

```
TicketState
  message: str                       ← input
  topic: str                         ← classify
  reviews: Annotated[list, add]      ← several nodes in the same step
  attempts: int                      ← read by the cap
each node returns only the fields it changes
```

## Code or model

```
code  : gate · route list (Literal) · aggregator · cap · limits · word count
model : classify · extract · draft · judge criteria that need reading
```
