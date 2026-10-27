"""Piece: a tool over a public HTTP API, with a timeout and every failure returned as data.

Run from the repo root:
    uv run python .claude/skills/agentic-workflow/references/examples/api_tool.py
Cost: 2 or more model calls to the project model and free calls to datos.gov.co (no key).
LangSmith: 1 trace only if LANGSMITH_TRACING=true.
"""

import json
import re
from datetime import date

import httpx
from langchain.agents import create_agent
from langchain_core.tools import tool
from project import build_model
from run_log import RunLog

# Colombian market exchange rate (TRM), published as open data. No key needed.
TRM_URL = "https://www.datos.gov.co/resource/32sa-8pi3.json"

SYSTEM_PROMPT = (
    f"Today is {date.today().isoformat()}. You are the support assistant of ACME, a fintech. "
    "ACME credits are paid in Colombian pesos. Check the exchange rate with the tool, use only the "
    "figures it returns and show the arithmetic. If the tool does not find the data, say so."
)


@tool(parse_docstring=True)
def get_exchange_rate(day: str) -> dict:
    """Get the TRM (Colombian pesos per US dollar) valid on a date, from datos.gov.co. Read only.

    Args:
        day: date in YYYY-MM-DD format.
    """
    where = f"vigenciadesde <= '{day}T00:00:00' AND vigenciahasta >= '{day}T00:00:00'"
    try:
        # Always set a timeout: without it a slow API blocks the agent.
        response = httpx.get(TRM_URL, params={"$where": where, "$limit": 1}, timeout=15)
    except httpx.HTTPError as error:
        return {"status": "unavailable", "message": f"datos.gov.co did not answer: {error}"}
    if response.is_error:
        # The API explains the problem (for example, a malformed date); pass it on, trimmed.
        return {"status": "unavailable", "message": response.text[:300]}
    rows = response.json()
    if not rows:
        return {"status": "not_found", "message": f"No TRM published for {day}."}
    # Return only the fields the model needs, and name the source.
    return {"status": "ok", "date": day, "cop_per_usd": float(rows[0]["valor"]), "source": "datos.gov.co · TRM"}


def check_answer(messages: list, usd: float) -> bool:
    """Deterministic check: the answer contains the pesos computed from the rate the API returned."""
    results = [json.loads(m.content) for m in messages if m.type == "tool"]
    found = [r for r in results if r["status"] == "ok"]
    if not found:
        return False
    expected = str(int(usd * found[-1]["cop_per_usd"]))
    return expected in re.sub(r"\D", "", messages[-1].text)


def main():
    agent = create_agent(build_model(), tools=[get_exchange_rate], system_prompt=SYSTEM_PROMPT)
    run_log = RunLog()
    result = agent.invoke(
        {"messages": [{"role": "user", "content": "I received 300 dollars today. How many pesos is that with today's TRM?"}]},
        config={"callbacks": [run_log]},
    )
    print(result["messages"][-1].text)
    print("Answer matches the API:", check_answer(result["messages"], usd=300))
    print(run_log.receipt())


if __name__ == "__main__":
    main()
