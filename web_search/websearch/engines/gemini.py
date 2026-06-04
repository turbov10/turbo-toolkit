from __future__ import annotations

import os

from .base import SearchEngine, SearchEngineError, SearchResult


class GeminiEngine(SearchEngine):
    name = "gemini"
    DEFAULT_MODEL = "gemini-2.5-flash"

    def search(self, query: str, limit: int = 10) -> list[SearchResult]:
        try:
            from google import genai
            from google.genai import types
        except ImportError as exc:
            raise SearchEngineError(
                "google-genai is not installed; run: pip install google-genai"
            ) from exc

        api_key = self._require_env("GEMINI_API_KEY")
        model = os.environ.get("GEMINI_MODEL", self.DEFAULT_MODEL)

        client = genai.Client(api_key=api_key)
        try:
            response = client.models.generate_content(
                model=model,
                contents=query,
                config=types.GenerateContentConfig(
                    tools=[types.Tool(google_search=types.GoogleSearch())],
                ),
            )
        except Exception as exc:
            raise SearchEngineError(f"gemini request failed: {exc}") from exc

        candidate = response.candidates[0] if response.candidates else None
        if candidate is None or candidate.grounding_metadata is None:
            return []

        gm = candidate.grounding_metadata
        chunks = list(gm.grounding_chunks or [])
        supports = list(gm.grounding_supports or [])

        snippets_by_chunk: dict[int, list[str]] = {}
        for s in supports:
            text = (s.segment.text or "").strip() if s.segment else ""
            if not text:
                continue
            for idx in s.grounding_chunk_indices or []:
                snippets_by_chunk.setdefault(idx, []).append(text)

        results: list[SearchResult] = []
        seen: set[str] = set()
        for i, chunk in enumerate(chunks):
            web = getattr(chunk, "web", None)
            if web is None:
                continue
            uri = getattr(web, "uri", "") or ""
            if not uri or uri in seen:
                continue
            seen.add(uri)
            title = getattr(web, "title", "") or uri
            snippet_parts = snippets_by_chunk.get(i, [])
            snippet = " ".join(snippet_parts).strip()
            if not snippet:
                snippet = (response.text or "").strip()[:300]
            results.append(
                SearchResult(title=title, link=uri, snippet=snippet)
            )
            if len(results) >= limit:
                break

        return results
