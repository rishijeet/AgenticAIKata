import json
from typing import Optional

import requests


class OllamaClient:
    def __init__(self, base_url: str = "http://localhost:11434") -> None:
        self.base_url = base_url.rstrip("/")

    def generate(self, prompt: str, model: str = "mistral:latest", timeout: float = 20.0) -> Optional[str]:
        try:
            resp = requests.post(
                f"{self.base_url}/api/generate",
                json={"model": model, "prompt": prompt, "stream": False},
                timeout=timeout,
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("response")
        except Exception:
            return None

    def summarize(self, text: str, model: str = "mistral:latest", timeout: float = 20.0) -> Optional[str]:
        prompt = (
            "You are a financial news assistant. Summarize the following article snippet in 1-2 concise sentences, "
            "focusing on facts and company impact. Avoid hype and hedging.\n\n" + text.strip()
        )
        return self.generate(prompt, model=model, timeout=timeout)
