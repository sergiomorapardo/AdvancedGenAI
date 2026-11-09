# Readings by week

Three books go with the course: implementation, agent design and application engineering. The readings add no class hours or deliverables. They are a selection by topic, chosen by the instructor, not a programme proposed by the authors.

## How to use this guide

1. Find the topic in the map and open its week.
2. Read the listed parts of the **main reading**, then follow the code files in the suggested order.
3. Use the **optional** reading to go deeper or clear up doubts. You do not need to read whole chapters before class.

Estimated times cover the main reading and the code, not every extension or running the examples.

## Books and repositories

| Code | Book and authors | Book repository | Use in the course |
|---|---|---|---|
| **LL** | [Learning LangChain](https://www.oreilly.com/library/view/learning-langchain/9781098167271/), Mayo Oshin and Nuno Campos | [langchain-ai/learning-langchain](https://github.com/langchain-ai/learning-langchain) | Python examples per chapter: calls, RAG, state, agents, deployment and evaluation. |
| **BA** | [Building Applications with AI Agents](https://www.oreilly.com/library/view/building-applications-with/9781098176495/), Michael Albada | [michaelalbada/BuildingApplicationsWithAIAgents](https://github.com/michaelalbada/BuildingApplicationsWithAIAgents) | Agent design and coordination, tools, memory, measurement and operation. |
| **AE** | [AI Engineering](https://github.com/chiphuyen/aie-book/blob/main/ToC.md), Chip Huyen | [chiphuyen/aie-book](https://github.com/chiphuyen/aie-book) | Design and evaluation criteria. Its repository holds resources, summaries and prompts, not runnable labs. |

Jinja, the workflow patterns and MCP are completed with official documentation and the guide in [patterns.md](patterns.md). Chapter numbers were checked against the books' public tables of contents; no pages are assigned and full-text access is not assumed. LL is archived. BA organises its code by component and scenario, not by chapter folder. File links are pinned to reviewed commits (listed at the end) so the mapping stays valid; open the repository roots for later versions.

## Map by topic

| Topic | Reference chapters | Weeks |
|---|---|---|
| Models, messages and prompts | LL 1; AE 2 and 5 | [1](#week-1), [2](#week-2) |
| Tools and MCP | BA 4; LL 6 | [3](#week-3), [7](#week-7) |
| RAG, history and memory | LL 2–5; BA 6; AE 6 | [4](#week-4), [5](#week-5) |
| Evaluation and answer revision | LL 10; BA 7 and 9; AE 3–4 | [6](#week-6), [11](#week-11) |
| State, routing and coordination | LL 4 and 7; BA 5 and 8 | [8](#week-8), [10](#week-10) |
| Human approval | LL 4 and 8; BA 3 and 13 | [9](#week-9) |
| Deployment and monitoring | LL 9; BA 10–11; AE 9–10 | [12](#week-12) |

## Before running external code

- Follow [SETUP.md](../SETUP.md): Python 3.12, uv and the course dependencies. Do not install the books' `requirements.txt`, Conda environments or install cells into that environment.
- Switch generation calls to Claude Haiku and check tools and structured output. The original examples may need other providers.
- Read files before importing or running them: some make paid calls, download models or start integrations when the module loads. This guide checks paths and content; it does not certify that the examples run unchanged in the course environment.
- Keep licences and attribution. The course labs are separate from the books' reference code.

## Weekly path

| Week | Topic | Books and chapters | Time |
|---|---|---|---|
| [1](#week-1) | Messages, templates, structured output and streaming | LL 1; AE 1–2 | 30 min |
| [2](#week-2) | Dynamic prompts with Jinja, schemas and traces | LL 1; AE 5 | 25 min |
| [3](#week-3) | Tools, a first agent and an external API | BA 4; LL 6 | 30 min |
| [4](#week-4) | Embeddings, vector stores and answers with citations | LL 2–3; AE 6 | 35 min |
| [5](#week-5) | Follow-up questions, multi-query and memory | LL 3–5; BA 6 | 35 min |
| [6](#week-6) | Datasets, code evaluators and a calibrated LLM-as-judge | AE 3–4; LL 10; BA 9 | 35 min |
| [7](#week-7) | Building MCP servers and an agent that uses them | BA 4; LL 6 | 15 min |
| [8](#week-8) | State, prompt chaining, routing and parallelization | LL 4; BA 5 and 8 | 30 min |
| [9](#week-9) | Human-in-the-loop: persistence, approval and resumption | LL 4 and 8; BA 3 and 13 | 30 min |
| [10](#week-10) | Orchestrator-workers and subgraphs | BA 5 and 8; LL 7 | 30 min |
| [11](#week-11) | Evaluator-optimizer and agent evaluation | BA 7 and 9; LL 10; AE 3–4 | 35 min |
| [12](#week-12) | Deployment, monitoring and operation | LL 9; AE 9–10; BA 10–11 | 30 min |

<a id="week-1"></a>

## Week 1 · Messages, templates, structured output and streaming

**Notebooks:** [L01](../notebooks/L01-IntroToLLMs.ipynb), [L02](../notebooks/L02-StructuredOutput.ipynb). **Time:** 30 min.

**Main reading:** LL ch. 1: messages, templates and structured extraction. **Optional:** AE ch. 1–2: application context and probabilistic behaviour.

**Code, in suggested order:**

- [LL · ch1/py/b-chat.py](https://github.com/langchain-ai/learning-langchain/blob/89301c62ac34893b6fbb693b817f0425d496572b/ch1/py/b-chat.py): the first conversation.
- [LL · ch1/py/c-system.py](https://github.com/langchain-ai/learning-langchain/blob/89301c62ac34893b6fbb693b817f0425d496572b/ch1/py/c-system.py): system instructions apart from the user message.
- [LL · ch1/py/f-chat-prompt.py](https://github.com/langchain-ai/learning-langchain/blob/89301c62ac34893b6fbb693b817f0425d496572b/ch1/py/f-chat-prompt.py): a parameterised template.
- [LL · ch1/py/g-chat-prompt-model.py](https://github.com/langchain-ai/learning-langchain/blob/89301c62ac34893b6fbb693b817f0425d496572b/ch1/py/g-chat-prompt-model.py): template and model together.
- [LL · ch1/py/h-structured.py](https://github.com/langchain-ai/learning-langchain/blob/89301c62ac34893b6fbb693b817f0425d496572b/ch1/py/h-structured.py): output with a schema.

**Adaptation:** use `ChatAnthropic`, Claude Haiku and current Pydantic. Agents start in week 3.

<a id="week-2"></a>

## Week 2 · Dynamic prompts with Jinja, schemas and traces

**Notebook:** [L03](../notebooks/L03-DynamicPrompting.ipynb). **Time:** 25 min.

**Main reading:** LL ch. 1: templates and structured output. AE ch. 5: instructions and prompt organisation. **Optional:** AE ch. 2, the structured outputs section.

**Code, in suggested order:**

- [LL · ch1/py/f-chat-prompt.py](https://github.com/langchain-ai/learning-langchain/blob/89301c62ac34893b6fbb693b817f0425d496572b/ch1/py/f-chat-prompt.py): compare template variables with Jinja rendering.
- [LL · ch1/py/h-structured.py](https://github.com/langchain-ai/learning-langchain/blob/89301c62ac34893b6fbb693b817f0425d496572b/ch1/py/h-structured.py): validate the structured answer.
- [AE · prompt-examples.md](https://github.com/chiphuyen/aie-book/blob/f375e0065ef19e4f411b809a2f9a2d65582db287/prompt-examples.md): prompts to compare instructions; not a runnable lab.

**Adaptation:** the books do not cover Jinja; use L03 and its documentation. Use `StrictUndefined`, declare optional fields and pass user input as data.

**Documentation:** [Jinja templates](https://jinja.palletsprojects.com/en/stable/templates/) · [Tracing in LangSmith](https://docs.langchain.com/langsmith/observability-quickstart).

<a id="week-3"></a>

## Week 3 · Tools, a first agent and an external API

**Notebooks:** [L04](../notebooks/L04-Tools.ipynb), [L05](../notebooks/L05-ToolsAPI.ipynb). **Time:** 30 min.

**Main reading:** BA ch. 4: tool contracts and use. LL ch. 6: the agent loop. **Optional:** AE ch. 6, the tools and planning section.

**Code, in suggested order:**

- [BA · src/frameworks/langchain/calculator_tool_use.py](https://github.com/michaelalbada/BuildingApplicationsWithAIAgents/blob/eeb325ab6e3af8eeba2e5e0d46f0185fc5933197/src/frameworks/langchain/calculator_tool_use.py): follow `bind_tools`, arguments, execution and returned results.
- [LL · ch6/py/a-basic-agent.py](https://github.com/langchain-ai/learning-langchain/blob/89301c62ac34893b6fbb693b817f0425d496572b/ch6/py/a-basic-agent.py): the model–tool loop.
- [LL · ch6/py/b-force-first-tool.py](https://github.com/langchain-ai/learning-langchain/blob/89301c62ac34893b6fbb693b817f0425d496572b/ch6/py/b-force-first-tool.py): when to force a first lookup.
- [LL · ch6/py/c-many-tools.py](https://github.com/langchain-ai/learning-langchain/blob/89301c62ac34893b6fbb693b817f0425d496572b/ch6/py/c-many-tools.py): choosing between several tools.

**Adaptation:** use the current `create_agent` and `@tool` with Haiku; explicit graphs come in week 8. The LL calculator uses `ast.literal_eval`, which does not evaluate general arithmetic. The BA example calls the model when the module runs; read it before running it.

**Documentation:** [Agents in LangChain](https://docs.langchain.com/oss/python/langchain/agents).

<a id="week-4"></a>

## Week 4 · Embeddings, vector stores and answers with citations

**Notebooks:** [L06](../notebooks/L06-Embeddings.ipynb), [L07](../notebooks/L07-VectorStores.ipynb), [L08](../notebooks/L08-RAG.ipynb). **Time:** 35 min.

**Main reading:** LL ch. 2–3: ingestion and RAG. AE ch. 6: information retrieval. **Optional:** BA ch. 6: knowledge and memory.

**Code, in suggested order:**

- [LL · ch2/py/c-pdf-loader.py](https://github.com/langchain-ai/learning-langchain/blob/89301c62ac34893b6fbb693b817f0425d496572b/ch2/py/c-pdf-loader.py): load PDF pages.
- [LL · ch2/py/d-rec-text-splitter.py](https://github.com/langchain-ai/learning-langchain/blob/89301c62ac34893b6fbb693b817f0425d496572b/ch2/py/d-rec-text-splitter.py): chunk size and overlap.
- [LL · ch2/py/g-embeddings.py](https://github.com/langchain-ai/learning-langchain/blob/89301c62ac34893b6fbb693b817f0425d496572b/ch2/py/g-embeddings.py): creating embeddings.
- [LL · ch3/py/a-basic-rag.py](https://github.com/langchain-ai/learning-langchain/blob/89301c62ac34893b6fbb693b817f0425d496572b/ch3/py/a-basic-rag.py): retrieval and answer together.
- [AE · resources.md](https://github.com/chiphuyen/aie-book/blob/f375e0065ef19e4f411b809a2f9a2d65582db287/resources.md#chapter-6-rag-and-agents): further links on retrieval and agents.

**Adaptation:** the course uses open local embeddings (`paraphrase-multilingual-MiniLM-L12-v2` with FastEmbed); LL uses OpenAI. Keep file and page citations.

<a id="week-5"></a>

## Week 5 · Follow-up questions, multi-query and memory

**Notebooks:** [L09](../notebooks/L09-ConversationalRAG.ipynb), [L10](../notebooks/L10-Memory.ipynb). **Time:** 35 min.

**Main reading:** LL ch. 3–5: rewriting, history and conversation. BA ch. 6: memory. **Optional:** AE ch. 6: retrieval and memory.

**Code, in suggested order:**

- [LL · ch3/py/b-rewrite.py](https://github.com/langchain-ai/learning-langchain/blob/89301c62ac34893b6fbb693b817f0425d496572b/ch3/py/b-rewrite.py): rewrite before retrieving.
- [LL · ch3/py/c-multi-query.py](https://github.com/langchain-ai/learning-langchain/blob/89301c62ac34893b6fbb693b817f0425d496572b/ch3/py/c-multi-query.py): several retrieval queries.
- [LL · ch4/py/c-persistent-memory.py](https://github.com/langchain-ai/learning-langchain/blob/89301c62ac34893b6fbb693b817f0425d496572b/ch4/py/c-persistent-memory.py): a persisted conversation.
- [LL · ch5/py/a-chatbot.py](https://github.com/langchain-ai/learning-langchain/blob/89301c62ac34893b6fbb693b817f0425d496572b/ch5/py/a-chatbot.py): history in the answer.
- [BA · src/frameworks/langgraph_agents/short_term_memory.py](https://github.com/michaelalbada/BuildingApplicationsWithAIAgents/blob/eeb325ab6e3af8eeba2e5e0d46f0185fc5933197/src/frameworks/langgraph_agents/short_term_memory.py): runs with and without a checkpointer.

**Adaptation:** update imports and persistence. The BA example keeps memory in the process; it is not the PostgreSQL persistence of week 12. Test that two conversations stay isolated.

<a id="week-6"></a>

## Week 6 · Datasets, code evaluators and a calibrated LLM-as-judge

**Notebook:** [L11](../notebooks/L11-RAGEvaluation.ipynb). **Time:** 35 min.

**Main reading:** AE ch. 3–4: evaluation methods and design. LL ch. 10: experiments. **Optional:** BA ch. 9: component evaluation.

**Code, in suggested order:**

- [LL · ch10/py/create_rag_dataset.py](https://github.com/langchain-ai/learning-langchain/blob/89301c62ac34893b6fbb693b817f0425d496572b/ch10/py/create_rag_dataset.py): reference answers.
- [LL · ch10/py/agent_evaluation_rag.py](https://github.com/langchain-ai/learning-langchain/blob/89301c62ac34893b6fbb693b817f0425d496572b/ch10/py/agent_evaluation_rag.py): a RAG experiment.
- [LL · ch10/py/retrieve_and_grade.py](https://github.com/langchain-ai/learning-langchain/blob/89301c62ac34893b6fbb693b817f0425d496572b/ch10/py/retrieve_and_grade.py): retrieval apart from generation.
- [BA · src/common/evaluation/ai_judge.py](https://github.com/michaelalbada/BuildingApplicationsWithAIAgents/blob/eeb325ab6e3af8eeba2e5e0d46f0185fc5933197/src/common/evaluation/ai_judge.py): rubrics with and without a reference answer.

**Adaptation:** update LangSmith and add OpenEvals. Calibrate the judge against human review. In `ai_judge.py` a non-numeric output ends as 0.0: count that format failure apart, so it is not confused with a bad answer.

<a id="week-7"></a>

## Week 7 · Building MCP servers and an agent that uses them

**Notebooks:** [L12](../notebooks/L12-MCPServer.ipynb), [L13](../notebooks/L13-MCPAgent.ipynb). **Time:** 15 min.

**Main reading:** BA ch. 4, the Model Context Protocol section. **Optional:** LL ch. 6, to review tool contracts.

**Code, in suggested order:**

- [BA · src/frameworks/langgraph_agents/langgraph_mcp_client.py](https://github.com/michaelalbada/BuildingApplicationsWithAIAgents/blob/eeb325ab6e3af8eeba2e5e0d46f0185fc5933197/src/frameworks/langgraph_agents/langgraph_mcp_client.py): tool discovery and transport settings.
- [BA · src/common/mcp/MCP_math_server.py](https://github.com/michaelalbada/BuildingApplicationsWithAIAgents/blob/eeb325ab6e3af8eeba2e5e0d46f0185fc5933197/src/common/mcp/MCP_math_server.py): read critically, see the note below.

**Adaptation:** the BA client points its `math` server at the weather server's path, and the math server wraps messages in its own `context/payload` envelope; do not treat that pair as a working MCP integration. The client uses `langchain-mcp-adapters`, replaced by `langchain.mcp`. The course builds the servers with the official SDK and checks negotiation, tool names and transports.

**Documentation:** [MCP in LangChain](https://docs.langchain.com/oss/python/langchain/mcp) · [Official MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk).

<a id="week-8"></a>

## Week 8 · State, prompt chaining, routing and parallelization

**Notebooks:** [L14](../notebooks/L14-LangGraphStudio.ipynb)–[L19](../notebooks/L19-Parallelization.ipynb). **Time:** 30 min.

**Main reading:** LL ch. 4: state and graph. BA ch. 5: orchestration. **Optional:** BA ch. 8: coordination between specialists.

**Code, in suggested order:**

- [LL · ch4/py/b-state-graph.py](https://github.com/langchain-ai/learning-langchain/blob/89301c62ac34893b6fbb693b817f0425d496572b/ch4/py/b-state-graph.py): nodes, state and transitions.
- [BA · src/frameworks/langgraph_agents/supply_chain/supply_chain_logistics_multi_agent.py](https://github.com/michaelalbada/BuildingApplicationsWithAIAgents/blob/eeb325ab6e3af8eeba2e5e0d46f0185fc5933197/src/frameworks/langgraph_agents/supply_chain/supply_chain_logistics_multi_agent.py): read `supervisor_node`, `route_to_specialist` and `construct_graph`.

**Adaptation:** the BA graph picks a single specialist and ends; it illustrates routing, not parallelization. For fixed concurrent branches use L19 and the official guide, with reducers for shared fields. See [patterns.md](patterns.md).

**Documentation:** [Routing](https://docs.langchain.com/oss/python/langgraph/workflows-agents#routing) · [Parallelization](https://docs.langchain.com/oss/python/langgraph/workflows-agents#parallelization).

<a id="week-9"></a>

## Week 9 · Human-in-the-loop: persistence, approval and resumption

**Notebook:** [L20](../notebooks/L20-HumanInTheLoop.ipynb). **Time:** 30 min.

**Main reading:** LL ch. 4 and 8: persistence and execution control. **Optional:** BA ch. 3 and 13: interaction, autonomy and human oversight.

**Code, in suggested order:**

- [LL · ch4/py/c-persistent-memory.py](https://github.com/langchain-ai/learning-langchain/blob/89301c62ac34893b6fbb693b817f0425d496572b/ch4/py/c-persistent-memory.py): conversation identity and persisted state.
- [LL · ch8/py/d-authorize.py](https://github.com/langchain-ai/learning-langchain/blob/89301c62ac34893b6fbb693b817f0425d496572b/ch8/py/d-authorize.py): the authorisation point.
- [LL · ch8/py/e-resume.py](https://github.com/langchain-ai/learning-langchain/blob/89301c62ac34893b6fbb693b817f0425d496572b/ch8/py/e-resume.py): resuming.
- [LL · ch8/py/f-edit-state.py](https://github.com/langchain-ai/learning-langchain/blob/89301c62ac34893b6fbb693b817f0425d496572b/ch8/py/f-edit-state.py): editing the state.

**Adaptation:** several LL ch. 8 examples are skeletons. Use the current `interrupt()` and `Command(resume=...)`. Test approve, reject and edit; cancelling a stream is not a persisted approval.

**Documentation:** [Interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts) · [Persistence](https://docs.langchain.com/oss/python/langgraph/persistence).

<a id="week-10"></a>

## Week 10 · Orchestrator-workers and subgraphs

**Notebook:** [L21](../notebooks/L21-Orchestrator.ipynb). **Time:** 30 min.

**Main reading:** BA ch. 5 and 8: coordination and division of responsibilities. LL ch. 7: subgraphs. **Optional:** AE ch. 6: planning.

**Code, in suggested order:**

- [LL · ch7/py/b-subgraph-direct.py](https://github.com/langchain-ai/learning-langchain/blob/89301c62ac34893b6fbb693b817f0425d496572b/ch7/py/b-subgraph-direct.py): composition with a shared state.
- [LL · ch7/py/c-subgraph-function.py](https://github.com/langchain-ai/learning-langchain/blob/89301c62ac34893b6fbb693b817f0425d496572b/ch7/py/c-subgraph-function.py): contracts between different states.
- [LL · ch7/py/d-supervisor.py](https://github.com/langchain-ai/learning-langchain/blob/89301c62ac34893b6fbb693b817f0425d496572b/ch7/py/d-supervisor.py): a supervisor compared with dynamic delegation.

**Adaptation:** a supervisor or a router does not, by itself, show orchestrator-workers. Add a structured plan, `Send`, result identity and a task cap, and contrast it with the fixed branches of week 8.

**Documentation:** [Orchestrator-worker](https://docs.langchain.com/oss/python/langgraph/workflows-agents#orchestrator-worker).

<a id="week-11"></a>

## Week 11 · Evaluator-optimizer and agent evaluation

**Notebook:** [L22](../notebooks/L22-EvaluatorOptimizer.ipynb). **Time:** 35 min.

**Main reading:** BA ch. 7: reflection. LL ch. 10: agent evaluation. **Optional:** BA ch. 9 and AE ch. 3–4: component versus system evaluation.

**Code, in suggested order:**

- [BA · src/frameworks/langgraph_agents/reflexion.py](https://github.com/michaelalbada/BuildingApplicationsWithAIAgents/blob/eeb325ab6e3af8eeba2e5e0d46f0185fc5933197/src/frameworks/langgraph_agents/reflexion.py): a reflection from a failed attempt.
- [LL · ch10/py/agent_evaluation_sql.py](https://github.com/langchain-ai/learning-langchain/blob/89301c62ac34893b6fbb693b817f0425d496572b/ch10/py/agent_evaluation_sql.py): checking agent behaviour.
- [LL · ch10/py/create_sql_dataset.py](https://github.com/langchain-ai/learning-langchain/blob/89301c62ac34893b6fbb693b817f0425d496572b/ch10/py/create_sql_dataset.py): references for the experiment.
- [BA · src/common/evaluation/memory_evaluation.py](https://github.com/michaelalbada/BuildingApplicationsWithAIAgents/blob/eeb325ab6e3af8eeba2e5e0d46f0185fc5933197/src/common/evaluation/memory_evaluation.py): deterministic metrics apart from model judgement.
- [AgentEvals](https://github.com/langchain-ai/agentevals/tree/946ad15b9f2ce9bc9843edd2bb773bd07d78ca7e): trajectory evaluators by match and by judge.

**Adaptation:** `reflexion.py` makes one reflection and stores it in a list; it is not a full evaluator-optimizer loop. Build the loop with L22, a structured rubric and a revision cap. Evaluation inside a turn and an experiment over a dataset do different jobs. A correct trajectory does not guarantee a correct answer: combine trajectory, deterministic checks and human review.

**Documentation:** [Evaluator-optimizer](https://docs.langchain.com/oss/python/langgraph/workflows-agents#evaluator-optimizer) · [Evaluation in LangSmith](https://docs.langchain.com/langsmith/evaluation) · [Trajectory evaluations](https://docs.langchain.com/langsmith/trajectory-evals) · [OpenEvals](https://github.com/langchain-ai/openevals).

<a id="week-12"></a>

## Week 12 · Deployment, monitoring and operation

**Material:** the [local support chat API](demo.md). **Time:** 30 min.

**Main reading:** LL ch. 9: application structure and deployment. AE ch. 10: architecture and feedback. **Optional:** BA ch. 10–11: monitoring and continuous improvement; AE ch. 9: latency.

**Code, in suggested order:**

- [LL · ch9/py/langgraph.json](https://github.com/langchain-ai/learning-langchain/blob/89301c62ac34893b6fbb693b817f0425d496572b/ch9/py/langgraph.json): the deployable entry point.
- [LL · ch9/py/src/retrieval_graph/graph.py](https://github.com/langchain-ai/learning-langchain/blob/89301c62ac34893b6fbb693b817f0425d496572b/ch9/py/src/retrieval_graph/graph.py): the application graph.
- [LL · ch9/py/src/retrieval_graph/configuration.py](https://github.com/langchain-ai/learning-langchain/blob/89301c62ac34893b6fbb693b817f0425d496572b/ch9/py/src/retrieval_graph/configuration.py): configuration per environment.
- [BA · src/common/evaluation/batch_evaluation.py](https://github.com/michaelalbada/BuildingApplicationsWithAIAgents/blob/eeb325ab6e3af8eeba2e5e0d46f0185fc5933197/src/common/evaluation/batch_evaluation.py): metrics per conversation and aggregation.
- [LL · ch8/py/b-streaming-output.py](https://github.com/langchain-ai/learning-langchain/blob/89301c62ac34893b6fbb693b817f0425d496572b/ch8/py/b-streaming-output.py): streaming and diagnosis.

**Adaptation:** update the CLI, configuration, credentials and persistence for the course environment. BA monitors with OpenTelemetry, Tempo and Loki; carry the ideas over to LangSmith without that infrastructure. Its batch evaluator skips examples that fail: count those failures too. Add production failures to the offline dataset and rerun it as a regression check.

**Documentation:** [Agent Server](https://docs.langchain.com/langsmith/agent-server) · [Evaluation in LangSmith](https://docs.langchain.com/langsmith/evaluation).

## Going further

Topics beyond the 12 weeks, as reading only:

- **Deep Agents:** an agent harness with planning, a file system, subagents and skills. [Overview](https://docs.langchain.com/oss/python/deepagents/overview) and the [text-to-SQL example](https://github.com/langchain-ai/deepagents/blob/0ce837bf69ff0efb10c2fa100039cc0c78a74a11/examples/text-to-sql-agent/agent.py). Planning and subagents multiply the calls per task: count them before running.
- **Agent-to-agent (A2A):** MCP connects an agent to tools; A2A connects agents to each other. The Agent Server publishes each graph at `/a2a/{assistant_id}` ([docs](https://docs.langchain.com/langsmith/server-a2a), [A2A and MCP](https://a2a-protocol.org/latest/topics/a2a-and-mcp/)). The endpoint is on by default: protect it or turn it off in deployments, and remember that every A2A message runs the graph.

## Reviewed code versions

These revisions pin the file links in this guide; they are not certified versions for running the labs.

- **LL:** [langchain-ai/learning-langchain · 89301c62](https://github.com/langchain-ai/learning-langchain/tree/89301c62ac34893b6fbb693b817f0425d496572b)
- **BA:** [michaelalbada/BuildingApplicationsWithAIAgents · eeb325ab](https://github.com/michaelalbada/BuildingApplicationsWithAIAgents/tree/eeb325ab6e3af8eeba2e5e0d46f0185fc5933197)
- **AE:** [chiphuyen/aie-book · f375e006](https://github.com/chiphuyen/aie-book/tree/f375e0065ef19e4f411b809a2f9a2d65582db287)
- **AgentEvals:** [langchain-ai/agentevals · 946ad15b](https://github.com/langchain-ai/agentevals/tree/946ad15b9f2ce9bc9843edd2bb773bd07d78ca7e)
- **Deep Agents:** [langchain-ai/deepagents · 0ce837bf](https://github.com/langchain-ai/deepagents/tree/0ce837bf69ff0efb10c2fa100039cc0c78a74a11)
