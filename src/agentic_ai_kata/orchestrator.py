from typing import Any, Dict

from .agents.fundamentals_agent import FundamentalsAgent
from .agents.news_agent import NewsAgent
from .utils.ollama_client import OllamaClient


class Orchestrator:
    def __init__(self) -> None:
        self.fundamentals = FundamentalsAgent()
        self.news = NewsAgent()

    def run(
        self,
        ticker: str,
        days: int = 7,
        summarize: bool = False,
        ollama_model: str = "mistral:latest",
        ollama_url: str = "http://localhost:11434",
    ) -> Dict[str, Any]:
        fundamentals = self.fundamentals.fetch(ticker)
        company_name = fundamentals.get("identity", {}).get("name")
        summarizer = None
        if summarize:
            client = OllamaClient(base_url=ollama_url)
            summarizer = lambda text: client.summarize(text, model=ollama_model)
        news_items = self.news.fetch(
            ticker, company_name=company_name, days=days, summarizer=summarizer
        )
        return {
            "fundamentals": fundamentals,
            "news": news_items,
        }
