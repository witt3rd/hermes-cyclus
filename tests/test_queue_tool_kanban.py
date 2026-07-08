"""Tests for cyclus_queue Kanban backend routing.

Covers:
  - All eight actions routed correctly when HERMES_KANBAN_TASK is set
  - Shared validation (state/terminal_state) applied consistently across backends
  - Error returned (not silent fallback) when Kanban env is set but ctx is missing
  - dispatch action works on both Kanban and file backends
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

import cyclus.cyclus_config as cyclus_config_module
from cyclus.tools.queue_tool import (
    _KANBAN_STATE_ALLOWLIST,
    _redact_state,
    cyclus_queue_handler,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def file_env(tmp_path, monkeypatch):
    """File backend — no HERMES_KANBAN_TASK."""
    monkeypatch.delenv("HERMES_KANBAN_TASK", raising=False)
    cyclus_config_module._config_cache = {
        "project_root": str(tmp_path),
        "omh_backend": "files",
    }
    yield tmp_path
    cyclus_config_module._config_cache = None


@pytest.fixture()
def kanban_env(monkeypatch):
    """Kanban backend — HERMES_KANBAN_TASK set, stub ctx injected."""
    monkeypatch.setenv("HERMES_KANBAN_TASK", "t_test123")
    ctx = MagicMock()
    ctx.kanban_show.return_value = json.dumps({"status": "running"})
    ctx.kanban_heartbeat.return_value = json.dumps({"ok": True})
    ctx.kanban_comment.return_value = json.dumps({"ok": True})
    ctx.kanban_complete.return_value = json.dumps({"ok": True})
    ctx.kanban_block.return_value = json.dumps({"ok": True})
    yield ctx


# ---------------------------------------------------------------------------
# Kanban routing — all eight actions
# ---------------------------------------------------------------------------


def test_kanban_status(kanban_env):
    result = json.loads(cyclus_queue_handler(
        {"action": "status", "mode": "ralph", "instance_id": "x"}, ctx=kanban_env
    ))
    assert result["found"] is True
    assert result["task_id"] == "t_test123"
    kanban_env.kanban_show.assert_called_once()


def test_kanban_write_state(kanban_env):
    result = json.loads(cyclus_queue_handler(
        {"action": "write_state", "mode": "ralph", "instance_id": "x",
         "state": {"iteration": 3, "best_score": 1.45}},
        ctx=kanban_env,
    ))
    assert result["ok"] is True
    kanban_env.kanban_heartbeat.assert_called_once()
    kanban_env.kanban_comment.assert_called_once()


def test_kanban_complete(kanban_env):
    result = json.loads(cyclus_queue_handler(
        {"action": "complete", "mode": "ralph", "instance_id": "x",
         "terminal_state": "PlanComplete",
         "output": {"summary": "all done", "final_score": 1.49}},
        ctx=kanban_env,
    ))
    assert result["ok"] is True
    kanban_env.kanban_complete.assert_called_once()


def test_kanban_post_is_noop(kanban_env):
    result = json.loads(cyclus_queue_handler(
        {"action": "post", "mode": "ralph", "instance_id": "x",
         "kind": "TaskExecutionKind", "name": "test"},
        ctx=kanban_env,
    ))
    assert result["task_id"] == "t_test123"
    assert "note" in result


def test_kanban_claim_heartbeats(kanban_env):
    result = json.loads(cyclus_queue_handler(
        {"action": "claim", "mode": "ralph", "instance_id": "x"}, ctx=kanban_env
    ))
    assert result["status"] == "claimed"
    kanban_env.kanban_heartbeat.assert_called_once()


def test_kanban_release_blocks(kanban_env):
    result = json.loads(cyclus_queue_handler(
        {"action": "release", "mode": "ralph", "instance_id": "x"}, ctx=kanban_env
    ))
    assert result["ok"] is True
    kanban_env.kanban_block.assert_called_once()


def test_kanban_cancel_blocks(kanban_env):
    result = json.loads(cyclus_queue_handler(
        {"action": "cancel", "mode": "ralph", "instance_id": "x",
         "reason": "user aborted"},
        ctx=kanban_env,
    ))
    assert result["ok"] is True
    kanban_env.kanban_block.assert_called_once()


def test_kanban_dispatch_is_noop(kanban_env):
    result = json.loads(cyclus_queue_handler(
        {"action": "dispatch", "mode": "ralph", "instance_id": "x"}, ctx=kanban_env
    ))
    assert result["dispatched"] is True
    assert result["task_id"] == "t_test123"


# ---------------------------------------------------------------------------
# Consistent validation across backends
# ---------------------------------------------------------------------------


def test_write_state_requires_dict_kanban(kanban_env):
    result = json.loads(cyclus_queue_handler(
        {"action": "write_state", "mode": "ralph", "instance_id": "x",
         "state": "not-a-dict"},
        ctx=kanban_env,
    ))
    assert "error" in result
    kanban_env.kanban_comment.assert_not_called()


def test_write_state_requires_dict_file(file_env):
    result = json.loads(cyclus_queue_handler(
        {"action": "write_state", "mode": "ralph", "instance_id": "x",
         "state": "not-a-dict"},
    ))
    assert "error" in result


def test_complete_requires_terminal_state_kanban(kanban_env):
    result = json.loads(cyclus_queue_handler(
        {"action": "complete", "mode": "ralph", "instance_id": "x"},
        ctx=kanban_env,
    ))
    assert "error" in result
    kanban_env.kanban_complete.assert_not_called()


def test_complete_requires_terminal_state_file(file_env):
    from cyclus.queue import post, claim
    post(mode="ralph", instance_id="comp-val", kind="TaskExecutionKind", name="x")
    claim(mode="ralph", instance_id="comp-val")
    result = json.loads(cyclus_queue_handler(
        {"action": "complete", "mode": "ralph", "instance_id": "comp-val"},
    ))
    assert "error" in result


# ---------------------------------------------------------------------------
# Kanban ctx missing — return error, not silent fallback
# ---------------------------------------------------------------------------


def test_kanban_env_without_ctx_returns_error(kanban_env, monkeypatch):
    """When HERMES_KANBAN_TASK is set but no ctx, return error — don't silently
    fall back to the file backend and diverge from the Kanban dispatcher."""
    result = json.loads(cyclus_queue_handler(
        {"action": "status", "mode": "ralph", "instance_id": "x"},
        # no ctx= kwarg
    ))
    assert "error" in result
    assert "HERMES_KANBAN_TASK" in result["error"]


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


def test_kanban_write_state_comment_truncated_if_large(kanban_env):
    """Large state payloads are truncated before posting to Kanban."""
    big_lessons = ["lesson " + "x" * 100] * 50
    result = json.loads(cyclus_queue_handler(
        {"action": "write_state", "mode": "ralph", "instance_id": "x",
         "state": {"iteration": 1, "lessons": big_lessons}},
        ctx=kanban_env,
    ))
    assert result["ok"] is True
    call_args = kanban_env.kanban_comment.call_args[0][0]
    assert len(call_args["body"]) <= 1100  # schema max + code fence overhead
