"""
cyclus_queue tool — backend-agnostic six-operation interface.

Backend detection (in priority order):
  1. Kanban  — HERMES_KANBAN_TASK env var set; kanban_* toolset active
  2. Saturate — SATURATE_TASK env var set (future)
  3. File    — default; atomic directory ops in .cyclus/queue/

Skills call cyclus_queue and never touch backend APIs directly.
"""

import json
import logging
import os

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Backend detection
# ---------------------------------------------------------------------------

def _active_backend() -> str:
    if os.environ.get("HERMES_KANBAN_TASK"):
        return "kanban"
    if os.environ.get("SATURATE_TASK"):
        return "saturate"
    return "file"


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
            # kanban_show gives us the current task state
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
            if state is None:
                return json.dumps({"error": "state is required for action=write_state"})
            # Kanban uses kanban_comment to record state, plus heartbeat to signal liveness
            kanban_ctx.kanban_heartbeat({"task_id": task_id})
            kanban_ctx.kanban_comment({
                "task_id": task_id,
                "body": f"**state update**\n```json\n{json.dumps(state, indent=2)}\n```",
            })
            return json.dumps({"ok": True})

        case "complete":
            terminal = args.get("terminal_state", "Complete")
            output = args.get("output", {})
            summary = (output or {}).get("summary", terminal)
            kanban_ctx.kanban_complete({
                "task_id": task_id,
                "summary": summary,
                "metadata": output,
            })
            return json.dumps({"ok": True})

        case "post":
            # In Kanban mode, the task was already created by the dispatcher.
            # post() is a no-op — we're already inside the task.
            return json.dumps({"task_id": task_id, "note": "kanban: task already exists"})

        case "claim":
            # Already claimed by the Kanban dispatcher. Return the task context.
            kanban_ctx.kanban_heartbeat({"task_id": task_id})
            return json.dumps({
                "status": "claimed",
                "item": {"task_id": task_id, "mode": mode, "instance_id": instance_id},
            })

        case "release":
            # In Kanban mode, release = block (let dispatcher reclaim)
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
            if state_data is None:
                return json.dumps({"error": "state is required for action=write_state"})
            if not isinstance(state_data, dict):
                return json.dumps({"error": "state must be an object for action=write_state"})
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
            if not terminal:
                return json.dumps({"error": "terminal_state is required for action=complete"})
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
                    "File backend: fire worker via delegate_task with cyclus-ralph skill. "
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
        "Cyclus work queue — backend-agnostic six-operation interface. "
        "Routes to Kanban (HERMES_KANBAN_TASK), Saturate (SATURATE_TASK), "
        "or file-based queue (default). "
        "Actions: post | claim | release | write_state | cancel | complete | status | dispatch. "
        "Skills write against this interface; backend is a deployment detail."
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
                "description": "Mode name: ralph, ralplan, deep-research, autopilot, etc. Required.",
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
                "description": "Tags for the work item (action=post only). Use 'HUMAN_GATED' for ClarificationKind.",
            },
            "spawned_by": {
                "type": "string",
                "description": "Parent task_id (action=post only).",
            },
            "depends_on": {
                "type": "array",
                "items": {"type": "string"},
                "description": "task_ids that must complete before this item is claimed (action=post only).",
            },
            "heartbeat_timeout_seconds": {
                "type": "integer",
                "description": "Reclaim window in seconds (action=claim only; default 300).",
            },
            "state": {
                "type": "object",
                "description": "Intermediate state dict (action=write_state only).",
            },
            "reason": {
                "type": "string",
                "description": "Cancellation reason (action=cancel only).",
            },
            "terminal_state": {
                "type": "string",
                "description": "Terminal state string (action=complete only). e.g. PlanComplete | ConsensusReached.",
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
            # Extract kanban tool context from kwargs (passed by Hermes tool dispatch)
            kanban_ctx = kwargs.get("ctx") or kwargs.get("kanban_ctx")
            if kanban_ctx is None:
                # No context available — fall back to file backend
                log.warning("cyclus_queue: Kanban env set but no ctx available; falling back to file")
                return _file_action(action, args)
            return _kanban_action(action, args, kanban_ctx)

        elif backend == "saturate":
            # Future: Saturate backend
            return json.dumps({"error": "Saturate backend not yet implemented"})

        else:
            return _file_action(action, args)

    except HumanGatedViolation as exc:
        return json.dumps({"error": f"HumanGatedViolation: {exc}"})
    except ValueError as exc:
        return json.dumps({"error": str(exc)})
    except Exception as exc:
        log.exception("cyclus_queue(%s, %s, %r) failed", action, mode, instance_id)
        return json.dumps({"error": f"cyclus_queue({action}, {mode}, {instance_id!r}) failed: {exc}"})
