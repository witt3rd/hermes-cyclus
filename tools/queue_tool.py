"""
cyclus_queue tool — Hermes tool handler wrapping the OMH internal queue.

Actions: post | claim | release | write_state | cancel | complete | status

All six operations delegate to queue.py. The handler is action-dispatched and
returns JSON strings, matching the pattern of state_tool.py.
"""

import json

from ..queue import (
    HumanGatedViolation,
    ClaimResult,
    cancel,
    claim,
    complete,
    post,
    release,
    status,
    write_state,
)

CYCLUS_QUEUE_SCHEMA = {
    "name": "cyclus_queue",
    "description": (
        "Cyclus work queue — file-based implementation of the six-operation interface. "
        "Actions: post | claim | release | write_state | cancel | complete | status | dispatch. "
        "Skills write against this interface; the plugin routes to the configured backend "
        "(files by default, kanban or saturate when configured). "
        "dispatch: post if not exists, return worker context for caller to fire via delegate_task."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": [
                    "post",
                    "claim",
                    "release",
                    "write_state",
                    "cancel",
                    "complete",
                    "status",
                    "dispatch",
                ],
                "description": "Operation to perform.",
            },
            "mode": {
                "type": "string",
                "description": (
                    "Mode name: ralph, ralplan, deep-research, autopilot, etc. "
                    "Required for all actions."
                ),
            },
            "instance_id": {
                "type": "string",
                "description": (
                    "Per-instance key (e.g. plan slug, goal slug). Required for all actions. "
                    "Slugified internally: lowercased, [a-z0-9-] only, max 80 chars."
                ),
            },
            # --- post-only ---
            "kind": {
                "type": "string",
                "description": (
                    "Saturate loop kind string (action=post only). "
                    "e.g. TaskExecutionKind | ConsensusKind | InformationSeekingKind | "
                    "ClarificationKind."
                ),
            },
            "name": {
                "type": "string",
                "description": "Human-readable loop name (action=post only).",
            },
            "max_turns": {
                "type": "integer",
                "description": (
                    "Maximum turns before forced terminal (action=post only; null = no limit)."
                ),
            },
            "tags": {
                "type": "array",
                "items": {"type": "string"},
                "description": (
                    "Tags for the work item (action=post only). "
                    "Use 'HUMAN_GATED' for ClarificationKind tasks that require explicit "
                    "human confirmation to complete."
                ),
            },
            "spawned_by": {
                "type": "string",
                "description": "Parent task_id (action=post only; null = root task).",
            },
            "depends_on": {
                "type": "array",
                "items": {"type": "string"},
                "description": (
                    "List of task_ids that must reach COMPLETE before this item is claimed "
                    "(action=post only)."
                ),
            },
            # --- claim-only ---
            "heartbeat_timeout_seconds": {
                "type": "integer",
                "description": (
                    "Seconds after which a RUNNING item with no heartbeat update is eligible "
                    "for reclaim (action=claim only; default 300). "
                    "Reduces deadlock window after a crash."
                ),
            },
            # --- write_state-only ---
            "state": {
                "type": "object",
                "description": (
                    "Intermediate state dict to persist to state_path and update last_heartbeat "
                    "(action=write_state only)."
                ),
            },
            # --- cancel-only ---
            "reason": {
                "type": "string",
                "description": "Cancellation reason (action=cancel only; default: 'user request').",
            },
            # --- complete-only ---
            "terminal_state": {
                "type": "string",
                "description": (
                    "Saturate TerminalState string (action=complete only). "
                    "e.g. PlanComplete | ConsensusReached | ResearchComplete | "
                    "Cancelled | Failed | Deadlocked."
                ),
            },
            "output": {
                "type": "object",
                "description": (
                    "Final output dict written to output_path (action=complete only; optional)."
                ),
            },
            "confirmed_by_human": {
                "type": "boolean",
                "description": (
                    "Must be true for HUMAN_GATED items (action=complete only; default false). "
                    "Set this after the human has explicitly confirmed completion."
                ),
            },
        },
        "required": ["action", "mode", "instance_id"],
    },
}


