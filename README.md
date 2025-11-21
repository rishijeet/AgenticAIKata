# Agentic AI Kata

Minimal sample showing local, no-API-key agents for company research:
- Fundamentals (yfinance)
- News (Google News RSS) with optional Ollama summaries
- SEC Filings (10-K/10-Q) section extraction
- Optional clustering/dedupe of news

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## CLI Usage

```bash
# Basics
PYTHONPATH=src python -m agentic_ai_kata.cli --ticker AAPL --days 7

# With local LLM summaries (Ollama)
PYTHONPATH=src python -m agentic_ai_kata.cli --ticker AAPL --days 7 \
  --summarize --ollama-model mistral:latest

# Add news clustering/dedupe
PYTHONPATH=src python -m agentic_ai_kata.cli --ticker AAPL --days 7 --cluster

# Include SEC filings (10-K/10-Q)
PYTHONPATH=src python -m agentic_ai_kata.cli --ticker AAPL --include-filings --filings-limit 2

# JSON output
PYTHONPATH=src python -m agentic_ai_kata.cli --ticker AAPL --days 7 --json
```

## Parallel Run (Supervisor)

```bash
PYTHONPATH=src python scripts/supervised_run.py --ticker AAPL --days 7 \
  --include-filings --cluster --summarize --ollama-model mistral:latest
```

## Notes
- Works without OpenAI/Google keys. Data from Yahoo (yfinance), Google News RSS, and SEC EDGAR.
- If rate-limited (429), agents return partial data; try again or reduce frequency.

---

© Rishijeet Mishra
