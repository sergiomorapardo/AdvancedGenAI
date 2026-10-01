"""Start the real dev server and verify its graphs without invoking any model."""

import argparse
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import tempfile
import time
from urllib.error import URLError
from urllib.request import ProxyHandler, Request, build_opener


ROOT = Path(__file__).resolve().parents[1]


def check_startup(config_path: Path, timeout: float) -> None:
    config = json.loads(config_path.read_text())
    expected = set(config["graphs"])
    if not expected:
        raise RuntimeError("No graphs are registered in the configuration.")

    # Keep the real registrations, resolving their paths before using a temporary cwd.
    for name, spec in config["graphs"].items():
        path, variable = spec.rsplit(":", 1)
        if path.endswith(".py"):
            config["graphs"][name] = f"{(ROOT / path).resolve()}:{variable}"
    config["dependencies"] = [
        str((ROOT / dependency).resolve()) if dependency.startswith(".") else dependency
        for dependency in config.get("dependencies", [])
    ]

    # Do not read developer .env files or send traces using inherited credentials.
    env = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith(("LANGSMITH_", "LANGCHAIN_", "LANGGRAPH_"))
    }
    config["env"] = {
        "ANTHROPIC_API_KEY": "ci-placeholder-not-a-real-key",
        "OPENAI_API_KEY": "ci-placeholder-not-a-real-key",
        "LANGSMITH_TRACING": "false",
        "LANGCHAIN_TRACING_V2": "false",
        "LANGGRAPH_CLI_NO_ANALYTICS": "1",
        "PYTHON_DOTENV_DISABLED": "1",
    }
    env.update(config["env"])

    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
    base_url = f"http://127.0.0.1:{port}"
    client = build_opener(ProxyHandler({}))

    with tempfile.TemporaryDirectory(prefix="langgraph-startup-") as directory:
        temporary = Path(directory)
        temporary_config = temporary / "langgraph.json"
        temporary_config.write_text(json.dumps(config))
        log_path = temporary / "server.log"
        with log_path.open("w") as log:
            process = subprocess.Popen(
                [
                    sys.executable, "-m", "langgraph_cli", "dev",
                    "--config", str(temporary_config),
                    "--host", "127.0.0.1", "--port", str(port),
                    "--no-browser", "--no-reload",
                ],
                cwd=temporary,
                env=env,
                stdout=log,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
            try:
                deadline = time.monotonic() + timeout
                while time.monotonic() < deadline:
                    if process.poll() is not None:
                        raise RuntimeError(f"LangGraph exited with code {process.returncode}.")
                    try:
                        with client.open(f"{base_url}/ok", timeout=1) as response:
                            if response.status == 200:
                                break
                    except (URLError, TimeoutError):
                        pass
                    time.sleep(0.5)
                else:
                    raise RuntimeError(f"LangGraph was not ready within {timeout:g} seconds.")

                request = Request(
                    f"{base_url}/assistants/search",
                    data=json.dumps({"limit": 1000}).encode(),
                    headers={"Content-Type": "application/json"},
                )
                with client.open(request, timeout=10) as response:
                    registered = {assistant["graph_id"] for assistant in json.load(response)}
                missing = expected - registered
                if missing:
                    raise RuntimeError(f"Graphs missing from the server: {sorted(missing)}")
                print(f"LangGraph startup OK: {', '.join(sorted(expected))}")
            except Exception:
                print(log_path.read_text(), file=sys.stderr)
                raise
            finally:
                if process.poll() is None:
                    os.killpg(process.pid, signal.SIGTERM)
                    try:
                        process.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        os.killpg(process.pid, signal.SIGKILL)
                        process.wait()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "langgraph.json")
    parser.add_argument("--timeout", type=float, default=90)
    args = parser.parse_args()
    check_startup(args.config, args.timeout)
