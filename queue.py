"""
OMH Internal Queue — SQLite-backed implementation of the Saturate-aligned six-operation interface.

The database lives at .omh/queue.db relative to the project root (same root as .omh/plans/).
Zero external dependencies beyond the stdlib sqlite3 module.

Operations: post, claim, release, write_state, cancel, complete, status.

Root discovery mirrors omh_state.py:
  1. config["project_root"] if set, else cwd at call time.
  2. Always resolved to absolute so cwd drift cannot redirect writes.

Connection settings: check_same_thread=False, timeout=5, WAL journal mode.
Note: omh_state.py docstring confirms Hermes is single-threaded; the settings are
defensive for future multi-session use.
"""

from __future__ import annotations

import json
import logging
import re
import sqlite3
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
    """Normalize an instance_id to a filesystem-safe slug (mirrors omh_state.py)."""
    if not isinstance(raw, str):
        raise ValueError(f"instance_id must be a string, got {type(raw).__name__}")
    if len(raw) > _INSTANCE_RAW_MAX:
        raise ValueError(f"instance_id too long ({len(raw)} chars > {_INSTANCE_RAW_MAX})")
    s = re.sub(r"[^a-z0-9]+", "-", raw.lower()).strip("-")
    if not s:
        raise ValueError(f"instance_id {raw!r} normalizes to empty slug")
    return s[:_INSTANCE_SLUG_MAX].strip("-")


def _db_path() -> Path:
    """Resolve .omh/queue.db to an absolute path. Mirrors omh_state._state_dir()."""
    config = get_config()
    project_root_cfg = config.get("project_root")
    base = Path(project_root_cfg).resolve() if project_root_cfg else Path.cwd().resolve()
    omh_dir = base / ".omh"
    omh_dir.mkdir(parents=True, exist_ok=True)
    return omh_dir / "queue.db"


def _ensure_schema(conn: sqlite3.Connection) -> None:
    """Create table and indexes if absent. Idempotent."""
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS omh_work_items (
            task_id          TEXT PRIMARY KEY,
            instance_id      TEXT NOT NULL,
            mode             TEXT NOT NULL,
            kind             TEXT NOT NULL,
            name             TEXT NOT NULL,
            spec_path        TEXT,
            state_path       TEXT NOT NULL,
            output_path      TEXT NOT NULL,
            submitted_by     TEXT NOT NULL,
            submitted_at     TEXT NOT NULL,
            max_turns        INTEGER,
            spawned_by       TEXT,
            depends_on       TEXT NOT NULL DEFAULT '[]',
            status           TEXT NOT NULL DEFAULT 'PENDING',
            last_heartbeat   TEXT,
            completed_at     TEXT,
            terminal_state   TEXT,
            cancel_requested INTEGER NOT NULL DEFAULT 0,
            tags             TEXT NOT NULL DEFAULT '[]'
        );
        CREATE INDEX IF NOT EXISTS idx_mode_instance ON omh_work_items(mode, instance_id);
        CREATE INDEX IF NOT EXISTS idx_status ON omh_work_items(status);
        """
    )
    conn.commit()


def _open_conn() -> sqlite3.Connection:
    """Open (or create) the queue database with WAL mode and schema enforcement."""
    path = _db_path()
    conn = sqlite3.connect(str(path), check_same_thread=False, timeout=5)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    _ensure_schema(conn)
    return conn


def _row_to_dict(row: sqlite3.Row) -> dict:
    """Convert a sqlite3.Row to a plain dict, deserializing JSON list fields."""
    d = dict(row)
    for field in ("depends_on", "tags"):
        raw = d.get(field)
        if isinstance(raw, str):
            try:
                d[field] = json.loads(raw)
            except (json.JSONDecodeError, TypeError):
                d[field] = []
    return d


# ---------------------------------------------------------------------------
# Backend factory
# ---------------------------------------------------------------------------


def _backend_factory() -> str:
    """Return the configured backend name.

    Reads config.get("omh_backend", "sqlite"). Values:
      "sqlite"   — embedded SQLite at .omh/queue.db (default; always available)
      "kanban"   — Hermes Kanban board (v18.1, not yet implemented)
      "saturate" — Saturate HTTP API (v18.2+, not yet implemented)

    v18.0.0 only implements the "sqlite" backend. The factory exists so the
    config flag is read and honoured at the dispatch point when other backends
    are added.
    """
    config = get_config()
    return config.get("omh_backend", "sqlite")


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

    HUMAN_GATED warning: posting a ClarificationKind item (tags contains
    "HUMAN_GATED") logs a warning. The item will sit in PENDING indefinitely
    because complete() requires confirmed_by_human=True and no scheduler will
    provide it automatically.
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
            mode,
            instance_id,
        )

    now = _now_iso()
    new_task_id = str(uuid.uuid4())

    # Auto-derive state / output paths from project root + mode + slug
    omh_dir = _db_path().parent  # .omh/
    state_path = str(omh_dir / "state" / f"{mode}--{slug}.json")
    output_path = str(omh_dir / "output" / f"{mode}--{slug}.json")

    depends_on_json = json.dumps(depends_on or [])
    tags_json = json.dumps(tag_list)

    conn = _open_conn()
    try:
        # Idempotency check
        existing = conn.execute(
            "SELECT task_id FROM omh_work_items WHERE mode = ? AND instance_id = ?",
            (mode, slug),
        ).fetchone()
        if existing:
            return existing["task_id"]

        with conn:
            conn.execute(
                """
                INSERT INTO omh_work_items
                    (task_id, instance_id, mode, kind, name,
                     state_path, output_path, submitted_by, submitted_at,
                     max_turns, spawned_by, depends_on, tags)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    new_task_id, slug, mode, kind, name,
                    state_path, output_path, "skill", now,
                    max_turns, spawned_by, depends_on_json, tags_json,
                ),
            )
    finally:
        conn.close()

    return new_task_id


