from .base import SearchEngine, SearchEngineError
from .baidu import BaiduEngine
from .bing import BingEngine
from .gemini import GeminiEngine
from .google import GoogleEngine

ENGINES: dict[str, type[SearchEngine]] = {
    "google": GoogleEngine,
    "bing": BingEngine,
    "baidu": BaiduEngine,
    "gemini": GeminiEngine,
}


def build_engine(name: str) -> SearchEngine:
    try:
        cls = ENGINES[name]
    except KeyError as exc:
        raise SearchEngineError(f"unknown engine type: {name!r}") from exc
    return cls()


__all__ = ["SearchEngine", "SearchEngineError", "ENGINES", "build_engine"]
