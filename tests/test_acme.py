import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")  # crear el modelo no llama a la API
os.environ["LANGSMITH_TRACING"] = "false"
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from langchain_core.embeddings import DeterministicFakeEmbedding
from langgraph.checkpoint.memory import InMemorySaver

with patch("dotenv.load_dotenv"):
    from agents import acme


class AcmeAgentChecks(unittest.TestCase):
    def test_credit_tool_reads_the_portfolio_and_returns_bad_codes_as_data(self):
        result = acme.check_credit.invoke({"customer": "c-3307", "product": "CLI"})
        self.assertEqual(result["status"], "ok")
        [credit] = result["credits"]
        self.assertEqual((credit["overdue"], credit["days_past_due"]), (2_070_000, 75))
        self.assertEqual(acme.check_credit.invoke({"customer": "1042"})["status"], "invalid")

    def test_policy_search_cites_file_and_page(self):
        acme.retriever.cache_clear()
        fake = lambda model_name: DeterministicFakeEmbedding(size=384)  # noqa: E731 -- sin descargar el modelo
        try:
            with patch.object(acme, "FastEmbedEmbeddings", fake):
                text = acme.search_policies.invoke({"query": "¿Puedo reestructurar mi crédito?"})
        finally:
            acme.retriever.cache_clear()
        self.assertEqual(text.count("[acme_"), 3)

    def test_graph_has_the_model_and_both_tools_and_accepts_a_checkpointer(self):
        graph = acme.make_graph(checkpointer=InMemorySaver())
        self.assertTrue({"model", "tools"} <= set(graph.get_graph().nodes))
        self.assertEqual(
            sorted(tool.name for tool in graph.nodes["tools"].bound.tools_by_name.values()),
            ["check_credit", "search_policies"],
        )


if __name__ == "__main__":
    unittest.main()