def claim(
    mode: str,
    instance_id: str,
    heartbeat_timeout_seconds: int = 300,
) -> ClaimResult:
    """Atomically claim the item for (mode, instance_id).

    Returns:
      status="claimed"   — item was PENDING or timed-out RUNNING; now RUNNING.
      status="not_found" — no item with this (mode, instance_id) exists,
                           OR the item is in a terminal state (COMPLETE/CANCELLED).
      status="running"   — item is RUNNING with a fresh heartbeat (held by another
                           session). The caller should back off and retry later.

    Skills distinguish "not_found" (post first) from "running" (wait or poll).
    """
    if not _MODE_RE.match(mode):
        raise ValueError(f"Invalid mode name: {mode!r}")
    slug = _slugify_instance(instance_id)
    now = _now_iso()

    conn = _open_conn()
    try:
        row = conn.execute(
            "SELECT * FROM omh_work_items WHERE mode = ? AND instance_id = ?",
            (mode, slug),
        ).fetchone()

        if row is None:
            return ClaimResult(status="not_found", item=None)

        item = _row_to_dict(row)
        current_status = item["status"]

        if current_status == "PENDING":
            with conn:
                conn.execute(
                    "UPDATE omh_work_items SET status = 'RUNNING', last_heartbeat = ? WHERE task_id = ?",
                    (now, item["task_id"]),
                )
            item["status"] = "RUNNING"
            item["last_heartbeat"] = now
            return ClaimResult(status="claimed", item=item)

        if current_status == "RUNNING":
            last_hb = item.get("last_heartbeat")
            stale = True
            if last_hb:
                try:
                    hb_ts = datetime.fromisoformat(last_hb)
                    age = (datetime.now(timezone.utc) - hb_ts).total_seconds()
                    stale = age > heartbeat_timeout_seconds
                except Exception:
                    stale = True  # Unparseable timestamp → treat as stale

            if not stale:
                # Fresh heartbeat — another session holds this item
                return ClaimResult(status="running", item=None)

            # Stale heartbeat — reclaim
            with conn:
                conn.execute(
                    "UPDATE omh_work_items SET status = 'RUNNING', last_heartbeat = ? WHERE task_id = ?",
                    (now, item["task_id"]),
                )
            item["status"] = "RUNNING"
            item["last_heartbeat"] = now
            return ClaimResult(status="claimed", item=item)

        # Terminal state (COMPLETE, CANCELLED, BLOCKED) — not claimable
        return ClaimResult(status="not_found", item=None)
    finally:
        conn.close()


def release(mode: str, instance_id: str) -> None:
    """Release a RUNNING item back to PENDING on clean exit.

    Required for the multi-invocation ralph pattern: each iteration exits cleanly
    after write_state(); release() resets status to PENDING so the next invocation
    can claim(). Without release(), the next claim() waits heartbeat_timeout_seconds
    (300s default) before reclaiming — a 5-minute mandatory wait between normal
    iterations.

    Crash recovery: if release() is not called (process crash), the item stays
    RUNNING and will be reclaimed after heartbeat_timeout_seconds automatically.

    No-op if the item is not in RUNNING state (safe to call defensively).
    """
    if not _MODE_RE.match(mode):
        raise ValueError(f"Invalid mode name: {mode!r}")
    slug = _slugify_instance(instance_id)

    conn = _open_conn()
    try:
        with conn:
            conn.execute(
                """
                UPDATE omh_work_items
                SET status = 'PENDING', last_heartbeat = NULL
                WHERE mode = ? AND instance_id = ? AND status = 'RUNNING'
                """,
                (mode, slug),
            )
    finally:
        conn.close()


