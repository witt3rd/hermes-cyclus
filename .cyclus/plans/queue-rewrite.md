# Ralph Plan — queue.py file-based rewrite (issue #5)

## Goal

Replace `queue.py` SQLite internals with atomic directory operations.
NFS-safe. Same six-operation interface. All tests pass.

## Context

- Repo: `/home/dt/src/witt3rd/cyclus`
- Issue: https://github.com/witt3rd/hermes-cyclus/issues/5
- Branch: `fix/5-file-based-queue`

## Tasks

### Task 1 — Rewrite queue.py with atomic directory operations

**Priority:** 1
**Dependencies:** none
**Files to modify:**
- `queue.py`

**Files to create:**
- none (tests already exist at `tests/test_queue.py`)

**Description:**

Replace the SQLite implementation in `queue.py` with atomic directory
operations. The `.cyclus/queue/` directory structure:

```
.cyclus/
  queue/
    pending/   <task_id>.json   # posted, awaiting claim
    active/    <task_id>.json   # claimed, heartbeat updated in-place
    done/      <task_id>.json   # completed or cancelled
  state/
    <mode>--<instance_id>/     # write_state() output per task
```

`claim()` = `os.rename(pending/<id>.json → active/<id>.json)`.
POSIX `rename()` is atomic within the same filesystem. NFS-safe.
No SQLite, no WAL, no journal files.

The six-operation interface (`post`, `claim`, `write_state`, `read_state`,
`record_turn`, `complete`, `release`, `cancel`, `status`, `counts`) stays
**identical** — same signatures, same return shapes, same `ClaimResult`
enum values.

Key implementation notes:
- Queue root defaults to `.cyclus/` in cwd; accept optional `root` param
- Use `uuid.uuid4()` for task IDs (already the pattern)
- `claim()` should scan `pending/` sorted by priority desc, mtime asc, attempt rename
- If rename fails (another worker claimed it), try next item — return `not_found` if none left
- `write_state()` writes a JSON sidecar to `state/<mode>--<instance_id>/state.json`
- `record_turn()` appends to `state/<mode>--<instance_id>/turns.jsonl`
- `heartbeat` = update `active/<id>.json` mtime via `os.utime`
- `complete()` = rename `active/<id>.json → done/<id>.json`, merge output into JSON
- `release()` = rename `active/<id>.json → pending/<id>.json`
- `cancel()` = set `cancel_requested: true` in the active JSON (in-place write)
- `status()` = read `active/<id>.json` or `done/<id>.json` or `pending/<id>.json`
- `counts()` = `len(listdir(pending))`, `len(listdir(active))`, `len(listdir(done))`

**Acceptance criteria:**

```python
def test_file_queue_claim_is_atomic():
    """Two concurrent claim() calls — exactly one wins, one gets not_found."""
    import threading
    q = FileQueue(root=tmp_path / ".cyclus")
    q.post("ralph", "test", "TaskExecutionKind", "test task")
    results = []
    def do_claim():
        r = q.claim("ralph", "test")
        results.append(r.status)
    t1 = threading.Thread(target=do_claim)
    t2 = threading.Thread(target=do_claim)
    t1.start(); t2.start()
    t1.join(); t2.join()
    assert results.count("claimed") == 1
    assert results.count("not_found") == 1

# All 79 existing tests must pass with no changes to test files
# (test_queue.py, test_integration.py, test_init.py, test_config.py, test_evidence.py)
```

**Commit message:**
```
feat(queue): replace SQLite with atomic file ops (NFS-safe)

Closes #5

claim() = os.rename(pending/→active/) — POSIX-atomic, NFS-safe.
Same six-operation interface. All 79 tests pass.
No WAL, no journal, no shared lock files.
```

## State

- [ ] Task 1 — queue.py rewrite
