from __future__ import annotations

import requests

from .base import SearchEngine, SearchEngineError, SearchResult

_ENDPOINT = "https://www.googleapis.com/customsearch/v1"


class GoogleEngine(SearchEngine):
    name = "google"

    def search(self, query: str, limit: int = 10) -> list[SearchResult]:
        api_key = self._require_env("GOOGLE_API_KEY", "GOOGLE_CX")
        cx = self._require_env("GOOGLE_CX")

        params = {
            "key": api_key,
            "cx": cx,
            "q": query,
            "num": max(1, min(limit, 10)),
        }
        try:
            resp = requests.get(_ENDPOINT, params=params, timeout=15)
        except requests.RequestException as exc:
            raise SearchEngineError(f"google request failed: {exc}") from exc

        if resp.status_code != 200:
            raise SearchEngineError(
                f"google api error {resp.status_code}: {resp.text[:300]}"
            )

        data = resp.json()
        return [
            SearchResult(
                title=item.get("title", ""),
                link=item.get("link", ""),
                snippet=item.get("snippet", ""),
            )
            for item in data.get("items", [])
        ]
