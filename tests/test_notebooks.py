import ast
import csv
from datetime import date
import json
import os
from pathlib import Path
import typing
import unittest

import shutil
import tempfile

import dotenv
import httpx
import langchain_anthropic
import langchain_community.embeddings
from langchain_core.embeddings import DeterministicFakeEmbedding
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.runnables import RunnableLambda
from pydantic import BaseModel
import nbformat
from nbclient import NotebookClient
from pypdf import PdfReader

root = Path(__file__).resolve().parents[1]
datasets = root / "datasets"

# Cada respuesta del modelo simulado cuenta como una llamada.
CALLS = []


# Valores de prueba para campos que los notebooks validan con un formato.
FIELD_VALUES = {"customer": "C-1042"}


def _sample_value(annotation, name=""):
    if name in FIELD_VALUES:
        return FIELD_VALUES[name]
    origin, args = typing.get_origin(annotation), typing.get_args(annotation)
    if origin is typing.Literal:
        return args[0]
    if origin is list:
        return []
    if type(None) in args:  # campo opcional: el dato no está
        return None
    if isinstance(annotation, type) and issubclass(annotation, BaseModel):
        return _sample_model(annotation)
    if annotation is int:
        return 1
    if annotation is float:
        return 1.0
    if annotation is bool:
        return False
    return "simulado"


def _sample_model(schema):
    return schema(**{name: _sample_value(field.annotation, name) for name, field in schema.model_fields.items()})


# Argumentos que el modelo simulado propone para cada herramienta de los notebooks.
TOOL_ARGS = {
    "lookup_credit": {"customer": "C-1042", "product": "CLI", "payment": 500_000},
    "check_restructuring": {"customer": "C-3307"},
    "get_exchange_rate": {"date": date.today().isoformat()},
    "search_documents": {"query": "¿Se puede reestructurar un crédito con mora?"},
    "request_disbursement": {"customer": "C-4415", "amount_cop": 25_000_000},
}


class FakeChatAnthropic(BaseChatModel):
    """Reemplaza a ChatAnthropic dentro del kernel: no llama a ningún proveedor.

    Con herramientas, pide la primera (o la forzada) y responde en texto
    cuando recibe su resultado: así se recorre el ciclo de un agente.
    """

    model: str = "fake"
    max_tokens: int | None = None
    thinking: dict | None = None
    timeout: float | None = None
    max_retries: int | None = None
    tool_names: list[str] = []

    @property
    def _llm_type(self):
        return "fake-anthropic"

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        CALLS.append(messages)
        usage = {"input_tokens": len(messages), "output_tokens": 1, "total_tokens": len(messages) + 1}
        if self.tool_names and messages[-1].type != "tool":
            name = self.tool_names[0]
            call = {"name": name, "args": TOOL_ARGS[name], "id": f"call_{len(CALLS)}", "type": "tool_call"}
            message = AIMessage(content="", tool_calls=[call], usage_metadata=usage)
        else:
            message = AIMessage(content="Respuesta simulada.", usage_metadata=usage)
        return ChatResult(generations=[ChatGeneration(message=message)])

    def with_structured_output(self, schema, include_raw=False, **kwargs):
        def respond(prompt):
            CALLS.append(prompt)
            parsed = _sample_model(schema)
            if include_raw:
                usage = {"input_tokens": 1, "output_tokens": 1, "total_tokens": 2}
                return {"raw": AIMessage(content="", usage_metadata=usage), "parsed": parsed, "parsing_error": None}
            return parsed

        return RunnableLambda(respond)

    def bind_tools(self, tools, tool_choice=None, **kwargs):
        names = [getattr(tool, "name", None) or tool.__name__ for tool in tools]
        if isinstance(tool_choice, str) and tool_choice in names:
            names = [tool_choice]
        # bind() devuelve un RunnableBinding con .kwargs, como el modelo real.
        return self.model_copy(update={"tool_names": names}).bind(tool_choice=tool_choice)


class FakeResponse:
    """Respuesta simulada de la API de la TRM en datos.gov.co."""

    def __init__(self, status_code, payload):
        self.status_code = status_code
        self.is_error = status_code >= 400
        self._payload = payload
        self.text = json.dumps(payload)

    def json(self):
        return self._payload


def fake_get(url, params=None, timeout=None):
    params = params or {}
    if "precio" in params.get("$order", "") or "'2" not in params.get("$where", "'2"):
        return FakeResponse(400, {"message": "query.soql.no-such-column"})
    if "2099" in params.get("$where", ""):
        return FakeResponse(200, [])
    row = {"valor": "4000.00", "unidad": "COP", "vigenciadesde": "2026-01-01T00:00:00.000",
           "vigenciahasta": "2026-01-01T00:00:00.000"}
    return FakeResponse(200, [row] * int(params.get("$limit", 1)))


