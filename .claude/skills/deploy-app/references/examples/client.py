"""Smoke test of a running API: two turns on one thread, a stream, and a second thread that must not remember.

Run from the repo root while api.py is serving:
    uv run python .claude/skills/deploy-app/references/examples/client.py http://127.0.0.1:8001
Cost: about 5 model calls (each turn that uses the tool makes 2). It spends paid tokens through the API.
"""

import json
import sys
import uuid

import httpx


def chat(base: str, chat_id: str, message: str) -> list[dict]:
    response = httpx.post(f"{base}/chat/{chat_id}", json={"message": message}, timeout=120)
    response.raise_for_status()
    return response.json()


def stream(base: str, chat_id: str, message: str) -> str:
    parts = []
    with httpx.stream("POST", f"{base}/chat/{chat_id}/stream", json={"message": message}, timeout=120) as response:
        response.raise_for_status()
        for line in response.iter_lines():
            if line.startswith("data: "):
                content = json.loads(line.removeprefix("data: "))["content"]
                parts.append(content if isinstance(content, str) else "".join(b.get("text", "") for b in content))
    return "".join(parts)


def main(base: str):
    assert httpx.get(f"{base}/health", timeout=10).json() == {"status": "ok"}
    thread = f"smoke-{uuid.uuid4().hex[:8]}"  # a new thread each run, so old checkpoints do not interfere
    first = chat(base, thread, "Soy el cliente C-3307, ¿cuánto tengo vencido?")
    print("Turn 1:", first[-1]["content"])
    second = chat(base, thread, "¿Y en cuántos mensajes me lo dijiste?")
    print("Turn 2:", second[-1]["content"], f"({len(second)} messages in the thread)")
    print("Stream:", stream(base, thread, "Repite la cifra, por favor."))
    other = chat(base, f"{thread}-other", "¿Cuánto te dije que debo?")
    print("Other thread:", other[-1]["content"], f"({len(other)} messages)")
    print("Memory per thread:", len(second) > len(first) and len(other) < len(second))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8001")
