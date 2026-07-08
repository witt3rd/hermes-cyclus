# hermes-cyclus — Architecture

> **Status:** Active — 2026-07-07
> **Companion:** [`loop-spec`](https://github.com/witt3rd/loop-spec) · [`saturate`](https://github.com/witt3rd/saturate)
>
> **Co-design:** Cyclus, loop-spec, and Saturate evolve together. loop-spec is the
> shared contract — neither Cyclus nor Saturate owns it. When a new field is needed,
> it lands in loop-spec first; both consumers adopt it. Changes may land in any repo
> in any turn depending on where the seam is.

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

**`repo` field** — specs that commit/revert hypotheses (MetricOptimizationKind,
TaskExecutionKind) declare the target as a git URL (`https://`, `git@`, `file://`).
The execution fabric clones it into an isolated worktree. Absolute local paths are
rejected by the validator — the spec is machine-agnostic.

---

## The Universal Execution Pattern

Every backend — Kanban, file-based, Saturate — implements the same pattern:

```
1. DISPATCH   Dispatcher assigns a task (loop spec + state path) to one or more workers
2. WORK       Worker(s) run as fast as inference allows, doing iterations
3. COMPLETE   Worker calls complete() with result — loop is done
   OR
3. TIMEOUT    Dispatcher detects stale worker, reclaims the task, dispatches a new worker
              New worker reads state, continues from where the last one stopped
```

**The dispatcher is the loop controller, not the worker.**
**The worker's only job:** do as much work as possible before context runs out, write state.
**The dispatcher's only job:** keep a worker on every active task; reclaim immediately on timeout.

---

## Two Worker Topologies

### Serial (single worker)

One worker at a time. Dispatcher assigns the task, worker iterates, exits or times out,
dispatcher re-assigns. State accumulates across worker boundaries via state_path.

Best for: `TaskExecutionKind`, `ConsensusKind`, `ClarificationKind` — loops where
each turn builds on the previous one and parallelism doesn't help.

```
Dispatcher → Worker 1 (iterates, times out) → Worker 2 (reads state, continues) → ... → DONE
```

### Swarm (parallel workers + verifier)

N workers run simultaneously, each trying a different hypothesis. A verifier/synthesizer
picks the best result and advances the baseline. Loop continues with the winner.

Best for: `MetricOptimizationKind`, `SelectionKind` — loops where hypotheses are
independent and trying many simultaneously is faster than trying them serially.

```
               ┌─ Worker A (hypothesis α) ─┐
Dispatcher ────┼─ Worker B (hypothesis β) ─┼──► Verifier/Synthesizer ──► best result → baseline
               └─ Worker C (hypothesis γ) ─┘    (discards losers, commits winner)
```

Swarm is not a different architecture — it is the serial pattern with `N > 1` at
the dispatch step. The verifier is the loop controller in both topologies.

---

## Kanban as the Reference Implementation

Kanban (Hermes v0.18.0+) is the first backend. The dispatcher is built in
(gateway process), handles reclaim automatically, and `goal_mode=True` gives
loop-until-done semantics natively.

### Serial loop on Kanban

```bash
hermes kanban create \
  --title "function-minimization: optimize to 1.49" \
  --body "spec: examples/function_minimization/spec.yaml" \
  --assignee forge \
  --goal-mode
```

Worker profile has the appropriate cyclus skill loaded. When the worker times out,
Kanban reclaims and re-dispatches automatically.

### Swarm on Kanban

```bash
hermes kanban swarm  # creates root + N parallel workers + gated verifier
```

This creates a full swarm graph: root orchestrator, parallel workers each trying
a different hypothesis, gated verifier that picks the best result, synthesizer
that commits the winner and updates the baseline. The verifier gate ensures only
one result advances before the next swarm generation begins.

### Key Kanban config for fast loops

```yaml
kanban:
  dispatch_stale_timeout_seconds: 600   # reclaim after 10 min (match agent timeout)
  dispatch_interval_seconds: 10         # check for stale tasks every 10s
```

With these settings, a timed-out worker is reclaimed and re-dispatched within 10
seconds. Near-zero idle time between worker runs.

### What the worker skill does

The cyclus skill loaded on the worker:
1. Calls `kanban_show` — reads task body (spec path, state path)
2. Reads state from state_path — picks up where last worker stopped
3. Checks terminal conditions — if done, calls `kanban_complete()` and exits
4. Otherwise: iterates as fast as possible, writing state after each iteration
5. Calls `kanban_heartbeat()` periodically to prevent premature reclaim
6. Approaching context limit: writes state cleanly, exits — Kanban reclaims

### HITL gates

```python
kanban_block(reason="needs_input",
             message="Plateau at 1.44 after 8 iterations. Try a different algorithm family?")
# Human comments, unblocks — dispatcher re-dispatches with context injected
```

---

## File-Based and Saturate: Same Pattern, Different Dispatcher

The worker skill is **identical** across all three backends. Only the dispatcher differs.

| Backend | Dispatcher | Serial reclaim | Swarm |
|---------|------------|----------------|-------|
| **Kanban** | Hermes gateway (built-in) | `dispatch_stale_timeout_seconds` — automatic | `hermes kanban swarm` |
| **File-based** | Parent `delegate_task` agent | Parent re-dispatches after child returns | Parent dispatches N children in parallel batch, collects best |
| **Saturate** | Saturate scheduler process | Heartbeat timeout → re-queue → re-dispatch | `BatchKind` tasks with `SpawnPolicy` — N parallel `MetricOptimizationKind` workers + synthesizer |

### Saturate swarm via BatchKind

Saturate's `BatchKind` is the swarm primitive. A `BatchKind` task fans out to N
child `MetricOptimizationKind` workers (each with a different hypothesis seed),
collects results via `depends_on` edges, and a synthesizer worker picks the winner.

```python
# Producer posts a BatchKind task
queue.post(BatchSpec(
    workers=N,
    child_kind=MetricOptimizationKind,
    child_spec=spec,
    synthesizer=SynthesizerSpec(strategy="best_metric"),
))
# Saturate scheduler spawns N child tasks automatically via SpawnPolicy
```

The `spawn` field in `MetricOptimizationSpec` declares whether a loop may
spawn child loops (e.g., when stagnated: try N parallel hypotheses, restart
from best). This is how a serial loop graduates to swarm when it gets stuck.

The worker skill never needs to know whether it is in a serial or swarm topology.
The spec and state_path are the same either way.

---

## Execution Backends

Three backends, one interface. Skills are written against the interface —
a backend swap is a config change, not a skill rewrite.

| Backend | When | Mechanism |
|---------|------|-----------|
| **File-based** | Always; zero config; NFS-safe | Atomic `os.rename()` across `pending/` → `active/` → `done/`. No database, no WAL. Works on Azure Files, NFS, any filesystem. |
| **Kanban** | Hermes v0.18.0+ | Native Hermes durable board. `kanban_create/next/comment/complete` implement the four operations. HITL gates via `kanban_block`. |
| **Saturate** | When configured | Distributed fleet. SQLite queue (file-based, NFS-safe) for Arc 1; PostgreSQL `SELECT FOR UPDATE SKIP LOCKED` for Arc 2+ concurrent fleet workers. Implements the full four-operation interface. |

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

**The judge gap.** For `MetricOptimizationKind`, Saturate's `correctness` field
is a shell command (exit 0 = pass). For Kanban `goal_mode`, acceptance criteria
can be a reasoning judgment evaluated by an auxiliary judge after each turn. These
are not equivalent. Saturate Arc 2 will need a judge executor step — either a
Hermes invocation or a structured LLM call — to reach full parity with Kanban
goal-mode for tasks where "done" requires semantic evaluation, not just a test exit code.

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

loop-spec v0.2   repo: git URL field — machine-agnostic target declaration (shipped)
                 Absolute paths rejected by validator

Cyclus v18.0.0   File-based queue, typed specs, load_spec() planning gate (shipped)
                 Depends on loop-spec-py via git URL

Cyclus v18.x     Arc 1 — cyclus_measure (MetricOptimizationKind eval primitive)
                 Arc 2 — cyclus-autoresearch (first MetricOptimizationKind skill)
                 Arc 3 — cyclus-loop-design (deliberation → typed spec)

Saturate Arc 1   SQLite queue, runner/executor/scheduler primitives (shipped)
                 repo field: clones git URL into isolated worktree per task
                 loop-spec conformant: load_spec(), ExecutorSpec, TerminalConditions

Saturate Arc 2   PostgreSQL SELECT FOR UPDATE SKIP LOCKED — concurrent fleet workers
                 Judge executor step — semantic acceptance criteria beyond exit codes

Continuum        Cognitive presence — surveys the Saturate fleet,
                 identifies what to spawn next, directs long-horizon work
```

---

*Cyclus designs work. Saturate executes it. The handoff is a typed spec.*

⚒️
