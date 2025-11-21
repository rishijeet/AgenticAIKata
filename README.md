# Agentic AI Kata: Fundamentals + News Agents (No API Keys)

This sample project provides two lightweight agents that work without paid API keys:

- FundamentalsAgent: pulls company fundamentals using yfinance (free).
- NewsAgent: fetches recent company news via Google News RSS (free) and produces concise summaries.

## Quickstart

1. Create and activate a virtual environment (optional but recommended)

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install dependencies

```bash
pip install -r requirements.txt
```

3. Run the CLI

```bash
python -m agentic_ai_kata.cli --ticker AAPL --days 7
```

Options:
- `--ticker` Stock ticker symbol (e.g., AAPL, MSFT, TSLA)
- `--days` Number of past days to search news (default: 7)
- `--json` Print JSON output instead of human-readable text

### Optional: Local LLM Summarization via Ollama

If you have Ollama running locally, you can get higher-quality news summaries without any cloud API keys.

```bash
# Use your installed model (example: mistral:latest)
python -m agentic_ai_kata.cli --ticker AAPL --days 7 \
  --summarize --ollama-model mistral:latest

# JSON output
python -m agentic_ai_kata.cli --ticker AAPL --days 7 \
  --summarize --ollama-model mistral:latest --json
```

If Ollama is at a non-default address:

```bash
python -m agentic_ai_kata.cli --ticker AAPL --days 7 --summarize \
  --ollama-model mistral:latest --ollama-url http://localhost:11434
```

## Project Structure

```
src/
  agentic_ai_kata/
    agents/
      fundamentals_agent.py
      news_agent.py
    orchestrator.py
    cli.py
```

## Notes

- No OpenAI/Google API keys needed. All data is from public endpoints (Yahoo/yfinance scraping and Google News RSS).
- yfinance can occasionally rate-limit or change fields; the code handles missing fields gracefully.
- Optional local LLM summarization is built-in via Ollama; enable with `--summarize` and choose a model with `--ollama-model`.

## Development

- Python version: 3.11+ recommended.
- Common tasks:
  - Lint/format: use your preferred tools; no linters are enforced here.
  - Venv: create `.venv/` and `pip install -r requirements.txt`.
- Git: a `.gitignore` is included to avoid committing virtual env, caches, and build artifacts.