def cyclus_queue_handler(args: dict, **kwargs) -> str:
    """Dispatch an cyclus_queue action and return a JSON string."""
    action = args.get("action")
    mode = args.get("mode", "")
    instance_id = args.get("instance_id", "")

    if not mode:
        return json.dumps({"error": "mode is required"})
    if not instance_id:
        return json.dumps({"error": "instance_id is required"})

    try:
        match action:
            case "post":
                kind = args.get("kind") or "TaskExecutionKind"
                name = args.get("name") or instance_id
                task_id = post(
                    mode=mode,
                    instance_id=instance_id,
                    kind=kind,
                    name=name,
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
                result: ClaimResult = claim(mode=mode, instance_id=instance_id, **extra)
                return json.dumps({"status": result.status, "item": result.item})

            case "release":
                release(mode=mode, instance_id=instance_id)
                return json.dumps({"ok": True})

            case "write_state":
                state_data = args.get("state")
                if state_data is None:
                    return json.dumps({"error": "state is required for action=write_state"})
                if not isinstance(state_data, dict):
                    return json.dumps({"error": "state must be an object for action=write_state"})
                write_state(mode=mode, instance_id=instance_id, state=state_data)
                return json.dumps({"ok": True})

            case "cancel":
                cancel(
                    mode=mode,
                    instance_id=instance_id,
                    reason=args.get("reason", "user request"),
                )
                return json.dumps({"ok": True})

            case "complete":
                terminal = args.get("terminal_state")
                if not terminal:
                    return json.dumps({"error": "terminal_state is required for action=complete"})
                complete(
                    mode=mode,
                    instance_id=instance_id,
                    terminal_state=terminal,
                    output=args.get("output"),
                    confirmed_by_human=bool(args.get("confirmed_by_human", False)),
                )
                return json.dumps({"ok": True})

            case "status":
                result_dict = status(mode=mode, instance_id=instance_id)
                return json.dumps(result_dict if result_dict is not None else {"found": False})

            case "dispatch":
                # Push model: post if not exists, return dispatch context.
                # For file-based backend: caller fires a worker via delegate_task.
                # For Kanban/Saturate: posting is sufficient (backend fires automatically).
                info = status(mode=mode, instance_id=instance_id)
                if info is None:
                    kind = args.get("kind", "TaskExecutionKind")
                    name = args.get("name", instance_id)
                    post(
                        mode=mode,
                        instance_id=instance_id,
                        kind=kind,
                        name=name,
                        max_turns=args.get("max_turns"),
                        tags=args.get("tags"),
                        spawned_by=args.get("spawned_by"),
                        depends_on=args.get("depends_on"),
                    )
                    info = status(mode=mode, instance_id=instance_id)
                if info and info.get("status") not in ("PENDING", "RUNNING"):
                    return json.dumps({
                        "error": f"Cannot dispatch: item is already {info['status']}"
                    })
                return json.dumps({
                    "dispatched": True,
                    "mode": mode,
                    "instance_id": instance_id,
                    "task_id": info["task_id"] if info else None,
                    "kind": info["kind"] if info else None,
                    "name": info["name"] if info else None,
                    "status": info["status"] if info else None,
                    "state_path": info["state_path"] if info else None,
                    "worker_note": (
                        "File-based backend: call delegate_task with cyclus-ralph skill "
                        "and this context to fire the worker. "
                        "Kanban/Saturate: backend fires automatically on post."
                    ),
                })

            case _:
                valid = "post, claim, release, write_state, cancel, complete, status"
                raise ValueError(
                    f"Unknown action: {action!r}. Valid actions: {valid}"
                )

    except HumanGatedViolation as exc:
        return json.dumps({"error": f"HumanGatedViolation: {exc}"})
    except ValueError as exc:
        return json.dumps({"error": str(exc)})
    except Exception as exc:
        logger_name = f"cyclus_queue({action}, {mode}, {instance_id!r})"
        import logging
        logging.getLogger(__name__).exception("%s failed", logger_name)
        return json.dumps({"error": f"{logger_name} failed: {exc}"})
