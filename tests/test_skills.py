"""Verifica todas las skills del repositorio sin llamar al modelo: nombres, descripciones, archivos compartidos y hooks."""

import ast
import importlib.util
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / ".claude/skills"
ALL_SKILLS = sorted(path.name for path in SKILLS.iterdir() if (path / "SKILL.md").exists())
# Las que generan apps con project.py y run_log.py copiados tal cual: el mismo archivo en todas.
APP_SKILLS = ["agentic-memory", "llm-prompts", "llm-rag", "llm-tools"]
# Nombres <área>-<capacidad>, con un conjunto cerrado de áreas (AGENTS.md).
AREAS = ("llm", "agentic", "mcp", "eval", "ops")
NAME = re.compile(rf"^({'|'.join(AREAS)})-[a-z]+(-[a-z]+)?$")
EXAMPLES = SKILLS / "llm-prompts/references/examples"
HOOK = ROOT / ".claude/hooks/check_jinja.py"
APP_HOOK = ROOT / ".claude/hooks/check_app.py"
# Lo único que conoce este repositorio; el resto de cada skill debe poder copiarse a otro proyecto.
PROJECT_FILES = {"project.md", "project.py"}
PORTABLE = re.compile(r"notebooks/|datasets/|agents\.servers|load_dotenv|(?<![-\w])L\d\d\b|\d\d_\w+\.py")


def frontmatter(skill):
    return (SKILLS / skill / "SKILL.md").read_text().split("---")[1]


@pytest.mark.parametrize("skill", ALL_SKILLS)
def test_name_follows_the_area_capability_pattern(skill):
    assert NAME.match(skill), skill
    assert re.search(rf"^name: {skill}$", frontmatter(skill), re.MULTILINE)


@pytest.mark.parametrize("skill", ALL_SKILLS)
def test_description_says_when_and_when_not_with_room_to_grow(skill):
    description = re.search(r"^description: (.+)$", frontmatter(skill), re.MULTILINE).group(1)
    # 1024 es el límite de Agent Skills; el margen evita que una skill quede sin espacio para crecer.
    assert 300 < len(description) <= 950, len(description)
    assert re.search(r"\bUse (it|when)\b", description) and "Not for" in description
    # Cada skill que nombra a otra la nombra como existe.
    for other in re.findall(r"\buse ([a-z]+-[a-z]+(?:-[a-z]+)?)", description):
        assert other in ALL_SKILLS, other


@pytest.mark.parametrize("skill", ALL_SKILLS)
def test_referenced_files_and_skills_exist(skill):
    folder = SKILLS / skill
    paths = set(re.findall(r"`((?:references|assets)/[\w./-]+)`", (folder / "SKILL.md").read_text()))
    assert paths
    for path in paths:
        assert (folder / path).exists(), path
    for text in [path.read_text() for path in folder.rglob("*.md")]:
        for other in re.findall(r"\b((?:llm|agentic|mcp|eval|ops)-[a-z]+(?:-[a-z]+)?) skill", text):
            assert other in ALL_SKILLS, (skill, other)


@pytest.mark.parametrize("skill", ALL_SKILLS)
def test_skill_is_portable_outside_the_project_files(skill):
    for path in (SKILLS / skill).rglob("*"):
        if path.is_file() and path.suffix in {".md", ".py", ".jinja", ".json"} and path.name not in PROJECT_FILES:
            assert not PORTABLE.search(path.read_text()), path.relative_to(SKILLS)


@pytest.mark.parametrize("skill", ALL_SKILLS)
def test_examples_and_templates_compile(skill):
    for path in (SKILLS / skill).rglob("*.py"):
        ast.parse(path.read_text(), filename=str(path))


@pytest.mark.parametrize("skill", APP_SKILLS)
def test_only_the_project_adapter_creates_the_model(skill):
    examples = SKILLS / skill / "references/examples"
    project = (examples / "project.py").read_text()
    assert 'MODEL = "claude-haiku-5-5"' in project and '"type": "disabled"' in project
    for path in [*examples.glob("*.py"), *(SKILLS / skill / "assets").glob("*.py")]:
        source = path.read_text()
        assert "temperature=" not in source, path.name
        if path.name != "project.py":
            assert "ChatAnthropic(" not in source and "load_dotenv" not in source, path.name


def test_shared_files_are_the_same_in_every_skill_that_copies_them():
    # project.py y run_log.py se copian tal cual junto a cada app: un cambio va en todas las copias.
    for name in ("project.py", "run_log.py"):
        copies = {(SKILLS / skill / "references/examples" / name).read_text() for skill in APP_SKILLS}
        assert len(copies) == 1, name
    run_log = (EXAMPLES / "run_log.py").read_text()
    assert (SKILLS / "agentic-patterns/references/examples/run_log.py").read_text() == run_log


