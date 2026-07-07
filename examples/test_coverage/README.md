# Test Coverage

Increase test coverage of hermes-cyclus itself by adding test cases targeting
untested code paths, edge cases, error handling, and boundary conditions.

This is the *meta* example: **Cyclus improving its own test suite**.

## Target files

Workers may add or modify files in:
- `tests/` — add new test files or extend existing ones

Workers must NOT modify:
- `queue.py`, `tools/`, `__init__.py`, `cyclus_config.py` — production code is
  off-limits; only the tests change

## Why this is interesting

- **Zero infrastructure**: runs against the repo itself, no external deps
- **Self-referential**: the loop that improves coverage is itself a Cyclus loop
- **Good Kanban test case**: moderate eval time (~5s), long-running improvement arc,
  human can review PRs from workers as they land

## Distributed advantage

Multiple workers can tackle different modules concurrently:
```
Worker 1: claim() → add edge cases for queue.py release()
Worker 2: claim() → add error handling tests for evidence_tool
Worker 3: claim() → add integration tests for cyclus_config
```

Workers coordinate via `write_state()` — each records which code paths it covered so
the next worker targets gaps rather than duplicating coverage.
