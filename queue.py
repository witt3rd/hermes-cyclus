"""
hermes-cyclus File-based Queue — NFS-safe implementation of the queue interface.

State lives in .cyclus/ relative to project root:
  .cyclus/
    queue/
      pending/   {mode}--{slug}.json   # posted, awaiting claim
      active/    {mode}--{slug}.json   # claimed; last_heartbeat in JSON
      done/      {mode}--{slug}.json   # completed or cancelled
    state/
      {mode}--{slug}/
        state.json      # write_state() output
        turns.jsonl     # record_turn() appends

claim() = os.rename(pending/→active/) — POSIX-atomic, NFS-safe.
No SQLite, no WAL, no journal files.
"""

from __future__ import annotations

import json
import logging
import os
import re
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from .cyclus_config import get_config

logger = logging.getLogger(__name__)

_MODE_RE = re.compile(r"^[a-zA-Z0-9_-]+$")
_INSTANCE_RAW_MAX = 200
_INSTANCE_SLUG_MAX = 80


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class HumanGatedViolation(Exception):
    """Raised by complete() when the item has the HUMAN_GATED tag and
    confirmed_by_human=False. ClarificationKind tasks require explicit
    human confirmation before they can be marked terminal."""


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------


@dataclass
class ClaimResult:
    """Return type for claim(). Distinguishes three exclusive states."""

    status: Literal["claimed", "not_found", "running"]
    item: dict | None  # populated only when status="claimed"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _slugify_instance(raw: str) -> str:
    """Normalize an instance_id to a filesystem-safe slug."""
    if not isinstance(raw, str):
        raise ValueError(f"instance_id must be a string, got {type(raw).__name__}")
    if len(raw) > _INSTANCE_RAW_MAX:
        raise ValueError(f"instance_id too long ({len(raw)} chars > {_INSTANCE_RAW_MAX})")
    s = re.sub(r"[^a-z0-9]+", "-", raw.lower()).strip("-")
    if not s:
        raise ValueError(f"instance_id {raw!r} normalizes to empty slug")
    return s[:_INSTANCE_SLUG_MAX].strip("-")


def _queue_root() -> Path:
    """Resolve .cyclus/ to an absolute path and ensure all subdirs exist."""
    config = get_config()
    project_root_cfg = config.get("project_root")
    base = Path(project_root_cfg).resolve() if project_root_cfg else Path.cwd().resolve()
    root = base / ".cyclus"
    for sub in ("queue/pending", "queue/active", "queue/done"):
        (root / sub).mkdir(parents=True, exist_ok=True)
    return root


def _item_name(mode: str, slug: str) -> str:
    return f"{mode}--{slug}.json"


def _find_item(root: Path, mode: str, slug: str) -> tuple[Path | None, str | None]:
    """Return (path, location) where location is 'active'|'pending'|'done'|None."""
    name = _item_name(mode, slug)
    for loc in ("active", "pending", "done"):
        p = root / "queue" / loc / name
        if p.exists():
            return p, loc
    return None, None


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


# ---------------------------------------------------------------------------
# Six operations
# ---------------------------------------------------------------------------


def post(
    mode: str,
    instance_id: str,
    kind: str,
    name: str,
    max_turns: int | None = None,
    tags: list[str] | None = None,
    spawned_by: str | None = None,
    depends_on: list[str] | None = None,
) -> str:
    """Submit a work item. Returns task_id. Idempotent on (mode, instance_id).

    If an item already exists for (mode, instance_id), its task_id is returned
    regardless of current status. Skills use a new instance_id for a fresh run.
    """
    if not _MODE_RE.match(mode):
        raise ValueError(f"Invalid mode name: {mode!r} (only [a-zA-Z0-9_-] allowed)")
    slug = _slugify_instance(instance_id)
    tag_list: list[str] = tags or []

    if "HUMAN_GATED" in tag_list:
        logger.warning(
            "post() received a HUMAN_GATED item (mode=%r, instance_id=%r). "
            "ClarificationKind tasks should not be posted to the queue — "
            "they will sit in PENDING indefinitely with no auto-complete path.",
            mode, instance_id,
        )

    root = _queue_root()

    # Idempotency: return existing task_id if (mode, instance_id) already posted
    path, _ = _find_item(root, mode, slug)
    if path is not None:
        return _read_json(path)["task_id"]

    now = _now_iso()
    task_id = str(uuid.uuid4())
    state_dir = root / "state" / f"{mode}--{slug}"
    state_path = str(state_dir / "state.json")
    output_path = str(state_dir / "output.json")

    data = {
        "task_id": task_id,
        "instance_id": slug,
        "mode": mode,
        "kind": kind,
        "name": name,
        "spec_path": None,
        "state_path": state_path,
        "output_path": output_path,
        "submitted_by": "skill",
        "submitted_at": now,
        "max_turns": max_turns,
        "spawned_by": spawned_by,
        "depends_on": depends_on or [],
        "status": "PENDING",
        "last_heartbeat": None,
        "completed_at": None,
        "terminal_state": None,
        "cancel_requested": 0,
        "tags": tag_list,
    }
    _write_json(root / "queue" / "pending" / _item_name(mode, slug), data)
    return task_id


