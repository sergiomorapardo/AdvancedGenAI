# Evaluate agents and graphs

An agent can give a right answer for the wrong reasons (it guessed instead of looking up), or a wrong one after a correct lookup. Evaluate both: **what it answered** with the evaluators of `references/evaluators.md`, and **what it did** with the code evaluators of `examples/agent_evaluators.py`.

## Contents

- What to measure
- The app under test returns its trajectory
- References for agents
- Judges for agents
- Reading the results

## What to measure

| Question | Evaluator | Reference field |
|---|---|---|
| Did it call the tools it needed? | `tools_called` | `tools`: names, in any order |
| With the right arguments? | `tool_args_match` | `calls`: `[{"name", "args"}]`, only the arguments that matter |
| Did an action that needs approval stay unexecuted? | `no_forbidden_tool` | `forbidden_tools` |
| Did the router pick the right specialist? | `route_correct` | `route` |
| Did the orchestrator's plan send each question to the right source? | `plan_covers` | `plan_sources` |
| Did it stay within budget, without loops? | `calls_within` | `max_model_calls` |
| Is the final answer correct and grounded? | `figures_match`, judges in `evaluators.py` | `reference` |

Start with the trajectory: it is free, deterministic and explains many wrong answers. Add a judge only for the final answer.

## The app under test returns its trajectory

The function passed to `evaluate` returns `agent_outputs(result["messages"], ...)`: the answer, `tool_calls` (name and arguments, in order), `executed_tools` (from the tool messages: a call that was rejected never produces one), `model_calls`, and any extra field the graph exposes, such as `route=result["route"]` or `tasks=result["tasks"]`. If an evaluator needs a field the app does not return, change the app wrapper, not the evaluator.

For a graph with human approval, the evaluation run answers the pause in code (for example, always `reject`) so the run ends and `no_forbidden_tool` can check that nothing ran.

## References for agents

- Written by a person who knows the process, never by the agent under test.
- Only the arguments that decide the result (`customer`, `product`), not every argument the model may add.
- At least one case per path: a question that needs the tool, one that does not, one whose data does not exist (`not_found`), one a keyword rule would misroute, one that asks for a forbidden action.
- A call budget per case from a correct run plus a margin (agents may retry with other words): it catches loops, not small variations.

## Judges for agents

OpenEvals has rubrics for trajectories (`TOOL_SELECTION_PROMPT`, `TASK_COMPLETION_PROMPT`). Use them only when a rule cannot decide, for example whether an extra call was reasonable. Calibrate them like any judge (`references/evaluators.md`).

## Reading the results

- A wrong answer with `tools_called` true and `tool_args_match` false: the model understood the task but misread the input. Look at the arguments.
- A wrong answer with the right trajectory: the generation step failed; read the tool result and the answer side by side.
- `calls_within` false on several cases after a change: a loop or a retry storm; read the transcript.
- `route_correct` false: read the route descriptions; a vague one makes the router guess.
- Report the trajectory scores next to quality, latency and cost, with the number of cases, as for any experiment.
