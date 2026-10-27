"""Project adapter: the only example file that knows this repository.

The example servers make no model calls; they only need the sample corpus and the embeddings model.
To reuse the skill in another project, rewrite this file and references/project.md.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
# Synthetic ACME policy PDFs that docs_server.py indexes. A generated server uses its own documents/ folder.
SAMPLE_DOCUMENTS = ROOT / "datasets"
# Open multilingual model, local: no key, no cost, documents never leave the machine.
EMBEDDINGS_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