def claim(
    mode: str,
    instance_id: str,
    heartbeat_timeout_seconds: int = 300,
) -> ClaimResult:
    """Atomically claim the item for (mode, instance_id).

    Returns:
      status="claimed"   — item was PENDING or stale RUNNING; now RUNNING.
      status="not_found" — no item exists, or item is in a terminal state.
      status="running"   — item is RUNNING with a fresh heartbeat (held by another
                           session). The caller should back off and retry later.

    claim() = os.rename(pending/→active/) — atomic on POSIX/NFS.
    """
    if not _MODE_RE.match(mode):
        raise ValueError(f"Invalid mode name: {mode!r}")
    slug = _slugify_instance(instance_id)
    root = _queue_root()
    name = _item_name(mode, slug)
    pending = root / "queue" / "pending" / name
    active = root / "queue" / "active" / name
    now = _now_iso()

    # Active: running or stale
    if active.exists():
        data = _read_json(active)
        last_hb = data.get("last_heartbeat")
        stale = True
        if last_hb:
            try:
                hb_ts = datetime.fromisoformat(last_hb)
                age = (datetime.now(timezone.utc) - hb_ts).total_seconds()
                stale = age > heartbeat_timeout_seconds
            except Exception:
                stale = True

        if not stale:
            return ClaimResult(status="running", item=None)

        # Stale heartbeat — reclaim in place (already in active/)
        data["status"] = "RUNNING"
        data["last_heartbeat"] = now
        _write_json(active, data)
        return ClaimResult(status="claimed", item=data)

    # Atomic claim from pending via rename
    if pending.exists():
        # Read data first for the update, but the actual claim is the rename.
        # Rename pending→active atomically; if it fails, another worker won.
        try:
            data = _read_json(pending)
        except (FileNotFoundError, json.JSONDecodeError):
            return ClaimResult(status="not_found", item=None)
        data["status"] = "RUNNING"
        data["last_heartbeat"] = now
        # Write updated content to a unique tmp, then atomically rename tmp→active.
        # The pending file stays until we unlink it — the race window is
        # pending.exists() → os.rename(tmp, active). Both callers may pass the
        # exists() check, but os.rename(tmp, active) does NOT clobber an existing
        # file on Linux (EEXIST/ENOTEMPTY for directories; for files it replaces).
        # The true mutual exclusion comes from trying to unlink pending after the
        # rename — only one caller can unlink it; the other finds it gone.
        # Actually: use rename(pending, active) directly as the atomic gate.
        try:
            os.rename(pending, active)
        except (FileNotFoundError, OSError):
            # Lost the race — another worker renamed pending away
            return ClaimResult(status="not_found", item=None)
        # We own it — write the updated content
        _write_json(active, data)
        return ClaimResult(status="claimed", item=data)

    # Done or absent — not claimable
    return ClaimResult(status="not_found", item=None)


def release(mode: str, instance_id: str) -> None:
    """Release a RUNNING item back to PENDING on clean exit.

    Required for the multi-invocation ralph pattern: each iteration exits cleanly
    after write_state(); release() resets status to PENDING so the next invocation
    can claim() immediately without waiting for heartbeat timeout.

    No-op if the item is not in RUNNING state.
    """
    if not _MODE_RE.match(mode):
        raise ValueError(f"Invalid mode name: {mode!r}")
    slug = _slugify_instance(instance_id)
    root = _queue_root()
    name = _item_name(mode, slug)
    active = root / "queue" / "active" / name
    pending = root / "queue" / "pending" / name

    if not active.exists():
        return  # no-op

    data = _read_json(active)
    data["status"] = "PENDING"
    data["last_heartbeat"] = None
    _write_json(active, data)
    try:
        os.rename(active, pending)
    except (FileNotFoundError, OSError):
        pass  # already gone — safe to ignore


def write_state(mode: str, instance_id: str, state: dict) -> None:
    """Write intermediate state dict to state_path and update last_heartbeat.

    Skills call write_state() at each iteration boundary. After writing, they
    should check status() for cancel_requested to honour external cancellation.
    """
    if not _MODE_RE.match(mode):
        raise ValueError(f"Invalid mode name: {mode!r}")
    slug = _slugify_instance(instance_id)
    root = _queue_root()
    name = _item_name(mode, slug)
    active = root / "queue" / "active" / name

    if not active.exists():
        raise ValueError(
            f"No active work item for mode={mode!r} instance_id={instance_id!r}. "
            "Call post() and claim() before write_state()."
        )

    now = _now_iso()
    data = _read_json(active)
    data["last_heartbeat"] = now
    _write_json(active, data)

    state_path = Path(data["state_path"])
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")


