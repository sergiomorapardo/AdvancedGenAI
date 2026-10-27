"""Code evaluators for agents and graphs: what they did, not only what they answered.

The app under test returns `agent_outputs(...)`: the answer, the tool calls in order, the tools that
actually ran, the route or plan when there is one, and the model calls. The references, written by a person,
say which tools and arguments are expected, which route, which tools must never run and the call budget.
Every evaluator returns None when its reference field is missing, so one dataset can mix question types.

No model calls: these evaluators are free and deterministic.
"""


def agent_outputs(messages: list, **extra) -> dict:
    """What the evaluators read, from the messages of a create_agent or graph run."""
    calls = [{"name": call["name"], "args": call["args"]} for m in messages if m.type == "ai" for call in m.tool_calls]
    executed = [m.name for m in messages if m.type == "tool"]
    return {"answer": messages[-1].text, "tool_calls": calls, "executed_tools": executed,
            "model_calls": sum(m.type == "ai" for m in messages), **extra}


def _same(expected, actual) -> bool:
    # Arguments match when every expected key has the same value; text ignores case and spaces at the ends.
    if isinstance(expected, str) and isinstance(actual, str):
        return expected.strip().lower() == actual.strip().lower()
    return expected == actual


def tools_called(outputs: dict, reference_outputs: dict) -> dict:
    """Every expected tool was called (other calls are allowed and listed in the comment)."""
    expected = reference_outputs.get("tools")
    if expected is None:
        return {"key": "tools_called", "score": None, "comment": "No expected tools."}
    called = [call["name"] for call in outputs["tool_calls"]]
    missing = [name for name in expected if name not in called]
    extra = sorted(set(called) - set(expected))
    comment = "; ".join(filter(None, [f"Missing: {missing}" if missing else "", f"Also called: {extra}" if extra else ""]))
    return {"key": "tools_called", "score": not missing, "comment": comment}


def tool_args_match(outputs: dict, reference_outputs: dict) -> dict:
    """Each expected call {name, args} was made with at least those arguments."""
    expected = reference_outputs.get("calls")
    if expected is None:
        return {"key": "tool_args_match", "score": None, "comment": "No expected arguments."}
    unmatched = [
        want for want in expected
        if not any(call["name"] == want["name"] and all(_same(v, call["args"].get(k)) for k, v in want["args"].items())
                   for call in outputs["tool_calls"])
    ]
    return {"key": "tool_args_match", "score": not unmatched, "comment": f"Not matched: {unmatched}" if unmatched else ""}


def no_forbidden_tool(outputs: dict, reference_outputs: dict) -> dict:
    """No tool that must stay unexecuted (moves money, sends, deletes) actually ran."""
    forbidden = reference_outputs.get("forbidden_tools")
    if forbidden is None:
        return {"key": "no_forbidden_tool", "score": None, "comment": "Nothing forbidden."}
    ran = sorted(set(outputs["executed_tools"]) & set(forbidden))
    return {"key": "no_forbidden_tool", "score": not ran, "comment": f"Executed: {ran}" if ran else ""}


def route_correct(outputs: dict, reference_outputs: dict) -> dict:
    """A router chose the route a person expects."""
    expected = reference_outputs.get("route")
    if expected is None:
        return {"key": "route_correct", "score": None, "comment": "No expected route."}
    chosen = outputs.get("route")
    return {"key": "route_correct", "score": chosen == expected,
            "comment": "" if chosen == expected else f"Chose {chosen}, expected {expected}."}


def plan_covers(outputs: dict, reference_outputs: dict) -> dict:
    """An orchestrator's plan sent tasks to every expected source, and to no unexpected one."""
    expected = reference_outputs.get("plan_sources")
    if expected is None:
        return {"key": "plan_covers", "score": None, "comment": "No expected plan."}
    used = {task["policy"] for task in outputs.get("tasks", [])}
    missing, unexpected = sorted(set(expected) - used), sorted(used - set(expected))
    comment = "; ".join(filter(None, [f"Missing: {missing}" if missing else "", f"Unexpected: {unexpected}" if unexpected else ""]))
    return {"key": "plan_covers", "score": not missing and not unexpected, "comment": comment}


def calls_within(outputs: dict, reference_outputs: dict) -> dict:
    """The run stayed within the model-call budget: loops and retries show up here first."""
    budget = reference_outputs.get("max_model_calls")
    if budget is None:
        return {"key": "calls_within", "score": None, "comment": "No budget."}
    used = outputs["model_calls"]
    return {"key": "calls_within", "score": used <= budget, "comment": f"{used} calls, budget {budget}."}


AGENT_EVALUATORS = [tools_called, tool_args_match, no_forbidden_tool, route_correct, plan_covers, calls_within]
