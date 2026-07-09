"""
cyclus_queue tool — backend-agnostic eight-operation interface.

Backend detection (in priority order):
  1. Kanban   — HERMES_KANBAN_TASK env var set; kanban_* toolset active
  2. Saturate — SATURATE_TASK env var set; SATURATE_QUEUE_DIR locates the queue
  3. Explicit — CYCLUS_BACKEND=kanban|saturate|file|filesystem (user/skill --backend choice)
               ('filesystem' is accepted as an alias for 'file')
  4. File     — default; atomic directory ops in .cyclus/queue/

All Saturate actions require SATURATE_TASK to be set (Saturate is task-scoped).
Skills call cyclus_queue and never touch backend APIs directly.
"""

import json
import logging
import os
from typing import Any

log = logging.getLogger(__name__)

# Module-level optional imports — independently guarded so SQLite unavailability
# doesn't prevent use of the file-based Queue.
try:
    from saturate.queue import Queue as SaturateQueue
except ImportError:
    SaturateQueue = None  # type: ignore[assignment,misc]

try:
    from saturate.queue_sqlite import SqliteQueue
except ImportError:
    SqliteQueue = None  # type: ignore[assignment,misc]

# Max chars of state payload posted to a Kanban comment to avoid leaks / size limits
_KANBAN_STATE_COMMENT_MAX = 1000

# Fields allowed in a Kanban state comment (allowlist to prevent leaking sensitive data)
_KANBAN_STATE_ALLOWLIST = {
    "iteration", "best_score", "plateau_count", "foreclosed", "lessons",
    "current_coverage", "best_coverage", "iteration_count", "status",
    "turn", "phase", "round", "files_improved", "target",
}


def _redact_state(state: dict) -> dict:
    """Return a copy of state with only allowlisted keys, values truncated."""
    out = {}
    for k, v in state.items():
        if k not in _KANBAN_STATE_ALLOWLIST:
            continue
        if isinstance(v, str) and len(v) > 200:
            v = v[:200] + "…"
        elif isinstance(v, list):
            trimmed = v[:10]
            trimmed = [s[:200] + "…" if isinstance(s, str) and len(s) > 200 else s for s in trimmed]
            if len(v) > 10:
                trimmed.append("…")
            v = trimmed
        out[k] = v
    return out


# ---------------------------------------------------------------------------
# Backend detection
# ---------------------------------------------------------------------------

def _active_backend() -> str:
    """Detect which backend is active.

    Priority order:
      1. HERMES_KANBAN_TASK — injected by Kanban dispatcher (identity signal, not overridable)
      2. SATURATE_TASK      — injected by Saturate scheduler (identity signal, not overridable)
      3. CYCLUS_BACKEND     — explicit user/skill choice (set via --backend modifier)
      4. cyclus.backend in profile config (future)
      5. file               — zero-config fallback

    The --backend kanban|saturate|file skill modifier sets CYCLUS_BACKEND for
    the duration of a skill invocation. This is distinct from the dispatcher
    identity signals (1, 2) which are injected by infrastructure, not chosen by users.
    """
    if os.environ.get("HERMES_KANBAN_TASK"):
        return "kanban"
    if os.environ.get("SATURATE_TASK"):
        return "saturate"
    backend = os.environ.get("CYCLUS_BACKEND", "").lower().strip()
    if backend in ("kanban", "saturate", "file", "filesystem"):
        return "file" if backend == "filesystem" else backend
    return "file"


# ---------------------------------------------------------------------------
# Saturate backend
# ---------------------------------------------------------------------------

