# Concepts: which pattern for which need

| Need | Pattern or piece | Why |
|---|---|---|
| One answer from one input | One call or a chain (agentic-workflow) | Cheapest and most predictable; every pattern below adds calls |
| Data shared by every step | `StateGraph(TypedDict)` | Nodes read the state and return only what they change |
| Several nodes write the same field in one step | `Annotated[list, operator.add]` | Without a reducer the updates collide (`InvalidUpdateError`) |
| A conversation as state | `MessagesState` (`add_messages`) | Appends new messages and replaces by `id` |
| Fixed steps; stop early when the input does not qualify | Prompt chaining with a gate | The gate is code: free, testable, saves the later calls |
| Each type of input needs its own prompt or context | Routing | Short, focused prompts instead of one that knows everything |
| The routes must not be invented | `Literal` in the route schema | The structured output cannot return a route that does not exist |
| Independent checks or subtasks | Parallelization (fan-out / fan-in) | Wall time ≈ the slowest branch, not the sum |
| The number of subtasks depends on the input | Orchestrator-workers with `Send` | One worker per task, each with its own input |
| A reusable unit with its own state | Subgraph | Tested alone; shares only the fields both states declare |
| Iterate until explicit criteria pass | Evaluator-optimizer | Feedback goes back to the generator; a cap ends the loop |
| An action that cannot be undone | `interrupt` + checkpointer + `Command(resume=...)` | The graph waits for a person and resumes where it stopped |
| The approval belongs to an agent's tool | `HumanInTheLoopMiddleware(interrupt_on={...})` | The tool does not run until a person approves, edits or rejects |
| See each step as it happens | `graph.stream(..., stream_mode="updates")` | One update per node, in order |

## Who controls what

- **The model suggests**: a topic, a route, a plan, a verdict, a draft.
- **The code decides**: the gate, the list of routes, the aggregator rule, the cap, the limits on amounts, the word count, whether a person must approve.
- A rule that must always hold is code. A rule in a prompt is a request: in the course, a judge approved an answer over the word limit its rubric set, and reviewers with different criteria all judged the same content.

## Cost of each pattern

| Pattern | Model calls per run | Main risk |
|---|---|---|
| Chaining | One per step on the path taken | Paying later steps for inputs the gate should stop |
| Routing | 1 route + 1 answer | A wrong route answers with the wrong policy |
| Parallelization | One per branch, at the same time | Branches that judge each other's criteria |
| Orchestrator-workers | 1 + N + 1, N decided by the plan | A badly split plan, or a task sent to the wrong source |
| Evaluator-optimizer | 2 per attempt, up to the cap | A judge that approves what the rubric forbids |
| Approval | Those of the graph; the pause adds none | Resuming without a checkpointer, or acting before asking |

## Approval, in one paragraph

`interrupt(value)` stops the node and returns `value` to the caller under `state["__interrupt__"]`. The checkpointer saves the state under the `thread_id`; nothing runs while the person decides. `graph.invoke(Command(resume=answer), config)` runs the node again from its start, and this time `interrupt` returns `answer`. So everything before `interrupt` in that node runs twice: keep it free of side effects, and act only after the decision.
