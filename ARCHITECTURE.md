# hermes-cyclus — Architecture

> **Status:** Active — 2026-07-07
> **Companion:** [`loop-spec`](https://github.com/witt3rd/loop-spec) · [`saturate`](https://github.com/witt3rd/saturate)

---

## The One-Line Summary

> **Cyclus designs work. Saturate executes it. The handoff is a typed spec.**

Cyclus is the **deliberation layer**. It validates intent into a typed loop spec
that any execution backend can run. It does not run loops itself — it produces
specs and manages the queue interface.

---

## The Loop Spec (Source of Truth)

The canonical schema lives at [`witt3rd/loop-spec`](https://github.com/witt3rd/loop-spec).
Cyclus depends on `loop-spec-py` for validation. Saturate depends on it for
scheduling. Neither owns the schema.

Six loop kinds — each has its own required fields:

| Kind | Terminal condition | Cyclus skill |
|------|--------------------|--------------|
| `MetricOptimizationKind` | score hits target OR plateau OR max_iterations | cyclus-autoresearch |
| `TaskExecutionKind` | all tasks pass | cyclus-ralph |
| `ConsensusKind` | all roles APPROVE (incl. DRI) | cyclus-ralplan |
| `InformationSeekingKind` | gap check passes | cyclus-deep-research |
| `ClarificationKind` | human confirms (HUMAN_GATED) | cyclus-deep-interview |
| `SelectionKind` | best candidate identified | *(future)* |

Maturity levels: **L1** (propose only) → **L2** (apply + confirm) → **L3** (autonomous).
All specs start at L1. Trust is earned.

`load_spec()` is the planning gate — every cyclus-ralph run validates the spec
before parsing the plan. A `ValidationError` halts immediately.

---

## The Universal Execution Pattern

Every backend — Kanban, file-based, Saturate — implements the same pattern:

```
1. DISPATCH   Dispatcher posts a task (loop spec + state path) and assigns it to a worker
2. WORK       Worker runs as fast as inference allows, iterating until terminal or timeout
3. COMPLETE   Worker calls complete() with result — loop is done
   OR
3. TIMEOUT    Dispatcher detects stale task, reclaims it, re-dispatches to a new worker
              New worker reads state, continues from where the last one stopped
```

This is how we saturate compute:
- The worker never idles waiting for a clock
- If the worker times out, the dispatcher immediately re-dispatches
- State persists across worker boundaries — each new worker picks up where the last left off
- The dispatcher is the loop controller, not the worker

**The worker's only job:** do as much work as possible before context runs out,
write state, call `complete()` if terminal or let the dispatcher reclaim if not.

**The dispatcher's only job:** keep a worker assigned to every active task.
When a worker finishes or times out, dispatch the next one immediately.

---

## Kanban as the Reference Implementation

Kanban (Hermes v0.18.0+) is the first backend because the dispatcher is built in.
The Kanban gateway dispatcher runs continuously, handles reclaim automatically,
and `goal_mode=True` gives us the loop-until-done semantic natively.

### How a Cyclus loop runs on Kanban

```python
# 1. Post the task (Cyclus producer)
hermes kanban create \
  --title "function-minimization: optimize combined_score to 1.49" \
  --body "spec: examples/function_minimization/spec.yaml\nstate: .cyclus/state/..." \
  --assignee forge \
  --goal-mode          # judge checks terminal condition after every turn

# 2. Dispatcher assigns to worker (automatic — Kanban gateway)
# Worker profile has cyclus-autoresearch skill loaded

# 3. Worker iterates (cyclus-autoresearch skill drives the loop)
#    - reads state from state_path
#    - runs eval, applies hypothesis, commits or reverts
#    - writes updated state
#    - calls kanban_heartbeat() to signal liveness
#    - when terminal: calls kanban_complete(summary=..., metadata={final_score: ...})

# 4. If worker times out before terminal:
#    - Kanban reclaims after dispatch_stale_timeout_seconds (default 4h, set lower for fast loops)
#    - New worker picks up — reads state, continues
```

### Key Kanban config for fast loops

```yaml
kanban:
  dispatch_stale_timeout_seconds: 600  # reclaim after 10 min (match agent timeout)
  dispatch_interval_seconds: 10        # check for stale tasks every 10s
```

With these settings, a timed-out worker is reclaimed and re-dispatched within
10 seconds. Zero idle time between worker runs.

### What the worker skill does

The cyclus skill (cyclus-ralph, cyclus-autoresearch, etc.) loaded on the worker:
1. Calls `kanban_show` to read the task body (spec path, state path)
2. Reads state from state_path
3. Checks terminal conditions — if done, calls `kanban_complete()` and exits
4. Otherwise: does one or more iterations, writing state after each
5. Calls `kanban_heartbeat()` periodically to prevent premature reclaim
6. If approaching context limit: writes state, exits cleanly (Kanban reclaims)

### HITL gates

```python
kanban_block(reason="needs_input",
             message="Score plateau at 1.44 after 8 iterations. Try a different algorithm family?")
# Human comments, unblocks
# Dispatcher re-dispatches with human context injected
```

---

## File-Based and Saturate: Same Pattern, Different Dispatcher

The worker skill is **identical** across all three backends. The difference is
only in what drives the dispatch loop:

| Backend | Dispatcher | Reclaim mechanism |
|---------|------------|-------------------|
| **Kanban** | Hermes gateway (built-in) | `dispatch_stale_timeout_seconds` — automatic |
| **File-based** | Orchestrating `delegate_task` call | Parent agent re-dispatches after child returns |
| **Saturate** | Saturate runner process | Saturate scheduler detects stale tasks and re-queues |

For **file-based**, the orchestrator is a simple agent that:
1. Calls `queue.post(spec)` 
2. Calls `delegate_task(worker, context=task)` — blocks until worker returns
3. Reads result — if not terminal, calls `queue.post(spec)` again and repeats
4. When terminal: stops

For **Saturate**, the Saturate runner IS the dispatcher — it runs continuously,
claims tasks from the PostgreSQL queue, spawns workers, and re-queues on timeout.

The worker skill never needs to know which dispatcher is driving it.

---

## Execution Backends

Three backends, one interface. Skills are written against the interface —
a backend swap is a config change, not a skill rewrite.

| Backend | When | Mechanism |
|---------|------|-----------|
| **File-based** | Always; zero config; NFS-safe | Atomic `os.rename()` across `pending/` → `active/` → `done/`. No database, no WAL. Works on Azure Files, NFS, any filesystem. |
| **Kanban** | Hermes v0.18.0+ | Native Hermes durable board. `kanban_create/next/comment/complete` implement the four operations. HITL gates via `kanban_block`. |
| **Saturate** | When configured | Distributed fleet. PostgreSQL `SELECT FOR UPDATE SKIP LOCKED` for concurrent workers. The production backend for N parallel workers. |

**Why not SQLite for Tier 1?** WAL mode corrupts on NFS — the exact reason
Hermes users on Azure Files disable Kanban. Atomic file renames are NFS-safe
by POSIX guarantee.

---

## The Four-Operation Interface

```
post(spec, submitted_by)     →  ScheduledTask
claim()                      →  Option[ClaimedTask]
write_state(task, state)     →  ActiveTask
complete(task, output)       →  TerminalTask
```

Cyclus is a **producer** — it calls `post()`.
Workers call `claim()`, `write_state()`, `complete()`.

The worker never knows which backend it's talking to.

**Push model — not pull.** The dispatcher hands work to workers via
`delegate_task`. Workers do not poll. `claim()` is called by the dispatcher
on behalf of the worker, not by the worker itself.

---

## State Persistence

Runtime state lives in `.cyclus/` — committed to the user's project repo
following the `.omh/` pattern:

```
.cyclus/
  plans/          ← committed (durable artifacts: plans, specs)
  queue/
    pending/      ← gitignored (runtime JSON)
    active/       ← gitignored (runtime JSON)
    done/         ← gitignored (runtime JSON)
  state/          ← gitignored (per-loop state.json, turns.jsonl)
```

`.cyclus/.gitignore` excludes runtime state. Plans are tracked.

`STATE.md` lives in the user's `--workdir`. It is **never** committed to the
Cyclus plugin repo — it is the user's project state.

---

## Cyclus Skills → Loop Kinds

| Skill | Loop kind | What one turn produces |
|-------|-----------|------------------------|
| cyclus-ralph | `TaskExecutionKind` | `TaskPassed \| TaskFailed \| TaskBlocked \| AllTasksPassed` |
| cyclus-ralplan | `ConsensusKind` | `RoundComplete \| ConsensusReached` |
| cyclus-deep-research | `InformationSeekingKind` | `FindingsAdded \| Sufficient` |
| cyclus-deep-interview | `ClarificationKind` *(HUMAN_GATED)* | `CoverageUpdated \| HumanConfirmed` |
| cyclus-autoresearch | `MetricOptimizationKind` | `Accepted \| Discarded` |

---

## The Forward Arc

```
loop-spec v0.1   Schema + Python reference implementation (shipped)
                 executor, output_dir, evaluate_extract, correctness, plan_path

Cyclus v18.0.0   File-based queue, typed specs, load_spec() planning gate (shipped)
                 Depends on loop-spec-py via git URL

Cyclus v18.x     Arc 1 — cyclus_measure (MetricOptimizationKind eval primitive)
                 Arc 2 — cyclus-autoresearch (first MetricOptimizationKind skill)
                 Arc 3 — cyclus-loop-design (deliberation → typed spec)

Saturate         Tier 3 backend — fleet execution at scale
                 Implements the four-operation interface over PostgreSQL

Continuum        Cognitive presence — surveys the Saturate fleet,
                 identifies what to spawn next, directs long-horizon work
```

---

*Cyclus designs work. Saturate executes it. The handoff is a typed spec.*

⚒️