def _get_saturate_queue():
    """Return the active Saturate Queue instance, using SATURATE_QUEUE_DIR.

    Queue selection:
      - If SATURATE_QUEUE_DIR/saturate.db exists AND SqliteQueue is available
        → SqliteQueue (concurrent-safe)
      - Otherwise → file-based Queue
    This applies both when SATURATE_QUEUE_DIR is set and for the default path.
    """
    if SaturateQueue is None:
        raise RuntimeError(
            "Saturate backend requested but the 'saturate' package is not installed. "
            "Install with: uv add 'hermes-cyclus[saturate]'"
        )
    import pathlib
    base = pathlib.Path(os.environ.get("SATURATE_QUEUE_DIR") or (pathlib.Path.home() / ".saturate"))
    db_path = base / "saturate.db"
    if db_path.exists() and SqliteQueue is not None:
        return SqliteQueue(base_dir=str(base))
    return SaturateQueue(base_dir=str(base))


def _saturate_action(action: str, args: dict) -> str:
    """Route cyclus_queue actions to the Saturate backend."""
    task_id = os.environ.get("SATURATE_TASK", "")
    mode = args.get("mode", "")
    instance_id = args.get("instance_id", "")

    # All Saturate actions are task-scoped — require SATURATE_TASK for all
    if not task_id:
        active_signals = [
            s for s in ("HERMES_KANBAN_TASK", "SATURATE_TASK", "CYCLUS_BACKEND")
            if os.environ.get(s)
        ]
        return json.dumps({
            "error": (
                f"action={action!r} requires a task_id but SATURATE_TASK is not set. "
                f"Active backend signals: {active_signals or ['none']}. "
                "Set SATURATE_TASK to the active Saturate task ID."
            )
        })

    try:
        q = _get_saturate_queue()
    except RuntimeError as e:
        return json.dumps({"error": str(e)})

    match action:
        case "status":
            task = q.get(task_id) if task_id else None
            if task is None:
                return json.dumps({"found": False})
            return json.dumps({
                "found": True,
                "task_id": task_id,
                "status": task.get("status", "unknown"),
                "kind": task.get("kind"),
                "instance_id": instance_id,
            })

        case "write_state":
            state = args.get("state")
            err = _validate_state(state)
            if err:
                return json.dumps({"error": err})
            assert isinstance(state, dict)
            q.write_state(task_id, state)
            return json.dumps({"ok": True})

        case "complete":
            terminal = args.get("terminal_state")
            err = _validate_terminal(terminal)
            if err:
                return json.dumps({"error": err})
            assert isinstance(terminal, str)
            # Copy to avoid mutating caller's args dict
            output = dict(args.get("output") or {})
            output["terminal_state"] = terminal
            q.complete(task_id, output)
            return json.dumps({"ok": True})

        case "post":
            # In Saturate mode, the task was already posted by the dispatcher.
            # post() is a no-op — we're already inside the task.
            return json.dumps({"task_id": task_id, "note": "saturate: task already exists"})

        case "claim":
            # Already claimed by the Saturate scheduler. Heartbeat via write_state.
            return json.dumps({
                "status": "claimed",
                "item": {"task_id": task_id, "mode": mode, "instance_id": instance_id},
            })

        case "release":
            # In Saturate mode, the scheduler reclaims the task when the worker
            # process exits. release() is a no-op here — the scheduler detects
            # completion via heartbeat expiry or explicit complete().
            return json.dumps({"ok": True, "note": "saturate: scheduler reclaims on worker exit"})

        case "cancel":
            reason = args.get("reason", "user request")
            if hasattr(q, "cancel"):
                # SqliteQueue.cancel(task_id, reason) — both args required
                q.cancel(task_id, reason=reason)
            else:
                # File-based Queue has no cancel — complete with Cancelled state
                q.complete(task_id, {"terminal_state": "Cancelled", "reason": reason})
            return json.dumps({"ok": True})

        case "dispatch":
            # Saturate dispatches automatically via its scheduler — no-op here.
            return json.dumps({
                "dispatched": True,
                "task_id": task_id,
                "mode": mode,
                "instance_id": instance_id,
                "note": "saturate: scheduler dispatches automatically",
            })

        case _:
            return json.dumps({"error": f"Saturate backend: unsupported action {action!r}"})


