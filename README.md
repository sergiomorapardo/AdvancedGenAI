# Advanced Topics in Analytics II - Generative AI

> **Status: Course proposal · In development.** Proposed for Pontificia Universidad Javeriana. Approval, delivery dates, and teaching hours are pending confirmation.

*Instructor: Sergio A. Mora Pardo*

- email: <sergioa.mora@javeriana.edu.co>
- github: [sergiomorapardo](https://github.com/sergiomorapardo)


This proposed course builds on *Advanced Topics in Analytics*, moving from classic NLP and Graph Learning into the world of **Generative AI**. Students will learn how to build real applications powered by **Large Language Models (LLMs)**, covering prompt engineering, working with commercial LLM APIs (OpenAI, Anthropic/Claude), embeddings and vector databases, **Retrieval-Augmented Generation (RAG)** from basics to advanced techniques (re-ranking, hybrid search, query transformation), **AI agents** (ReAct, tool use, function calling), orchestration frameworks such as **LangChain** and **LangGraph**, the **Model Context Protocol (MCP)**, multi-agent systems, evaluation of LLM applications (LLM-as-judge, RAGAS) and **LLMOps** for deployment. The course is project-oriented, with emphasis placed on writing software implementations that solve real-world problems end to end.


## Motivation

The original course (*Advanced Topics in Analytics*) taught students to **understand** language models — the NLP, embeddings and transformer foundations of how they work. This course takes the next step: it teaches students to **build** real systems that *use* those models, moving them from consumers of AI to engineers of AI.

Why this matters:

* **Employability** — RAG, LLM evaluation and LLMOps are precisely the skills companies are hiring GenAI and AI-application engineers for today.
* **Higher-order skills** — students progress from merely *applying* AI to *designing, evaluating and creating* AI systems.
* **Transferable, vendor-independent engineering** — the fundamentals of RAG, evaluation and agent architecture outlast any single model, provider or framework.

And one honest note: students will also learn **when *not* to reach for a heavy framework**. Recognizing that a direct API call is enough for the task at hand is itself a mark of good engineering judgment.


## Learning Outcomes

By the end of the course, students will be able to **design, connect (to real data), evaluate and deploy** LLM-powered applications.

| Module | Learning outcome |
| :----| :------------- |
| Intro to LLMs & Prompt Engineering | Explain how LLMs work and craft effective, structured prompts. |
| Working with LLM APIs | Integrate OpenAI and Anthropic APIs; manage tokens, parameters and streaming. |
| Embeddings & Vector Databases | Represent text as embeddings and store/query them in FAISS and Chroma. |
| RAG fundamentals | Build a retrieval-augmented pipeline that grounds an LLM on external data. |
| Advanced RAG | Improve retrieval with re-ranking, hybrid search and query transformation. |
| AI Agents fundamentals | Design agents that reason and use tools (ReAct, function calling). |
| LangChain | Compose LLM applications with chains, memory and tools. |
| LangGraph | Build stateful, multi-step agent workflows with explicit control flow. |
| MCP | Connect agents to external tools and data through the Model Context Protocol. |
| Multi-agent systems | Orchestrate multiple collaborating agents for complex tasks. |
| Evaluation of LLM apps | Measure quality with RAGAS and LLM-as-judge instead of relying on vibe-checks. |
| LLMOps & Deployment | Deploy, monitor and manage the cost/latency of LLM apps in production. |


## Requirements
* [Python](http://www.python.org) version >= 3.10;
* [LangChain](https://python.langchain.com), framework for building LLM applications;
* [LangGraph](https://langchain-ai.github.io/langgraph/), library for stateful, multi-step agents;
* [langchain-openai](https://python.langchain.com/docs/integrations/platforms/openai/), OpenAI integration for LangChain;
* [langchain-anthropic](https://python.langchain.com/docs/integrations/platforms/anthropic/), Anthropic/Claude integration for LangChain;
* [openai](https://github.com/openai/openai-python), the official OpenAI Python SDK;
* [anthropic](https://github.com/anthropics/anthropic-sdk-python), the official Anthropic (Claude) Python SDK;
* [chromadb](https://www.trychroma.com/), open-source embedding/vector database;
* [faiss-cpu](https://github.com/facebookresearch/faiss), library for efficient similarity search;
* [sentence-transformers](https://www.sbert.net/), embeddings for sentences and paragraphs;
* [tiktoken](https://github.com/openai/tiktoken), fast BPE tokenizer for OpenAI models;
* [ragas](https://docs.ragas.io/), evaluation framework for RAG pipelines;
* [python-dotenv](https://github.com/theskumar/python-dotenv), management of environment variables and API keys;
* [Jupyter](https://jupyter.org/), with the additional libraries required for the notebook interface.

A good, easy to install option that supports Mac, Windows, and Linux, and that has all of these packages (and much more) is the [Anaconda](https://www.anaconda.com/). All requirements are also listed in [`requirements.txt`](./requirements.txt).

You will need API keys to work with commercial LLMs. Copy [`.env.example`](./.env.example) to `.env` and fill in your `OPENAI_API_KEY` and `ANTHROPIC_API_KEY`.

GIT!! Unfortunatelly out of the scope of this class, but please take a look at these [tutorials](https://help.github.com/articles/good-resources-for-learning-git-and-github/)

## Proposed Evaluation

* 50% Project
* 40% Exercises
* 10% Class participation

## Proposed Schedule

*Draft sequence of 12 weekly sessions. Calendar dates will be added once the course is approved and scheduled.*

### 1. Intro to LLMs & Prompt Engineering
| Week | Session | Notebooks/Presentations | Exercises |
| :----| :----| :------------- | :------------- |
| Week 1 | Introduction to Large Language Models & Prompt Engineering | [L1 - Intro to LLMs](./notebooks/L1-IntroToLLMs.ipynb) | |

### 2. Working with LLM APIs (OpenAI, Anthropic/Claude)
| Week | Session | Notebooks/Presentations | Exercises |
| :----| :----| :------------- | :------------- |
| Week 2 | Calling LLM APIs: OpenAI and Anthropic/Claude | | |

### 3. Embeddings & Vector Databases (FAISS, Chroma)
| Week | Session | Notebooks/Presentations | Exercises |
| :----| :----| :------------- | :------------- |
| Week 3 | Embeddings and Vector Databases with FAISS and Chroma | | |

### 4. RAG basics
| Week | Session | Notebooks/Presentations | Exercises |
| :----| :----| :------------- | :------------- |
| Week 4 | Retrieval-Augmented Generation fundamentals | | |

### 5. Advanced RAG (re-ranking, hybrid search, query transformation)
| Week | Session | Notebooks/Presentations | Exercises |
| :----| :----| :------------- | :------------- |
| Week 5 | Advanced RAG: re-ranking, hybrid search and query transformation | | |

### 6. AI Agents fundamentals (ReAct, tool use, function calling)
| Week | Session | Notebooks/Presentations | Exercises |
| :----| :----| :------------- | :------------- |
| Week 6 | AI Agents: ReAct, tool use and function calling | | |

### 7. LangChain
| Week | Session | Notebooks/Presentations | Exercises |
| :----| :----| :------------- | :------------- |
| Week 7 | Building LLM applications with LangChain | | |

### 8. LangGraph (stateful/multi-step agents)
| Week | Session | Notebooks/Presentations | Exercises |
| :----| :----| :------------- | :------------- |
| Week 8 | Stateful, multi-step agents with LangGraph | | |

### 9. MCP - Model Context Protocol
| Week | Session | Notebooks/Presentations | Exercises |
| :----| :----| :------------- | :------------- |
| Week 9 | Connecting tools and data with the Model Context Protocol | | |

### 10. Multi-agent systems
| Week | Session | Notebooks/Presentations | Exercises |
| :----| :----| :------------- | :------------- |
| Week 10 | Designing and orchestrating multi-agent systems | | |

### 11. Evaluation of LLM apps (LLM-as-judge, RAGAS)
| Week | Session | Notebooks/Presentations | Exercises |
| :----| :----| :------------- | :------------- |
| Week 11 | Evaluating LLM applications: LLM-as-judge and RAGAS | | |

### 12. LLMOps & Deployment
| Week | Session | Notebooks/Presentations | Exercises |
| :----| :----| :------------- | :------------- |
| Week 12 | LLMOps: deploying and monitoring LLM applications | | |

## Interest Links 🔗
Module | Topic | Material |
| :----| :----| :----|
| LangChain | Official Documentation | [LangChain Docs](https://python.langchain.com) |
| LangGraph | Official Documentation | [LangGraph Docs](https://langchain-ai.github.io/langgraph/) |
| MCP | Model Context Protocol | [modelcontextprotocol.io](https://modelcontextprotocol.io) |
| GenAI | Short Courses | [DeepLearning.AI Short Courses](https://www.deeplearning.ai/short-courses/) |

---

> 📚 This course is a proposed continuation ("part 2") of [Advanced Topics in Analytics](https://github.com/sergiomorapardo/AdvancedTopicsAnalytics), which covered MLOps, Deep Learning, NLP and Graph Learning.
