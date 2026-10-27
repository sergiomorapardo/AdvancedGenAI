"""PostToolUse hook (S02): check every .jinja file that Claude writes or edits.

- Always: the template must parse (syntax errors are caught before anyone renders it).
- If <name>.example.json exists next to it: render it with StrictUndefined, so a
  variable used in the template but missing from the example context fails loudly.

Exit code 2 sends the message back to Claude so it fixes the template. No model calls.
"""

import json
import sys
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined, TemplateError


def check(path: Path) -> str | None:
    env = Environment(
        loader=FileSystemLoader(path.parent), undefined=StrictUndefined,
        trim_blocks=True, lstrip_blocks=True,
    )
    try:
        template = env.get_template(path.name)
        example = path.with_suffix(".example.json")
        if example.exists():
            template.render(**json.loads(example.read_text(encoding="utf-8")))
    except TemplateError as error:
        return f"{path.name}: {type(error).__name__}: {error}"
    except json.JSONDecodeError as error:
        return f"{path.with_suffix('.example.json').name}: invalid JSON: {error}"
    return None


def main() -> int:
    event = json.load(sys.stdin)
    file_path = event.get("tool_input", {}).get("file_path", "")
    if not file_path.endswith(".jinja"):
        return 0
    problem = check(Path(file_path))
    if problem:
        print(f"Jinja check failed. {problem}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
