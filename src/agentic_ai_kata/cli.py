import argparse
import json
from typing import Any

from .orchestrator import Orchestrator


def main() -> None:
    parser = argparse.ArgumentParser(description="Fundamentals + News agents (no API keys)")
    parser.add_argument("--ticker", required=True, help="Ticker symbol, e.g., AAPL, MSFT, TSLA")
    parser.add_argument("--days", type=int, default=7, help="Days to look back for news (default 7)")
    parser.add_argument("--json", action="store_true", help="Print JSON output")
    parser.add_argument("--summarize", action="store_true", help="Summarize news items using a local Ollama model")
    parser.add_argument("--ollama-model", default="mistral:latest", help="Ollama model name (default: mistral:latest)")
    parser.add_argument("--ollama-url", default="http://localhost:11434", help="Ollama base URL (default: http://localhost:11434)")
    args = parser.parse_args()

    orch = Orchestrator()
    result: Any = orch.run(
        args.ticker,
        days=args.days,
        summarize=args.summarize,
        ollama_model=args.ollama_model,
        ollama_url=args.ollama_url,
    )

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return

    f = result["fundamentals"]
    n = result["news"]

    print(f"\n=== Fundamentals for {f.get('ticker')} ===")
    ident = f.get("identity", {})
    print(f"Name: {ident.get('name')}")
    print(f"Sector: {ident.get('sector')} | Industry: {ident.get('industry')} | Exchange: {ident.get('exchange')}")

    price = f.get("price", {})
    print(f"Price: {price.get('last')} {price.get('currency')}")

    val = f.get("valuation", {})
    print(
        "Valuation -> Market Cap: {mc} | TTM P/E: {tpe} | Fwd P/E: {fpe} | P/B: {pb}".format(
            mc=val.get("market_cap"), tpe=val.get("trailing_pe"), fpe=val.get("forward_pe"), pb=val.get("price_to_book")
        )
    )

    fin = f.get("financials", {})
    print(
        "Financials -> Revenue: {rev} | Net Income: {ni} | Free Cash Flow: {fcf}".format(
            rev=fin.get("revenue"), ni=fin.get("net_income"), fcf=fin.get("free_cash_flow")
        )
    )

    print(f"\n=== Recent News (last {args.days} days) ===")
    if not n:
        print("No news found.")
    for i, item in enumerate(n, 1):
        print(f"\n{i}. {item.get('title')}")
        src = item.get("source")
        if src:
            print(f"   Source: {src}")
        if item.get("published"):
            print(f"   Published: {item.get('published')}")
        if item.get("summary"):
            print(f"   Summary: {item.get('summary')}")
        print(f"   Link: {item.get('link')}")


if __name__ == "__main__":
    main()
