"""Tests for tools/queue_tool.py — cyclus_queue_handler dispatch.

Covers all 8 action branches (post, claim, release, write_state, cancel,
complete, status, dispatch) plus error paths and the unknown-action fallback.
"""

from __future__ import annotations

import json

import pytest

import cyclus.cyclus_config as cyclus_config_module
from cyclus.tools.queue_tool import cyclus_queue_handler


@pytest.fixture()
def queue_env(tmp_path, monkeypatch):
    """Isolate queue I/O to tmp_path and force file backend for each test.

    Clears all backend-selection env vars so _active_backend() returns 'file'
    unconditionally, even when tests run inside a Kanban worker or when
    CYCLUS_BACKEND is set in the environment.
    """
    monkeypatch.delenv("HERMES_KANBAN_TASK", raising=False)
    monkeypatch.delenv("SATURATE_TASK_ID", raising=False)
    monkeypatch.delenv("SATURATE_TASK", raising=False)
    monkeypatch.delenv("CYCLUS_BACKEND", raising=False)
    cyclus_config_module._config_cache = {
        "project_root": str(tmp_path),
        "omh_backend": "files",
    }
    yield tmp_path
    cyclus_config_module._config_cache = None


# ---------------------------------------------------------------------------
# Validation guards
# ---------------------------------------------------------------------------


def test_missing_mode_returns_error(queue_env):
    result = json.loads(cyclus_queue_handler({"action": "post", "instance_id": "x"}))
    assert "error" in result
    assert "mode" in result["error"]


def test_missing_instance_id_returns_error(queue_env):
    result = json.loads(cyclus_queue_handler({"action": "post", "mode": "loop"}))
    assert "error" in result
    assert "instance_id" in result["error"]


# ---------------------------------------------------------------------------
# action=post
# ---------------------------------------------------------------------------


def test_post_action_returns_task_id(queue_env):
    result = json.loads(
        cyclus_queue_handler({
            "action": "post",
            "mode": "loop",
            "instance_id": "plan-001",
            "kind": "TaskExecutionKind",
            "name": "Test plan",
        })
    )
    assert "task_id" in result
    assert isinstance(result["task_id"], str)
    assert len(result["task_id"]) > 0


def test_post_action_idempotent(queue_env):
    args = {"action": "post", "mode": "loop", "instance_id": "plan-idem"}
    r1 = json.loads(cyclus_queue_handler(args))
    r2 = json.loads(cyclus_queue_handler(args))
    assert r1["task_id"] == r2["task_id"]


def test_post_action_defaults_kind(queue_env):
    """post without explicit kind should still succeed."""
    result = json.loads(
        cyclus_queue_handler({
            "action": "post",
            "mode": "loop",
            "instance_id": "plan-default-kind",
        })
    )
    assert "task_id" in result


def test_post_action_with_tags(queue_env):
    result = json.loads(
        cyclus_queue_handler({
            "action": "post",
            "mode": "loop",
            "instance_id": "plan-tagged",
            "tags": ["my-tag"],
        })
    )
    assert "task_id" in result


# ---------------------------------------------------------------------------
# action=claim
# ---------------------------------------------------------------------------


def test_claim_after_post(queue_env):
    cyclus_queue_handler({
        "action": "post",
        "mode": "loop",
        "instance_id": "plan-claim",
    })
    result = json.loads(
        cyclus_queue_handler({
            "action": "claim",
            "mode": "loop",
            "instance_id": "plan-claim",
        })
    )
    assert result["status"] == "claimed"
    assert result["item"] is not None


def test_claim_nonexistent_returns_not_found(queue_env):
    result = json.loads(
        cyclus_queue_handler({
            "action": "claim",
            "mode": "loop",
            "instance_id": "nonexistent-xyz",
        })
    )
    assert result["status"] == "not_found"


def test_claim_with_heartbeat_timeout(queue_env):
    cyclus_queue_handler({
        "action": "post",
        "mode": "loop",
        "instance_id": "plan-hb",
    })
    result = json.loads(
        cyclus_queue_handler({
            "action": "claim",
            "mode": "loop",
            "instance_id": "plan-hb",
            "heartbeat_timeout_seconds": 600,
        })
    )
    assert result["status"] == "claimed"