# ---------------------------------------------------------------------------
# Shared validation
# ---------------------------------------------------------------------------

def _validate_state(state: Any) -> str | None:
    """Return an error string if state is invalid, else None."""
    if state is None:
        return "state is required for action=write_state"
    if not isinstance(state, dict):
        return "state must be an object for action=write_state"
    return None

def _validate_terminal(terminal: Any) -> str | None:
    """Return an error string if terminal_state is invalid, else None."""
    if not terminal:
        return "terminal_state is required for action=complete"
    return None


# ---------------------------------------------------------------------------
# Kanban backend — delegates to kanban_* toolset via Hermes context
# ---------------------------------------------------------------------------

def _kanban_action(action: str, args: dict, kanban_ctx) -> str:
    """Route cyclus_queue actions to the Kanban backend via kanban_* tools."""
    task_id = os.environ.get("HERMES_KANBAN_TASK", "")
    mode = args.get("mode", "")
    instance_id = args.get("instance_id", "")

    match action:
        case "status":
            result = kanban_ctx.kanban_show({"task_id": task_id})
            data = json.loads(result) if isinstance(result, str) else result
            return json.dumps({
                "found": True,
                "task_id": task_id,
                "status": data.get("status", "unknown"),
                "kind": args.get("kind"),
                "instance_id": instance_id,
            })

        case "write_state":
            state = args.get("state")
            err = _validate_state(state)
            if err:
                return json.dumps({"error": err})
            assert isinstance(state, dict)  # narrowed by _validate_state
            # Redact to allowlist, truncate to avoid leaks / size limits
            redacted = _redact_state(state)
            payload = json.dumps(redacted, indent=2)
            if len(payload) > _KANBAN_STATE_COMMENT_MAX:
                payload = payload[:_KANBAN_STATE_COMMENT_MAX] + "\n… (truncated)"
            kanban_ctx.kanban_heartbeat({"task_id": task_id})
            kanban_ctx.kanban_comment({
                "task_id": task_id,
                "body": f"**state**\n```json\n{payload}\n```",
            })
            return json.dumps({"ok": True})

        case "complete":
            terminal = args.get("terminal_state")
            err = _validate_terminal(terminal)
            if err:
                return json.dumps({"error": err})
            assert isinstance(terminal, str)  # narrowed by _validate_terminal
            output = args.get("output") or {}
            summary = output.get("summary", terminal)
            kanban_ctx.kanban_complete({
                "task_id": task_id,
                "summary": summary,
                "metadata": output,
            })
            return json.dumps({"ok": True})

        case "post":
            # In Kanban mode the task already exists — post() is a no-op.
            return json.dumps({"task_id": task_id, "note": "kanban: task already exists"})

        case "claim":
            # Already claimed by the Kanban dispatcher.
            kanban_ctx.kanban_heartbeat({"task_id": task_id})
            return json.dumps({
                "status": "claimed",
                "item": {"task_id": task_id, "mode": mode, "instance_id": instance_id},
            })

        case "release":
            kanban_ctx.kanban_block({
                "task_id": task_id,
                "reason": "dependency",
                "message": "Worker releasing task back to dispatcher",
            })
            return json.dumps({"ok": True})

        case "cancel":
            kanban_ctx.kanban_block({
                "task_id": task_id,
                "reason": "dependency",
                "message": args.get("reason", "cancelled"),
            })
            return json.dumps({"ok": True})

        case "dispatch":
            # In Kanban mode, dispatch is equivalent to post (no-op) — the
            # gateway handles dispatch automatically after task creation.
            return json.dumps({
                "dispatched": True,
                "task_id": task_id,
                "mode": mode,
                "instance_id": instance_id,
                "note": "kanban: gateway dispatches automatically",
            })

        case _:
            return json.dumps({"error": f"Kanban backend: unsupported action {action!r}"})


# ---------------------------------------------------------------------------
# File backend — existing queue.py implementation
# ---------------------------------------------------------------------------

