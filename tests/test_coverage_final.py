"""Tests for uncovered lines in cyclus_config.py and __init__.py.

Targets:
  - cyclus_config.py L27: _find_config_file() returning None
  - __init__.py L29-33: _install_skills() with hermes_cli success path (skills_dest_root=None)
  - __init__.py L36: _install_skills() fallback when hermes_cli unavailable + skills_dest_root=None
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

import cyclus.cyclus_config as cyclus_config_module
from cyclus.cyclus_config import _find_config_file, get_config, reload_config


@pytest.fixture(autouse=True)
def reset_config_cache():
    original = cyclus_config_module._config_cache
    yield
    cyclus_config_module._config_cache = original


# ---------------------------------------------------------------------------
# cyclus_config.py L27: _find_config_file returns None when nothing exists
# ---------------------------------------------------------------------------


def test_find_config_file_returns_none_when_missing(tmp_path, monkeypatch):
    """_find_config_file() returns None when neither candidate exists."""
    import cyclus.cyclus_config as mod

    # Patch Path.exists to always return False so real _find_config_file sees nothing
    monkeypatch.setattr(Path, "exists", lambda self: False)
    result = mod._find_config_file()
    assert result is None


def test_get_config_when_find_returns_none(monkeypatch):
    """get_config() returns {} when _find_config_file() returns None."""
    import cyclus.cyclus_config as mod
    mod._config_cache = None
    monkeypatch.setattr(mod, "_find_config_file", lambda: None)
    result = get_config()
    assert result == {}


# ---------------------------------------------------------------------------
# __init__.py L29-33: _install_skills with skills_dest_root=None + hermes_cli works
# ---------------------------------------------------------------------------


def test_install_skills_with_hermes_cli_success(tmp_path, monkeypatch):
    """When hermes_cli.config is importable, _install_skills uses get_hermes_home()."""
    from cyclus import _install_skills

    src = tmp_path / "src"
    skill = src / "test-skill"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text("# test skill")

    fake_hermes_home = tmp_path / "fake-hermes-home"
    expected_dest = fake_hermes_home / "skills" / "cyclus"

    # Mock hermes_cli.config.get_hermes_home to return our tmp path
    mock_get_hermes_home = MagicMock(return_value=fake_hermes_home)
    mock_hermes_cli_config = MagicMock()
    mock_hermes_cli_config.get_hermes_home = mock_get_hermes_home
    mock_hermes_cli = MagicMock()
    mock_hermes_cli.config = mock_hermes_cli_config

    with patch.dict(
        "sys.modules",
        {
            "hermes_cli": mock_hermes_cli,
            "hermes_cli.config": mock_hermes_cli_config,
        },
    ):
        # Pass skills_dest_root=None to trigger the hermes_cli import branch
        _install_skills(skills_src_root=src, skills_dest_root=None)

    # The skill should have been installed to the hermes-home derived path
    assert (expected_dest / "test-skill" / "SKILL.md").exists()


# ---------------------------------------------------------------------------
# __init__.py L36: fallback when hermes_cli is unavailable + skills_dest_root=None
# ---------------------------------------------------------------------------


def test_install_skills_fallback_when_hermes_cli_missing(tmp_path, monkeypatch):
    """When hermes_cli is not importable, falls back to ~/.hermes/skills/cyclus."""
    from cyclus import _install_skills

    src = tmp_path / "src"
    skill = src / "fallback-skill"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text("# fallback skill")

    # We can't easily redirect Path.home() here, so pass explicit dest
    # but trigger the except branch by making the import fail at the module level.
    # The cleanest way: pass skills_dest_root=None but patch sys.modules
    # to make hermes_cli unavailable, then capture where install goes by
    # patching Path.home() temporarily.

    fake_home = tmp_path / "fake-home"
    expected_dest = fake_home / ".hermes" / "skills" / "cyclus"

    import sys
    # Remove hermes_cli from sys.modules to force ImportError
    orig_modules = {k: v for k, v in sys.modules.items() if "hermes_cli" in k}
    for k in list(orig_modules.keys()):
        del sys.modules[k]

    try:
        with patch("pathlib.Path.home", return_value=fake_home):
            _install_skills(skills_src_root=src, skills_dest_root=None)
    finally:
        # Restore
        sys.modules.update(orig_modules)

    assert (expected_dest / "fallback-skill" / "SKILL.md").exists()
