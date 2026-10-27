"""Servidor MCP de créditos: consultas parametrizadas y de solo lectura sobre SQLite.

Lo arranca el cliente, desde cualquier carpeta del proyecto:
    python -m agents.servers.credits          # stdio: el cliente lo abre como subproceso
    python -m agents.servers.credits --http   # streamable HTTP en http://127.0.0.1:8001/mcp

CREDITS_DB apunta a otra base SQLite con la misma tabla `credits`. Por defecto usa
data/acme_credits.db, que se crea la primera vez con datasets/acme_credits.sql.
"""

import os
import re
import sqlite3
import sys
import unicodedata
from pathlib import Path
from typing import Annotated, Literal

from mcp.server import MCPServer
from mcp.server.mcpserver import AcceptedElicitation, Context, Elicit, ElicitationResult, Resolve
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import ToolAnnotations
from pydantic import BaseModel, Field, create_model

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DB = ROOT / "data" / "acme_credits.db"
DB = Path(os.getenv("CREDITS_DB", DEFAULT_DB))

# En stdio, stdout es el canal del protocolo: el servidor nunca debe usar print().
mcp = MCPServer(
    "creditos",
    instructions="Cartera sintética de ACME: saldo, cuotas vencidas y días de mora por cliente y producto. Solo lectura.",
    log_level="WARNING",
)
READ_ONLY = ToolAnnotations(read_only_hint=True, open_world_hint=False)

Customer = Annotated[str, Field(description="Código del cliente, por ejemplo «C-1042».")]
Product = Annotated[str, Field(description="Código (CLI, CEX) o nombre del producto; vacío para todos sus créditos.")]


def unaccent(text: str) -> str:
    """«Crédito» y «credito» deben encontrar lo mismo."""
    return "".join(c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn").lower()


def connect() -> sqlite3.Connection:
    if DB == DEFAULT_DB and not DB.exists():
        DB.parent.mkdir(exist_ok=True)
        with sqlite3.connect(DB) as setup:
            setup.executescript((ROOT / "datasets" / "acme_credits.sql").read_text(encoding="utf-8"))
    # mode=ro: la conexión no puede escribir, aunque alguien cambie una consulta.
    connection = sqlite3.connect(f"{DB.resolve().as_uri()}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    connection.create_function("unaccent", 1, unaccent, deterministic=True)
    return connection


def find_credits(customer: str, product: str) -> list[dict]:
    if not re.fullmatch(r"C-\d{4}", customer.strip().upper()):
        # ToolError: el modelo lee el mensaje; cualquier otra excepción llega como un error genérico.
        raise ToolError("Escribe el código del cliente con el formato C-1234.")
    if len(product) > 80 or any(character in product for character in "%_"):
        raise ToolError("Escribe el producto en máximo 80 caracteres, sin comodines % ni _.")
    # Los valores van como parámetros (?), nunca pegados al texto del SQL.
    sql = """
        SELECT customer, code, product, balance, installment * overdue_installments AS overdue, days_past_due
        FROM credits
        WHERE customer = ? AND (? = '' OR unaccent(code || ' ' || product) LIKE ?)
        ORDER BY code
    """
    with connect() as connection:
        rows = connection.execute(sql, (customer.strip().upper(), product, f"%{unaccent(product)}%"))
        return [dict(row) for row in rows]


class CreditRow(BaseModel):
    """Un crédito de la cartera. Con este tipo de salida, el SDK publica el outputSchema de la herramienta."""

    customer: str
    code: str
    product: str
    balance: int = Field(description="Saldo del crédito, en pesos colombianos.")
    overdue: int = Field(description="Monto vencido: cuota por cuotas vencidas, en pesos colombianos.")
    days_past_due: int = Field(description="Días de mora.")


class ProductChoice(BaseModel):
    code: str = Field(description="Código del crédito que la persona quiere consultar.")


async def choose_product(customer: str, ctx: Context, product: str = "") -> ProductChoice | Elicit[ProductChoice]:
    """Si el cliente tiene varios créditos que coinciden, se lo pregunta a la persona (elicitation)."""
    codes = sorted({row["code"]: row["product"] for row in find_credits(customer, product)}.items())
    capabilities = ctx.client_capabilities
    if len(codes) <= 1 or not (capabilities and capabilities.elicitation):
        return ProductChoice(code="")  # nada que elegir, o un cliente que no puede preguntar: todas las filas
    options = ", ".join(f"{code} ({name})" for code, name in codes)
    choice = create_model(
        "ProductChoice", code=(Literal[tuple(code for code, _ in codes)], Field(description="Código del crédito."))
    )
    return Elicit(f"El cliente {customer} tiene varios créditos: {options}. ¿Cuál consulto?", choice)


@mcp.tool(annotations=READ_ONLY)
async def check_credit(
    customer: Customer,
    choice: Annotated[ElicitationResult[ProductChoice], Resolve(choose_product)],
    product: Product = "",
) -> list[CreditRow]:
    """Consulta los créditos de un cliente de ACME.

    Devuelve una fila por crédito con el saldo (balance), el monto vencido (overdue) y los días de mora,
    en pesos colombianos. Si el cliente tiene varios créditos y no se indica cuál, pregunta a la persona.
    """
    rows = find_credits(customer, product)
    if isinstance(choice, AcceptedElicitation) and choice.data.code:
        rows = [row for row in rows if row["code"] == choice.data.code]
    return [CreditRow(**row) for row in rows]


@mcp.tool(annotations=READ_ONLY)
def list_products() -> list[str]:
    """Lista los productos de crédito que tienen clientes registrados."""
    with connect() as connection:
        return [row["product"] for row in connection.execute("SELECT DISTINCT product FROM credits ORDER BY product")]


@mcp.resource("schema://credits", mime_type="text/plain")
def credits_schema() -> str:
    """La definición de la tabla credits: columnas y restricciones."""
    with connect() as connection:
        return connection.execute("SELECT sql FROM sqlite_master WHERE name = 'credits'").fetchone()["sql"]


if __name__ == "__main__":
    if "--http" in sys.argv:
        mcp.run("streamable-http", port=8001)
    else:
        mcp.run()
