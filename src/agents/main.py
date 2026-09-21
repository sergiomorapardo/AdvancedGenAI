from dotenv import find_dotenv, load_dotenv

from langchain.agents import create_agent


# find_dotenv sube por las carpetas hasta encontrar el .env de la raíz
load_dotenv(find_dotenv())

def get_weather(city: str) -> str:
    """Get weather for a given city."""
    return f"It's always sunny in {city}!"


agent = create_agent(
    model="anthropic:claude-haiku-4-5",
    tools=[get_weather],
    system_prompt="You are a helpful assistant",
)