def cancel(mode: str, instance_id: str, reason: str = "user request") -> None:
    """Signal cancellation by setting cancel_requested=1.

    Advisory signal only — does not force-stop any running process.
    No-op if no item exists for (mode, instance_id).
    """
    if not _MODE_RE.match(mode):
        raise ValueError(f"Invalid mode name: {mode!r}")
    slug = _slugify_instance(instance_id)
    root = _queue_root()
    path, _ = _find_item(root, mode, slug)
    if path is None:
        return
    data = _read_json(path)
    data["cancel_requested"] = 1
    _write_json(path, data)


def complete(
    mode: str,
    instance_id: str,
    terminal_state: str,
    output: dict | None = None,
    confirmed_by_human: bool = False,
) -> None:
    """Mark the item terminal.

    terminal_state: PlanComplete | ConsensusReached | ResearchComplete |
                    Cancelled | Failed | Deadlocked

    Raises:
      HumanGatedViolation — if the item has "HUMAN_GATED" in tags and
                             confirmed_by_human is False.
      ValueError          — if no item exists for (mode, instance_id).
    """
    if not _MODE_RE.match(mode):
        raise ValueError(f"Invalid mode name: {mode!r}")
    slug = _slugify_instance(instance_id)
    root = _queue_root()
    path, loc = _find_item(root, mode, slug)

    if path is None:
        raise ValueError(
            f"No work item found for mode={mode!r} instance_id={instance_id!r}. "
            "Call post() before complete()."
        )

    data = _read_json(path)

    if "HUMAN_GATED" in data.get("tags", []) and not confirmed_by_human:
        raise HumanGatedViolation(
            f"Work item mode={mode!r} instance_id={instance_id!r} has the HUMAN_GATED tag. "
            "Set confirmed_by_human=True after explicit human confirmation."
        )

    now = _now_iso()
    data["status"] = "COMPLETE"
    data["terminal_state"] = terminal_state
    data["completed_at"] = now

    if output is not None:
        output_path = Path(data["output_path"])
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")

    done = root / "queue" / "done" / _item_name(mode, slug)
    _write_json(path, data)
    if loc != "done":
        try:
            os.rename(path, done)
        except (FileNotFoundError, OSError):
            # Race — write to done directly
            _write_json(done, data)


def status(mode: str, instance_id: str) -> dict | None:
    """Read-only snapshot of the current work item.

    Returns None if no item exists for (mode, instance_id).
    Does NOT update last_heartbeat — purely read-only.

    Used by driver skills for observability and cancel-check patterns:
      info = cyclus_queue(action="status", ...)
      if info and info.get("cancel_requested"):
          cyclus_queue(action="complete", terminal_state="Cancelled", ...)
    """
    if not _MODE_RE.match(mode):
        raise ValueError(f"Invalid mode name: {mode!r}")
    slug = _slugify_instance(instance_id)
    root = _queue_root()
    path, _ = _find_item(root, mode, slug)
    if path is None:
        return None
    return _read_json(path)


# ---------------------------------------------------------------------------
# Additional operations
# ---------------------------------------------------------------------------


def read_state(mode: str, instance_id: str) -> dict:
    """Read the state file for a work item. Returns {} if not yet written."""
    slug = _slugify_instance(instance_id)
    root = _queue_root()
    state_path = root / "state" / f"{mode}--{slug}" / "state.json"
    if not state_path.exists():
        return {}
    return json.loads(state_path.read_text(encoding="utf-8"))


def record_turn(mode: str, instance_id: str, turn: dict) -> None:
    """Append a turn record to the turns.jsonl file."""
    slug = _slugify_instance(instance_id)
    root = _queue_root()
    turns_path = root / "state" / f"{mode}--{slug}" / "turns.jsonl"
    turns_path.parent.mkdir(parents=True, exist_ok=True)
    with turns_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(turn, ensure_ascii=False) + "\n")


def turn_history(mode: str, instance_id: str) -> list[dict]:
    """Return all recorded turns for a work item."""
    slug = _slugify_instance(instance_id)
    root = _queue_root()
    turns_path = root / "state" / f"{mode}--{slug}" / "turns.jsonl"
    if not turns_path.exists():
        return []
    return [
        json.loads(line)
        for line in turns_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def counts() -> dict:
    """Return counts of items in each queue directory."""
    root = _queue_root()
    return {
        "pending": len(list((root / "queue" / "pending").glob("*.json"))),
        "active": len(list((root / "queue" / "active").glob("*.json"))),
        "done": len(list((root / "queue" / "done").glob("*.json"))),
    }


def get(mode: str, instance_id: str) -> dict | None:
    """Alias for status()."""
    return status(mode, instance_id)
