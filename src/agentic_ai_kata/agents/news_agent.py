from datetime import datetime
import html
import re
from typing import Any, Dict, List, Optional, Callable

import feedparser
from urllib.parse import quote_plus


def _clean_text(t: str) -> str:
    if not t:
        return t
    t = html.unescape(t)
    t = re.sub(r"<[^>]+>", " ", t)
    t = re.sub(r"\s+", " ", t)
    return t.strip()


class NewsAgent:
    """
    Fetches company-related news via Google News RSS and produces concise items.
    No API keys required.
    """

    def _build_query(self, ticker: str, company_name: Optional[str]) -> str:
        if company_name:
            # Use OR to broaden recall, quoted name to improve precision
            return f'"{company_name}" OR {ticker}'
        return ticker

    def fetch(
        self,
        ticker: str,
        company_name: Optional[str] = None,
        days: int = 7,
        max_items: int = 15,
        summarizer: Optional[Callable[[str], Optional[str]]] = None,
    ) -> List[Dict[str, Any]]:
        query = self._build_query(ticker, company_name)
        qparam = quote_plus(query)
        url = (
            "https://news.google.com/rss/search?"
            f"q={qparam}+when:{days}d&hl=en-US&gl=US&ceid=US:en"
        )
        feed = feedparser.parse(url)
        items: List[Dict[str, Any]] = []

        for e in feed.entries[:max_items]:
            title = _clean_text(getattr(e, "title", ""))
            link = getattr(e, "link", None)
            summary = _clean_text(getattr(e, "summary", ""))
            source = _clean_text(getattr(getattr(e, "source", {}), "title", ""))
            published = getattr(e, "published", None)
            try:
                published_parsed = getattr(e, "published_parsed", None)
                if published_parsed:
                    published_iso = datetime(*published_parsed[:6]).isoformat()
                else:
                    published_iso = None
            except Exception:
                published_iso = None

            concise = summary[:240] + ("…" if len(summary) > 240 else "") if summary else None

            # Optional LLM summarization via provided callback
            if summarizer is not None:
                basis = (title or "") + (". " + summary if summary else "")
                try:
                    llm_sum = summarizer(basis.strip()) if basis.strip() else None
                    if llm_sum:
                        concise = llm_sum.strip()
                except Exception:
                    # Fail silently, keep extractive summary
                    pass

            items.append(
                {
                    "title": title or None,
                    "source": source or None,
                    "published": published_iso or published,
                    "link": link,
                    "summary": concise,
                }
            )

        return items
