"""Local run log: every LangChain event of one run, saved in runs/<timestamp>/.

- events.jsonl: raw events, one per line, written as they happen.
- transcript.md: call by call, what entered the context and what the model answered.

Pass it on the top-level call: chain.invoke(inputs, config={"callbacks": [run_log]}).
Callbacks propagate to every model and tool call inside a chain or an agent.
It never sends anything outside the machine, so it does not use LangSmith traces.
"""

import json
from datetime import datetime
from pathlib import Path

from langchain_core.callbacks import BaseCallbackHandler


class RunLog(BaseCallbackHandler):
    def __init__(self, folder: str | Path = "runs"):
        self.path = Path(folder) / datetime.now().astimezone().strftime("%Y%m%d-%H%M%S-%f")
        self.path.mkdir(parents=True, exist_ok=True)
        self.model_calls = 0
        self.context_size = 0
        self.input_tokens = 0
        self.output_tokens = 0

    def _event(self, event: str, **data):
        record = {"time": datetime.now().astimezone().isoformat(), "event": event, **data}
        with (self.path / "events.jsonl").open("a", encoding="utf-8") as file:
            file.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")

    def _write(self, text: str):
        with (self.path / "transcript.md").open("a", encoding="utf-8") as file:
            file.write(text + "\n")

    def on_chat_model_start(self, serialized, messages, **kwargs):
        context = messages[0]
        # In an agent loop each call repeats the previous messages; show only the new ones.
        new = context[self.context_size:] if len(context) > self.context_size else context
        self.context_size = len(context)
        self.model_calls += 1
        self._event("model_start", messages=[message.model_dump() for message in context])
        self._write(f"\n## Model call {self.model_calls}: {len(context)} messages, {len(new)} new\n")
        for message in new:
            content = message.content if isinstance(message.content, str) else json.dumps(
                message.content, ensure_ascii=False, default=str
            )
            self._write(f"- **{message.type}**: {content[:1500]}")

    def on_llm_end(self, response, **kwargs):
        message = response.generations[0][0].message
        usage = message.usage_metadata or {}
        self.input_tokens += usage.get("input_tokens", 0)
        self.output_tokens += usage.get("output_tokens", 0)
        self._event("model_end", message=message.model_dump())
        tokens = f"{usage.get('input_tokens', '?')} in / {usage.get('output_tokens', '?')} out"
        self._write(f"\n**ai** ({tokens}): {message.text or '(no text)'}")
        for call in message.tool_calls:
            self._write(f"- tool call `{call['name']}` {json.dumps(call['args'], ensure_ascii=False)}")

    def on_tool_start(self, serialized, input_str, **kwargs):
        self._event("tool_start", name=serialized.get("name"), input=input_str)

    def on_tool_end(self, output, **kwargs):
        self._event("tool_end", output=output)

    def on_llm_error(self, error, **kwargs):
        self._event("model_error", error=repr(error))
        self._write(f"\n**model error**: {error!r}")

    def on_tool_error(self, error, **kwargs):
        self._event("tool_error", error=repr(error))
        self._write(f"\n**tool error**: {error!r}")

    def receipt(self) -> str:
        return (
            f"{self.model_calls} model calls, {self.input_tokens} input tokens, "
            f"{self.output_tokens} output tokens. Log: {self.path}"
        )
