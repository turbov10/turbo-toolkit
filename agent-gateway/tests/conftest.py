"""Shared pytest fixtures."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import textwrap
import pytest


@pytest.fixture
def fake_monorepo(tmp_path: Path) -> Path:
    """Return a tmp_path monorepo pre-populated with two stub tool dirs."""
    (tmp_path / "alpha-tool").mkdir()
    (tmp_path / "beta-tool").mkdir()
    (tmp_path / "agent-gateway").mkdir()  # should be excluded
    (tmp_path / ".github").mkdir()         # should be excluded
    (tmp_path / "docs").mkdir()            # should be excluded
    return tmp_path


def write_mcp_tools(
    tool_dir: Path,
    namespace: str,
    fn_name: str = "hello",
    return_value: str = "world",
) -> Path:
    """Write a minimal valid mcp_tools.py in `tool_dir` and return the path."""
    path = tool_dir / "mcp_tools.py"
    path.write_text(textwrap.dedent(f'''
        import argparse
        import json
        TOOL_NAMESPACE = {namespace!r}

        def {fn_name}(name: str = "world") -> str:
            return {return_value!r}

        def register(mcp):
            mcp.tool(
                name=f"{{TOOL_NAMESPACE}}__{fn_name}",
                description="stub tool",
            )({fn_name})

        if __name__ == "__main__":
            _parser = argparse.ArgumentParser()
            _sub = _parser.add_subparsers(dest="cmd", required=True)
            _call_p = _sub.add_parser("call")
            _call_p.add_argument("--name", required=True)
            _call_p.add_argument("--args", default="{{}}")
            _ns = _parser.parse_args()
            if _ns.cmd == "call":
                _func = globals()[_ns.name]
                _result = _func(**json.loads(_ns.args))
                print(json.dumps(_result, ensure_ascii=False))
    ''').lstrip())
    return path
