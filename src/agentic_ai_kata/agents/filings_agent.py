import re
from typing import Any, Dict, List, Optional

from bs4 import BeautifulSoup  # type: ignore

from ..utils.http import HttpClient
from ..utils.ollama_client import OllamaClient


class FilingsAgent:
    """
    Fetches recent 10-K/10-Q filings from SEC EDGAR (Atom feed) and extracts key sections.
    Uses simple heuristics and optional local LLM via Ollama to summarize sections.
    """

    def __init__(self, http: Optional[HttpClient] = None) -> None:
        self.http = http or HttpClient(user_agent="AgenticAIKata/1.0 (contact: local dev)")

    def _sec_feed(self, ticker: str, limit: int) -> Optional[str]:
        # Use SEC browse endpoint with output=atom and type filter
        url = (
            "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany"
            f"&CIK={ticker}&type=10-%25&owner=exclude&count={limit}&output=atom"
        )
        r = self.http.get(url, headers={"Accept": "application/atom+xml"}, retries=2)
        return r.text if r is not None else None

    def _extract_primary_doc_url(self, filing_page_url: str) -> Optional[str]:
        # Filing detail page contains a table of documents. Pick the first HTML/TXT document.
        r = self.http.get(filing_page_url, retries=2)
        if r is None:
            return None
        soup = BeautifulSoup(r.text, "lxml")
        table = soup.find("table", class_="tableFile") or soup.find("table", summary=re.compile("Document Format Files", re.I))
        if not table:
            return None
        href: Optional[str] = None
        for row in table.find_all("tr"):
            cols = row.find_all("td")
            if len(cols) >= 3:
                doc_type = (cols[3].get_text(strip=True) if len(cols) > 3 else "").upper()
                link_tag = cols[2].find("a") if len(cols) > 2 else None
                if link_tag and link_tag.get("href"):
                    candidate = link_tag["href"]
                    if candidate.lower().endswith((".htm", ".html", ".txt")):
                        href = candidate
                        break
        if not href:
            return None
        if href.startswith("http"):
            return href
        # Build absolute URL
        base = "https://www.sec.gov"
        return base + href

    def _clean_text(self, html_text: str) -> str:
        soup = BeautifulSoup(html_text, "lxml")
        text = soup.get_text(" ")
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def _extract_sections(self, text: str) -> Dict[str, str]:
        # Very simple ITEM section splitter for 10-K/10-Q
        sections = {}
        # Define common section markers
        markers = [
            ("Business", r"ITEM\s+1\.?\s+BUSINESS"),
            ("Risk Factors", r"ITEM\s+1A\.?\s+RISK\s+FACTORS"),
            ("MD&A", r"ITEM\s+7\.?\s+MANAGEMENT'S\s+DISCUSSION"),
        ]
        # Find indices
        spans = []
        for name, pat in markers:
            m = re.search(pat, text, flags=re.I)
            if m:
                spans.append((name, m.start()))
        spans.sort(key=lambda x: x[1])
        for i, (name, start) in enumerate(spans):
            end = spans[i + 1][1] if i + 1 < len(spans) else None
            snippet = text[start:end].strip() if end else text[start:].strip()
            sections[name] = snippet[:5000]
        return sections

    def fetch(self, ticker: str, limit: int = 2, summarize: bool = False, ollama_model: str = "mistral:latest", ollama_url: str = "http://localhost:11434") -> Dict[str, Any]:
        feed_xml = self._sec_feed(ticker, limit)
        if not feed_xml:
            return {"ticker": ticker.upper(), "filings": [], "error": "no_feed"}

        soup = BeautifulSoup(feed_xml, "xml")
        entries = soup.find_all("entry")
        filings: List[Dict[str, Any]] = []
        client = OllamaClient(base_url=ollama_url) if summarize else None

        for e in entries:
            title = e.title.get_text(strip=True) if e.title else None
            link_tag = e.link
            filing_url = link_tag.get("href") if link_tag else None
            updated = e.updated.get_text(strip=True) if e.updated else None

            sections: Dict[str, str] = {}
            summary: Optional[str] = None

            if filing_url:
                primary = self._extract_primary_doc_url(filing_url)
                if primary:
                    resp = self.http.get(primary, retries=1)
                    if resp is not None:
                        cleaned = self._clean_text(resp.text)
                        sections = self._extract_sections(cleaned)
                        # Build a short extractive summary baseline
                        baseline = cleaned[:800]
                        if summarize and client:
                            prompt = (
                                "Summarize the key points of this SEC filing excerpt (10-K/10-Q) in 3-5 concise bullets, "
                                "focusing on business overview, major risks, and financial highlights.\n\n" + baseline
                            )
                            summary = client.generate(prompt, model=ollama_model) or None
                        else:
                            summary = baseline

            filings.append(
                {
                    "title": title,
                    "filing_page": filing_url,
                    "primary_doc": primary if filing_url else None,
                    "updated": updated,
                    "sections": sections,
                    "summary": summary,
                }
            )

        return {"ticker": ticker.upper(), "filings": filings}
