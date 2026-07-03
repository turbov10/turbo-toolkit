from pathlib import Path
import textwrap
import pytest

from agent_gateway.config import GatewayConfig, load_config


def test_defaults_when_no_file(tmp_path: Path) -> None:
    cfg = load_config(tmp_path / "missing.yaml")
    assert cfg.root == tmp_path
    assert cfg.exclude == ["agent-gateway", ".github", "docs"]
    assert cfg.timeout_seconds == 30
    assert cfg.tools == {}


def test_loads_yaml(tmp_path: Path) -> None:
    cfg_file = tmp_path / "gateway.yaml"
    cfg_file.write_text(textwrap.dedent('''
        root: "."
        exclude: ["foo", "bar"]
        timeout_seconds: 60
        tools:
          web-trigger:
            timeout_seconds: 120
    ''').strip())
    cfg = load_config(cfg_file)
    assert cfg.root == tmp_path
    assert cfg.exclude == ["foo", "bar"]
    assert cfg.timeout_seconds == 60
    assert cfg.tools == {"web-trigger": {"timeout_seconds": 120}}


def test_root_resolved_relative_to_yaml(tmp_path: Path) -> None:
    cfg_file = tmp_path / "sub" / "gateway.yaml"
    cfg_file.parent.mkdir()
    cfg_file.write_text('root: ".."\n')
    cfg = load_config(cfg_file)
    assert cfg.root == tmp_path


def test_invalid_yaml_raises(tmp_path: Path) -> None:
    cfg_file = tmp_path / "gateway.yaml"
    cfg_file.write_text("this: is: not: valid: yaml: [\n")
    with pytest.raises(Exception):
        load_config(cfg_file)


def test_exclude_accepts_string_or_list(tmp_path: Path) -> None:
    cfg_file = tmp_path / "gateway.yaml"
    cfg_file.write_text('exclude: "only-one"\n')
    cfg = load_config(cfg_file)
    assert cfg.exclude == ["only-one"]
