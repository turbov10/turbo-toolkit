from pathlib import Path
import textwrap
import pytest

from agent_gateway.discovery import (
    DiscoveredTool,
    discover_all,
    DiscoveryError,
)


def test_discovers_tool_dirs_with_mcp_tools_py(fake_monorepo: Path) -> None:
    from tests.conftest import write_mcp_tools
    write_mcp_tools(fake_monorepo / "alpha-tool", "alpha")
    write_mcp_tools(fake_monorepo / "beta-tool", "beta")

    tools = discover_all(fake_monorepo)
    namespaces = {t.namespace for t in tools}
    assert namespaces == {"alpha", "beta"}


def test_excludes_listed_dirs(fake_monorepo: Path) -> None:
    from tests.conftest import write_mcp_tools
    write_mcp_tools(fake_monorepo / "alpha-tool", "alpha")
    # agent-gateway/, .github/, docs/ must never be discovered even with mcp_tools.py
    write_mcp_tools(fake_monorepo / "agent-gateway", "self")
    write_mcp_tools(fake_monorepo / ".github", "gh")
    write_mcp_tools(fake_monorepo / "docs", "docs")

    tools = discover_all(fake_monorepo)
    namespaces = {t.namespace for t in tools}
    assert "self" not in namespaces
    assert "gh" not in namespaces
    assert "docs" not in namespaces
    assert "alpha" in namespaces


def test_excludes_dirs_without_mcp_tools_py(fake_monorepo: Path) -> None:
    # beta-tool has no mcp_tools.py; only alpha-tool should appear
    from tests.conftest import write_mcp_tools
    write_mcp_tools(fake_monorepo / "alpha-tool", "alpha")
    tools = discover_all(fake_monorepo)
    assert [t.namespace for t in tools] == ["alpha"]


def test_validates_too_namespace_present(tmp_path: Path) -> None:
    (tmp_path / "bad").mkdir()
    (tmp_path / "bad" / "mcp_tools.py").write_text("def register(mcp): pass\n")
    with pytest.raises(DiscoveryError, match="TOOL_NAMESPACE"):
        discover_all(tmp_path, strict=True)


def test_validates_register_callable(tmp_path: Path) -> None:
    (tmp_path / "bad").mkdir()
    (tmp_path / "bad" / "mcp_tools.py").write_text(
        "TOOL_NAMESPACE = 'bad'\nregister = 'not a function'\n"
    )
    with pytest.raises(DiscoveryError, match="register"):
        discover_all(tmp_path, strict=True)


def test_venv_python_attribute(fake_monorepo: Path) -> None:
    from tests.conftest import write_mcp_tools
    write_mcp_tools(fake_monorepo / "alpha-tool", "alpha")
    tools = discover_all(fake_monorepo)
    t = tools[0]
    assert t.venv_python.name in ("python", "python.exe")
    assert t.venv_python.parent.name in ("bin", "Scripts")
    # Falls back to sys.executable when no .venv exists
    assert t.venv_python.exists() or t.venv_python == t.system_python


def test_exclude_is_overridable(fake_monorepo: Path) -> None:
    from tests.conftest import write_mcp_tools
    write_mcp_tools(fake_monorepo / "alpha-tool", "alpha")
    tools = discover_all(fake_monorepo, exclude=[])
    assert "alpha" in {t.namespace for t in tools}
