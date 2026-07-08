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

## Execution: The Two-Job Chain

This is the core execution pattern. It applies to every loop kind.

```
Proposer job                    Verifier job
─────────────────               ─────────────────────────────────
Does one unit of work           Receives proposer output via --context-from
Writes to STATE.md              Reads state.json
Triggers Verifier               Checks terminal conditions:
                                  DONE  → stop, report final result
                                  NOT DONE → triggers Proposer
```

**The verifier is the loop controller.** It is the only agent with full
information: the eval result, the state history, and the terminal conditions.
It decides whether to stop or continue.

**Self-triggering via `cronjob(action='run', job_id=...)`** — no clock drives
the loop. Each agent triggers the next immediately before exiting. The cron
schedule is only for the initial launch.

**`--context-from`** wires the proposer's stdout into the verifier's prompt.
The verifier sees what the proposer produced without any extra infrastructure.

This pattern is universal across all loop kinds and all three backends.

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
