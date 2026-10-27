"""Piece: an MCP server over a read-only SQLite table that asks the person when a request is ambiguous.

Tools: check_credit (typed output, so the SDK publishes its outputSchema; elicitation when a
customer has several credits) and list_products. Resource: schema://credits. The connection
itself cannot write.

A client starts it; run it by hand only to try HTTP. No model calls, no cost:
    uv run python .claude/skills/mcp-server/references/examples/credits_server.py          # stdio
    uv run python .claude/skills/mcp-server/references/examples/credits_server.py --http   # http://127.0.0.1:8001/mcp
CREDITS_DB points to another SQLite file with the same table; by default a synthetic one is created
in the temporary folder.
"""

import os
import re
import sqlite3
import sys
import tempfile
import unicodedata
from pathlib import Path
from typing import Annotated, Literal

from mcp.server import MCPServer
from mcp.server.mcpserver import AcceptedElicitation, Context, Elicit, ElicitationResult, Resolve
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import ToolAnnotations
from pydantic import BaseModel, Field, create_model

# Synthetic data of a fictional fintech, with two traps: a customer with two credits and one up to date.
SEED = """
CREATE TABLE credits (
    customer TEXT NOT NULL,
    code TEXT NOT NULL,
    product TEXT NOT NULL,
    balance INTEGER NOT NULL CHECK (balance >= 0),
    installment INTEGER NOT NULL CHECK (installment >= 0),
    overdue_installments INTEGER NOT NULL CHECK (overdue_installments >= 0),
    days_past_due INTEGER NOT NULL CHECK (days_past_due >= 0),
    PRIMARY KEY (customer, code)
);
INSERT INTO credits VALUES
 ('C-1042', 'CLI', 'Crédito Libre Inversión', 8450000, 412000, 2, 45),
 ('C-1042', 'CEX', 'Crédito Express', 600000, 150000, 0, 0),
 ('C-2210', 'CEX', 'Crédito Express', 1200000, 215000, 0, 0),
 ('C-3307', 'CLI', 'Crédito Libre Inversión', 15300000, 690000, 3, 75);
"""
DEFAULT_DB = Path(tempfile.gettempdir()) / "mcp-credits-example.db"
DB = Path(os.getenv("CREDITS_DB", DEFAULT_DB))

# In stdio, stdout is the protocol channel: the server never prints. Logs go to stderr.
mcp = MCPServer("credits", instructions="Synthetic credit portfolio by customer and product, in COP. Read only.", log_level="WARNING")
READ_ONLY = ToolAnnotations(read_only_hint=True, open_world_hint=False)

Customer = Annotated[str, Field(description="Customer code, for example 'C-1042'.")]
Product = Annotated[str, Field(description="Product code (CLI, CEX) or name; empty for every credit of the customer.")]


def unaccent(text: str) -> str:
    """'Crédito' and 'credito' must find the same rows."""
    return "".join(c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn").lower()


def connect() -> sqlite3.Connection:
    if DB == DEFAULT_DB and not DB.exists():
        with sqlite3.connect(DB) as setup:
            setup.executescript(SEED)
    # mode=ro: this connection cannot write, whatever a tool or a model asks.
    connection = sqlite3.connect(f"{DB.resolve().as_uri()}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    connection.create_function("unaccent", 1, unaccent, deterministic=True)
    return connection


def find_credits(customer: str, product: str) -> list[dict]:
    if not re.fullmatch(r"C-\d{4}", customer.strip().upper()):
        # ToolError: the client receives this message; any other exception arrives as a generic error.
        raise ToolError("Write the customer code as C-1234.")
    if len(product) > 80 or any(character in product for character in "%_"):
        raise ToolError("Write the product in 80 characters at most, without the wildcards % or _.")
    # Values travel as parameters (?), never pasted into the SQL.
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
    """One credit. Returning this type makes the SDK publish the tool's outputSchema."""

    customer: str
    code: str
    product: str
    balance: int = Field(description="Credit balance, in Colombian pesos.")
    overdue: int = Field(description="Overdue amount: installment times overdue installments, in pesos.")
    days_past_due: int = Field(description="Days past due.")


class ProductChoice(BaseModel):
    code: str = Field(description="Code of the credit the person wants.")


async def choose_product(customer: str, ctx: Context, product: str = "") -> ProductChoice | Elicit[ProductChoice]:
    """Resolver: runs before the tool and asks the person (elicitation) when several credits match."""
    codes = sorted({row["code"]: row["product"] for row in find_credits(customer, product)}.items())
    capabilities = ctx.client_capabilities
    if len(codes) <= 1 or not (capabilities and capabilities.elicitation):
        return ProductChoice(code="")  # nothing to choose, or a client that cannot ask: every row
    options = ", ".join(f"{code} ({name})" for code, name in codes)
    # The form only accepts the matching codes: an enum built from the query.
    choice = create_model("ProductChoice", code=(Literal[tuple(code for code, _ in codes)], Field(description="Code.")))
    return Elicit(f"Customer {customer} has several credits: {options}. Which one?", choice)


@mcp.tool(annotations=READ_ONLY)
async def check_credit(
    customer: Customer,
    choice: Annotated[ElicitationResult[ProductChoice], Resolve(choose_product)],
    product: Product = "",
) -> list[CreditRow]:
    """Check the credits of a customer, one row per credit, in Colombian pesos.

    overdue = installment x overdue installments. If the customer has several credits, asks the person which one.
    """
    # The tool runs again from the start after the person answers: nothing irreversible before this point.
    rows = find_credits(customer, product)
    if isinstance(choice, AcceptedElicitation) and choice.data.code:
        rows = [row for row in rows if row["code"] == choice.data.code]
    return [CreditRow(**row) for row in rows]


@mcp.tool(annotations=READ_ONLY)
def list_products() -> list[str]:
    """List the credit products that have customers."""
    with connect() as connection:
        return [row["product"] for row in connection.execute("SELECT DISTINCT product FROM credits ORDER BY product")]


@mcp.resource("schema://credits", mime_type="text/plain")
def credits_schema() -> str:
    """Definition of the credits table: columns and constraints."""
    with connect() as connection:
        return connection.execute("SELECT sql FROM sqlite_master WHERE name = 'credits'").fetchone()["sql"]


if __name__ == "__main__":
    if "--http" in sys.argv:
        mcp.run("streamable-http", port=8001)
    else:
        mcp.run()