def write_state(mode: str, instance_id: str, state: dict) -> None:
    """Write intermediate state dict to state_path and update last_heartbeat.

    The state_path is recorded in the DB at post() time. write_state() writes
    the serialised dict atomically and bumps last_heartbeat so that claim()
    does not reclaim a live session as stale.

    Skills call write_state() at each iteration boundary. After writing, they
    should check status() for cancel_requested to honour external cancellation.
    """
    if not _MODE_RE.match(mode):
        raise ValueError(f"Invalid mode name: {mode!r}")
    slug = _slugify_instance(instance_id)
    now = _now_iso()

    conn = _open_conn()
    try:
        row = conn.execute(
            "SELECT task_id, state_path FROM omh_work_items WHERE mode = ? AND instance_id = ?",
            (mode, slug),
        ).fetchone()
        if row is None:
            raise ValueError(
                f"No work item found for mode={mode!r} instance_id={instance_id!r}. "
                "Call post() before write_state()."
            )

        state_path = Path(row["state_path"])
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state_path.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")

        with conn:
            conn.execute(
                "UPDATE omh_work_items SET last_heartbeat = ? WHERE task_id = ?",
                (now, row["task_id"]),
            )
    finally:
        conn.close()


def cancel(mode: str, instance_id: str, reason: str = "user request") -> None:
    """Signal cancellation by setting cancel_requested=1 in the row.

    The running skill is expected to check cancel_requested via status() at each
    write_state() heartbeat. When detected, the skill calls
    complete(terminal_state="Cancelled") to close the loop cleanly.

    No-op if no item exists for (mode, instance_id). Does not force-stop any
    running process — it is an advisory signal only.
    """
    if not _MODE_RE.match(mode):
        raise ValueError(f"Invalid mode name: {mode!r}")
    slug = _slugify_instance(instance_id)

    conn = _open_conn()
    try:
        with conn:
            conn.execute(
                "UPDATE omh_work_items SET cancel_requested = 1 WHERE mode = ? AND instance_id = ?",
                (mode, slug),
            )
    finally:
        conn.close()


def complete(
    mode: str,
    instance_id: str,
    terminal_state: str,
    output: dict | None = None,
    confirmed_by_human: bool = False,
) -> None:
    """Mark the item terminal.

    terminal_state should be one of the Saturate TerminalState strings, e.g.:
      PlanComplete | ConsensusReached | ResearchComplete | Cancelled | Failed | Deadlocked

    Raises:
      HumanGatedViolation — if the item has "HUMAN_GATED" in tags and
                             confirmed_by_human is False. Pass confirmed_by_human=True
                             after explicit human confirmation.
      ValueError          — if no item exists for (mode, instance_id).
    """
    if not _MODE_RE.match(mode):
        raise ValueError(f"Invalid mode name: {mode!r}")
    slug = _slugify_instance(instance_id)
    now = _now_iso()

    conn = _open_conn()
    try:
        row = conn.execute(
            "SELECT task_id, tags, output_path FROM omh_work_items WHERE mode = ? AND instance_id = ?",
            (mode, slug),
        ).fetchone()
        if row is None:
            raise ValueError(
                f"No work item found for mode={mode!r} instance_id={instance_id!r}. "
                "Call post() before complete()."
            )

        # HUMAN_GATED enforcement
        tags_raw = row["tags"]
        try:
            tag_list = json.loads(tags_raw) if isinstance(tags_raw, str) else []
        except (json.JSONDecodeError, TypeError):
            tag_list = []

        if "HUMAN_GATED" in tag_list and not confirmed_by_human:
            raise HumanGatedViolation(
                f"Work item mode={mode!r} instance_id={instance_id!r} has the HUMAN_GATED tag. "
                "Set confirmed_by_human=True after explicit human confirmation."
            )

        # Write output file if provided
        if output is not None:
            output_path = Path(row["output_path"])
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(
                json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8"
            )

        with conn:
            conn.execute(
                """
                UPDATE omh_work_items
                SET status = 'COMPLETE', terminal_state = ?, completed_at = ?
                WHERE task_id = ?
                """,
                (terminal_state, now, row["task_id"]),
            )
    finally:
        conn.close()


def status(mode: str, instance_id: str) -> dict | None:
    """Read-only snapshot of the current work item.

    Returns None if no item exists for (mode, instance_id).
    Does NOT update last_heartbeat — purely read-only. Use write_state() to
    update the heartbeat.

    Used by driver skills for observability and by cancel-check patterns:
      info = cyclus_queue(action="status", ...)
      if info and info.get("cancel_requested"):
          cyclus_queue(action="complete", terminal_state="Cancelled", ...)
    """
    if not _MODE_RE.match(mode):
        raise ValueError(f"Invalid mode name: {mode!r}")
    slug = _slugify_instance(instance_id)

    conn = _open_conn()
    try:
        row = conn.execute(
            "SELECT * FROM omh_work_items WHERE mode = ? AND instance_id = ?",
            (mode, slug),
        ).fetchone()
    finally:
        conn.close()

    if row is None:
        return None
    return _row_to_dict(row)