# ---------------------------------------------------------------------------
# action=release
# ---------------------------------------------------------------------------


def test_release_after_claim(queue_env):
    cyclus_queue_handler({"action": "post", "mode": "loop", "instance_id": "plan-rel"})
    cyclus_queue_handler({"action": "claim", "mode": "loop", "instance_id": "plan-rel"})
    result = json.loads(
        cyclus_queue_handler({"action": "release", "mode": "loop", "instance_id": "plan-rel"})
    )
    assert result == {"ok": True}


def test_release_nonexistent_is_ok(queue_env):
    result = json.loads(
        cyclus_queue_handler({"action": "release", "mode": "loop", "instance_id": "no-such"})
    )
    assert result == {"ok": True}


# ---------------------------------------------------------------------------
# action=write_state
# ---------------------------------------------------------------------------


def test_write_state_after_claim(queue_env):
    cyclus_queue_handler({"action": "post", "mode": "loop", "instance_id": "plan-ws"})
    cyclus_queue_handler({"action": "claim", "mode": "loop", "instance_id": "plan-ws"})
    result = json.loads(
        cyclus_queue_handler({
            "action": "write_state",
            "mode": "loop",
            "instance_id": "plan-ws",
            "state": {"iteration": 1, "score": 0.75},
        })
    )
    assert result == {"ok": True}


def test_write_state_missing_state_field(queue_env):
    cyclus_queue_handler({"action": "post", "mode": "loop", "instance_id": "plan-ws-err"})
    cyclus_queue_handler({"action": "claim", "mode": "loop", "instance_id": "plan-ws-err"})
    result = json.loads(
        cyclus_queue_handler({
            "action": "write_state",
            "mode": "loop",
            "instance_id": "plan-ws-err",
            # no "state" key
        })
    )
    assert "error" in result
    assert "state is required" in result["error"]


def test_write_state_non_dict_state(queue_env):
    cyclus_queue_handler({"action": "post", "mode": "loop", "instance_id": "plan-ws-nd"})
    cyclus_queue_handler({"action": "claim", "mode": "loop", "instance_id": "plan-ws-nd"})
    result = json.loads(
        cyclus_queue_handler({
            "action": "write_state",
            "mode": "loop",
            "instance_id": "plan-ws-nd",
            "state": "not-a-dict",
        })
    )
    assert "error" in result
    assert "must be an object" in result["error"]


# ---------------------------------------------------------------------------
# action=cancel
# ---------------------------------------------------------------------------


def test_cancel_after_post(queue_env):
    cyclus_queue_handler({"action": "post", "mode": "loop", "instance_id": "plan-cancel"})
    result = json.loads(
        cyclus_queue_handler({
            "action": "cancel",
            "mode": "loop",
            "instance_id": "plan-cancel",
            "reason": "test cancellation",
        })
    )
    assert result == {"ok": True}


def test_cancel_nonexistent_is_ok(queue_env):
    result = json.loads(
        cyclus_queue_handler({
            "action": "cancel",
            "mode": "loop",
            "instance_id": "no-such-cancel",
        })
    )
    assert result == {"ok": True}


# ---------------------------------------------------------------------------
# action=complete
# ---------------------------------------------------------------------------


def test_complete_after_claim(queue_env):
    cyclus_queue_handler({"action": "post", "mode": "loop", "instance_id": "plan-done"})
    cyclus_queue_handler({"action": "claim", "mode": "loop", "instance_id": "plan-done"})
    result = json.loads(
        cyclus_queue_handler({
            "action": "complete",
            "mode": "loop",
            "instance_id": "plan-done",
            "terminal_state": "PlanComplete",
        })
    )
    assert result == {"ok": True}


def test_complete_missing_terminal_state(queue_env):
    result = json.loads(
        cyclus_queue_handler({
            "action": "complete",
            "mode": "loop",
            "instance_id": "plan-no-ts",
        })
    )
    assert "error" in result
    assert "terminal_state is required" in result["error"]


