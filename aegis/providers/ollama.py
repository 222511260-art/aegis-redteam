"""Ollama chat provider — queries a local model over the Ollama HTTP API.

This talks to ``http://127.0.0.1:11434`` by default and never contacts any
remote service, matching the local-privacy requirement of the lab.
"""

from __future__ import annotations

import json
import urllib.request
import urllib.error

from .base import Provider


class OllamaProvider(Provider):
    name = "ollama"

    def __init__(
        self,
        model: str = "llama3.2",
        base_url: str = "http://127.0.0.1:11434",
        temperature: float = 0.0,
        timeout: int = 120,
        **_ignored,
    ):
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.temperature = temperature
        self.timeout = timeout

    def describe(self) -> str:
        return f"ollama:{self.model}"

    def generate(self, system: str, user: str) -> str:
        payload = {
            "model": self.model,
            "stream": False,
            "options": {"temperature": self.temperature},
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{self.base_url}/api/chat",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                body = json.loads(resp.read().decode("utf-8"))
        except urllib.error.URLError as exc:  # pragma: no cover - network dependent
            raise RuntimeError(
                f"Could not reach Ollama at {self.base_url}. "
                f"Is it running? (`ollama serve`). Original error: {exc}"
            )
        return body.get("message", {}).get("content", "")
