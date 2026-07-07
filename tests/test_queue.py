"""
Unit tests for queue.py — all six operations plus invariants.

Tests run without a live Hermes session. All I/O is isolated to tmp_path via
a monkeypatched cyclus_config cache that sets project_root to tmp_path.

Convention: each test gets a fresh queue in its own tmp_path subdirectory via
the `queue_env` fixture, so no test can leak state to another.
"""

from __future__ import annotations

import json
import threading
import time
from pathlib import Path

import pytest

import cyclus.cyclus_config as cyclus_config_module
from cyclus.queue import (
    ClaimResult,
    HumanGatedViolation,
    cancel,
    claim,
    complete,
    counts,
    get,
    post,
    read_state,
    record_turn,
    release,
    status,
    turn_history,
    write_state,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def queue_env(tmp_path, monkeypatch):
    """Isolate every queue operation to tmp_path by pointing project_root there.

    Also resets the cyclus_config cache before and after each test so config
    mutations from one test cannot leak into the next.
    """
    cyclus_config_module._config_cache = {
        "project_root": str(tmp_path),
        "omh_backend": "files",
    }
    yield tmp_path
    cyclus_config_module._config_cache = None


# ---------------------------------------------------------------------------
# T1.3 — Required tests
# ---------------------------------------------------------------------------


class TestPost:
    def test_post_is_idempotent(self, queue_env):
        """Calling post() twice with the same (mode, instance_id) returns the same task_id."""
        task_id_1 = post(mode="ralph", instance_id="plan-alpha", kind="TaskExecutionKind", name="Alpha Plan")
        task_id_2 = post(mode="ralph", instance_id="plan-alpha", kind="TaskExecutionKind", name="Alpha Plan (dup)")
        assert task_id_1 == task_id_2

    def test_post_different_instance_ids_are_distinct(self, queue_env):
        """Different instance_ids produce different task_ids."""
        task_id_1 = post(mode="ralph", instance_id="plan-a", kind="TaskExecutionKind", name="A")
        task_id_2 = post(mode="ralph", instance_id="plan-b", kind="TaskExecutionKind", name="B")
        assert task_id_1 != task_id_2

    def test_post_creates_queue_dirs(self, queue_env):
        """The queue directories are created at <project_root>/.cyclus/queue/."""
        post(mode="ralph", instance_id="plan-x", kind="TaskExecutionKind", name="X")
        for sub in ("pending", "active", "done"):
            assert (queue_env / ".cyclus" / "queue" / sub).exists()

    def test_post_sets_spec_path_to_none(self, queue_env):
        """spec_path is None in v18.0.0 (Saturate gap acknowledged in design doc)."""
        post(mode="ralph", instance_id="plan-null-spec", kind="TaskExecutionKind", name="NS")
        info = status(mode="ralph", instance_id="plan-null-spec")
        assert info is not None
        assert info["spec_path"] is None

    def test_post_schema_has_cancel_requested_field(self, queue_env):
        """The cancel_requested field must exist with default 0."""
        post(mode="ralph", instance_id="plan-cr", kind="TaskExecutionKind", name="CR")
        info = status(mode="ralph", instance_id="plan-cr")
        assert info is not None
        assert info["cancel_requested"] == 0


class TestClaim:
    def test_claim_returns_claimed_for_pending(self, queue_env):
        """claim() on a PENDING item returns status='claimed' with a populated item dict."""
        post(mode="ralph", instance_id="pending-test", kind="TaskExecutionKind", name="Pending")
        result = claim(mode="ralph", instance_id="pending-test")
        assert isinstance(result, ClaimResult)
        assert result.status == "claimed"
        assert result.item is not None
        assert result.item["status"] == "RUNNING"
        assert result.item["last_heartbeat"] is not None

    def test_claim_returns_running_for_held_item(self, queue_env):
        """claim() on an item in RUNNING with a fresh heartbeat returns status='running'."""
        post(mode="ralph", instance_id="held-item", kind="TaskExecutionKind", name="Held")
        first = claim(mode="ralph", instance_id="held-item")
        assert first.status == "claimed"
        second = claim(mode="ralph", instance_id="held-item", heartbeat_timeout_seconds=300)
        assert second.status == "running"
        assert second.item is None

    def test_claim_returns_not_found_for_absent_item(self, queue_env):
        """claim() for a (mode, instance_id) that does not exist returns status='not_found'."""
        result = claim(mode="ralph", instance_id="does-not-exist")
        assert result.status == "not_found"
        assert result.item is None

    def test_claim_reclaims_timed_out(self, queue_env):
        """claim() reclaims a RUNNING item whose heartbeat has exceeded the timeout."""
        post(mode="ralph", instance_id="stale-item", kind="TaskExecutionKind", name="Stale")
        first = claim(mode="ralph", instance_id="stale-item")
        assert first.status == "claimed"

        # Force the active JSON to have a very old heartbeat
        active_path = queue_env / ".cyclus" / "queue" / "active" / "ralph--stale-item.json"
        data = json.loads(active_path.read_text())
        data["last_heartbeat"] = "2000-01-01T00:00:00+00:00"
        active_path.write_text(json.dumps(data))

        second = claim(mode="ralph", instance_id="stale-item", heartbeat_timeout_seconds=1)
        assert second.status == "claimed", "Timed-out RUNNING item should be reclaimed"
        assert second.item is not None
        assert second.item["status"] == "RUNNING"
        assert second.item["last_heartbeat"] != "2000-01-01T00:00:00+00:00"


class TestRelease:
    def test_release_allows_immediate_reclaim(self, queue_env):
        """release() + claim() succeeds immediately without waiting for the heartbeat timeout."""
        post(mode="ralph", instance_id="release-me", kind="TaskExecutionKind", name="Release")
        first = claim(mode="ralph", instance_id="release-me")
        assert first.status == "claimed"

        release(mode="ralph", instance_id="release-me")

        # After release(), item is PENDING — verify via status()
        info = status(mode="ralph", instance_id="release-me")
        assert info is not None
        assert info["status"] == "PENDING"
        assert info["last_heartbeat"] is None

        # A new claim should succeed immediately
        second = claim(mode="ralph", instance_id="release-me", heartbeat_timeout_seconds=300)
        assert second.status == "claimed"

    def test_release_noop_on_non_running(self, queue_env):
        """release() on a PENDING item is a safe no-op (idempotent)."""
        post(mode="ralph", instance_id="noop-release", kind="TaskExecutionKind", name="NR")
        release(mode="ralph", instance_id="noop-release")
        info = status(mode="ralph", instance_id="noop-release")
        assert info is not None
        assert info["status"] == "PENDING"


class TestCancel:
    def test_cancel_sets_flag(self, queue_env):
        """cancel() sets cancel_requested=1; status() returns it."""
        post(mode="ralph", instance_id="cancel-me", kind="TaskExecutionKind", name="Cancel")
        claim(mode="ralph", instance_id="cancel-me")
        cancel(mode="ralph", instance_id="cancel-me", reason="test request")
        info = status(mode="ralph", instance_id="cancel-me")
        assert info is not None
        assert info["cancel_requested"] == 1

    def test_cancel_noop_on_missing_item(self, queue_env):
        """cancel() on a non-existent item is a safe no-op (does not raise)."""
        cancel(mode="ralph", instance_id="ghost-item", reason="test")


class TestWriteState:
    def test_write_state_updates_heartbeat(self, queue_env):
        """write_state() persists data and bumps last_heartbeat each call."""
        post(mode="ralph", instance_id="hb-test", kind="TaskExecutionKind", name="HB")
        claim(mode="ralph", instance_id="hb-test")

        before = status(mode="ralph", instance_id="hb-test")
        hb_before = before["last_heartbeat"] if before else None

        time.sleep(1.1)

        write_state(mode="ralph", instance_id="hb-test", state={"task": 3, "phase": "execute"})

        after = status(mode="ralph", instance_id="hb-test")
        assert after is not None
        hb_after = after["last_heartbeat"]
        assert hb_after is not None
        if hb_before is not None:
            assert hb_after >= hb_before

    def test_write_state_writes_file(self, queue_env):
        """write_state() serialises the dict to state_path on disk."""
        post(mode="ralph", instance_id="file-test", kind="TaskExecutionKind", name="File")
        claim(mode="ralph", instance_id="file-test")

        payload = {"task_index": 7, "done": False}
        write_state(mode="ralph", instance_id="file-test", state=payload)

        info = status(mode="ralph", instance_id="file-test")
        assert info is not None
        sp = Path(info["state_path"])
        assert sp.exists()
        data = json.loads(sp.read_text())
        assert data["task_index"] == 7


class TestComplete:
    def test_complete_marks_terminal(self, queue_env):
        """complete() sets status=COMPLETE, terminal_state, and completed_at."""
        post(mode="ralph", instance_id="done-item", kind="TaskExecutionKind", name="Done")
        claim(mode="ralph", instance_id="done-item")
        complete(mode="ralph", instance_id="done-item", terminal_state="PlanComplete")
        info = status(mode="ralph", instance_id="done-item")
        assert info is not None
        assert info["status"] == "COMPLETE"
        assert info["terminal_state"] == "PlanComplete"
        assert info["completed_at"] is not None

    def test_complete_raises_on_human_gated_without_confirmation(self, queue_env):
        """complete() raises HumanGatedViolation for HUMAN_GATED items if confirmed_by_human=False."""
        post(
            mode="deep-interview",
            instance_id="interview-001",
            kind="ClarificationKind",
            name="Spec Interview",
            tags=["HUMAN_GATED"],
        )
        claim(mode="deep-interview", instance_id="interview-001")

        with pytest.raises(HumanGatedViolation, match="HUMAN_GATED"):
            complete(
                mode="deep-interview",
                instance_id="interview-001",
                terminal_state="SpecConfirmed",
                confirmed_by_human=False,
            )

        info = status(mode="deep-interview", instance_id="interview-001")
        assert info is not None
        assert info["status"] == "RUNNING"

    def test_complete_human_gated_with_confirmation_succeeds(self, queue_env):
        """complete() with confirmed_by_human=True succeeds for HUMAN_GATED items."""
        post(
            mode="deep-interview",
            instance_id="interview-002",
            kind="ClarificationKind",
            name="Spec Interview 2",
            tags=["HUMAN_GATED"],
        )
        claim(mode="deep-interview", instance_id="interview-002")
        complete(
            mode="deep-interview",
            instance_id="interview-002",
            terminal_state="SpecConfirmed",
            confirmed_by_human=True,
        )
        info = status(mode="deep-interview", instance_id="interview-002")
        assert info is not None
        assert info["status"] == "COMPLETE"
        assert info["terminal_state"] == "SpecConfirmed"


class TestStatus:
    def test_status_is_readonly(self, queue_env):
        """status() does not update last_heartbeat — it is purely read-only."""
        post(mode="ralph", instance_id="readonly-test", kind="TaskExecutionKind", name="RO")
        claim(mode="ralph", instance_id="readonly-test")

        info1 = status(mode="ralph", instance_id="readonly-test")
        assert info1 is not None
        hb1 = info1["last_heartbeat"]

        time.sleep(1.1)

        info2 = status(mode="ralph", instance_id="readonly-test")
        assert info2 is not None
        hb2 = info2["last_heartbeat"]

        assert hb1 == hb2, (
            f"status() must not update last_heartbeat: before={hb1!r}, after={hb2!r}"
        )

    def test_status_returns_none_for_absent(self, queue_env):
        """status() returns None when no item exists for (mode, instance_id)."""
        result = status(mode="ralph", instance_id="absent-item")
        assert result is None

    def test_status_reflects_cancel_requested(self, queue_env):
        """status() after cancel() shows cancel_requested=1."""
        post(mode="ralph", instance_id="cancel-status", kind="TaskExecutionKind", name="CS")
        claim(mode="ralph", instance_id="cancel-status")
        cancel(mode="ralph", instance_id="cancel-status")
        info = status(mode="ralph", instance_id="cancel-status")
        assert info is not None
        assert info["cancel_requested"] == 1


# ---------------------------------------------------------------------------
# Additional coverage — ClaimResult for completed items
# ---------------------------------------------------------------------------


class TestClaimTerminalItem:
    def test_claim_returns_not_found_for_completed_item(self, queue_env):
        """A COMPLETE item cannot be claimed — claim() returns 'not_found'."""
        post(mode="ralph", instance_id="already-done", kind="TaskExecutionKind", name="Done")
        claim(mode="ralph", instance_id="already-done")
        complete(mode="ralph", instance_id="already-done", terminal_state="PlanComplete")
        result = claim(mode="ralph", instance_id="already-done")
        assert result.status == "not_found", (
            "Completed items should be un-claimable; got status={!r}".format(result.status)
        )


# ---------------------------------------------------------------------------
# Import check — no omh_state imports, no sqlite3 in queue.py
# ---------------------------------------------------------------------------


def test_queue_has_no_omh_state_imports():
    """queue.py must not import from omh_state (independence invariant)."""
    import re as _re
    queue_path = Path(__file__).parent.parent / "queue.py"
    assert queue_path.exists()
    source = queue_path.read_text(encoding="utf-8")
    import_lines = [
        line.strip()
        for line in source.splitlines()
        if _re.match(r"\s*(from|import)\s+.*omh_state", line)
    ]
    assert not import_lines, f"queue.py must not import from omh_state.py — found: {import_lines}"


def test_queue_tool_has_no_omh_state_imports():
    """queue_tool.py must not import from omh_state."""
    tool_path = Path(__file__).parent.parent / "tools" / "queue_tool.py"
    assert tool_path.exists()
    source = tool_path.read_text(encoding="utf-8")
    assert "omh_state" not in source


def test_queue_has_no_sqlite3_import():
    """queue.py must not import sqlite3 (file-based backend, no DB)."""
    queue_path = Path(__file__).parent.parent / "queue.py"
    source = queue_path.read_text(encoding="utf-8")
    import_lines = [
        line.strip()
        for line in source.splitlines()
        if "import sqlite3" in line
    ]
    assert not import_lines, f"queue.py must not import sqlite3 — found: {import_lines}"


# ---------------------------------------------------------------------------
# Atomic claim test — two threads, one winner
# ---------------------------------------------------------------------------


def test_file_queue_claim_is_atomic(queue_env):
    """Two concurrent claim() calls on one pending item — exactly one wins."""
    post(mode="ralph", instance_id="atomic-test", kind="TaskExecutionKind", name="Atomic")

    results = []

    def do_claim():
        r = claim(mode="ralph", instance_id="atomic-test")
        results.append(r.status)

    t1 = threading.Thread(target=do_claim)
    t2 = threading.Thread(target=do_claim)
    t1.start(); t2.start()
    t1.join(); t2.join()

    assert len(results) == 2
    assert results.count("claimed") == 1
    # The loser sees the item already active (fresh heartbeat) → "running"
    assert results.count("not_found") + results.count("running") == 1


# ---------------------------------------------------------------------------
# Additional operations
# ---------------------------------------------------------------------------


class TestReadState:
    def test_read_state_returns_empty_before_write(self, queue_env):
        post(mode="ralph", instance_id="rs-test", kind="TaskExecutionKind", name="RS")
        assert read_state(mode="ralph", instance_id="rs-test") == {}

    def test_read_state_after_write(self, queue_env):
        post(mode="ralph", instance_id="rs-written", kind="TaskExecutionKind", name="RSW")
        claim(mode="ralph", instance_id="rs-written")
        write_state(mode="ralph", instance_id="rs-written", state={"x": 42})
        assert read_state(mode="ralph", instance_id="rs-written") == {"x": 42}


class TestRecordTurn:
    def test_record_turn_appends(self, queue_env):
        post(mode="ralph", instance_id="turn-test", kind="TaskExecutionKind", name="TT")
        claim(mode="ralph", instance_id="turn-test")
        record_turn(mode="ralph", instance_id="turn-test", turn={"n": 1})
        record_turn(mode="ralph", instance_id="turn-test", turn={"n": 2})
        history = turn_history(mode="ralph", instance_id="turn-test")
        assert len(history) == 2
        assert history[0]["n"] == 1
        assert history[1]["n"] == 2


class TestCounts:
    def test_counts_reflects_queue_state(self, queue_env):
        post(mode="ralph", instance_id="count-a", kind="TaskExecutionKind", name="A")
        post(mode="ralph", instance_id="count-b", kind="TaskExecutionKind", name="B")
        c = counts()
        assert c["pending"] == 2
        assert c["active"] == 0
        claim(mode="ralph", instance_id="count-a")
        c = counts()
        assert c["pending"] == 1
        assert c["active"] == 1


class TestGet:
    def test_get_is_alias_for_status(self, queue_env):
        post(mode="ralph", instance_id="get-test", kind="TaskExecutionKind", name="GT")
        assert get(mode="ralph", instance_id="get-test") == status(mode="ralph", instance_id="get-test")