from ..queue import (
    HumanGatedViolation,
    ClaimResult,
    cancel as _file_cancel,
    claim as _file_claim,
    complete as _file_complete,
    post as _file_post,
    release as _file_release,
    status as _file_status,
    write_state as _file_write_state,
)


def _file_action(action: str, args: dict) -> str:
    mode = args.get("mode", "")
    instance_id = args.get("instance_id", "")

    match action:
        case "post":
            task_id = _file_post(
                mode=mode,
                instance_id=instance_id,
                kind=args.get("kind") or "TaskExecutionKind",
                name=args.get("name") or instance_id,
                max_turns=args.get("max_turns"),
                tags=args.get("tags"),
                spawned_by=args.get("spawned_by"),
                depends_on=args.get("depends_on"),
            )
            return json.dumps({"task_id": task_id})

        case "claim":
            extra: dict = {}
            if "heartbeat_timeout_seconds" in args:
                extra["heartbeat_timeout_seconds"] = int(args["heartbeat_timeout_seconds"])
            result: ClaimResult = _file_claim(mode=mode, instance_id=instance_id, **extra)
            return json.dumps({"status": result.status, "item": result.item})

        case "release":
            _file_release(mode=mode, instance_id=instance_id)
            return json.dumps({"ok": True})

        case "write_state":
            state_data = args.get("state")
            err = _validate_state(state_data)
            if err:
                return json.dumps({"error": err})
            assert isinstance(state_data, dict)  # narrowed by _validate_state
            _file_write_state(mode=mode, instance_id=instance_id, state=state_data)
            return json.dumps({"ok": True})

        case "cancel":
            _file_cancel(
                mode=mode,
                instance_id=instance_id,
                reason=args.get("reason", "user request"),
            )
            return json.dumps({"ok": True})

        case "complete":
            terminal = args.get("terminal_state")
            err = _validate_terminal(terminal)
            if err:
                return json.dumps({"error": err})
            assert isinstance(terminal, str)  # narrowed by _validate_terminal
            _file_complete(
                mode=mode,
                instance_id=instance_id,
                terminal_state=terminal,
                output=args.get("output"),
                confirmed_by_human=bool(args.get("confirmed_by_human", False)),
            )
            return json.dumps({"ok": True})

        case "status":
            result_dict = _file_status(mode=mode, instance_id=instance_id)
            return json.dumps(result_dict if result_dict is not None else {"found": False})

        case "dispatch":
            info = _file_status(mode=mode, instance_id=instance_id)
            if info is None:
                _file_post(
                    mode=mode,
                    instance_id=instance_id,
                    kind=args.get("kind", "TaskExecutionKind"),
                    name=args.get("name", instance_id),
                    max_turns=args.get("max_turns"),
                    tags=args.get("tags"),
                    spawned_by=args.get("spawned_by"),
                    depends_on=args.get("depends_on"),
                )
                info = _file_status(mode=mode, instance_id=instance_id)
            if info and info.get("status") not in ("PENDING", "RUNNING"):
                return json.dumps({"error": f"Cannot dispatch: item is already {info['status']}"})
            return json.dumps({
                "dispatched": True,
                "mode": mode,
                "instance_id": instance_id,
                "task_id": info["task_id"] if info else None,
                "kind": info["kind"] if info else None,
                "status": info["status"] if info else None,
                "state_path": info["state_path"] if info else None,
                "worker_note": (
                    "File backend: fire worker via delegate_task with cyclus-loop skill. "
                    "Kanban/Saturate: backend fires automatically on post."
                ),
            })

        case _:
            raise ValueError(f"Unknown action: {action!r}")


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

