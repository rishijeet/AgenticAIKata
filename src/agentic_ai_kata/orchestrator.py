from typing import Any, Dict

from .agents.fundamentals_agent import FundamentalsAgent
from .agents.news_agent import NewsAgent
from .utils.ollama_client import OllamaClient
from .agents.filings_agent import FilingsAgent
from .utils.cluster import cluster_news


class Orchestrator:
    def __init__(self) -> None:
        self.fundamentals = FundamentalsAgent()
        self.news = NewsAgent()
        self.filings = FilingsAgent()

    def run(
        self,
        ticker: str,
        days: int = 7,
        summarize: bool = False,
        ollama_model: str = "mistral:latest",
        ollama_url: str = "http://localhost:11434",
        include_filings: bool = False,
        filings_limit: int = 2,
        cluster_dedupe: bool = False,
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
        result: Dict[str, Any] = {
            "fundamentals": fundamentals,
            "news": news_items,
        }
        if cluster_dedupe:
            clusters = cluster_news(news_items)
            # Optionally, create a short summary per cluster using summarizer
            cluster_summaries = []
            for c in clusters:
                title = c.get("title") or ""
                # Merge member summaries into basis text
                members = c.get("items", [])
                basis_parts = [m.get("title") or "" for m in members]
                # Fall back to concatenated titles
                basis_text = ". ".join([p for p in basis_parts if p])[:1000]
                summary_text = None
                if summarize and summarizer and basis_text:
                    try:
                        summary_text = summarizer(basis_text)
                    except Exception:
                        summary_text = None
                cluster_summaries.append({
                    "title": title,
                    "size": len(members),
                    "summary": summary_text,
                    "items": members,
                })
            result["news_clusters"] = cluster_summaries if summarize else clusters

        if include_filings:
            filings = self.filings.fetch(
                ticker, limit=filings_limit, summarize=summarize, ollama_model=ollama_model, ollama_url=ollama_url
            )
            result["filings"] = filings

        return result
