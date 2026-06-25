from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


class SearchEngineError(RuntimeError):
    """Raised when an engine is misconfigured or the upstream call fails."""


@dataclass(frozen=True)
class SearchResult:
    title: str
    link: str
    snippet: str

    def to_dict(self) -> dict:
        return {"title": self.title, "link": self.link, "snippet": self.snippet}


class SearchEngine(ABC):
    name: str

    @abstractmethod
    def search(self, query: str, limit: int = 10) -> list[SearchResult]:
        """Run the query and return a list of normalised results."""

    @staticmethod
    def _require_env(*names: str) -> str:
        import os

        missing = [n for n in names if not os.environ.get(n)]
        if missing:
            raise SearchEngineError(
                "missing required env var(s): " + ", ".join(missing)
            )
        return os.environ[names[0]]