CYCLUS_QUEUE_SCHEMA = {
    "name": "cyclus_queue",
    "description": (
        "Cyclus work queue — backend-agnostic interface. "
        "Backend is auto-detected in priority order: "
        "(1) HERMES_KANBAN_TASK set → Kanban; "
        "(2) SATURATE_TASK set → Saturate; "
        "(3) CYCLUS_BACKEND env var → explicit choice (set via --backend kanban|saturate|file, "
        "or 'filesystem' as an alias for 'file'); "
        "(4) file-based queue (default, zero-config). "
        "Actions: post | claim | release | write_state | cancel | complete | status | dispatch."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["post", "claim", "release", "write_state", "cancel", "complete", "status", "dispatch"],
                "description": "Operation to perform.",
            },
            "mode": {
                "type": "string",
                "description": "Mode name: loop, plan, research, interview, triage, autopilot, etc. Required.",
            },
            "instance_id": {
                "type": "string",
                "description": "Per-instance key (e.g. plan slug, goal slug). Required.",
            },
            "kind": {
                "type": "string",
                "description": "Loop kind (action=post only). e.g. TaskExecutionKind | ConsensusKind.",
            },
            "name": {
                "type": "string",
                "description": "Human-readable loop name (action=post only).",
            },
            "max_turns": {
                "type": "integer",
                "description": "Maximum turns before forced terminal (action=post only).",
            },
            "tags": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Tags (action=post only). Use 'HUMAN_GATED' for ClarificationKind.",
            },
            "spawned_by": {
                "type": "string",
                "description": "Parent task_id (action=post only).",
            },
            "depends_on": {
                "type": "array",
                "items": {"type": "string"},
                "description": "task_ids that must complete first (action=post only).",
            },
            "heartbeat_timeout_seconds": {
                "type": "integer",
                "description": "Reclaim window in seconds (action=claim only; default 300).",
            },
            "state": {
                "type": "object",
                "description": "Intermediate state dict (action=write_state only). Must be a JSON object.",
            },
            "reason": {
                "type": "string",
                "description": "Cancellation reason (action=cancel only).",
            },
            "terminal_state": {
                "type": "string",
                "description": "Terminal state string (action=complete only; required). e.g. PlanComplete | ConsensusReached.",
            },
            "output": {
                "type": "object",
                "description": "Final output dict (action=complete only).",
            },
            "confirmed_by_human": {
                "type": "boolean",
                "description": "Required true for HUMAN_GATED items (action=complete only).",
            },
        },
        "required": ["action", "mode", "instance_id"],
    },
}


# ---------------------------------------------------------------------------
# Main handler
# ---------------------------------------------------------------------------

def cyclus_queue_handler(args: dict, **kwargs) -> str:
    """Dispatch a cyclus_queue action to the active backend."""
    action: str = args.get("action") or ""
    mode = args.get("mode", "")
    instance_id = args.get("instance_id", "")

    if not action:
        return json.dumps({"error": "action is required"})
    if not mode:
        return json.dumps({"error": "mode is required"})
    if not instance_id:
        return json.dumps({"error": "instance_id is required"})

    backend = _active_backend()

    try:
        if backend == "kanban":
            kanban_ctx = kwargs.get("ctx") or kwargs.get("kanban_ctx")
            if kanban_ctx is None:
                # No ctx available — error rather than silently side-effecting
                # the file queue from inside a Kanban worker session.
                return json.dumps({
                    "error": (
                        "HERMES_KANBAN_TASK is set but no Kanban context (ctx) was passed. "
                        "Refusing to fall back to file backend to avoid diverging from the "
                        "Kanban dispatcher's source of truth."
                    )
                })
            return _kanban_action(action, args, kanban_ctx)

        elif backend == "saturate":
            return _saturate_action(action, args)

        else:
            return _file_action(action, args)

    except HumanGatedViolation as exc:
        return json.dumps({"error": f"HumanGatedViolation: {exc}"})
    except ValueError as exc:
        return json.dumps({"error": str(exc)})
    except Exception as exc:
        log.exception("cyclus_queue(%s, %s, %r) failed", action, mode, instance_id)
        return json.dumps({"error": f"cyclus_queue({action}, {mode}, {instance_id!r}) failed: {exc}"})
