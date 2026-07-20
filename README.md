# Advanced Topics in Analytics II - Generative AI

*Instructor: Sergio A. Mora Pardo*

- email: <sergioa.mora@javeriana.edu.co>
- github: [sergiomorapardo](https://github.com/sergiomorapardo)


This course is the second part of *Advanced Topics in Analytics*, moving from classic NLP and Graph Learning into the world of **Generative AI**. Students will learn how to build real applications powered by **Large Language Models (LLMs)**, covering prompt engineering, working with commercial LLM APIs (OpenAI, Anthropic/Claude), embeddings and vector databases, **Retrieval-Augmented Generation (RAG)** from basics to advanced techniques (re-ranking, hybrid search, query transformation), **AI agents** (ReAct, tool use, function calling), orchestration frameworks such as **LangChain** and **LangGraph**, the **Model Context Protocol (MCP)**, multi-agent systems, evaluation of LLM applications (LLM-as-judge, RAGAS) and **LLMOps** for deployment. The course is project-oriented, with emphasis placed on writing software implementations that solve real-world problems end to end.


## Requiriments
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

## Evaluation

* 50% Project
* 40% Exercises
* 10% Class participation

## Schedule

*Sessions are weekly on Saturdays, Aug 1 - Oct 17, 2026.*

### 1. Intro to LLMs & Prompt Engineering
| Date | Session | Notebooks/Presentations | Exercises |
| :----| :----| :------------- | :------------- |
| August 1st, 2026 | Introduction to Large Language Models & Prompt Engineering | [L1 - Intro to LLMs](./notebooks/L1-IntroToLLMs.ipynb) | |

### 2. Working with LLM APIs (OpenAI, Anthropic/Claude)
| Date | Session | Notebooks/Presentations | Exercises |
| :----| :----| :------------- | :------------- |
| August 8th, 2026 | Calling LLM APIs: OpenAI and Anthropic/Claude | | |

### 3. Embeddings & Vector Databases (FAISS, Chroma)
| Date | Session | Notebooks/Presentations | Exercises |
| :----| :----| :------------- | :------------- |
| August 15th, 2026 | Embeddings and Vector Databases with FAISS and Chroma | | |

### 4. RAG basics
| Date | Session | Notebooks/Presentations | Exercises |
| :----| :----| :------------- | :------------- |
| August 22nd, 2026 | Retrieval-Augmented Generation fundamentals | | |

### 5. Advanced RAG (re-ranking, hybrid search, query transformation)
| Date | Session | Notebooks/Presentations | Exercises |
| :----| :----| :------------- | :------------- |
| August 29th, 2026 | Advanced RAG: re-ranking, hybrid search and query transformation | | |

### 6. AI Agents fundamentals (ReAct, tool use, function calling)
| Date | Session | Notebooks/Presentations | Exercises |
| :----| :----| :------------- | :------------- |
| September 5th, 2026 | AI Agents: ReAct, tool use and function calling | | |

### 7. LangChain
| Date | Session | Notebooks/Presentations | Exercises |
| :----| :----| :------------- | :------------- |
| September 12th, 2026 | Building LLM applications with LangChain | | |

### 8. LangGraph (stateful/multi-step agents)
| Date | Session | Notebooks/Presentations | Exercises |
| :----| :----| :------------- | :------------- |
| September 19th, 2026 | Stateful, multi-step agents with LangGraph | | |

### 9. MCP - Model Context Protocol
| Date | Session | Notebooks/Presentations | Exercises |
| :----| :----| :------------- | :------------- |
| September 26th, 2026 | Connecting tools and data with the Model Context Protocol | | |

### 10. Multi-agent systems
| Date | Session | Notebooks/Presentations | Exercises |
| :----| :----| :------------- | :------------- |
| October 3rd, 2026 | Designing and orchestrating multi-agent systems | | |

### 11. Evaluation of LLM apps (LLM-as-judge, RAGAS)
| Date | Session | Notebooks/Presentations | Exercises |
| :----| :----| :------------- | :------------- |
| October 10th, 2026 | Evaluating LLM applications: LLM-as-judge and RAGAS | | |

### 12. LLMOps & Deployment
| Date | Session | Notebooks/Presentations | Exercises |
| :----| :----| :------------- | :------------- |
| October 17th, 2026 | LLMOps: deploying and monitoring LLM applications | | |

## Interest Links 🔗
Module | Topic | Material |
| :----| :----| :----|
| LangChain | Official Documentation | [LangChain Docs](https://python.langchain.com) |
| LangGraph | Official Documentation | [LangGraph Docs](https://langchain-ai.github.io/langgraph/) |
| MCP | Model Context Protocol | [modelcontextprotocol.io](https://modelcontextprotocol.io) |
| GenAI | Short Courses | [DeepLearning.AI Short Courses](https://www.deeplearning.ai/short-courses/) |

---

> 📚 This course is a continuation ("part 2") of [Advanced Topics in Analytics](https://github.com/sergiomorapardo/AdvancedTopicsAnalytics), which covered MLOps, Deep Learning, NLP and Graph Learning.
