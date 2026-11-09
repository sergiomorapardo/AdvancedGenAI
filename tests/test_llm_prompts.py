"""Verifica los ejemplos de la skill llm-prompts sin llamar al modelo."""

import importlib.util
import sys
from pathlib import Path

import pytest
from jinja2 import UndefinedError

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / ".claude/skills/llm-prompts"
EXAMPLES = SKILL / "references/examples"


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


def test_chain_prompt_keeps_the_question_apart(monkeypatch):
    chain = load_example("chain", monkeypatch)
    messages = chain.PROMPT.format_messages(context=chain.TICKET, question="How much is each charge?")
    assert [m.type for m in messages] == ["system", "human", "human"]
    assert "185,000 COP" in messages[1].content


def test_jinja_example_renders_and_fails_on_missing_data(monkeypatch):
    jinja = load_example("jinja_prompt", monkeypatch)
    prompt = jinja.render_system_prompt(jinja.TICKET, jinja.RULES)
    assert "- Charge date: yesterday" in prompt and "2. Do not convert" in prompt
    assert prompt.count("- Charge: 185000 COP") == 2
    without_customer = {key: value for key, value in jinja.TICKET.items() if key != "customer"}
    with pytest.raises(UndefinedError):
        jinja.render_system_prompt(without_customer, [])
