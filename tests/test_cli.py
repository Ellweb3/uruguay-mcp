"""Tests for the CLI: logging config and the `install` subcommand."""

from __future__ import annotations

import json
import logging

import pytest

from uruguay_mcp import cli


def test_configure_logging_levels():
    cli._configure_logging(verbose=False, debug=False)
    assert logging.getLogger().level == logging.WARNING
    cli._configure_logging(verbose=True, debug=False)
    assert logging.getLogger().level == logging.INFO
    cli._configure_logging(verbose=False, debug=True)
    assert logging.getLogger().level == logging.DEBUG


def test_config_snippet_shape():
    snip = cli._config_snippet()
    assert snip["command"] == "uruguay-mcp"
    assert snip["args"] == []
    assert snip["env"] == {}


def test_install_creates_config(tmp_path, monkeypatch, capsys):
    cfg = tmp_path / "claude_desktop_config.json"
    monkeypatch.setattr(cli, "_claude_desktop_config_path", lambda: cfg)

    rc = cli._install(object())  # args unused by _install
    assert rc == 0

    data = json.loads(cfg.read_text(encoding="utf-8"))
    assert data["mcpServers"]["uruguay-mcp"]["command"] == "uruguay-mcp"

    out = capsys.readouterr().out
    assert "mcpServers" in out


def test_install_preserves_unrelated_keys(tmp_path, monkeypatch):
    cfg = tmp_path / "claude_desktop_config.json"
    cfg.write_text(
        json.dumps({"theme": "dark", "mcpServers": {"other": {"command": "x"}}}),
        encoding="utf-8",
    )
    monkeypatch.setattr(cli, "_claude_desktop_config_path", lambda: cfg)

    rc = cli._install(object())
    assert rc == 0

    data = json.loads(cfg.read_text(encoding="utf-8"))
    assert data["theme"] == "dark"
    assert data["mcpServers"]["other"]["command"] == "x"
    assert data["mcpServers"]["uruguay-mcp"]["command"] == "uruguay-mcp"


def test_install_path_none_prints_instructions(monkeypatch, capsys):
    monkeypatch.setattr(cli, "_claude_desktop_config_path", lambda: None)
    rc = cli._install(object())
    assert rc == 0
    out = capsys.readouterr().out
    assert "manually" in out.lower()


def test_install_rejects_invalid_existing_json(tmp_path, monkeypatch):
    cfg = tmp_path / "claude_desktop_config.json"
    cfg.write_text("{not valid json", encoding="utf-8")
    monkeypatch.setattr(cli, "_claude_desktop_config_path", lambda: cfg)
    rc = cli._install(object())
    assert rc == 1


def test_main_serve_invokes_build(monkeypatch):
    calls = {}

    class FakeMCP:
        def run(self, *a, **k):
            calls["ran"] = (a, k)

    monkeypatch.setattr(cli, "build_server", lambda: FakeMCP())
    monkeypatch.setattr(cli.sys, "argv", ["uruguay-mcp"])
    with pytest.raises(SystemExit) as exc:
        cli.main()
    assert exc.value.code == 0
    assert "ran" in calls


def test_main_install_subcommand(monkeypatch, tmp_path):
    cfg = tmp_path / "claude_desktop_config.json"
    monkeypatch.setattr(cli, "_claude_desktop_config_path", lambda: cfg)
    monkeypatch.setattr(cli.sys, "argv", ["uruguay-mcp", "install"])
    with pytest.raises(SystemExit) as exc:
        cli.main()
    assert exc.value.code == 0
