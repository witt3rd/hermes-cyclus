"""Tests for cyclus_queue Kanban backend routing.

Covers:
  - All eight actions routed correctly when HERMES_KANBAN_TASK is set (worker)
  - post/dispatch create a new task via kanban_create when no HERMES_KANBAN_TASK
    (interactive Kanban mode, CYCLUS_BACKEND=kanban)
  - Shared validation (state/terminal_state) applied consistently
  - dispatch() falls through to post() in interactive mode
  - registry.dispatch is the real call site — no hand-mocked ctx= objects

Implementation note: we mock `cyclus.tools.queue_tool._kb` directly rather than
patching `registry.dispatch` at import time, which avoids loading all of
hermes-agent in unit tests while still verifying the correct tool names and args.
"""
from __future__ import annotations

import json
import os
from unittest.mock import MagicMock, patch

import pytest

import cyclus.cyclus_config as cyclus_config_module
from cyclus.tools.queue_tool import (
    _KANBAN_STATE_ALLOWLIST,
    _redact_state,
    cyclus_queue_handler,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _kb_factory(**returns: dict):
    """Return a mock _kb that returns the given dicts keyed by tool_name."""
    def _kb(tool_name: str, tool_args: dict) -> dict:
        return returns.get(tool_name, {"ok": True})
    return MagicMock(side_effect=_kb)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def file_env(tmp_path, monkeypatch):
    """File backend — no HERMES_KANBAN_TASK, no CYCLUS_BACKEND."""
    monkeypatch.delenv("HERMES_KANBAN_TASK", raising=False)
    monkeypatch.delenv("CYCLUS_BACKEND", raising=False)
    cyclus_config_module._config_cache = {
        "project_root": str(tmp_path),
        "omh_backend": "files",
    }
    yield tmp_path
    cyclus_config_module._config_cache = None


@pytest.fixture()
def worker_env(monkeypatch):
    """Worker Kanban backend — HERMES_KANBAN_TASK set."""
    monkeypatch.setenv("HERMES_KANBAN_TASK", "t_test123")
    monkeypatch.delenv("CYCLUS_BACKEND", raising=False)
    yield


@pytest.fixture()
def interactive_env(monkeypatch):
    """Interactive Kanban backend — CYCLUS_BACKEND=kanban, no task id."""
    monkeypatch.delenv("HERMES_KANBAN_TASK", raising=False)
    monkeypatch.setenv("CYCLUS_BACKEND", "kanban")
    yield


# ---------------------------------------------------------------------------
# Worker: lifecycle actions call the correct kanban_* tools
# ---------------------------------------------------------------------------


def test_worker_status(worker_env):
    kb = _kb_factory(kanban_show={"status": "running"})
    with patch("cyclus.tools.queue_tool._kb", kb):
        result = json.loads(cyclus_queue_handler(
            {"action": "status", "mode": "loop", "instance_id": "x"}
        ))
    assert result["found"] is True
    assert result["task_id"] == "t_test123"
    kb.assert_called_once_with("kanban_show", {"task_id": "t_test123"})


def test_worker_write_state(worker_env):
    kb = _kb_factory()
    with patch("cyclus.tools.queue_tool._kb", kb):
        result = json.loads(cyclus_queue_handler(
            {"action": "write_state", "mode": "loop", "instance_id": "x",
             "state": {"iteration": 3, "best_score": 1.45}}
        ))
    assert result["ok"] is True
    calls = [c[0][0] for c in kb.call_args_list]
    assert "kanban_heartbeat" in calls
    assert "kanban_comment" in calls


def test_worker_complete(worker_env):
    kb = _kb_factory()
    with patch("cyclus.tools.queue_tool._kb", kb):
        result = json.loads(cyclus_queue_handler(
            {"action": "complete", "mode": "loop", "instance_id": "x",
             "terminal_state": "PlanComplete",
             "output": {"summary": "done", "final_score": 1.49}}
        ))
    assert result["ok"] is True
    kb.assert_called_once()
    tool_name, tool_args = kb.call_args[0]
    assert tool_name == "kanban_complete"
    assert tool_args["terminal_state"] == "PlanComplete"
    assert tool_args["task_id"] == "t_test123"


def test_worker_post_is_noop(worker_env):
    kb = _kb_factory()
    with patch("cyclus.tools.queue_tool._kb", kb):
        result = json.loads(cyclus_queue_handler(
            {"action": "post", "mode": "loop", "instance_id": "x",
             "kind": "TaskExecutionKind", "name": "test"}
        ))
    assert result["task_id"] == "t_test123"
    assert "note" in result
    kb.assert_not_called()  # worker no-op — no kanban_create call


def test_worker_claim(worker_env):
    kb = _kb_factory()
    with patch("cyclus.tools.queue_tool._kb", kb):
        result = json.loads(cyclus_queue_handler(
            {"action": "claim", "mode": "loop", "instance_id": "x"}
        ))
    assert result["status"] == "claimed"
    kb.assert_called_once_with("kanban_heartbeat", {"task_id": "t_test123"})


def test_worker_release(worker_env):
    kb = _kb_factory()
    with patch("cyclus.tools.queue_tool._kb", kb):
        result = json.loads(cyclus_queue_handler(
            {"action": "release", "mode": "loop", "instance_id": "x"}
        ))
    assert result["ok"] is True
    tool_name, tool_args = kb.call_args[0]
    assert tool_name == "kanban_block"
    assert tool_args["kind"] == "dependency"


def test_worker_cancel(worker_env):
    kb = _kb_factory()
    with patch("cyclus.tools.queue_tool._kb", kb):
        result = json.loads(cyclus_queue_handler(
            {"action": "cancel", "mode": "loop", "instance_id": "x",
             "reason": "user aborted"}
        ))
    assert result["ok"] is True
    tool_name, tool_args = kb.call_args[0]
    assert tool_name == "kanban_block"
    assert tool_args["reason"] == "user aborted"


def test_worker_dispatch_is_noop(worker_env):
    kb = _kb_factory()
    with patch("cyclus.tools.queue_tool._kb", kb):
        result = json.loads(cyclus_queue_handler(
            {"action": "dispatch", "mode": "loop", "instance_id": "x"}
        ))
    assert result["dispatched"] is True
    assert result["task_id"] == "t_test123"
    kb.assert_not_called()


# ---------------------------------------------------------------------------
# Interactive: post creates a new task via kanban_create
# ---------------------------------------------------------------------------


def test_interactive_post_creates_task(interactive_env):
    kb = _kb_factory(kanban_create={"task_id": "new_task_abc"})
    with patch("cyclus.tools.queue_tool._kb", kb):
        result = json.loads(cyclus_queue_handler(
            {"action": "post", "mode": "loop", "instance_id": "my-loop",
             "kind": "TaskExecutionKind", "name": "My Loop",
             "assignee": "forge"}
        ))
    assert result["task_id"] == "new_task_abc"
    tool_name, tool_args = kb.call_args[0]
    assert tool_name == "kanban_create"
    assert tool_args["assignee"] == "forge"
    assert tool_args["title"] == "My Loop"


def test_interactive_post_propagates_kanban_create_error(interactive_env):
    kb = _kb_factory(kanban_create={"error": "assignee profile not found"})
    with patch("cyclus.tools.queue_tool._kb", kb):
        result = json.loads(cyclus_queue_handler(
            {"action": "post", "mode": "loop", "instance_id": "x", "assignee": "forge"}
        ))
    assert "error" in result
    assert "kanban_create failed" in result["error"]


def test_interactive_post_errors_on_empty_task_id(interactive_env):
    kb = _kb_factory(kanban_create={})  # no task_id or id key
    with patch("cyclus.tools.queue_tool._kb", kb):
        result = json.loads(cyclus_queue_handler(
            {"action": "post", "mode": "loop", "instance_id": "x", "assignee": "forge"}
        ))
    assert "error" in result
    assert "no task_id" in result["error"]

def test_interactive_post_defaults_assignee_to_forge(interactive_env):
    kb = _kb_factory(kanban_create={"task_id": "t_xyz"})
    with patch("cyclus.tools.queue_tool._kb", kb):
        cyclus_queue_handler(
            {"action": "post", "mode": "loop", "instance_id": "x",
             "kind": "TaskExecutionKind"}
        )
    _, tool_args = kb.call_args[0]
    assert tool_args["assignee"] == "forge"


def test_interactive_dispatch_delegates_to_post(interactive_env):
    kb = _kb_factory(kanban_create={"task_id": "t_dispatch"})
    with patch("cyclus.tools.queue_tool._kb", kb):
        result = json.loads(cyclus_queue_handler(
            {"action": "dispatch", "mode": "loop", "instance_id": "x",
             "assignee": "forge"}
        ))
    # dispatch() calls _kanban_action("post", ...) which calls kanban_create
    assert result["task_id"] == "t_dispatch"
    tool_name, _ = kb.call_args[0]
    assert tool_name == "kanban_create"


def test_interactive_lifecycle_without_task_id_errors(interactive_env):
    """Non-post actions in interactive mode (no HERMES_KANBAN_TASK) return error."""
    kb = _kb_factory()
    with patch("cyclus.tools.queue_tool._kb", kb):
        for action in ("status", "write_state", "claim", "release", "cancel", "complete"):
            result = json.loads(cyclus_queue_handler(
                {"action": action, "mode": "loop", "instance_id": "x",
                 "state": {"iteration": 1}, "terminal_state": "Done"}
            ))
            assert "error" in result, f"expected error for action={action}"
    kb.assert_not_called()


# ---------------------------------------------------------------------------
# Consistent validation across backends
# ---------------------------------------------------------------------------


def test_write_state_requires_dict_kanban(worker_env):
    kb = _kb_factory()
    with patch("cyclus.tools.queue_tool._kb", kb):
        result = json.loads(cyclus_queue_handler(
            {"action": "write_state", "mode": "loop", "instance_id": "x",
             "state": "not-a-dict"}
        ))
    assert "error" in result
    kb.assert_not_called()


def test_write_state_requires_dict_file(file_env):
    result = json.loads(cyclus_queue_handler(
        {"action": "write_state", "mode": "loop", "instance_id": "x",
         "state": "not-a-dict"}
    ))
    assert "error" in result


def test_complete_requires_terminal_state_kanban(worker_env):
    kb = _kb_factory()
    with patch("cyclus.tools.queue_tool._kb", kb):
        result = json.loads(cyclus_queue_handler(
            {"action": "complete", "mode": "loop", "instance_id": "x"}
        ))
    assert "error" in result
    kb.assert_not_called()


def test_complete_requires_terminal_state_file(file_env):
    from cyclus.queue import post, claim
    post(mode="loop", instance_id="comp-val", kind="TaskExecutionKind", name="x")
    claim(mode="loop", instance_id="comp-val")
    result = json.loads(cyclus_queue_handler(
        {"action": "complete", "mode": "loop", "instance_id": "comp-val"}
    ))
    assert "error" in result


# ---------------------------------------------------------------------------
# _kb raises RuntimeError → returned as error dict
# ---------------------------------------------------------------------------


def test_kb_unavailable_returns_error(worker_env):
    def broken_kb(tool_name, tool_args):
        raise RuntimeError("kanban backend unavailable: no module named 'tools.registry'")

    with patch("cyclus.tools.queue_tool._kb", broken_kb):
        result = json.loads(cyclus_queue_handler(
            {"action": "status", "mode": "loop", "instance_id": "x"}
        ))
    assert "error" in result
    assert "kanban backend unavailable" in result["error"]


# ---------------------------------------------------------------------------
# State redaction
# ---------------------------------------------------------------------------


def test_redact_state_removes_unlisted_keys():
    state = {
        "iteration": 3,
        "best_score": 1.45,
        "secret_key": "should-not-appear",
        "user_input": "raw command output with secrets",
    }
    redacted = _redact_state(state)
    assert "iteration" in redacted
    assert "best_score" in redacted
    assert "secret_key" not in redacted
    assert "user_input" not in redacted


def test_redact_state_truncates_long_strings():
    state = {"iteration": 1, "lessons": ["x" * 300]}
    redacted = _redact_state(state)
    assert len(redacted["lessons"][0]) <= 203  # 200 + "…"


def test_worker_write_state_comment_truncated_if_large(worker_env):
    """Large state payloads are truncated before posting to Kanban."""
    big_lessons = ["lesson " + "x" * 100] * 50
    kb = _kb_factory()
    with patch("cyclus.tools.queue_tool._kb", kb):
        result = json.loads(cyclus_queue_handler(
            {"action": "write_state", "mode": "loop", "instance_id": "x",
             "state": {"iteration": 1, "lessons": big_lessons}}
        ))
    assert result["ok"] is True
    # Find the kanban_comment call and verify body length
    for c in kb.call_args_list:
        tool_name, tool_args = c[0]
        if tool_name == "kanban_comment":
            assert len(tool_args["body"]) <= 1100
            break
    else:
        pytest.fail("kanban_comment was not called")
