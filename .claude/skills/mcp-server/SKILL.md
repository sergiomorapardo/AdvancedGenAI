---
name: mcp-server
description: Wizard that builds an MCP server in Python so that several apps (Claude Code, a LangChain agent, other MCP clients) share the same tools, data and prompts, and that reviews third-party servers before connecting them. Decides one thing at a time with AskUserQuestion and ASCII diagrams (what to expose as tools, resources or prompts, the data source and its read-only control, typed output, elicitation when the input is ambiguous, stdio or streamable HTTP, where to register it), generates the server with the official SDK, checks it with real MCP clients and never calls a model. Use when someone asks to "build an MCP server", "expose this tool, database or RAG over MCP", "connect X to Claude Code", "MCP tool, resource or prompt", "elicitation", ".mcp.json", "is this MCP server safe?", "tool poisoning", "MCP Inspector" or "MCP Registry", or types /mcp-server. Not for the agent that uses the tools (use agentic-workflow, which consumes MCP servers) or for evaluating answers (use evaluate-app).
---

# MCP server

A server publishes capabilities once, with names, descriptions and schemas, and every MCP client discovers and uses them the same way. You and the person decide four things and write them down: **what is shared** (tools, resources, prompts), **where the data comes from** and what stops a write, **how clients reach it** (stdio or HTTP) and **who it is registered for**. The server never calls a generative model: the client's model decides and writes.

This file is the map. Each phase lives in `references/`: open the file of the phase when you reach it, in full, and not before.

## Flow

Copy this checklist into your answer and tick it as you go:

```
- [ ] 0. Project            → read references/project.md (SDK, paths, registration, hooks)
- [ ] 1. Wizard              → read references/wizard.md and references/concepts.md
- [ ] 2. Blueprint confirmed by the person
- [ ] 3. Build               → read references/build.md + the example of each chosen piece
- [ ] 4. Checks with clients → read references/validation.md (in memory, stdio, review; no model)
- [ ] 5. Register, only where the person chose
- [ ] 6. If something fails  → references/gotchas.md, fix only that, back to step 4
- [ ] 7. Delivery with paths, tool list, review report and how to connect it
```

To **review a server someone else wrote**, skip the wizard: read `references/security.md` and run `references/examples/inspect_server.py` on it.

## What to open and when

| Phase or question | Open |
|---|---|
| SDK version, where servers live, how they are registered, the hooks of this project | `references/project.md` |
| Running the wizard: what to ask, which options | `references/wizard.md` |
| "Do I need MCP or a @tool?", "tool, resource or prompt?", "stdio or HTTP?", "what is elicitation?", diagrams | `references/concepts.md` |
| Which piece to use, which files to generate, rules that are not negotiable | `references/build.md` |
| Checks with real clients and the delivery | `references/validation.md` |
| A third-party server, tool poisoning, the Registry, remote servers | `references/security.md` |
| An error symptom | `references/gotchas.md` |

## Verified examples

Read in full the example of the piece you are about to write. Copy the shape, change the content.

| Piece | Example |
|---|---|
| Tools over a read-only SQLite table: parameters, `ToolError`, described arguments, `read_only_hint`, typed output with `outputSchema`, elicitation with a resolver when several items match, a fixed resource, stdio and HTTP | `references/examples/credits_server.py` |
| Document search as a server: fragments with `[file, p. N]`, a resource template limited to one folder, a prompt with a `resource_link`, an index built once per process | `references/examples/docs_server.py` |
| Review any server without a model: definitions, missing descriptions and hints, descriptions that give orders, changes since an approved snapshot | `references/examples/inspect_server.py` |
| The only file that knows this project: sample documents and embeddings model | `references/examples/project.py` |

## What is never skipped

1. **One decision per question**, with AskUserQuestion and an ASCII diagram in the `preview`. With "you decide" or no human: the recommended options.
2. **MCP only when several apps share it.** One app with one tool keeps a `@tool`; say so in the first step.
3. **Read only by default, enforced below the server**: a read-only connection, file or credential. An annotation is a hint for the client, not a control.
4. **Inputs travel as parameters** and are validated; the model never writes SQL, paths or commands. Errors the model should read are `ToolError`.
5. **stdout is the protocol in stdio.** No `print()` in a server; logs go to stderr.
6. **Descriptions describe, never instruct.** Every tool and argument has one; none tells the model what to do with other tools or what to hide.
7. **Resources are limited** to an allow list; no path from a client opens a file outside it.
8. **Elicitation asks the person, never for secrets**, and the tool does nothing irreversible before asking: it runs again after the answer.
9. **No secrets in code or results**; configuration comes from environment variables. Synthetic or authorized data only.
10. **A server you did not write is reviewed** before it runs or connects, and its version is pinned.
11. **Not done without the checks** of `references/validation.md` passing with a real client, and the tool list shown to the person.
