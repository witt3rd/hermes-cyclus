"""Tests for CYCLUS_BACKEND env var — user backend selection."""
from __future__ import annotations

import json
from unittest.mock import patch

import pytest

from cyclus.tools.queue_tool import _active_backend, cyclus_queue_handler


# ---------------------------------------------------------------------------
# _active_backend priority
# ---------------------------------------------------------------------------

def test_kanban_dispatcher_wins_over_cyclus_backend(monkeypatch):
    """HERMES_KANBAN_TASK beats CYCLUS_BACKEND — dispatcher identity is not overridable."""
    monkeypatch.setenv("HERMES_KANBAN_TASK", "t_abc")
    monkeypatch.setenv("CYCLUS_BACKEND", "file")
    assert _active_backend() == "kanban"


def test_saturate_dispatcher_wins_over_cyclus_backend(monkeypatch):
    """SATURATE_TASK_ID beats CYCLUS_BACKEND — dispatcher identity is not overridable."""
    monkeypatch.setenv("SATURATE_TASK_ID", "t_xyz")
    monkeypatch.setenv("CYCLUS_BACKEND", "file")
    monkeypatch.delenv("HERMES_KANBAN_TASK", raising=False)
    assert _active_backend() == "saturate"


def test_cyclus_backend_selects_kanban(monkeypatch):
    monkeypatch.setenv("CYCLUS_BACKEND", "kanban")
    monkeypatch.delenv("HERMES_KANBAN_TASK", raising=False)
    monkeypatch.delenv("SATURATE_TASK_ID", raising=False)
    assert _active_backend() == "kanban"


def test_cyclus_backend_selects_saturate(monkeypatch):
    monkeypatch.setenv("CYCLUS_BACKEND", "saturate")
    monkeypatch.delenv("HERMES_KANBAN_TASK", raising=False)
    monkeypatch.delenv("SATURATE_TASK_ID", raising=False)
    assert _active_backend() == "saturate"


def test_cyclus_backend_selects_file(monkeypatch):
    monkeypatch.setenv("CYCLUS_BACKEND", "file")
    monkeypatch.delenv("HERMES_KANBAN_TASK", raising=False)
    monkeypatch.delenv("SATURATE_TASK_ID", raising=False)
    assert _active_backend() == "file"


def test_cyclus_backend_filesystem_alias(monkeypatch):
    """'filesystem' is accepted as an alias for 'file'."""
    monkeypatch.setenv("CYCLUS_BACKEND", "filesystem")
    monkeypatch.delenv("HERMES_KANBAN_TASK", raising=False)
    monkeypatch.delenv("SATURATE_TASK_ID", raising=False)
    assert _active_backend() == "file"


def test_cyclus_backend_case_insensitive(monkeypatch):
    monkeypatch.setenv("CYCLUS_BACKEND", "KANBAN")
    monkeypatch.delenv("HERMES_KANBAN_TASK", raising=False)
    monkeypatch.delenv("SATURATE_TASK_ID", raising=False)
    assert _active_backend() == "kanban"


def test_cyclus_backend_unknown_falls_back_to_file(monkeypatch):
    monkeypatch.setenv("CYCLUS_BACKEND", "redis")
    monkeypatch.delenv("HERMES_KANBAN_TASK", raising=False)
    monkeypatch.delenv("SATURATE_TASK_ID", raising=False)
    assert _active_backend() == "file"


def test_no_env_vars_defaults_to_file(monkeypatch):
    monkeypatch.delenv("HERMES_KANBAN_TASK", raising=False)
    monkeypatch.delenv("SATURATE_TASK_ID", raising=False)
    monkeypatch.delenv("CYCLUS_BACKEND", raising=False)
    assert _active_backend() == "file"


# ---------------------------------------------------------------------------
# CYCLUS_BACKEND=kanban routes to Kanban (needs ctx)
# ---------------------------------------------------------------------------

def test_cyclus_backend_kanban_without_ctx_returns_error(monkeypatch):
    """CYCLUS_BACKEND=kanban with no ctx → error, not silent fallback."""
    monkeypatch.setenv("CYCLUS_BACKEND", "kanban")
    monkeypatch.delenv("HERMES_KANBAN_TASK", raising=False)
    monkeypatch.delenv("SATURATE_TASK_ID", raising=False)
    result = json.loads(cyclus_queue_handler(
        {"action": "status", "mode": "loop", "instance_id": "x"}
        # no ctx kwarg
    ))
    assert "error" in result


# ---------------------------------------------------------------------------
# CYCLUS_BACKEND=saturate routes to Saturate (needs SATURATE_TASK_ID or queue)
# ---------------------------------------------------------------------------

def test_cyclus_backend_saturate_routes_correctly(monkeypatch):
    """CYCLUS_BACKEND=saturate routes to _saturate_action."""
    monkeypatch.setenv("CYCLUS_BACKEND", "saturate")
    monkeypatch.setenv("SATURATE_TASK_ID", "explicit-task-id")
    monkeypatch.delenv("HERMES_KANBAN_TASK", raising=False)

    from unittest.mock import MagicMock
    mock_q = MagicMock()
    mock_q.get.return_value = {"status": "running", "kind": "MetricOptimizationKind"}

    with patch("cyclus.tools.queue_tool._get_saturate_queue", return_value=mock_q):
        result = json.loads(cyclus_queue_handler(
            {"action": "status", "mode": "loop", "instance_id": "x"}
        ))
    assert result["found"] is True
