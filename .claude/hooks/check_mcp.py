"""PostToolUse hook: check every MCP server that Claude writes or edits in this repository.

A Python file is an MCP server when it creates `<name> = MCPServer(...)` at module level. Then:
- no print(): in stdio, stdout is the protocol channel and a print corrupts the messages;
- the server must load and list its tools in memory, without a model and without starting a process;
- every tool and every argument has a description, each tool declares read_only_hint or
  destructive_hint, and no description gives orders to the model (review_tools of the mcp-server skill).

Exit code 2 sends the message back to Claude so it fixes the file. No model calls.
"""

import ast
import asyncio
import importlib.util
import json
import os
import sys
from pathlib import Path

REVIEW = Path(__file__).resolve().parents[1] / "skills/mcp-server/references/examples/inspect_server.py"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def server_names(tree: ast.Module) -> list[str]:
    names = []
    for node in tree.body:
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
            func = node.value.func
            if getattr(func, "id", getattr(func, "attr", "")) == "MCPServer":
                names += [target.id for target in node.targets if isinstance(target, ast.Name)]
    return names


async def list_tools(server) -> list:
    from mcp import Client  # only for servers: other edits stay fast

    async with Client(server) as client:
        return (await client.list_tools()).tools


def check(path: Path) -> list[str]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except SyntaxError as error:
        return [f"SyntaxError: {error}"]
    names = server_names(tree)
    if not names:
        return []
    problems = [
        f"line {node.lineno}: print() writes to stdout, the protocol channel in stdio; log to stderr instead"
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and getattr(node.func, "id", "") == "print"
    ]
    sys.path.insert(0, str(path.parent))  # a server imports its neighbours, such as project.py
    try:
        module = load(path, "server_under_check")
        tools = [tool for name in names for tool in asyncio.run(list_tools(getattr(module, name)))]
    except Exception as error:  # noqa: BLE001 -- the message goes back to Claude, whatever failed
        return [*problems, f"the server does not load or list its tools: {type(error).__name__}: {error}"]
    return problems + load(REVIEW, "inspect_server").review_tools(tools)


def main() -> int:
    event = json.load(sys.stdin)
    file_path = Path(event.get("tool_input", {}).get("file_path", ""))
    root = Path(os.environ.get("CLAUDE_PROJECT_DIR", Path.cwd())).resolve()
    try:
        relative = file_path.resolve().relative_to(root)
    except ValueError:
        return 0
    if relative.suffix != ".py" or not file_path.exists():
        return 0
    problems = check(file_path)
    if problems:
        print(f"MCP server check failed for {relative}:\n- " + "\n- ".join(problems), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
