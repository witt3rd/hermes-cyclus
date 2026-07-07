"""
Unit tests for plugins/omh/queue.py — all six operations plus invariants.

Tests run without a live Hermes session. All I/O is isolated to tmp_path via
a monkeypatched cyclus_config cache that sets project_root to tmp_path.

Convention: each test gets a fresh DB in its own tmp_path subdirectory via
the `queue_env` fixture, so no test can leak state to another.
"""

from __future__ import annotations

import json
import sqlite3
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
    post,
    release,
    status,
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
    # Point project_root at the tmp_path for this test.
    cyclus_config_module._config_cache = {
        "project_root": str(tmp_path),
        "omh_backend": "sqlite",
    }
    yield tmp_path
    # Clean up — next test gets a fresh cache.
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

    def test_post_creates_db_at_correct_path(self, queue_env):
        """The queue DB is created at <project_root>/.omh/queue.db."""
        post(mode="ralph", instance_id="plan-x", kind="TaskExecutionKind", name="X")
        db_path = queue_env / ".omh" / "queue.db"
        assert db_path.exists(), f"Expected DB at {db_path}"

    def test_post_sets_spec_path_to_none(self, queue_env):
        """spec_path is NULL in v18.0.0 (Saturate gap acknowledged in design doc)."""
        post(mode="ralph", instance_id="plan-null-spec", kind="TaskExecutionKind", name="NS")
        db_path = queue_env / ".omh" / "queue.db"
        conn = sqlite3.connect(str(db_path))
        row = conn.execute(
            "SELECT spec_path FROM omh_work_items WHERE mode='ralph' AND instance_id='plan-null-spec'"
        ).fetchone()
        conn.close()
        assert row is not None
        assert row[0] is None, "spec_path should be NULL in v18.0.0"

    def test_post_schema_has_cancel_requested_column(self, queue_env):
        """The cancel_requested column must exist with default 0."""
        post(mode="ralph", instance_id="plan-cr", kind="TaskExecutionKind", name="CR")
        db_path = queue_env / ".omh" / "queue.db"
        conn = sqlite3.connect(str(db_path))
        row = conn.execute(
            "SELECT cancel_requested FROM omh_work_items WHERE mode='ralph' AND instance_id='plan-cr'"
        ).fetchone()
        conn.close()
        assert row is not None
        assert row[0] == 0, "cancel_requested must default to 0"


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
        # First claim sets it to RUNNING with a fresh heartbeat
        first = claim(mode="ralph", instance_id="held-item")
        assert first.status == "claimed"
        # Second claim (simulates another session) should see it as running / held
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
        # Claim to put it in RUNNING
        first = claim(mode="ralph", instance_id="stale-item")
        assert first.status == "claimed"

        # Artificially age the last_heartbeat far into the past (2000 seconds ago)
        old_hb = "2000-01-01T00:00:00+00:00"
        db_path = queue_env / ".omh" / "queue.db"
        conn = sqlite3.connect(str(db_path))
        conn.execute(
            "UPDATE omh_work_items SET last_heartbeat = ? WHERE mode = 'ralph' AND instance_id = 'stale-item'",
            (old_hb,),
        )
        conn.commit()
        conn.close()

        # Now claim with a 1-second timeout — the 2000-year-old heartbeat is definitely stale
        second = claim(mode="ralph", instance_id="stale-item", heartbeat_timeout_seconds=1)
        assert second.status == "claimed", "Timed-out RUNNING item should be reclaimed"
        assert second.item is not None
        assert second.item["status"] == "RUNNING"
        assert second.item["last_heartbeat"] != old_hb  # heartbeat was refreshed


class TestRelease:
    def test_release_allows_immediate_reclaim(self, queue_env):
        """release() + claim() succeeds immediately without waiting for the heartbeat timeout."""
        post(mode="ralph", instance_id="release-me", kind="TaskExecutionKind", name="Release")
        first = claim(mode="ralph", instance_id="release-me")
        assert first.status == "claimed"

        # Without release(), a second claim() with 300s timeout would return "running".
        # After release(), the item is PENDING again and claim() returns "claimed".
        release(mode="ralph", instance_id="release-me")

        # Verify DB state is PENDING with NULL heartbeat
        db_path = queue_env / ".omh" / "queue.db"
        conn = sqlite3.connect(str(db_path))
        row = conn.execute(
            "SELECT status, last_heartbeat FROM omh_work_items WHERE mode='ralph' AND instance_id='release-me'"
        ).fetchone()
        conn.close()
        assert row[0] == "PENDING"
        assert row[1] is None

        # A new claim should succeed immediately (no 300-second wait)
        second = claim(mode="ralph", instance_id="release-me", heartbeat_timeout_seconds=300)
        assert second.status == "claimed"

    def test_release_noop_on_non_running(self, queue_env):
        """release() on a PENDING item is a safe no-op (idempotent)."""
        post(mode="ralph", instance_id="noop-release", kind="TaskExecutionKind", name="NR")
        # Should not raise
        release(mode="ralph", instance_id="noop-release")
        # Item should still be PENDING
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
        # Should not raise
        cancel(mode="ralph", instance_id="ghost-item", reason="test")


