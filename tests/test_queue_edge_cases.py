"""Edge-case tests targeting uncovered lines in queue.py.

Covers:
  - Invalid mode validation in all six operations + extras
  - _slugify_instance edge cases (non-string, too-long, empty-normalizing)
  - write_state on non-RUNNING item (no active file)
  - complete on non-existent item
  - Stale heartbeat parse exception path (claim)
  - record_turn / turn_history on invalid mode
  - __init__.py _install_skills edge cases
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

import cyclus.cyclus_config as cyclus_config_module
from cyclus.queue import (
    cancel,
    claim,
    complete,
    get,
    post,
    read_state,
    record_turn,
    release,
    status,
    turn_history,
    write_state,
)


@pytest.fixture()
def queue_env(tmp_path, monkeypatch):
    cyclus_config_module._config_cache = {
        "project_root": str(tmp_path),
        "omh_backend": "files",
    }
    yield tmp_path
    cyclus_config_module._config_cache = None


# ---------------------------------------------------------------------------
# _slugify_instance validation
# ---------------------------------------------------------------------------


def test_post_non_string_instance_id_raises(queue_env):
    with pytest.raises(ValueError, match="must be a string"):
        post(mode="ralph", instance_id=123, kind="TaskExecutionKind", name="x")  # type: ignore[arg-type]


def test_post_too_long_instance_id_raises(queue_env):
    long_id = "a" * 300
    with pytest.raises(ValueError, match="too long"):
        post(mode="ralph", instance_id=long_id, kind="TaskExecutionKind", name="x")


def test_post_empty_normalizing_instance_id_raises(queue_env):
    # A string composed entirely of special chars normalizes to empty slug
    with pytest.raises(ValueError, match="normalizes to empty slug"):
        post(mode="ralph", instance_id="---!!!", kind="TaskExecutionKind", name="x")


# ---------------------------------------------------------------------------
# Invalid mode in all six operations (+ extras)
# ---------------------------------------------------------------------------


def test_post_invalid_mode_raises(queue_env):
    with pytest.raises(ValueError, match="Invalid mode name"):
        post(mode="bad mode!", instance_id="x", kind="TaskExecutionKind", name="x")


def test_claim_invalid_mode_raises(queue_env):
    with pytest.raises(ValueError, match="Invalid mode name"):
        claim(mode="bad mode!", instance_id="x")


def test_release_invalid_mode_raises(queue_env):
    with pytest.raises(ValueError, match="Invalid mode name"):
        release(mode="bad mode!", instance_id="x")


def test_write_state_invalid_mode_raises(queue_env):
    with pytest.raises(ValueError, match="Invalid mode name"):
        write_state(mode="bad mode!", instance_id="x", state={"k": 1})


def test_cancel_invalid_mode_raises(queue_env):
    with pytest.raises(ValueError, match="Invalid mode name"):
        cancel(mode="bad mode!", instance_id="x")


def test_complete_invalid_mode_raises(queue_env):
    with pytest.raises(ValueError, match="Invalid mode name"):
        complete(mode="bad mode!", instance_id="x", terminal_state="Done")


def test_status_invalid_mode_raises(queue_env):
    with pytest.raises(ValueError, match="Invalid mode name"):
        status(mode="bad mode!", instance_id="x")


def test_read_state_invalid_mode_raises(queue_env):
    with pytest.raises(ValueError, match="Invalid mode name"):
        read_state(mode="bad mode!", instance_id="x")


def test_record_turn_invalid_mode_raises(queue_env):
    with pytest.raises(ValueError, match="Invalid mode name"):
        record_turn(mode="bad mode!", instance_id="x", turn={})


def test_turn_history_invalid_mode_raises(queue_env):
    with pytest.raises(ValueError, match="Invalid mode name"):
        turn_history(mode="bad mode!", instance_id="x")


# ---------------------------------------------------------------------------
# write_state on item that has no active file
# ---------------------------------------------------------------------------


def test_write_state_on_non_running_item_raises(queue_env):
    """write_state requires an active (RUNNING) item; PENDING item should fail."""
    post(mode="ralph", instance_id="ws-pending", kind="TaskExecutionKind", name="x")
    # Item is PENDING, not claimed → no active file
    with pytest.raises(ValueError, match="No active work item"):
        write_state(mode="ralph", instance_id="ws-pending", state={"k": 1})


# ---------------------------------------------------------------------------
# complete on non-existent item
# ---------------------------------------------------------------------------


def test_complete_nonexistent_raises(queue_env):
    with pytest.raises(ValueError, match="No work item found"):
        complete(mode="ralph", instance_id="no-such-99", terminal_state="Done")


# ---------------------------------------------------------------------------
# turn_history returns [] when no turns file exists
# ---------------------------------------------------------------------------


def test_turn_history_no_file(queue_env):
    post(mode="ralph", instance_id="th-none", kind="TaskExecutionKind", name="x")
    result = turn_history(mode="ralph", instance_id="th-none")
    assert result == []


# ---------------------------------------------------------------------------
# Claim: stale heartbeat parse exception path
# ---------------------------------------------------------------------------


def test_claim_reclaims_active_with_corrupt_heartbeat(queue_env, tmp_path):
    """When last_heartbeat is unparseable, the item should be treated as stale."""
    # Post and claim to move item to active/
    post(mode="ralph", instance_id="hb-corrupt", kind="TaskExecutionKind", name="x")
    claim(mode="ralph", instance_id="hb-corrupt")

    # Corrupt the heartbeat timestamp in the active file
    active_dir = tmp_path / ".cyclus" / "queue" / "active"
    active_file = next(active_dir.glob("*.json"))
    data = json.loads(active_file.read_text())
    data["last_heartbeat"] = "not-a-valid-iso-timestamp"
    active_file.write_text(json.dumps(data))

    # Claim again — corrupt heartbeat → treated as stale → re-claimed
    result = claim(mode="ralph", instance_id="hb-corrupt")
    assert result.status == "claimed"


# ---------------------------------------------------------------------------
# __init__.py: _install_skills edge cases
# ---------------------------------------------------------------------------


def test_install_skills_no_src_dir(tmp_path):
    """If skills_src_root doesn't exist, _install_skills returns early."""
    from cyclus import _install_skills

    missing_src = tmp_path / "no-skills-here"
    dest = tmp_path / "dest-skills"
    _install_skills(skills_src_root=missing_src, skills_dest_root=dest)
    # Should not create dest or raise
    assert not dest.exists()


