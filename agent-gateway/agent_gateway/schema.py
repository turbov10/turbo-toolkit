"""CapturingMCP: an MCP stand-in that records tool registrations and proxies them."""
from __future__ import annotations
import inspect
import logging
import types
from dataclasses import dataclass
from typing import Any, Callable, get_type_hints

from mcp.server.fastmcp import FastMCP

from agent_gateway.runner import SubprocessRunner

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class ToolRecord:
    full_name: str        # e.g. "image-ocr__ocr_image"
    bare_name: str        # e.g. "ocr_image"
    source_func: Callable
    description: str | None


def _make_proxy(
    full_name: str,
    bare_name: str,
    runner: SubprocessRunner,
    source_func: Callable,
) -> Callable[..., Any]:
    """Return a wrapper that calls the runner and preserves source's signature.

    FastMCP introspects the registered function's `__signature__` and
    `__annotations__` to build the input JSON schema, so we copy them across.
    We also re-bind the wrapper to the source function's globals so that
    `inspect.signature(func, eval_str=True)` can resolve string annotations
    (e.g. `Literal[...]` under `from __future__ import annotations`).
    """
    sig = inspect.signature(source_func, eval_str=True)

    def proxy(**kwargs: Any) -> Any:
        return runner.run(full_name, kwargs)

    proxy = types.FunctionType(
        proxy.__code__,
        source_func.__globals__,
        bare_name,
        proxy.__defaults__,
        proxy.__closure__,
    )
    proxy.__signature__ = sig
    proxy.__annotations__ = get_type_hints(source_func)
    proxy.__doc__ = source_func.__doc__
    proxy.__wrapped__ = source_func
    return proxy


class CapturingMCP:
    """MCP-compatible wrapper that captures tool registrations and proxies them.

    Usage:
        cap = CapturingMCP("agent-gateway", runner)
        for module in discovered_modules:
            module.register(cap)
        # cap.real is the FastMCP instance ready to .run()
        # cap.captures is a list of ToolRecord for the gateway's CLI/registry
    """

    def __init__(self, server_name: str, runner: SubprocessRunner) -> None:
        self._real = FastMCP(server_name)
        self._runner = runner
        self._captures: list[ToolRecord] = []

    @property
    def real(self) -> FastMCP:
        return self._real

    @property
    def captures(self) -> list[ToolRecord]:
        return list(self._captures)

    def tool(
        self,
        name: str | None = None,
        description: str | None = None,
        **_: Any,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            bare_name = func.__name__
            full_name = name or bare_name
            desc = description or (func.__doc__ or "").strip().splitlines()[0] if func.__doc__ else None
            proxy = _make_proxy(full_name, bare_name, self._runner, func)
            self._real.add_tool(
                fn=proxy,
                name=full_name,
                description=desc,
            )
            self._captures.append(
                ToolRecord(
                    full_name=full_name,
                    bare_name=bare_name,
                    source_func=func,
                    description=desc,
                )
            )
            return func

        return decorator
