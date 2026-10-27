"""Modelo simulado para ejecutar los notebooks sin llamar a proveedores.

`install()` reemplaza `ChatAnthropic` y la carga de `.env` dentro del kernel
del notebook. Cada respuesta del modelo cuenta como una llamada en `CALLS`.
"""

import typing

import dotenv
import langchain_anthropic
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.runnables import RunnableLambda

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


def install():
    langchain_anthropic.ChatAnthropic = FakeChatAnthropic
    dotenv.load_dotenv = lambda *args, **kwargs: False
