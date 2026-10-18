import importlib
import json
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import Mock, patch

os.environ['LANGSMITH_TRACING'] = 'false'
os.environ['LANGCHAIN_TRACING_V2'] = 'false'
root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / 'src'))

from langchain_core.documents import Document
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.runnables import RunnableLambda

booking_node = Mock()
with patch('dotenv.load_dotenv'), patch('langchain.chat_models.init_chat_model'), patch('langchain.agents.create_agent', return_value=RunnableLambda(booking_node)):
    graph_module = importlib.import_module('agents.support.agent')
    conversation = importlib.import_module('agents.support.nodes.conversation.node')
    extractor = importlib.import_module('agents.support.nodes.extractor.node')
    tools = importlib.import_module('agents.support.nodes.conversation.tools')
    intent = importlib.import_module('agents.support.routes.intent.route')


class SupportChecks(unittest.TestCase):
    def setUp(self):
        router = patch.object(intent, 'llm')
        self.route_model = router.start()
        self.addCleanup(router.stop)
        self.route_model.invoke.return_value = intent.RouteIntent(step='conversation')
        booking_node.reset_mock()

    def test_contact_fields_survive_graph(self):
        contact = extractor.ContactInfo(name='Ana', email='ana@example.com', phone='123', age=30)
        with patch.object(extractor, 'llm_with_structured_output') as model, patch.object(conversation, 'llm_with_tools') as chat:
            model.invoke.return_value = contact
            chat.invoke.return_value = AIMessage(content='Hola Ana')
            result = graph_module.agent.invoke({'messages': [HumanMessage(content='Soy Ana')]})
        self.assertEqual({key: result[key] for key in ('name', 'email', 'phone', 'age')}, contact.model_dump())
        self.assertEqual(result['customer_name'], 'Ana')
        self.assertEqual(len(result['messages']), 2)
        self.assertIn('Ana', chat.invoke.call_args.args[0][0].content)
        self.route_model.invoke.assert_called_once()
        booking_node.assert_not_called()

    def test_tool_round_trip(self):
        responses = [
            AIMessage(content='', tool_calls=[{'name': 'search_docs', 'args': {'query': 'RAG'}, 'id': 'call-1', 'type': 'tool_call'}]),
            AIMessage(content='Respuesta con fuente'),
        ]
        retriever = Mock()
        retriever.invoke.return_value = [Document(page_content='RAG info', metadata={'source': '/pdfs/course.pdf', 'page': 1})]
        with patch.object(conversation, 'llm_with_tools') as chat, patch.object(tools, '_get_retriever', return_value=retriever), patch.object(extractor, 'llm_with_structured_output') as extract:
            chat.invoke.side_effect = responses
            result = graph_module.agent.invoke({'messages': [HumanMessage(content='Qué es RAG?')], 'customer_name': 'Ana'})
        extract.invoke.assert_not_called()
        retriever.invoke.assert_called_once_with('RAG')
        self.assertEqual(chat.invoke.call_count, 2)
        self.assertIsInstance(result['messages'][-2], ToolMessage)
        self.assertEqual(result['messages'][-2].content, '[course.pdf p.2]\nRAG info')
        self.assertEqual(result['messages'][-1].content, 'Respuesta con fuente')
        self.route_model.invoke.assert_called_once()
        booking_node.assert_not_called()

    def test_booking_route_preserves_contact_and_skips_conversation(self):
        self.route_model.invoke.return_value = intent.RouteIntent(step='booking')
        history = [HumanMessage(content='Quiero agendar una cita')]
        response = AIMessage(content='¿Con qué doctor deseas la cita?')
        booking_node.return_value = {'messages': [response]}
        state = {'messages': history, 'customer_name': 'Ana', 'email': 'ana@example.com'}
        with patch.object(extractor, 'llm_with_structured_output') as extract, patch.object(conversation, 'llm_with_tools') as chat, patch.object(tools, '_get_retriever') as retrieve:
            result = graph_module.agent.invoke(state)
        self.route_model.invoke.assert_called_once()
        booking_node.assert_called_once()
        self.assertEqual(booking_node.call_args.args[0]['customer_name'], 'Ana')
        self.assertEqual(booking_node.call_args.args[0]['email'], 'ana@example.com')
        self.assertEqual(result['messages'], [*history, response])
        self.assertEqual(result['customer_name'], 'Ana')
        self.assertEqual(result['email'], 'ana@example.com')
        extract.invoke.assert_not_called()
        chat.invoke.assert_not_called()
        retrieve.assert_not_called()
        self.assertEqual(state['messages'], history)

    def test_intent_routes_use_system_prompt_and_preserve_history(self):
        history = [HumanMessage(content='Hola')]
        state = {'messages': history}
        for step in ('conversation', 'booking'):
            with self.subTest(step=step):
                self.route_model.reset_mock()
                self.route_model.invoke.return_value = intent.RouteIntent(step=step)
                self.assertEqual(intent.route_intent(state), step)
                self.route_model.invoke.assert_called_once()
                sent = self.route_model.invoke.call_args.args[0]
                self.assertIsInstance(sent[0], SystemMessage)
                self.assertEqual(sent[0].content, intent.SYSTEM_PROMPT)
                self.assertEqual(sent[1:], history)
                self.assertEqual(state, {'messages': history})
                self.assertEqual(len(history), 1)

    def test_intent_rejects_unknown_destination(self):
        self.route_model.invoke.return_value = Mock(step='unknown')
        with self.assertRaisesRegex(ValueError, 'Invalid step: unknown'):
            intent.route_intent({'messages': [HumanMessage(content='Hola')]})

    def test_extraction_threshold(self):
        with patch.object(extractor, 'llm_with_structured_output') as model:
            model.invoke.return_value = extractor.ContactInfo(name='Ana')
            self.assertEqual(extractor.extractor({'messages': [HumanMessage(content='Hola')] * 9, 'customer_name': 'Ana'}), {})
            model.invoke.assert_not_called()
            result = extractor.extractor({'messages': [HumanMessage(content='Hola')] * 10, 'customer_name': 'Ana'})
            model.invoke.assert_called_once()
            self.assertEqual(result['customer_name'], 'Ana')

    def test_missing_contact_values(self):
        contact = extractor.ContactInfo(name=None, email=None, phone=None, age=None)
        with patch.object(extractor, 'llm_with_structured_output') as model:
            model.invoke.return_value = contact
            result = extractor.extractor({'messages': [HumanMessage(content='Hola')]})
        self.assertTrue(all(value is None for value in result.values()))

    def test_paths_and_lazy_retrieval(self):
        self.assertEqual(tools.ROOT_DIR, root)
        self.assertEqual(tools._get_retriever.cache_info().currsize, 0)
        self.assertEqual(tools._format_documents([Document(page_content='Text')]), '[documento p.1]\nText')

    def test_registration_and_independence(self):
        graphs = json.loads((root / 'langgraph.json').read_text())['graphs']
        self.assertTrue({'agent', 'simple', 'rag', 'contact', 'support', 'react', 'booking'} <= set(graphs))
        self.assertEqual(graphs['support'], './src/agents/support/agent.py:agent')
        self.assertNotIn('agents.contact', sys.modules)
        self.assertNotIn('agents.rag', sys.modules)
        for entry in graphs.values():
            self.assertTrue((root / entry.split(':')[0]).is_file())

    def test_extractor_prompt_and_input_not_mutated(self):
        history = [HumanMessage(content="Soy Ana")]
        state = {"messages": history}
        with patch.object(extractor, "llm_with_structured_output") as model:
            model.invoke.return_value = extractor.ContactInfo(name="Ana")
            update = extractor.extractor(state)
        sent = model.invoke.call_args.args[0]
        self.assertIsInstance(sent[0], SystemMessage)
        self.assertEqual(sent[0].content, extractor.SYSTEM_PROMPT)
        self.assertEqual(sent[1:], history)
        self.assertEqual(state, {"messages": history})
        self.assertEqual(len(history), 1)
        self.assertNotIn("messages", update)

    def test_conversation_returns_only_new_message(self):
        history = [HumanMessage(content="Hola")]
        state = {"messages": history, "customer_name": "Ana", "email": "ana@example.com"}
        response = AIMessage(content="Hola Ana")
        with patch.object(conversation, "llm_with_tools") as model:
            model.invoke.return_value = response
            update = conversation.conversation(state)
        self.assertEqual(update, {"messages": [response]})
        self.assertEqual(state["email"], "ana@example.com")
        self.assertEqual(state["messages"], history)
        self.assertEqual(len(history), 1)

    def test_existing_vector_store_is_reused(self):
        tools._get_retriever.cache_clear()
        try:
            with patch.object(tools, "Chroma") as chroma, patch.object(tools, "OpenAIEmbeddings") as embeddings, patch.object(tools, "DirectoryLoader") as loader, patch.object(tools, "CHROMA_DIR") as directory:
                directory.__str__.return_value = "/existing/chroma"
                store = chroma.return_value
                store.get.return_value = {"ids": ["existing-chunk"]}
                retriever = tools._get_retriever()
                self.assertIs(tools._get_retriever(), retriever)
                chroma.assert_called_once_with(
                    collection_name="advancedgenai-course-rag",
                    embedding_function=embeddings.return_value,
                    persist_directory="/existing/chroma",
                )
                embeddings.assert_called_once_with(model="text-embedding-3-small")
                loader.assert_not_called()
                store.add_documents.assert_not_called()
                store.as_retriever.assert_called_once_with(search_kwargs={"k": 4})
        finally:
            tools._get_retriever.cache_clear()


if __name__ == '__main__':
    unittest.main(verbosity=2)
