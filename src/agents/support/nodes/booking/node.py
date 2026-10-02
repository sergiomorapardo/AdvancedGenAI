from dotenv import find_dotenv, load_dotenv

from langchain.agents import create_agent
from src.agents.support.nodes.booking.tools import tools
from src.agents.support.nodes.booking.prompt import prompt_template


# find_dotenv sube por las carpetas hasta encontrar el .env de la raíz
load_dotenv(find_dotenv())

booking_node = create_agent(
    model="anthropic:claude-haiku-4-5",
    tools=tools,
    system_prompt=prompt_template.format(),
)
