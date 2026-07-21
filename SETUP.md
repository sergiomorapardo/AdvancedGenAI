# Getting Started

This guide walks you through setting up the AdvancedGenAI course environment so you can run the notebooks locally.

## Prerequisites

- **Python 3.10+**
- **git**
- An **OpenAI** and/or **Anthropic** API key

## 1. Clone the repo

```bash
git clone https://github.com/sergiomorapardo/AdvancedGenAI.git
cd AdvancedGenAI
```

## 2. Create a virtual environment

**macOS / Linux**

```bash
python3 -m venv .venv && source .venv/bin/activate
```

**Windows**

```bash
python -m venv .venv && .venv\Scripts\activate
```

## 3. Install dependencies

```bash
pip install -r requirements.txt
```

## 4. Configure API keys

Copy the example environment file and add your keys:

```bash
cp .env.example .env
```

Then edit `.env` and set your credentials:

```
OPENAI_API_KEY=your-openai-key-here
ANTHROPIC_API_KEY=your-anthropic-key-here
```

> **Note:** `.env` is gitignored and must **never** be committed — it holds your secret API keys.

## 5. Launch Jupyter

```bash
jupyter notebook
```

(or `jupyter lab`), then open `notebooks/L1-IntroToLLMs.ipynb`.

## Troubleshooting

- **Wrong Python version:** run `python --version` and make sure it's 3.10 or newer.
- **Command/package not found:** confirm the virtual environment is activated (you should see `(.venv)` in your prompt). Re-run the activation command from step 2 if needed.
- **API key not loaded:** double-check that `.env` exists, contains the correct keys, and that `python-dotenv` is installed (it's included in `requirements.txt`).