class FakeFastEmbedEmbeddings(DeterministicFakeEmbedding):
    """Reemplaza a FastEmbedEmbeddings: vectores deterministas sin descargar el modelo."""

    model_name: str = "fake"
    size: int = 384


def install():
    """Instala los modelos y la API simulados, y anula la carga de `.env` en el kernel."""
    langchain_anthropic.ChatAnthropic = FakeChatAnthropic
    langchain_community.embeddings.FastEmbedEmbeddings = FakeFastEmbedEmbeddings
    httpx.get = fake_get
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

    def test_l4_runs_offline_with_the_documented_calls(self):
        self.assertEqual(run_notebook("L4-RAG.ipynb"), 3,
                         "Actualiza el número de llamadas en la introducción de L4")

    def test_l11_runs_offline_with_the_documented_calls(self):
        self.assertEqual(run_notebook("L11-structured_output.ipynb"), 8,
                         "Actualiza el número de llamadas en la introducción de L11")

    def test_l18_runs_offline_with_the_documented_calls(self):
        self.assertEqual(run_notebook("L18-ConversationalRAG.ipynb"), 8,
                         "Actualiza el número de llamadas en la introducción de L18")

    def test_l9_agent_runs_offline(self):
        # El agente decide cuántas veces busca: solo se comprueba que el recorrido corre.
        self.assertGreater(run_notebook("L9-Memory.ipynb"), 0)

    def test_tool_notebooks_run_offline(self):
        # Los agentes deciden cuántas veces llamar al modelo: se comprueba que el recorrido corre.
        for name in ("L13-tools.ipynb", "L19-ToolsAPI.ipynb"):
            with self.subTest(notebook=name):
                self.assertGreater(run_notebook(name), 0)

    def test_langgraph_notebooks_run_offline(self):
        expected = {"L7-LangGraphSimple.ipynb": 0, "L8-LangGraphMessages.ipynb": 2,
                    "L14-Routing.ipynb": 6, "L15-Paralelization.ipynb": 3}
        for name, calls in expected.items():
            with self.subTest(notebook=name):
                self.assertEqual(run_notebook(name), calls)
        # El agente de L22 se pausa antes de la herramienta: se comprueba que el recorrido corre.
        self.assertGreater(run_notebook("L22-HumanInTheLoop.ipynb"), 0)
        # La compuerta de L10 depende de la clasificación: solo se comprueba que corre.
        self.assertGreater(run_notebook("L10-chaining.ipynb"), 0)

    def test_embedding_notebooks_run_offline_without_model_calls(self):
        for name in ("L3-Embeddings.ipynb", "L2-PDFSearchFAISS.ipynb"):
            with self.subTest(notebook=name):
                self.assertEqual(run_notebook(name), 0)

    def test_new_notebooks_use_haiku_5_5_without_temperature(self):
        for name in ("L1-IntroToLLMs.ipynb", "L11-structured_output.ipynb", "L12-dynamic-prompting.ipynb", "L4-RAG.ipynb",
                     "L18-ConversationalRAG.ipynb", "L9-Memory.ipynb",
                     "L13-tools.ipynb", "L19-ToolsAPI.ipynb", "L5-RAGEvaluation.ipynb",
                     "L21-MCPAgent.ipynb", "L22-HumanInTheLoop.ipynb"):
            source = "\n".join(
                "".join(cell["source"])
                for cell in json.loads((root / "notebooks" / name).read_text())["cells"]
                if cell["cell_type"] == "code"
            )
            with self.subTest(notebook=name):
                self.assertIn('model="claude-haiku-5-5"', source)
                self.assertIn('thinking={"type": "disabled"}', source)
                self.assertNotIn("temperature", source)


    def test_langsmith_notebooks_compile_without_running(self):
        # L5 escribe en LangSmith y L20–L21 arrancan servidores (probados en test_servers.py):
        # offline solo se comprueba que compilan.
        for name in ("L5-RAGEvaluation.ipynb", "L20-MCPServer.ipynb", "L21-MCPAgent.ipynb"):
            notebook = json.loads((root / "notebooks" / name).read_text())
            for index, cell in enumerate(notebook["cells"]):
                if cell["cell_type"] == "code":
                    with self.subTest(notebook=name, cell=index):
                        # Jupyter acepta await en el nivel superior, como IPython.
                        compile("".join(cell["source"]), f"{name}[{index}]", "exec",
                                flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT)


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

    def test_review_set_points_to_known_questions(self):
        with open(datasets / "acme_questions.csv", encoding="utf-8") as file:
            ids = {row["id"] for row in csv.DictReader(file)}
        with open(datasets / "acme_review_set.csv", encoding="utf-8") as file:
            reviews = list(csv.DictReader(file))
        self.assertTrue(reviews)
        for row in reviews:
            with self.subTest(review=row["review_id"]):
                self.assertIn(row["id"], ids)
                self.assertIn(row["human_correct"], {"0", "1"})


if __name__ == "__main__":
    unittest.main()
