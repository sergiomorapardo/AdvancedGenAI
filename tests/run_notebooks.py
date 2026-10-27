"""Prepara los notebooks de clase para versionarlos: diagramas como imagen y salidas reales.

GitHub y Colab no dibujan los bloques ```mermaid de las celdas Markdown. `diagrams`
convierte cada bloque en una imagen PNG adjunta a la celda (renderizada por mermaid.ink)
y conserva el código Mermaid plegado debajo; volver a correrlo solo descarga los
diagramas nuevos o modificados. No llama a ningún modelo.

`execute` corre los notebooks contra Claude Haiku y LangSmith tal como están, y solo
escribe un notebook si terminó sin errores. Cuesta llamadas reales: L11 además crea
trazas y experimentos en LangSmith. Quita los avisos de Python, la metadata de tiempos
y las rutas del equipo, y renumera las celdas.

    uv run python tests/run_notebooks.py diagrams [L08-RAG.ipynb ...]
    uv run python tests/run_notebooks.py execute [L08-RAG.ipynb ...]
"""

import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import re

import httpx
import nbformat
from nbclient import NotebookClient

root = Path(__file__).resolve().parents[1]
notebooks = root / "notebooks"

FENCE = re.compile(r"```mermaid\n(.*?)\n```", re.S)
RENDERED = re.compile(
    r"!\[[^\]]*\]\(attachment:mermaid-[0-9a-f]{8}\.png\)\n\n"
    r"<details><summary>Código Mermaid</summary>\n\n(```mermaid\n.*?\n```)\n\n</details>",
    re.S,
)
# Precio de Claude Haiku por millón de tokens (US$), el mismo de L11.
PRICE_PER_MILLION = {"input": 0.10, "output": 0.50}
SECRETS = re.compile(r"sk-ant-|lsv2_|sk-proj-")

USAGE_SETUP = """
from langchain_anthropic import ChatAnthropic
USAGE = []
def _record(message):
    if getattr(message, "usage_metadata", None):
        USAGE.append(dict(message.usage_metadata))
_generate, _agenerate, _stream = ChatAnthropic._generate, ChatAnthropic._agenerate, ChatAnthropic._stream
def _generate_and_record(self, *args, **kwargs):
    result = _generate(self, *args, **kwargs)
    _record(result.generations[0].message)
    return result
async def _agenerate_and_record(self, *args, **kwargs):
    result = await _agenerate(self, *args, **kwargs)
    _record(result.generations[0].message)
    return result
def _stream_and_record(self, *args, **kwargs):
    for chunk in _stream(self, *args, **kwargs):
        _record(chunk.message)
        yield chunk
ChatAnthropic._generate = _generate_and_record
ChatAnthropic._agenerate = _agenerate_and_record
ChatAnthropic._stream = _stream_and_record
"""
REPORT = "import json; print(json.dumps(USAGE))"


def render(code):
    """Pide a mermaid.ink el PNG de un diagrama."""
    encoded = base64.urlsafe_b64encode(code.encode()).decode()
    response = httpx.get(f"https://mermaid.ink/img/{encoded}", params={"type": "png", "bgColor": "!white"}, timeout=60)
    response.raise_for_status()
    return base64.b64encode(response.content).decode()


def diagrams(path):
    """Adjunta a cada celda Markdown la imagen de sus diagramas Mermaid."""
    notebook = nbformat.read(path, as_version=4)
    rendered = 0
    for cell in notebook.cells:
        if cell.cell_type != "markdown":
            continue
        source = RENDERED.sub(r"\1", cell.source)  # vuelve al Markdown original
        if not FENCE.search(source):
            continue
        old = cell.get("attachments", {})
        attachments = {}

        def replace(match):
            nonlocal rendered
            name = f"mermaid-{hashlib.sha256(match[1].encode()).hexdigest()[:8]}.png"
            if name in old:
                attachments[name] = old[name]
            else:
                attachments[name] = {"image/png": render(match[1])}
                rendered += 1
            return (f"![Diagrama](attachment:{name})\n\n<details><summary>Código Mermaid</summary>\n\n"
                    f"{match[0]}\n\n</details>")

        cell.source = FENCE.sub(replace, source)
        cell.attachments = attachments
    nbformat.write(notebook, path)
    return rendered


def clean(notebook):
    """Deja solo lo que debe versionarse: sin avisos, tiempos ni rutas del equipo."""
    home = str(Path.home())
    for count, cell in enumerate((c for c in notebook.cells if c.cell_type == "code"), 1):
        cell.execution_count = count
        cell.metadata.pop("execution", None)
        outputs = []
        for output in cell.outputs:
            if output.output_type == "stream" and output.name == "stderr":
                continue
            if "execution_count" in output:
                output.execution_count = count
            outputs.append(output)
        cell.outputs = outputs
    text = nbformat.writes(notebook).replace(home, "~")
    if SECRETS.search(text):
        raise RuntimeError("Una salida parece contener una clave: no se escribe el notebook")
    return nbformat.reads(text, as_version=4)


def execute(path):
    """Corre el notebook contra los servicios reales y lo guarda con sus salidas."""
    notebook = nbformat.read(path, as_version=4)
    notebook.cells.insert(0, nbformat.v4.new_code_cell(USAGE_SETUP))
    notebook.cells.append(nbformat.v4.new_code_cell(REPORT))
    NotebookClient(notebook, timeout=600, kernel_name="python3",
                   resources={"metadata": {"path": str(notebooks)}}).execute()
    usage = json.loads(notebook.cells[-1].outputs[0]["text"])
    notebook.cells = notebook.cells[1:-1]
    nbformat.write(clean(notebook), path)
    return usage


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("step", choices=["diagrams", "execute"])
    parser.add_argument("names", nargs="*", help="notebooks de notebooks/; todos si se omiten")
    args = parser.parse_args()
    paths = [notebooks / name for name in args.names] or sorted(notebooks.glob("*.ipynb"))
    if args.step == "diagrams":
        for path in paths:
            print(f"{path.name}: {diagrams(path)} diagramas renderizados")
        return
    os.environ["LANGSMITH_TRACING"] = "false"  # solo L11 traza, con tracing_context
    total = {"input": 0, "output": 0}
    for path in paths:
        usage = execute(path)
        tokens = {kind: sum(u[f"{kind}_tokens"] for u in usage) for kind in total}
        for kind in total:
            total[kind] += tokens[kind]
        print(f"{path.name}: {len(usage)} llamadas, {tokens['input']} tokens de entrada, {tokens['output']} de salida")
    cost = sum(total[kind] * PRICE_PER_MILLION[kind] / 1e6 for kind in total)
    print(f"Total: {total['input']} de entrada, {total['output']} de salida, ≈ US${cost:.4f}")


if __name__ == "__main__":
    main()
