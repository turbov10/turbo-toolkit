from __future__ import annotations

import requests

from .base import SearchEngine, SearchEngineError, SearchResult

_ENDPOINT = "https://api.bing.microsoft.com/v7.0/search"


class BingEngine(SearchEngine):
    name = "bing"

    def search(self, query: str, limit: int = 10) -> list[SearchResult]:
        api_key = self._require_env("BING_API_KEY")

        headers = {"Ocp-Apim-Subscription-Key": api_key}
        params = {
            "q": query,
            "count": max(1, min(limit, 50)),
            "mkt": "zh-CN",
            "textDecorations": "false",
            "textFormat": "Raw",
        }
        try:
            resp = requests.get(_ENDPOINT, headers=headers, params=params, timeout=15)
        except requests.RequestException as exc:
            raise SearchEngineError(f"bing request failed: {exc}") from exc

        if resp.status_code != 200:
            raise SearchEngineError(
                f"bing api error {resp.status_code}: {resp.text[:300]}"
            )

        data = resp.json()
        pages = (data.get("webPages") or {}).get("value") or []
        return [
            SearchResult(
                title=item.get("name", ""),
                link=item.get("url", ""),
                snippet=item.get("snippet", ""),
            )
            for item in pages
        ]