def load_example(name, monkeypatch):
    # Los ejemplos se ejecutan como scripts e importan run_log desde su carpeta.
    monkeypatch.syspath_prepend(str(EXAMPLES))
    # Cada skill tiene su project.py: se descarta el que haya cargado otra prueba.
    for shared in ("project", "run_log"):
        monkeypatch.delitem(sys.modules, shared, raising=False)
    spec = importlib.util.spec_from_file_location(name, EXAMPLES / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_hook(file_path):
    event = json.dumps({"tool_name": "Write", "tool_input": {"file_path": str(file_path)}})
    return subprocess.run(
        [sys.executable, str(HOOK)], input=event, capture_output=True, text=True, check=False
    )


def test_run_log_writes_events_and_transcript(monkeypatch, tmp_path):
    run_log_module = load_example("run_log", monkeypatch)
    run_log = run_log_module.RunLog(tmp_path / "runs")
    model = GenericFakeChatModel(messages=iter([AIMessage("185,000 COP.")]))
    chain = ChatPromptTemplate.from_messages([("human", "{question}")]) | model
    chain.invoke({"question": "How much is each charge?"}, config={"callbacks": [run_log]})
    events = [json.loads(line) for line in (run_log.path / "events.jsonl").read_text().splitlines()]
    assert [event["event"] for event in events] == ["model_start", "model_end"]
    transcript = (run_log.path / "transcript.md").read_text()
    assert "Model call 1" in transcript and "185,000 COP." in transcript
    assert run_log.model_calls == 1


def test_hook_accepts_the_example_template_and_ignores_other_files(tmp_path):
    assert run_hook(EXAMPLES / "prompts/ticket.jinja").returncode == 0
    assert run_hook(ROOT / "datasets/acme_ticket.jinja").returncode == 0
    assert run_hook(tmp_path / "notes.md").returncode == 0


def test_hook_rejects_syntax_errors_and_missing_variables(tmp_path):
    broken = tmp_path / "broken.jinja"
    broken.write_text("{% if ticket %}Ticket {{ ticket.code }}")
    result = run_hook(broken)
    assert result.returncode == 2 and "TemplateSyntaxError" in result.stderr

    template = tmp_path / "ticket.jinja"
    template.write_text("Customer: {{ ticket.customer }}")
    (tmp_path / "ticket.example.json").write_text(json.dumps({"ticket": {"code": "T-1"}}))
    result = run_hook(template)
    assert result.returncode == 2 and "UndefinedError" in result.stderr


def test_project_settings_register_the_hooks_and_ask_before_paid_runs():
    settings = json.loads((ROOT / ".claude/settings.json").read_text())
    hook = settings["hooks"]["PostToolUse"][0]
    assert {"Write", "Edit"} <= set(hook["matcher"].split("|"))
    commands = " ".join(entry["command"] for entry in hook["hooks"])
    assert "check_jinja.py" in commands and "check_app.py" in commands
    assert "Bash(uv run python labs/*)" in settings["permissions"]["ask"]


def run_app_hook(file_path, root):
    event = json.dumps({"tool_name": "Write", "tool_input": {"file_path": str(file_path)}})
    return subprocess.run(
        [sys.executable, str(APP_HOOK)], input=event, capture_output=True, text=True, check=False,
        env={**os.environ, "CLAUDE_PROJECT_DIR": str(root)}, cwd=ROOT,
    )


def test_app_hook_accepts_an_example_and_ignores_files_outside_labs(tmp_path):
    app = tmp_path / "labs/ticket-check/app.py"
    app.parent.mkdir(parents=True)
    app.write_text((EXAMPLES / "chain.py").read_text())
    assert run_app_hook(app, tmp_path).returncode == 0
    outside = tmp_path / "notes.py"
    outside.write_text("this is not python")
    assert run_app_hook(outside, tmp_path).returncode == 0


def test_app_hook_rejects_temperature_keys_and_lint_errors(tmp_path):
    app = tmp_path / "labs/bad/app.py"
    app.parent.mkdir(parents=True)
    app.write_text('from langchain_anthropic import ChatAnthropic\n\nKEY = "sk-ant-0123456789"\n'
                   'model = ChatAnthropic(model="x", temperature=0)\n')
    result = run_app_hook(app, tmp_path)
    assert result.returncode == 2
    assert "temperature" in result.stderr and "literal API key" in result.stderr
    app.write_text("import os\n")
    result = run_app_hook(app, tmp_path)
    assert result.returncode == 2 and "F401" in result.stderr
    app.write_text("def broken(:\n")
    assert "SyntaxError" in run_app_hook(app, tmp_path).stderr
