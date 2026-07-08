# LOOP.md — hermes-cyclus Dogfood Loops

> hermes-cyclus eats its own dogfood. All future work on this repo runs
> through Cyclus loops. This file documents every active loop, the exact
> commands to start it, and its current phase.
>
> Pattern: Greyling's loop-engineering `LOOP.md` convention.

---

## Philosophy

Loop engineering replaces you as the person who prompts the agent — you
design the system that does it instead. For hermes-cyclus specifically:

- **Implementation work** (issues, rewrites) → `cyclus-ralph` TaskExecutionKind loop
- **Metric optimization** (eval improvement) → `MetricOptimizationKind` loop  
- **Self-improvement** (test coverage) → `MetricOptimizationKind` loop on itself

All loops start at **L1 (report-only)**. No loop auto-commits until L1 output
has been reviewed for at least one full cycle.

---

## Active Loops

### 1. function-minimization (L1 — MetricOptimizationKind)

Optimizes `examples/function_minimization/code/initial_program.py` to find
the global minimum of `f(x,y) = sin(x)*cos(y) + sin(x*y) + (x²+y²)/20`.
Baseline: `combined_score = 0.56`. Target: > 1.3.

**Start (L1 — propose only, no commits):**

```bash
hermes cron create "0 8 * * 1-5" \
  --name "cyclus-function-minimization" \
  --skill cyclus-ralph \
  --workdir "/home/dt/src/witt3rd/cyclus" \
  --deliver local \
  "Read examples/function_minimization/spec.md. Read STATE.md. \
Run one MetricOptimizationKind turn: propose one improvement to \
examples/function_minimization/code/initial_program.py between the \
EVOLVE-BLOCK markers. Write the proposed diff as a fenced patch block \
to STATE.md under 'Loop Run Log'. Do NOT apply the patch (level: L1). \
Run the eval command and report the projected combined_score. \
Update STATE.md Last run timestamp."
```

**Status:** 🔲 not started  
**Spec:** `examples/function_minimization/spec.md`

---

### 2. test-coverage (L1 — MetricOptimizationKind)

Increases test coverage of hermes-cyclus itself. Baseline: run eval first
to establish. Target: 90% line coverage.

**Start (L1 — propose new tests, no commits):**

```bash
hermes cron create "0 9 * * 1-5" \
  --name "cyclus-test-coverage" \
  --skill cyclus-ralph \
  --workdir "/home/dt/src/witt3rd/cyclus" \
  --deliver local \
  "Read examples/test_coverage/spec.md. Read STATE.md. \
Run one MetricOptimizationKind turn: identify the least-covered code \
path in the Cyclus source, propose a new test or test extension as a \
fenced patch block. Do NOT apply the patch (level: L1). \
Run: PYTHONPATH=. uv run pytest tests/ --cov=. --cov-report=json -q 2>/dev/null \
and report coverage_percent. Update STATE.md."
```

**Status:** 🔲 not started  
**Spec:** `examples/test_coverage/spec.md`

---

### 3. queue-rewrite (L1 — TaskExecutionKind / cyclus-ralph)

Implements hermes-cyclus issue #5: replace `queue.py` SQLite internals
with file-based atomic directory operations (NFS-safe).

**Start (L1 — implement in worktree, propose PR):**

```bash
hermes cron create "0 10 * * *" \
  --name "cyclus-queue-rewrite" \
  --skill cyclus-ralph \
  --workdir "/home/dt/src/witt3rd/cyclus" \
  --deliver local \
  "Read https://github.com/witt3rd/hermes-cyclus/issues/5. \
Read queue.py and tests/test_queue.py. \
Run one cyclus-ralph task: implement the file-based queue backend \
(atomic os.rename, pending/active/done dirs, same six-operation interface). \
Create a git worktree at /tmp/cyclus-queue-rewrite, apply changes there, \
run PYTHONPATH=. uv run pytest tests/ -q to verify all 35 tests pass. \
Write a summary of what was done and the test results to STATE.md. \
Do NOT commit (level: L1 — human reviews before commit)."
```

**Status:** 🔲 not started  
**Issue:** https://github.com/witt3rd/hermes-cyclus/issues/5

---

## Multi-Loop Schedule

```
08:00  function-minimization proposer (weekdays)
09:00  test-coverage proposer (weekdays)
10:00  queue-rewrite implementer (daily)
```

No loops share target files — no collision risk at current scope.

## Budget

| Loop | Max runs/day | Deliver |
|------|-------------|---------|
| function-minimization | 1 | local |
| test-coverage | 1 | local |
| queue-rewrite | 1 | local |

Kill switch: set `loop-pause-all: true` in `STATE.md`.

## Safety (L1 — all loops)

- All loops `--deliver local` — output in `~/.hermes/profiles/forge/cron/`
- No loop auto-commits until human has reviewed one full cycle
- `STATE.md` is the human inbox — read it before enabling L2

## Operations

```bash
hermes cron list                        # see all loops
hermes cron run <job-id>               # fire once immediately
hermes cron pause <job-id>             # pause without removing
hermes cron resume <job-id>            # resume
hermes cron remove <job-id>            # remove permanently
```

## Graduation to L2

When a loop's L1 output is consistently correct and useful:

1. Verify eval command is read-only (does not modify repo state)
2. Add a verifier cron job chained via `--context-from <proposer-id>`
3. Verifier applies the patch in an isolated `git worktree`, runs tests
4. Update `level: L2` in the spec and this file

---

*"Build the loop. Stay the engineer."* — Addy Osmani
