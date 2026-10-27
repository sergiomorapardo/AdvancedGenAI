"""PostToolUse hook: check every Python file that Claude writes or edits under labs/.

- The file must parse.
- No ChatAnthropic(..., temperature=...): the default model rejects it; the model comes from project.py.
- No literal Anthropic or LangSmith key: credentials come from .env through project.py.
- ruff must pass its basic rules (E4, E7, E9, F), whatever the repository's own selection.

Exit code 2 sends the message back to Claude so it fixes the file. No model calls.
"""

import ast
import json
import os
import re
import subprocess
import sys
from pathlib import Path

APPS = "labs"
KEY = re.compile(r"sk-ant-[\w-]{8,}|lsv2_[\w-]{8,}")


def check(path: Path) -> list[str]:
    source = path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError as error:
        return [f"SyntaxError: {error}"]
    problems = []
    for node in ast.walk(tree):
        name = getattr(node, "func", None) and getattr(node.func, "id", getattr(node.func, "attr", ""))
        if name == "ChatAnthropic" and any(keyword.arg == "temperature" for keyword in node.keywords):
            problems.append(f"line {node.lineno}: ChatAnthropic with temperature; use build_model() from project.py")
    if KEY.search(source):
        problems.append("a literal API key; load credentials from .env through project.py")
    lint = subprocess.run(
        [sys.executable, "-m", "ruff", "check", "--select", "E4,E7,E9,F", "--output-format=concise", "--quiet", str(path)], capture_output=True, text=True, check=False
    )
    if lint.returncode:
        problems.append(f"ruff:\n{lint.stdout.strip() or lint.stderr.strip()}")
    return problems


def main() -> int:
    event = json.load(sys.stdin)
    file_path = Path(event.get("tool_input", {}).get("file_path", ""))
    root = Path(os.environ.get("CLAUDE_PROJECT_DIR", Path.cwd())).resolve()
    try:
        relative = file_path.resolve().relative_to(root)
    except ValueError:
        return 0
    if relative.suffix != ".py" or relative.parts[:1] != (APPS,) or not file_path.exists():
        return 0
    problems = check(file_path)
    if problems:
        print(f"App check failed for {relative}:\n- " + "\n- ".join(problems), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