def test_install_skills_skips_existing_skill(tmp_path):
    """If dest skill already exists, installation is skipped."""
    from cyclus import _install_skills

    src = tmp_path / "src-skills"
    skill_dir = src / "my-skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("# my skill")

    dest = tmp_path / "dest-skills"
    dest_skill = dest / "my-skill"
    dest_skill.mkdir(parents=True)
    (dest_skill / "SKILL.md").write_text("# existing — must not be overwritten")

    _install_skills(skills_src_root=src, skills_dest_root=dest)
    # Existing skill must be unchanged
    assert (dest_skill / "SKILL.md").read_text() == "# existing — must not be overwritten"


def test_install_skills_fresh_install(tmp_path):
    """New skill is copied to dest when dest doesn't exist yet."""
    from cyclus import _install_skills

    src = tmp_path / "src-skills"
    skill_dir = src / "fresh-skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("# fresh skill content")

    dest = tmp_path / "dest-skills"

    _install_skills(skills_src_root=src, skills_dest_root=dest)
    assert (dest / "fresh-skill" / "SKILL.md").read_text() == "# fresh skill content"


def test_install_skills_handles_file_not_dir(tmp_path):
    """Files in src are skipped (only directories become skills)."""
    from cyclus import _install_skills

    src = tmp_path / "src-skills"
    src.mkdir()
    (src / "not-a-skill.txt").write_text("random file")
    skill_dir = src / "real-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("# real")

    dest = tmp_path / "dest-skills"
    _install_skills(skills_src_root=src, skills_dest_root=dest)
    assert (dest / "real-skill").exists()
    assert not (dest / "not-a-skill.txt").exists()


def test_install_skills_cleans_tmp_on_error(tmp_path, monkeypatch):
    """If copytree fails partway through, the tmp dir is cleaned up."""
    from cyclus import _install_skills

    src = tmp_path / "src-skills"
    skill_dir = src / "broken-skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("# broken")

    dest = tmp_path / "dest-skills"

    # Make shutil.copytree raise to simulate a failure
    original_copytree = shutil.copytree

    def failing_copytree(src_arg, dst_arg, **kwargs):
        raise OSError("simulated copytree failure")

    monkeypatch.setattr(shutil, "copytree", failing_copytree)

    _install_skills(skills_src_root=src, skills_dest_root=dest)
    # Dest skill should NOT exist — failed install cleaned up
    assert not (dest / "broken-skill").exists()
    # No tmp artifact left behind
    tmp_remnant = dest / "broken-skill._installing"
    assert not tmp_remnant.exists()
