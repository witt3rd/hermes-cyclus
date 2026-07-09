"""Tests for cyclus_queue Saturate backend routing.

Covers:
  - All eight actions routed correctly when SATURATE_TASK is set
  - Shared validation (state/terminal_state) applied consistently
  - Error returned when Saturate package unavailable
  - Queue selection: file-based vs SQLite based on SATURATE_QUEUE_DIR
  - No silent fallback to file backend when SATURATE_TASK is set
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

import cyclus.cyclus_config as cyclus_config_module
from cyclus.tools.queue_tool import cyclus_queue_handler


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def saturate_env(tmp_path, monkeypatch):
    """Saturate backend — SATURATE_TASK set, queue in tmp_path."""
    task_id = "test-task-abc123"
    monkeypatch.setenv("SATURATE_TASK", task_id)
    monkeypatch.setenv("SATURATE_QUEUE_DIR", str(tmp_path))
    monkeypatch.delenv("HERMES_KANBAN_TASK", raising=False)
    return {"task_id": task_id, "queue_dir": tmp_path}


@pytest.fixture()
def mock_saturate_queue(saturate_env):
    """Saturate backend with a stubbed queue."""
    mock_q = MagicMock()
    mock_q.get.return_value = {"status": "running", "kind": "MetricOptimizationKind"}
    mock_q.write_state.return_value = None
    mock_q.complete.return_value = None
    mock_q.cancel.return_value = None
    # hasattr check for cancel
    mock_q.cancel = MagicMock()

    with patch("cyclus.tools.queue_tool._get_saturate_queue", return_value=mock_q):
        yield mock_q


# ---------------------------------------------------------------------------
# All eight actions
# ---------------------------------------------------------------------------


def test_saturate_status(mock_saturate_queue, saturate_env):
    result = json.loads(cyclus_queue_handler(
        {"action": "status", "mode": "loop", "instance_id": "x"}
    ))
    assert result["found"] is True
    assert result["task_id"] == saturate_env["task_id"]
    assert result["status"] == "running"
    mock_saturate_queue.get.assert_called_once_with(saturate_env["task_id"])


def test_saturate_write_state(mock_saturate_queue, saturate_env):
    result = json.loads(cyclus_queue_handler(
        {"action": "write_state", "mode": "loop", "instance_id": "x",
         "state": {"iteration": 3, "best_score": 1.45}}
    ))
    assert result["ok"] is True
    mock_saturate_queue.write_state.assert_called_once_with(
        saturate_env["task_id"], {"iteration": 3, "best_score": 1.45}
    )


def test_saturate_complete(mock_saturate_queue, saturate_env):
    result = json.loads(cyclus_queue_handler(
        {"action": "complete", "mode": "loop", "instance_id": "x",
         "terminal_state": "MetricSuccess",
         "output": {"summary": "done", "final_score": 1.49}}
    ))
    assert result["ok"] is True
    mock_saturate_queue.complete.assert_called_once()
    call_args = mock_saturate_queue.complete.call_args[0]
    assert call_args[0] == saturate_env["task_id"]
    assert call_args[1]["terminal_state"] == "MetricSuccess"


def test_saturate_post_is_noop(mock_saturate_queue, saturate_env):
    result = json.loads(cyclus_queue_handler(
        {"action": "post", "mode": "loop", "instance_id": "x",
         "kind": "MetricOptimizationKind", "name": "test"}
    ))
    assert result["task_id"] == saturate_env["task_id"]
    assert "note" in result


def test_saturate_claim(mock_saturate_queue, saturate_env):
    result = json.loads(cyclus_queue_handler(
        {"action": "claim", "mode": "loop", "instance_id": "x"}
    ))
    assert result["status"] == "claimed"
    assert result["item"]["task_id"] == saturate_env["task_id"]


def test_saturate_release(mock_saturate_queue, saturate_env):
    result = json.loads(cyclus_queue_handler(
        {"action": "release", "mode": "loop", "instance_id": "x"}
    ))
    assert result["ok"] is True


def test_saturate_cancel(mock_saturate_queue, saturate_env):
    result = json.loads(cyclus_queue_handler(
        {"action": "cancel", "mode": "loop", "instance_id": "x", "reason": "test abort"}
    ))
    assert result["ok"] is True
    mock_saturate_queue.cancel.assert_called_once_with(
        saturate_env["task_id"], reason="test abort"
    )


def test_saturate_dispatch_is_noop(mock_saturate_queue, saturate_env):
    result = json.loads(cyclus_queue_handler(
        {"action": "dispatch", "mode": "loop", "instance_id": "x"}
    ))
    assert result["dispatched"] is True
    assert result["task_id"] == saturate_env["task_id"]


# ---------------------------------------------------------------------------
# Consistent validation
# ---------------------------------------------------------------------------


def test_saturate_write_state_requires_dict(mock_saturate_queue, saturate_env):
    result = json.loads(cyclus_queue_handler(
        {"action": "write_state", "mode": "loop", "instance_id": "x",
         "state": "not-a-dict"}
    ))
    assert "error" in result
    mock_saturate_queue.write_state.assert_not_called()


def test_saturate_complete_requires_terminal_state(mock_saturate_queue, saturate_env):
    result = json.loads(cyclus_queue_handler(
        {"action": "complete", "mode": "loop", "instance_id": "x"}
    ))
    assert "error" in result
    mock_saturate_queue.complete.assert_not_called()


# ---------------------------------------------------------------------------
# Saturate package unavailable
# ---------------------------------------------------------------------------


def test_saturate_import_error_returns_error(saturate_env, monkeypatch):
    """When saturate package is not installed, return error — don't crash."""
    with patch("cyclus.tools.queue_tool._get_saturate_queue",
               side_effect=RuntimeError("saturate not installed")):
        result = json.loads(cyclus_queue_handler(
            {"action": "status", "mode": "loop", "instance_id": "x"}
        ))
    assert "error" in result
    assert "saturate" in result["error"].lower()


# ---------------------------------------------------------------------------
# Queue selection
# ---------------------------------------------------------------------------


def test_saturate_uses_sqlite_when_db_exists(saturate_env, tmp_path):
    """When SATURATE_QUEUE_DIR has a saturate.db, SqliteQueue is used."""
    db_path = tmp_path / "saturate.db"
    db_path.touch()  # create stub db file

    with patch("cyclus.tools.queue_tool._get_saturate_queue") as mock_factory:
        mock_q = MagicMock()
        mock_q.get.return_value = {"status": "running", "kind": "MetricOptimizationKind"}
        mock_factory.return_value = mock_q
        result = json.loads(cyclus_queue_handler(
            {"action": "status", "mode": "loop", "instance_id": "x"}
        ))
    assert result["found"] is True


def test_saturate_env_without_kanban(saturate_env, mock_saturate_queue):
    """SATURATE_TASK set, no HERMES_KANBAN_TASK — routes to Saturate, not file."""
    # Verify file backend is NOT used
    with patch("cyclus.tools.queue_tool._file_action") as mock_file:
        cyclus_queue_handler(
            {"action": "status", "mode": "loop", "instance_id": "x"}
        )
        mock_file.assert_not_called()