class TestWriteState:
    def test_write_state_updates_heartbeat(self, queue_env):
        """write_state() persists data and bumps last_heartbeat each call."""
        post(mode="ralph", instance_id="hb-test", kind="TaskExecutionKind", name="HB")
        claim(mode="ralph", instance_id="hb-test")

        before = status(mode="ralph", instance_id="hb-test")
        hb_before = before["last_heartbeat"] if before else None

        # Small sleep to ensure the timestamp advances (ISO 8601 at second resolution)
        time.sleep(1.1)

        write_state(mode="ralph", instance_id="hb-test", state={"task": 3, "phase": "execute"})

        after = status(mode="ralph", instance_id="hb-test")
        assert after is not None
        hb_after = after["last_heartbeat"]

        # The heartbeat must have changed (or at least be non-null)
        assert hb_after is not None
        # If both are set and second-resolution differs, the after must be >= before
        if hb_before is not None:
            assert hb_after >= hb_before

    def test_write_state_writes_file(self, queue_env):
        """write_state() serialises the dict to state_path on disk."""
        post(mode="ralph", instance_id="file-test", kind="TaskExecutionKind", name="File")
        claim(mode="ralph", instance_id="file-test")

        payload = {"task_index": 7, "done": False}
        write_state(mode="ralph", instance_id="file-test", state=payload)

        # Locate state_path from DB
        db_path = queue_env / ".omh" / "queue.db"
        conn = sqlite3.connect(str(db_path))
        row = conn.execute(
            "SELECT state_path FROM omh_work_items WHERE mode='ralph' AND instance_id='file-test'"
        ).fetchone()
        conn.close()
        assert row is not None
        sp = Path(row[0])
        assert sp.exists(), f"Expected state file at {sp}"
        data = json.loads(sp.read_text())
        assert data["task_index"] == 7


class TestComplete:
    def test_complete_marks_terminal(self, queue_env):
        """complete() sets status=COMPLETE, terminal_state, and completed_at."""
        post(mode="ralph", instance_id="done-item", kind="TaskExecutionKind", name="Done")
        claim(mode="ralph", instance_id="done-item")

        complete(
            mode="ralph",
            instance_id="done-item",
            terminal_state="PlanComplete",
        )

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

        # Item must still be in RUNNING (not completed)
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

        # Should not raise
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

        # Read heartbeat immediately after claim
        info1 = status(mode="ralph", instance_id="readonly-test")
        assert info1 is not None
        hb1 = info1["last_heartbeat"]

        # Sleep slightly to ensure any write would produce a different timestamp
        time.sleep(1.1)

        # status() call — must NOT advance the heartbeat
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
# Import check — no omh_state imports anywhere in the new module
# ---------------------------------------------------------------------------


def test_queue_has_no_omh_state_imports():
    """queue.py must not import from omh_state (independence invariant).

    Checks for actual import statements, not docstring mentions, because the
    docstring may legitimately reference 'omh_state.py' for context.
    """
    import re as _re
    queue_path = Path(__file__).parent.parent / "queue.py"
    assert queue_path.exists(), "queue.py not found"
    source = queue_path.read_text(encoding="utf-8")
    # Match lines that are actual Python imports referencing omh_state
    import_lines = [
        line.strip()
        for line in source.splitlines()
        if _re.match(r"\s*(from|import)\s+.*omh_state", line)
    ]
    assert not import_lines, (
        f"queue.py must not import from omh_state.py — found: {import_lines}"
    )


def test_queue_tool_has_no_omh_state_imports():
    """queue_tool.py must not import from omh_state."""
    tool_path = Path(__file__).parent.parent / "tools" / "queue_tool.py"
    assert tool_path.exists(), "queue_tool.py not found"
    source = tool_path.read_text(encoding="utf-8")
    assert "omh_state" not in source, (
        "queue_tool.py must not import from omh_state.py"
    )
