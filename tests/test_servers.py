import asyncio
import importlib
import os
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import patch

from langchain_core.embeddings import DeterministicFakeEmbedding
from mcp import Client
from mcp.types import ElicitResult

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / "src"))


def run(coroutine):
    return asyncio.run(coroutine)


class CreditsServerChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Base temporal: las pruebas no tocan data/ del repositorio.
        cls.workdir = tempfile.TemporaryDirectory()
        database = Path(cls.workdir.name) / "credits.db"
        with sqlite3.connect(database) as setup:
            setup.executescript((root / "datasets" / "acme_credits.sql").read_text(encoding="utf-8"))
        with patch.dict(os.environ, {"CREDITS_DB": str(database)}):
            cls.server = importlib.reload(importlib.import_module("agents.servers.credits"))

    @classmethod
    def tearDownClass(cls):
        cls.workdir.cleanup()

    def call(self, arguments, **client_options):
        async def go():
            async with Client(self.server.mcp, **client_options) as client:
                return await client.call_tool("check_credit", arguments)

        return run(go())

    def test_tools_are_read_only_and_publish_an_output_schema(self):
        async def go():
            async with Client(self.server.mcp) as client:
                return await client.list_tools()

        tools = {tool.name: tool for tool in run(go()).tools}
        self.assertEqual(set(tools), {"check_credit", "list_products"})
        self.assertTrue(all(tool.annotations.read_only_hint for tool in tools.values()))
        self.assertIn("CreditRow", tools["check_credit"].output_schema["$defs"])

    def test_overdue_is_installment_times_overdue_installments(self):
        result = self.call({"customer": "c-3307", "product": "credito libre inversion"})
        self.assertFalse(result.is_error)
        [row] = result.structured_content["result"]
        self.assertEqual((row["code"], row["overdue"], row["days_past_due"]), ("CLI", 2_070_000, 75))

    def test_invalid_input_is_a_readable_error_and_injection_finds_nothing(self):
        self.assertTrue(self.call({"customer": "1042"}).is_error)
        self.assertTrue(self.call({"customer": "C-1042", "product": "%"}).is_error)
        injection = self.call({"customer": "C-1042", "product": "x' OR '1'='1"})
        self.assertEqual(injection.structured_content["result"], [])

    def test_ambiguous_customer_asks_only_clients_that_can_elicit(self):
        questions = []

        async def ask(context, params):
            questions.append(params.message)
            return ElicitResult(action="accept", content={"code": "CLI"})

        chosen = self.call({"customer": "C-1042"}, elicitation_callback=ask)
        everything = self.call({"customer": "C-1042"})
        self.assertEqual(len(questions), 1)
        self.assertEqual([row["code"] for row in chosen.structured_content["result"]], ["CLI"])
        self.assertEqual([row["code"] for row in everything.structured_content["result"]], ["CEX", "CLI"])

    def test_connection_cannot_write(self):
        with self.assertRaises(sqlite3.OperationalError):
            self.server.connect().execute("DELETE FROM credits")


class DocumentsServerChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = importlib.import_module("agents.servers.documents")
        cls.server.retriever.cache_clear()
        # Embeddings deterministas: no se descarga el modelo.
        cls.embeddings = patch.object(cls.server, "embeddings", lambda: DeterministicFakeEmbedding(size=384))
        cls.embeddings.start()

    @classmethod
    def tearDownClass(cls):
        cls.embeddings.stop()
        cls.server.retriever.cache_clear()

    def test_search_returns_three_cited_fragments(self):
        async def go():
            async with Client(self.server.mcp) as client:
                return await client.call_tool("search_documents", {"query": "¿Puedo reestructurar mi crédito?"})

        text = run(go()).content[0].text
        self.assertEqual(text.count("[acme_"), 3)

    def test_resources_only_open_the_policy_files(self):
        async def go():
            async with Client(self.server.mcp) as client:
                policy = await client.read_resource("docs://acme_collections_policy.pdf")
                with self.assertRaises(Exception):
                    await client.read_resource("docs://../.env")
                return policy

        self.assertIn("Reestructuración", run(go()).contents[0].text)

    def test_prompt_links_the_collections_policy(self):
        async def go():
            async with Client(self.server.mcp) as client:
                return await client.get_prompt("restructuring_request", {"customer": "C-1042"})

        messages = run(go()).messages
        self.assertEqual([message.content.type for message in messages], ["text", "resource_link"])
        self.assertEqual(messages[-1].content.uri, "docs://acme_collections_policy.pdf")


if __name__ == "__main__":
    unittest.main()
