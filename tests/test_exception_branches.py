"""Tests targeting remaining uncovered exception/race branches.

Targets:
  - queue.py L241-242: FileNotFoundError/JSONDecodeError when reading pending in claim()
  - queue.py L250-252: os.rename race in claim() (lost race path)
  - queue.py L287-288: os.rename OSError in release()
  - queue.py L390-392: os.rename race in complete(), fallback write to done/
  - tools/queue_tool.py L276-280: generic Exception handler
  - __init__.py L29-36: hermes_cli import path + fallback
  - __init__.py L52: _install_skills tmp_dest cleanup on pre-existing tmp
"""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path
from unittest.mock import patch

import pytest

import cyclus.cyclus_config as cyclus_config_module
from cyclus.queue import (
    ClaimResult,
    claim,
    complete,
    post,
    release,
)
from cyclus.tools.queue_tool import cyclus_queue_handler


@pytest.fixture()
def queue_env(tmp_path, monkeypatch):
    cyclus_config_module._config_cache = {
        "project_root": str(tmp_path),
        "omh_backend": "files",
    }
    yield tmp_path
    cyclus_config_module._config_cache = None


# ---------------------------------------------------------------------------
# queue.py L241-242: corrupt pending file
# ---------------------------------------------------------------------------


def test_claim_corrupt_pending_json_returns_not_found(queue_env, tmp_path):
    """If the pending JSON is corrupt, claim should return not_found."""
    post(mode="loop", instance_id="corrupt-pend", kind="TaskExecutionKind", name="x")

    # Corrupt the pending file
    pending_dir = tmp_path / ".cyclus" / "queue" / "pending"
    f = next(pending_dir.glob("*.json"))
    f.write_text("{ this is not valid json {{")

    result = claim(mode="loop", instance_id="corrupt-pend")
    assert result.status == "not_found"


# ---------------------------------------------------------------------------
# queue.py L250-252: os.rename race in claim() — another worker wins
# ---------------------------------------------------------------------------


def test_claim_rename_race_returns_not_found(queue_env, tmp_path):
    """If os.rename fails (FileNotFoundError — another worker claimed it), return not_found."""
    post(mode="loop", instance_id="race-claim", kind="TaskExecutionKind", name="x")

    original_rename = os.rename

    call_count = [0]

    def failing_rename(src, dst):
        # Only fail the claim rename (pending→active), not other renames
        call_count[0] += 1
        if "pending" in str(src) and call_count[0] == 1:
            raise FileNotFoundError("simulated race: another worker got there first")
        return original_rename(src, dst)

    with patch("cyclus.queue.os.rename", side_effect=failing_rename):
        result = claim(mode="loop", instance_id="race-claim")

    assert result.status == "not_found"


# ---------------------------------------------------------------------------
# queue.py L287-288: os.rename OSError in release()
# ---------------------------------------------------------------------------


def test_release_rename_oserror_is_swallowed(queue_env):
    """OSError in os.rename during release() should be silently swallowed."""
    post(mode="loop", instance_id="rel-oserr", kind="TaskExecutionKind", name="x")
    claim(mode="loop", instance_id="rel-oserr")

    original_rename = os.rename

    def failing_rename(src, dst):
        if "active" in str(src) and "pending" in str(dst):
            raise OSError("simulated rename failure during release")
        return original_rename(src, dst)

    with patch("cyclus.queue.os.rename", side_effect=failing_rename):
        # Should not raise
        release(mode="loop", instance_id="rel-oserr")


# ---------------------------------------------------------------------------
# queue.py L390-392: os.rename race in complete()
# ---------------------------------------------------------------------------


def test_complete_rename_race_falls_back_to_done_write(queue_env, tmp_path):
    """If os.rename from active→done raises, complete() writes to done/ directly."""
    post(mode="loop", instance_id="comp-race", kind="TaskExecutionKind", name="x")
    claim(mode="loop", instance_id="comp-race")

    original_rename = os.rename
    call_count = [0]

    def failing_rename(src, dst):
        call_count[0] += 1
        # Fail the rename on first call (the active→done rename in complete())
        if "active" in str(src) and "done" in str(dst) and call_count[0] <= 1:
            raise FileNotFoundError("simulated complete rename race")
        return original_rename(src, dst)

    with patch("cyclus.queue.os.rename", side_effect=failing_rename):
        complete(mode="loop", instance_id="comp-race", terminal_state="PlanComplete")

    # Item should be in done/ (written directly)
    done_dir = tmp_path / ".cyclus" / "queue" / "done"
    done_files = list(done_dir.glob("*.json"))
    assert len(done_files) == 1
    data = json.loads(done_files[0].read_text())
    assert data["status"] == "COMPLETE"


# ---------------------------------------------------------------------------
# tools/queue_tool.py L276-280: generic Exception handler
# ---------------------------------------------------------------------------


def test_queue_tool_generic_exception_returns_error(queue_env):
    """If the underlying queue operation raises an unexpected Exception,
    cyclus_queue_handler should catch it and return a JSON error."""

    with patch("cyclus.tools.queue_tool._file_post", side_effect=RuntimeError("boom")):
        result = json.loads(
            cyclus_queue_handler({
                "action": "post",
                "mode": "loop",
                "instance_id": "exc-test",
            })
        )
    assert "error" in result
    assert "boom" in result["error"]


# ---------------------------------------------------------------------------
# __init__.py L29-36: hermes_cli import success and fallback
# ---------------------------------------------------------------------------


def test_install_skills_hermes_cli_fallback(tmp_path, monkeypatch):
    """When hermes_cli.config is unavailable, falls back to ~/.hermes/skills/cyclus."""
    from cyclus import _install_skills
    import sys

    src = tmp_path / "src"
    skill = src / "my-skill"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text("# test")

    dest = tmp_path / "dest"

    # Remove hermes_cli* from sys.modules so the import inside _install_skills raises
    saved = {k: v for k, v in sys.modules.items() if "hermes_cli" in k}
    for k in saved:
        del sys.modules[k]

    try:
        with patch.dict("sys.modules", {"hermes_cli": None, "hermes_cli.config": None}):
            _install_skills(skills_src_root=src, skills_dest_root=dest)
    finally:
        sys.modules.update(saved)

    assert (dest / "my-skill" / "SKILL.md").exists()


def test_install_skills_tmp_dest_cleanup_before_copy(tmp_path):
    """If a stale ._installing tmp dir exists, it is cleaned before copytree."""
    from cyclus import _install_skills

    src = tmp_path / "src"
    skill = src / "my-skill"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text("# fresh")

    dest = tmp_path / "dest"
    dest.mkdir()

    # Create stale tmp artifact
    stale_tmp = dest / "my-skill._installing"
    stale_tmp.mkdir()
    (stale_tmp / "STALE.md").write_text("stale")

    _install_skills(skills_src_root=src, skills_dest_root=dest)

    # Installed from src, not stale
    assert (dest / "my-skill" / "SKILL.md").read_text() == "# fresh"
    # Stale tmp is gone
    assert not stale_tmp.exists()
