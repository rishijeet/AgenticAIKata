import time
from typing import Dict, Optional

import requests


class HttpClient:
    def __init__(self, user_agent: Optional[str] = None, timeout: float = 20.0) -> None:
        self.s = requests.Session()
        self.timeout = timeout
        self.user_agent = user_agent or "AgenticAIKata/1.0 (https://example.local)"

    def get(self, url: str, headers: Optional[Dict[str, str]] = None, retries: int = 2, backoff: float = 0.8) -> Optional[requests.Response]:
        h = {"User-Agent": self.user_agent}
        if headers:
            h.update(headers)
        last_err = None
        for i in range(retries + 1):
            try:
                r = self.s.get(url, headers=h, timeout=self.timeout)
                r.raise_for_status()
                return r
            except Exception as e:
                last_err = e
                if i < retries:
                    time.sleep(backoff * (2 ** i))
        return None
