import importlib
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import Mock, patch

import requests
from langchain.agents import create_agent
from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

os.environ['LANGSMITH_TRACING'] = 'false'
os.environ['LANGCHAIN_TRACING_V2'] = 'false'
root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / 'src'))

# Import the tools without loading credentials or constructing a real model.
with patch('dotenv.load_dotenv'), patch('langchain.agents.create_agent'):
    react = importlib.import_module('agents.support.ReAct')


class ToolCallingModel(FakeMessagesListChatModel):
    def bind_tools(self, tools, **kwargs):
        return self


def api_response(data):
    response = Mock()
    response.json.return_value = data
    return response


class ReactChecks(unittest.TestCase):
    def weather_responses(self):
        return [
            api_response({'results': [{'latitude': 4.61, 'longitude': -74.08}]}),
            api_response({'current_weather': {'temperature': 16.2, 'windspeed': 13.4}}),
        ]

    def test_products_are_returned_with_their_prices(self):
        response = api_response([
            {'title': 'Camiseta', 'price': 20.0},
            {'title': 'Chaqueta', 'price': 100.0},
        ])
        with patch.object(react.requests, 'get', return_value=response) as get:
            result = react.get_products.invoke({})
        self.assertEqual(result, 'Camiseta: $20.0\nChaqueta: $100.0')
        get.assert_called_once_with('https://fakestoreapi.com/products', timeout=15)
        response.raise_for_status.assert_called_once()

    def test_weather_uses_geocoded_coordinates(self):
        responses = self.weather_responses()
        with patch.object(react.requests, 'get', side_effect=responses) as get:
            result = react.get_weather.invoke({'city': 'Bogotá'})
        self.assertIn('Bogotá', result)
        self.assertIn('16.2 °C', result)
        self.assertIn('13.4 km/h', result)
        self.assertEqual(get.call_count, 2)
        self.assertEqual(get.call_args_list[0].kwargs['params']['name'], 'Bogotá')
        self.assertEqual(get.call_args_list[1].args[0], 'https://api.open-meteo.com/v1/forecast')
        params = get.call_args_list[1].kwargs['params']
        self.assertEqual(params['latitude'], 4.61)
        self.assertEqual(params['longitude'], -74.08)
        self.assertTrue(params['current_weather'])
        for response in responses:
            response.raise_for_status.assert_called_once()

    def test_failed_geocoding_does_not_request_a_forecast(self):
        response = Mock()
        response.raise_for_status.side_effect = requests.HTTPError('503 Service Unavailable')
        with patch.object(react.requests, 'get', return_value=response) as get:
            with self.assertRaises(requests.HTTPError):
                react.get_weather.invoke({'city': 'Bogotá'})
        self.assertEqual(get.call_count, 1)
        response.json.assert_not_called()

    def test_agent_executes_the_requested_tool_and_returns_to_the_model(self):
        model = ToolCallingModel(responses=[
            AIMessage(content='', tool_calls=[{
                'name': 'get_weather', 'args': {'city': 'Bogotá'},
                'id': 'weather-call', 'type': 'tool_call',
            }]),
            AIMessage(content='En Bogotá hay 16.2 °C y viento de 13.4 km/h.'),
        ])
        agent = create_agent(model=model, tools=react.tools, system_prompt=react.prompt_template.format())
        with patch.object(react.requests, 'get', side_effect=self.weather_responses()) as get:
            result = agent.invoke({'messages': [HumanMessage(content='¿Qué clima hace en Bogotá?')]})
        history = result['messages']
        self.assertEqual(len(history), 4)
        self.assertEqual(history[1].tool_calls[0]['name'], 'get_weather')
        self.assertIsInstance(history[2], ToolMessage)
        self.assertEqual(history[2].tool_call_id, 'weather-call')
        self.assertIn('16.2 °C', history[2].content)
        self.assertEqual(history[3].content, 'En Bogotá hay 16.2 °C y viento de 13.4 km/h.')
        self.assertFalse(history[3].tool_calls)
        self.assertEqual(get.call_count, 2)


if __name__ == '__main__':
    unittest.main(verbosity=2)
