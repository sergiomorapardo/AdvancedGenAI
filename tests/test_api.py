import asyncio
import importlib
import json
import os
from pathlib import Path
import sys
import threading
import types
import unittest
from unittest.mock import Mock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage, AIMessageChunk, HumanMessage
from starlette.requests import Request

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

# Import the HTTP layer without constructing models or reading developer secrets.
graph_stub = types.ModuleType("agents.support.agent")
graph_stub.make_graph = Mock()
with patch.dict(sys.modules, {"agents.support.agent": graph_stub}), patch("dotenv.load_dotenv"):
    api = importlib.import_module("api.main")
    db = importlib.import_module("api.db")


class ApiChecks(unittest.TestCase):
    def setUp(self):
        self.checkpointer = Mock()
        self.app = api.app
        self.app.dependency_overrides[db.get_checkpointer] = lambda: self.checkpointer
        self.client = TestClient(self.app)

    def tearDown(self):
        self.client.close()
        self.app.dependency_overrides.clear()

    def test_chat_passes_thread_and_returns_history_off_event_loop(self):
        graph = Mock()

        def invoke(state, config):
            with self.assertRaises(RuntimeError):
                asyncio.get_running_loop()
            self.assertEqual(config, {"configurable": {"thread_id": "session-1"}})
            self.assertEqual(state["messages"][0].content, "Hola")
            return {"messages": [HumanMessage(content="Hola"), AIMessage(content="Hola Ana")]}

        graph.invoke.side_effect = invoke
        with patch.object(api, "make_graph", return_value=graph) as factory:
            response = self.client.post("/chat/session-1", json={"message": "Hola"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual([item["content"] for item in response.json()], ["Hola", "Hola Ana"])
        factory.assert_called_once_with(checkpointer=self.checkpointer)

    def test_stream_frames_multiline_and_content_blocks_and_hides_internal_calls(self):
        graph = Mock()
        content_blocks = [{"type": "text", "text": "Booking reply"}]

        def stream(state, config, stream_mode):
            with self.assertRaises(RuntimeError):
                asyncio.get_running_loop()
            self.assertEqual(config["configurable"]["thread_id"], "session-2")
            self.assertEqual(stream_mode, "messages")
            self.assertEqual(state["messages"][0].content, "Hola")
            yield AIMessageChunk(content="private extraction"), {"langgraph_node": "extractor"}
            yield AIMessageChunk(content=""), {"langgraph_node": "conversation"}
            yield AIMessageChunk(content="Hola\n\nmundo"), {"langgraph_node": "conversation"}
            yield AIMessageChunk(content=content_blocks), {"langgraph_node": "model"}

        graph.stream.side_effect = stream
        with patch.object(api, "make_graph", return_value=graph):
            response = self.client.post("/chat/session-2/stream", json={"message": "Hola"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/event-stream", response.headers["content-type"])
        frames = response.text.strip().split("\n\n")
        self.assertEqual([json.loads(frame.removeprefix("data: ")) for frame in frames], [
            {"content": "Hola\n\nmundo"}, {"content": content_blocks}
        ])

    def test_invalid_messages_are_rejected(self):
        with patch.object(api, "make_graph") as factory:
            for path in ("/chat/test", "/chat/test/stream"):
                for payload in ({}, {"message": ""}, {"message": None}):
                    self.assertEqual(self.client.post(path, json=payload).status_code, 422)
            factory.assert_not_called()


class DatabaseChecks(unittest.IsolatedAsyncioTestCase):
    async def test_missing_uri_fails_with_actionable_error(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "Set DB_URI"):
                async with db.lifespan(FastAPI()):
                    self.fail("Lifespan should fail before serving requests")

    async def test_lifespan_initializes_and_closes_app_scoped_saver(self):
        app = FastAPI()
        request = Request({"type": "http", "app": app})
        with self.assertRaisesRegex(RuntimeError, "not initialized"):
            db.get_checkpointer(request)
        event_loop_thread = threading.get_ident()
        with patch.dict(os.environ, {"DB_URI": "postgresql://example/test"}), patch.object(db.PostgresSaver, "from_conn_string") as connect:
            saver = connect.return_value.__enter__.return_value
            saver.setup.side_effect = lambda: self.assertNotEqual(threading.get_ident(), event_loop_thread)
            with self.assertRaisesRegex(ValueError, "test error"):
                async with db.lifespan(app):
                    self.assertIs(db.get_checkpointer(request), saver)
                    saver.setup.assert_called_once()
                    raise ValueError("test error")
            connect.assert_called_once_with("postgresql://example/test")
            connect.return_value.__exit__.assert_called_once()
        with self.assertRaisesRegex(RuntimeError, "not initialized"):
            db.get_checkpointer(request)


if __name__ == "__main__":
    unittest.main()