def test_complete_with_output(queue_env):
    cyclus_queue_handler({"action": "post", "mode": "loop", "instance_id": "plan-out"})
    cyclus_queue_handler({"action": "claim", "mode": "loop", "instance_id": "plan-out"})
    result = json.loads(
        cyclus_queue_handler({
            "action": "complete",
            "mode": "loop",
            "instance_id": "plan-out",
            "terminal_state": "PlanComplete",
            "output": {"score": 0.95, "notes": "done"},
        })
    )
    assert result == {"ok": True}


def test_complete_human_gated_violation(queue_env):
    cyclus_queue_handler({
        "action": "post",
        "mode": "loop",
        "instance_id": "plan-hg",
        "tags": ["HUMAN_GATED"],
    })
    cyclus_queue_handler({"action": "claim", "mode": "loop", "instance_id": "plan-hg"})
    result = json.loads(
        cyclus_queue_handler({
            "action": "complete",
            "mode": "loop",
            "instance_id": "plan-hg",
            "terminal_state": "PlanComplete",
            "confirmed_by_human": False,
        })
    )
    assert "error" in result
    assert "HumanGatedViolation" in result["error"]


def test_complete_human_gated_with_confirmation(queue_env):
    cyclus_queue_handler({
        "action": "post",
        "mode": "loop",
        "instance_id": "plan-hg-ok",
        "tags": ["HUMAN_GATED"],
    })
    cyclus_queue_handler({"action": "claim", "mode": "loop", "instance_id": "plan-hg-ok"})
    result = json.loads(
        cyclus_queue_handler({
            "action": "complete",
            "mode": "loop",
            "instance_id": "plan-hg-ok",
            "terminal_state": "PlanComplete",
            "confirmed_by_human": True,
        })
    )
    assert result == {"ok": True}


# ---------------------------------------------------------------------------
# action=status
# ---------------------------------------------------------------------------


def test_status_after_post(queue_env):
    cyclus_queue_handler({"action": "post", "mode": "loop", "instance_id": "plan-stat"})
    result = json.loads(
        cyclus_queue_handler({"action": "status", "mode": "loop", "instance_id": "plan-stat"})
    )
    assert result.get("status") == "PENDING"


def test_status_nonexistent_returns_not_found(queue_env):
    result = json.loads(
        cyclus_queue_handler({"action": "status", "mode": "loop", "instance_id": "no-such-stat"})
    )
    assert result == {"found": False}


# ---------------------------------------------------------------------------
# action=dispatch
# ---------------------------------------------------------------------------


def test_dispatch_creates_and_returns_context(queue_env):
    result = json.loads(
        cyclus_queue_handler({
            "action": "dispatch",
            "mode": "loop",
            "instance_id": "plan-dispatch",
            "kind": "TaskExecutionKind",
            "name": "Dispatch test",
        })
    )
    assert result.get("dispatched") is True
    assert result.get("mode") == "loop"
    assert result.get("status") == "PENDING"
    assert "task_id" in result


def test_dispatch_idempotent(queue_env):
    args = {
        "action": "dispatch",
        "mode": "loop",
        "instance_id": "plan-dispatch-idem",
    }
    r1 = json.loads(cyclus_queue_handler(args))
    r2 = json.loads(cyclus_queue_handler(args))
    assert r1["task_id"] == r2["task_id"]
    assert r2["dispatched"] is True


def test_dispatch_already_complete_returns_error(queue_env):
    cyclus_queue_handler({"action": "post", "mode": "loop", "instance_id": "plan-dc-done"})
    cyclus_queue_handler({"action": "claim", "mode": "loop", "instance_id": "plan-dc-done"})
    cyclus_queue_handler({
        "action": "complete",
        "mode": "loop",
        "instance_id": "plan-dc-done",
        "terminal_state": "PlanComplete",
    })
    result = json.loads(
        cyclus_queue_handler({
            "action": "dispatch",
            "mode": "loop",
            "instance_id": "plan-dc-done",
        })
    )
    assert "error" in result
    assert "Cannot dispatch" in result["error"]


# ---------------------------------------------------------------------------
# Unknown action
# ---------------------------------------------------------------------------


def test_unknown_action_raises_value_error(queue_env):
    result = json.loads(
        cyclus_queue_handler({
            "action": "frobnicate",
            "mode": "loop",
            "instance_id": "plan-bad",
        })
    )
    assert "error" in result
    assert "frobnicate" in result["error"]
