"""Review an MCP server before connecting it: what it offers and what its descriptions ask the model.

It connects as a plain client, without any model, prints every tool, resource and prompt with its full
description and flags:
- tools that declare neither read_only_hint nor destructive_hint;
- arguments without a description (the model guesses what to send);
- descriptions that give orders instead of describing: hidden tags, "before answering", "do not tell"
  (tool poisoning, or shadowing when they point at another server's tools).
With --snapshot it saves the definitions and, on later runs, reports any change since the approval
(a "rug pull"). A clean report is a signal, not a proof: read the descriptions yourself.

stdio starts the server's code on this machine with your permissions. For a server you did not write,
read its source first or run it in a container.

Run from the repo root (no model calls):
    uv run python .claude/skills/mcp-server/references/examples/inspect_server.py -- python path/to/server.py
    uv run python .claude/skills/mcp-server/references/examples/inspect_server.py --url http://127.0.0.1:8001/mcp
    uv run python .claude/skills/mcp-server/references/examples/inspect_server.py --snapshot reviews/credits.json -- python server.py
Exit code 1 when something is flagged or changed.
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

from mcp import Client, StdioServerParameters

# Phrases that address the model instead of describing the tool. Extend the list with what you find.
SUSPICIOUS = (
    "<important", "<instructions", "<system", "ignore previous", "ignore all", "before answering", "before responding",
    "do not tell", "don't tell", "do not mention", "without telling", "the user must not",
    "antes de responder", "no le digas", "no menciones", "ignora las instrucciones",
)


def review_tools(tools) -> list[str]:
    """Problems in the tool definitions, one line each. Takes the tools of list_tools()."""
    problems = []
    for tool in tools:
        if not (tool.description or "").strip():
            problems.append(f"{tool.name}: no description")
        hints = tool.annotations
        if hints is None or (hints.read_only_hint is None and hints.destructive_hint is None):
            problems.append(f"{tool.name}: declares neither read_only_hint nor destructive_hint")
        texts = [tool.description or ""]
        for argument, schema in tool.input_schema.get("properties", {}).items():
            if not schema.get("description"):
                problems.append(f"{tool.name}: argument '{argument}' has no description")
            texts.append(schema.get("description", ""))
        text = " ".join(texts).lower()
        problems += [f"{tool.name}: the description gives orders ('{phrase}')" for phrase in SUSPICIOUS if phrase in text]
    return problems


def definitions(tools, resources, templates, prompts) -> dict:
    """What the client receives, in a stable form to save and compare."""
    return {
        "tools": {t.name: {"description": t.description, "input": t.input_schema, "output": t.output_schema,
                           "annotations": t.annotations.model_dump() if t.annotations else None} for t in tools},
        "resources": sorted(str(r.uri) for r in resources),
        "templates": sorted(t.uri_template for t in templates),
        "prompts": {p.name: p.description for p in prompts},
    }


def changes(old: dict, new: dict) -> list[str]:
    found = []
    for section, after in new.items():
        before = old.get(section)
        if isinstance(after, dict):
            for name in sorted(set(before or {}) | set(after)):
                if (before or {}).get(name) != after.get(name):
                    state = "new" if name not in (before or {}) else "removed" if name not in after else "changed"
                    found.append(f"{section}/{name}: {state}")
        elif before != after:
            found.append(f"{section}: {before} -> {after}")
    return found


async def inspect(server) -> dict:
    async with Client(server) as client:
        capabilities = client.server_capabilities
        tools = (await client.list_tools()).tools
        resources = (await client.list_resources()).resources if capabilities.resources else []
        templates = (await client.list_resource_templates()).resource_templates if capabilities.resources else []
        prompts = (await client.list_prompts()).prompts if capabilities.prompts else []
        return {"server": client.server_info.name, "instructions": client.instructions,
                "tools": tools, "definitions": definitions(tools, resources, templates, prompts)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--url", help="streamable HTTP endpoint, for example http://127.0.0.1:8001/mcp")
    parser.add_argument("--snapshot", type=Path, help="JSON file with the approved definitions")
    parser.add_argument("command", nargs="*", help="stdio command after --, for example: python server.py")
    args = parser.parse_args()
    if bool(args.url) == bool(args.command):
        parser.error("give either --url or a command after --")
    server = args.url or StdioServerParameters(command=args.command[0], args=args.command[1:])

    report = asyncio.run(inspect(server))
    print(f"Server: {report['server']}\nInstructions: {report['instructions']}\n")
    for tool in report["tools"]:
        print(f"- tool {tool.name}: {tool.description}")
        print(f"    annotations: {tool.annotations.model_dump(exclude_none=True) if tool.annotations else None}")
        for argument, schema in tool.input_schema.get("properties", {}).items():
            print(f"    {argument}: {schema.get('description', '(no description)')}")
    found = report["definitions"]
    print(f"\nResources: {found['resources']} · templates: {found['templates']} · prompts: {list(found['prompts'])}")

    problems = review_tools(report["tools"])
    if args.snapshot:
        if args.snapshot.exists():
            problems += [f"changed since the snapshot: {line}" for line in
                         changes(json.loads(args.snapshot.read_text()), found)]
        else:
            args.snapshot.parent.mkdir(parents=True, exist_ok=True)
            args.snapshot.write_text(json.dumps(found, indent=2, ensure_ascii=False, sort_keys=True))
            print(f"Snapshot saved to {args.snapshot}: compare against it before each new version.")
    print("\n" + ("Flags:\n- " + "\n- ".join(problems) if problems else "No flags. Read the descriptions anyway."))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
