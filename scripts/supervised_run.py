import argparse
import asyncio
from typing import Any, Dict

from agentic_ai_kata.utils.supervisor import Supervisor
from agentic_ai_kata.agents.fundamentals_agent import FundamentalsAgent
from agentic_ai_kata.agents.news_agent import NewsAgent
from agentic_ai_kata.agents.filings_agent import FilingsAgent
from agentic_ai_kata.utils.ollama_client import OllamaClient
from agentic_ai_kata.utils.cluster import cluster_news

def heartbeat_printer(beat: Dict[str, Any]) -> None:
    print(f"[heartbeat] {beat}")

async def main():
    parser = argparse.ArgumentParser(description="Supervisor parallel run")
    parser.add_argument("--ticker", required=True)
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--summarize", action="store_true")
    parser.add_argument("--ollama-model", default="mistral:latest")
    parser.add_argument("--ollama-url", default="http://localhost:11434")
    parser.add_argument("--include-filings", action="store_true")
    parser.add_argument("--filings-limit", type=int, default=2)
    parser.add_argument("--cluster", action="store_true")
    args = parser.parse_args()

    fundamentals = FundamentalsAgent()
    news = NewsAgent()
    filings = FilingsAgent()

    summarizer = None
    if args.summarize:
        client = OllamaClient(base_url=args.ollama_url)
        summarizer = lambda text: client.summarize(text, model=args.ollama_model)

    sup = Supervisor(heartbeat_cb=heartbeat_printer)

    # Wrap sync calls using asyncio.to_thread so Supervisor can await them.
    tasks = [
        ("fundamentals", asyncio.to_thread(fundamentals.fetch, args.ticker), 20.0),
        ("news", asyncio.to_thread(news.fetch, args.ticker, None, args.days, 20, summarizer), 25.0),
    ]
    if args.include_filings:
        tasks.append((
            "filings",
            asyncio.to_thread(filings.fetch, args.ticker, args.filings_limit, args.summarize, args.ollama_model, args.ollama_url),
            40.0
        ))

    results = await sup.run_parallel(tasks)

    # Post-processing: clustering (optional)
    if args.cluster and results.get("news", {}).get("result"):
        news_items = results["news"]["result"]
        clusters = cluster_news(news_items)
        if summarizer:
            # Summarize cluster titles concatenated
            summaries = []
            for c in clusters:
                titles = ". ".join([(i.get("title") or "") for i in c.get("items", [])])[:1000]
                s = summarizer(titles) if titles else None
                summaries.append({
                    "title": c.get("title"),
                    "size": len(c.get("items", [])),
                    "summary": s,
                    "items": c.get("items", [])
                })
            results["news_clusters"] = summaries
        else:
            results["news_clusters"] = clusters

    # Print a compact view (customize as needed)
    print("\n=== Supervisor Results ===")
    for name, payload in results.items():
        err = payload.get("error")
        print(f"- {name}: {'OK' if not err else 'ERROR: ' + err}")
    if "news_clusters" in results:
        print(f"- news_clusters: {len(results['news_clusters'])} clusters")

if __name__ == "__main__":
    asyncio.run(main())