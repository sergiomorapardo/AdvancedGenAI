from langchain_core.prompts import PromptTemplate
from datetime import date
from dotenv import find_dotenv, load_dotenv
import requests

from langchain_core.tools import tool
from langchain.agents import create_agent

# find_dotenv sube por las carpetas hasta encontrar el .env de la raíz
load_dotenv(find_dotenv())

template = """\
You are a helpful assistant that can check the weather in a city and get the products that a store offers filtered by price.
as a reference today is {today}. 

You have the following tools available:
- get_weather: Obtiene el clima actual de una ciudad.
- get_products: Get the products that the store offers filtered by price

Extra rules:
- You can only check the weather for cities that exist.
- If you know the weather for a city, you can answer with get_products that the store offers for that weather.
"""

today = date.today().strftime("%Y-%m-%d")
prompt_template = PromptTemplate.from_template(template, partial_variables={"today": today})

# API de e-commerce con productos ficticios; no requiere token para consultarlos.
# Directorio: https://publicapi.dev/fake-store-api
# Documentación: https://github.com/keikaavousi/fake-store-api

@tool("get_products", description="Get the products that the store offers filtered by price")
def get_products():
    """
    Devuelve una lista de productos disponibles en la tienda que sean menores o iguales al precio dado.
    """
    response = requests.get("https://fakestoreapi.com/products", timeout=15)
    response.raise_for_status()
    products = response.json()
    return "\n".join([f"{product['title']}: ${product['price']}" for product in products])

@tool("get_weather", description="Obtiene el clima actual de una ciudad.")
def get_weather(city: str) -> str:
    response = requests.get(
        "https://geocoding-api.open-meteo.com/v1/search",
        params={"name": city, "count": 1},
        timeout=15,
    )
    response.raise_for_status()
    location = response.json()["results"][0]

    response = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": location["latitude"],
            "longitude": location["longitude"],
            "current_weather": True,
        },
        timeout=15,
    )
    response.raise_for_status()
    weather = response.json()["current_weather"]
    return f"El clima en {city} es de {weather['temperature']} °C con viento de {weather['windspeed']} km/h."

tools = [get_products, get_weather]


react_node = create_agent(
    model="anthropic:claude-haiku-4-5",
    tools=[get_weather, get_products],
    system_prompt=prompt_template.format(),
)
