import csv
import json
import os
from pathlib import Path
import typing
import unittest

import shutil
import tempfile

import dotenv
import langchain_anthropic
import langchain_community.embeddings
from langchain_core.embeddings import DeterministicFakeEmbedding
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.runnables import RunnableLambda
import nbformat
from nbclient import NotebookClient
from pypdf import PdfReader

root = Path(__file__).resolve().parents[1]
datasets = root / "datasets"

# Cada respuesta del modelo simulado cuenta como una llamada.
CALLS = []


def _sample_value(annotation):
    if annotation is int:
        return 0
    if annotation is float:
        return 0.0
    if annotation is bool:
        return False
    if typing.get_origin(annotation) is list:
        return []
    return "simulado"


class FakeChatAnthropic(BaseChatModel):
    """Reemplaza a ChatAnthropic dentro del kernel: no llama a ningún proveedor."""

    model: str = "fake"
    max_tokens: int | None = None
    thinking: dict | None = None
    timeout: float | None = None
    max_retries: int | None = None

    @property
    def _llm_type(self):
        return "fake-anthropic"

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        CALLS.append(messages)
        return ChatResult(generations=[ChatGeneration(message=AIMessage(content="Respuesta simulada."))])

    def with_structured_output(self, schema, **kwargs):
        def respond(prompt):
            CALLS.append(prompt)
            values = {name: _sample_value(field.annotation) for name, field in schema.model_fields.items()}
            return schema(**values)

        return RunnableLambda(respond)


class FakeFastEmbedEmbeddings(DeterministicFakeEmbedding):
    """Reemplaza a FastEmbedEmbeddings: vectores deterministas sin descargar el modelo."""

    model_name: str = "fake"
    size: int = 384


def install():
    """Instala los modelos simulados y anula la carga de `.env` en el kernel."""
    langchain_anthropic.ChatAnthropic = FakeChatAnthropic
    langchain_community.embeddings.FastEmbedEmbeddings = FakeFastEmbedEmbeddings
    dotenv.load_dotenv = lambda *args, **kwargs: False


# Celdas que se ejecutan antes y después del notebook.
SETUP = f"""
import sys
sys.path.insert(0, {str(root / 'tests')!r})
import test_notebooks
test_notebooks.install()
"""
REPORT = "print(len(test_notebooks.CALLS))"


def run_notebook(name):
    """Ejecuta un notebook con los modelos simulados y devuelve sus llamadas al modelo.

    Corre en una copia temporal de notebooks/ y datasets/: los índices que el
    notebook guarda en ../data no tocan el repositorio.
    """
    notebook = nbformat.read(root / "notebooks" / name, as_version=4)
    notebook.cells.insert(0, nbformat.v4.new_code_cell(SETUP))
    notebook.cells.append(nbformat.v4.new_code_cell(REPORT))
    for key in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "LANGSMITH_API_KEY"):
        os.environ.pop(key, None)
    os.environ["LANGSMITH_TRACING"] = "false"
    with tempfile.TemporaryDirectory() as workdir:
        shutil.copytree(datasets, Path(workdir) / "datasets")
        (Path(workdir) / "notebooks").mkdir()
        NotebookClient(notebook, timeout=120, kernel_name="python3",
                       resources={"metadata": {"path": str(Path(workdir) / "notebooks")}}).execute()
    return int(notebook.cells[-1].outputs[0]["text"])


class NotebookChecks(unittest.TestCase):
    def test_l1_runs_offline_with_the_documented_calls(self):
        self.assertEqual(run_notebook("L1-IntroToLLMs.ipynb"), 18,
                         "Actualiza el número de llamadas en la introducción de L1")

    def test_l12_runs_offline_with_the_documented_calls(self):
        self.assertEqual(run_notebook("L12-dynamic-prompting.ipynb"), 4,
                         "Actualiza el número de llamadas en la introducción de L12")

    def test_embedding_notebooks_run_offline_without_model_calls(self):
        for name in ("L3-Embeddings.ipynb", "L2-PDFSearchFAISS.ipynb"):
            with self.subTest(notebook=name):
                self.assertEqual(run_notebook(name), 0)

    def test_new_notebooks_use_haiku_5_5_without_temperature(self):
        for name in ("L1-IntroToLLMs.ipynb", "L12-dynamic-prompting.ipynb"):
            source = "\n".join(
                "".join(cell["source"])
                for cell in json.loads((root / "notebooks" / name).read_text())["cells"]
                if cell["cell_type"] == "code"
            )
            with self.subTest(notebook=name):
                self.assertIn('model="claude-haiku-5-5"', source)
                self.assertIn('thinking={"type": "disabled"}', source)
                self.assertNotIn("temperature", source)


class AcmeDatasetChecks(unittest.TestCase):
    def test_questions_point_to_existing_policy_pages(self):
        with open(datasets / "acme_questions.csv", encoding="utf-8") as file:
            rows = list(csv.DictReader(file))
        self.assertEqual(len({row["id"] for row in rows}), len(rows), "ids repetidos")
        for row in rows:
            with self.subTest(question=row["id"]):
                self.assertTrue(row["question"] and row["reference"])
                if not row["source"]:
                    # Pregunta sin respuesta en los documentos
                    self.assertFalse(row["page"])
                    continue
                pages = PdfReader(datasets / row["source"]).pages
                self.assertLessEqual(int(row["page"]), len(pages))


if __name__ == "__main__":
    unittest.main()
