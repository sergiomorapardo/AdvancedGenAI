import json
import os
from pathlib import Path
import unittest

import nbformat
from nbclient import NotebookClient

root = Path(__file__).resolve().parents[1]

# Celda que se ejecuta antes del notebook: instala el modelo simulado.
SETUP = f"""
import sys
sys.path.insert(0, {str(root / 'tests')!r})
import fake_models
fake_models.install()
"""
REPORT = "import fake_models; print(len(fake_models.CALLS))"


def run_notebook(name):
    """Ejecuta un notebook con el modelo simulado y devuelve sus llamadas al modelo."""
    notebook = nbformat.read(root / "notebooks" / name, as_version=4)
    notebook.cells.insert(0, nbformat.v4.new_code_cell(SETUP))
    notebook.cells.append(nbformat.v4.new_code_cell(REPORT))
    for key in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "LANGSMITH_API_KEY"):
        os.environ.pop(key, None)
    os.environ["LANGSMITH_TRACING"] = "false"
    NotebookClient(notebook, timeout=120, kernel_name="python3",
                   resources={"metadata": {"path": str(root / "notebooks")}}).execute()
    return int(notebook.cells[-1].outputs[0]["text"])


class NotebookChecks(unittest.TestCase):
    def test_l1_runs_offline_with_the_documented_calls(self):
        self.assertEqual(run_notebook("L1-IntroToLLMs.ipynb"), 18,
                         "Actualiza el número de llamadas en la introducción de L1")

    def test_new_notebooks_use_haiku_5_5_without_temperature(self):
        for name in ("L1-IntroToLLMs.ipynb",):
            source = "\n".join(
                "".join(cell["source"])
                for cell in json.loads((root / "notebooks" / name).read_text())["cells"]
                if cell["cell_type"] == "code"
            )
            with self.subTest(notebook=name):
                self.assertIn('model="claude-haiku-5-5"', source)
                self.assertIn('thinking={"type": "disabled"}', source)
                self.assertNotIn("temperature", source)


if __name__ == "__main__":
    unittest.main()
