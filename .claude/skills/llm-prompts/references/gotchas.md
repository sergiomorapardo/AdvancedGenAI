# Gotchas: symptom → cause → fix

Observed with `langchain` 1.4, `langchain-anthropic` 1.7 and `claude-haiku-5-5`.

| Symptom | Cause | Fix |
|---|---|---|
| 400 error mentioning `temperature` | Haiku 5.5 rejects it | Remove `temperature` |
| Empty or cut answer with `max_tokens=400` | Default reasoning spends the token budget | `thinking={"type": "disabled"}` |
| 400 error about prefill or the final assistant message | The conversation sent to the model ends in an AI message | Send a list that ends in a human or tool message; keep the reply apart (`conversation = messages + [response]`) |
| `ChatPromptTemplate` with `template_format="jinja2"` asks for a variable only used inside an `if` | It requires every variable it finds | Pass optional fields as `None` |
| A missing variable renders as an empty string | LangChain's Jinja uses the lenient `Undefined` | Render with `Environment(undefined=StrictUndefined)` |
| `{{ ticket.items }}` prints `<built-in method items…>` | In Jinja, `items` resolves to `dict.items` | Use another key, such as `charges` |
| `{ user_message }` stays literal | Jinja needs double braces | `{{ user_message }}` |
| `TemplateNotFound` from another folder | `FileSystemLoader("prompts")` is relative to the working directory | Resolve from `Path(__file__).resolve().parent / "prompts"` |
| Many LangSmith traces from one run | `ChatPromptTemplate.invoke` and `tool.invoke` each create a trace | Use `format_messages`; keep tracing off unless approved |
| The agent answers in English to a Spanish thread without context | The system prompt does not fix the language | Add "answer always in <language>" to the system prompt |
