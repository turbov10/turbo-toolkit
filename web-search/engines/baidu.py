from __future__ import annotations

from typing import cast

import requests

from .base import SearchEngine, SearchEngineError, SearchResult

_ENDPOINT = "https://www.baidu.com/s"
_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36"
)
_BLOCK_HINTS = (
    "百度安全验证",
    "网络不给力",
    "请输入验证码",
    "百度网址安全中心",
    "timeout-title",
    "timeout-button",
)
_SKIP_LINK_HOSTS = ("top.baidu.com/board",)
_SKIP_TITLE_TEXTS = (
    "换一换",
    "广告",
    "更多",
    "登录",
    "百度热搜",
)
_AD_CONTAINER_HINTS = (
    "tuiguang",
    "ec-pc",
    "ec_tuiguang",
    "hot-refresh",
    "hotsearch",
    "s-hotsearch",
)


class BaiduEngine(SearchEngine):
    name = "baidu"

    def search(self, query: str, limit: int = 10) -> list[SearchResult]:
        try:
            from bs4 import BeautifulSoup
        except ImportError as exc:
            raise SearchEngineError(
                "beautifulsoup4 is not installed; run: pip install beautifulsoup4"
            ) from exc

        params = {"wd": query, "ie": "utf-8", "rn": max(1, min(limit, 50))}
        headers = {
            "User-Agent": _USER_AGENT,
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }
        try:
            resp = requests.get(_ENDPOINT, params=params, headers=headers, timeout=15)
        except requests.RequestException as exc:
            raise SearchEngineError(f"baidu request failed: {exc}") from exc

        if resp.status_code != 200:
            raise SearchEngineError(
                f"baidu returned {resp.status_code}: {resp.text[:200]}"
            )

        resp.encoding = resp.apparent_encoding or "utf-8"
        if any(h in resp.text for h in _BLOCK_HINTS):
            raise SearchEngineError(
                "baidu is showing a security verification page; "
                "the 'baidu' scraper only works from IPs not flagged as "
                "bots. Retry later or use a different engine."
            )

        soup = BeautifulSoup(resp.text, "html.parser")

        candidates = soup.select(
            "div.c-container, div.result-op, div.result, "
            "div[class*='result c-container']"
        )

        results: list[SearchResult] = []
        seen: set[str] = set()

        for c in candidates:
            ancestor_classes = " ".join(
                cls for el in c.find_parents() for cls in (el.get("class") or [])
            )
            container_classes = " ".join(c.get("class") or [])
            combined_classes = container_classes + " " + ancestor_classes
            if any(h in combined_classes for h in _AD_CONTAINER_HINTS):
                continue

            if any(
                tag.get_text(strip=True) == "广告"
                for tag in c.find_all(["span", "i", "em"])
            ):
                continue

            a = c.select_one("h3 a") or c.select_one("h2 a")
            if a is None:
                a = next(
                    (
                        el
                        for el in c.select("a[href]")
                        if cast(str, el.get("href") or "").startswith(
                            ("http://", "https://")
                        )
                        and el.get_text(strip=True)
                    ),
                    None,
                )
            if a is None:
                continue

            link = cast(str, a.get("href", "") or "")
            if not link or link in seen:
                continue
            if link.startswith("javascript:"):
                continue
            if any(h in link for h in _SKIP_LINK_HOSTS):
                continue
            seen.add(link)

            title = a.get_text(strip=True)
            if not title or any(t == title for t in _SKIP_TITLE_TEXTS):
                continue

            snippet = self._extract_snippet(c)
            if not snippet:
                continue

            results.append(SearchResult(title=title, link=link, snippet=snippet))
            if len(results) >= limit:
                break

        return results

    @staticmethod
    def _extract_snippet(container) -> str:
        for sel in (
            "div.c-abstract",
            "span.c-abstract",
            "div.c-summary",
            "div.content-right_8Zs40",
        ):
            el = container.select_one(sel)
            if el:
                text = el.get_text(" ", strip=True)
                if len(text) > 20:
                    return text
        candidates = []
        for el in container.select("p, div, span"):
            cls = " ".join(el.get("class") or [])
            if any(h in cls for h in _AD_CONTAINER_HINTS):
                continue
            text = el.get_text(" ", strip=True)
            if 30 <= len(text) <= 400 and " " in text:
                candidates.append(text)
        if candidates:
            return max(candidates, key=len)
        return ""
