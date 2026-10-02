import importlib.util
import os
from pathlib import Path
import sys
import unittest
from datetime import date, timedelta
from unittest.mock import patch

from langchain.agents import create_agent
from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

os.environ['LANGSMITH_TRACING'] = 'false'
os.environ['LANGCHAIN_TRACING_V2'] = 'false'
root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))
sys.path.insert(0, str(root / 'src'))


class BookingModel(FakeMessagesListChatModel):
    def bind_tools(self, tools, **kwargs):
        return self


def load_booking_agent(responses):
    model = BookingModel(responses=responses)

    def create_test_agent(**kwargs):
        return create_agent(
            model=model,
            tools=kwargs['tools'],
            system_prompt=kwargs['system_prompt'],
        )

    spec = importlib.util.spec_from_file_location(
        'booking_under_test', root / 'src/agents/support/nodes/booking/node.py'
    )
    module = importlib.util.module_from_spec(spec)
    with patch('dotenv.load_dotenv'), patch('langchain.agents.create_agent', side_effect=create_test_agent):
        spec.loader.exec_module(module)
    return module.booking_node, {tool.name: tool for tool in module.tools}


class BookingChecks(unittest.TestCase):
    def test_availability_and_booking_results_return_to_the_model(self):
        appointment_date = (date.today() + timedelta(days=7)).isoformat()
        appointment = {'date': appointment_date, 'time': '10:00', 'doctor': 'Elena'}
        agent, tools = load_booking_agent([
            AIMessage(content='', tool_calls=[{
                'name': 'get_appointment_availability', 'args': appointment,
                'id': 'availability-call', 'type': 'tool_call',
            }]),
            AIMessage(content='', tool_calls=[{
                'name': 'book_appointment', 'args': {**appointment, 'patient': 'Ana'},
                'id': 'booking-call', 'type': 'tool_call',
            }]),
            AIMessage(content='Reserva simulada para Ana con Elena a las 10:00.'),
        ])
        availability = tools['get_appointment_availability']
        booking = tools['book_appointment']
        with patch.object(availability, 'func', wraps=availability.func) as check, patch.object(booking, 'func', wraps=booking.func) as book:
            result = agent.invoke({'messages': [HumanMessage(content='Consulta disponibilidad y simula la reserva para Ana.')]})
        check.assert_called_once_with(**appointment)
        book.assert_called_once_with(**appointment, patient='Ana')
        history = result['messages']
        self.assertEqual(len(history), 6)
        self.assertIsInstance(history[2], ToolMessage)
        self.assertEqual(history[2].tool_call_id, 'availability-call')
        self.assertIn('Elena', history[2].content)
        self.assertIsInstance(history[4], ToolMessage)
        self.assertEqual(history[4].tool_call_id, 'booking-call')
        self.assertIn('Ana', history[4].content)
        self.assertIn(appointment_date, history[4].content)
        self.assertEqual(history[5].content, 'Reserva simulada para Ana con Elena a las 10:00.')
        self.assertFalse(history[5].tool_calls)

    def test_missing_patient_returns_a_tool_error_without_booking(self):
        agent, tools = load_booking_agent([
            AIMessage(content='', tool_calls=[{
                'name': 'book_appointment',
                'args': {'date': (date.today() + timedelta(days=7)).isoformat(), 'time': '10:00', 'doctor': 'Elena'},
                'id': 'incomplete-booking', 'type': 'tool_call',
            }]),
            AIMessage(content='¿Cuál es el nombre del paciente?'),
        ])
        booking = tools['book_appointment']
        with patch.object(booking, 'func', wraps=booking.func) as book:
            result = agent.invoke({'messages': [HumanMessage(content='Simula una reserva con Elena.')]})
        book.assert_not_called()
        history = result['messages']
        self.assertIsInstance(history[2], ToolMessage)
        self.assertEqual(history[2].tool_call_id, 'incomplete-booking')
        self.assertEqual(history[2].status, 'error')
        self.assertIn('patient', history[2].content)
        self.assertEqual(history[3].content, '¿Cuál es el nombre del paciente?')


if __name__ == '__main__':
    unittest.main(verbosity=2)
