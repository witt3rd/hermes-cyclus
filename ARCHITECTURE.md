# hermes-cyclus — Architecture

> **Status:** Active — 2026-07-06  
> **Companion:** [`saturate/ARCHITECTURE.md`](https://github.com/witt3rd/saturate/blob/main/ARCHITECTURE.md)

---

## The Unified Purpose

hermes-cyclus and Saturate are two halves of one arc:

> **Cyclus designs work. Saturate executes it. The handoff is a typed spec.**

Cyclus is the deliberation layer. Its single job is one type transformation:

```
WorkSpec  →  DesignedWork
```

A `WorkSpec` is unvalidated intent — a vague goal, a description, a path to a
spec file. `DesignedWork` is a typed loop spec that has survived deliberation:
the goal is verifiable, the loop kind is declared, terminal states are named,
blast radius is documented, verification level is honest.

That proof is Cyclus's unique contribution. Saturate never needs to know how
deliberation happened — it just needs a conforming typed spec.

---

## The Loop Taxonomy (Saturate's — Cyclus maps to it)

The loop taxonomy is Saturate's. See
[`saturate/ARCHITECTURE.md — The Loop Taxonomy`](https://github.com/witt3rd/saturate/blob/main/ARCHITECTURE.md)
for the full typed definitions. Cyclus maps each skill to a Saturate loop kind:

| Cyclus Skill | Saturate LoopKind | What one turn produces |
|-----------|-------------------|------------------------|
| **ralplan** | `ConsensusKind` | `RoundComplete \| ConsensusReached` |
| **ralph** | `TaskExecutionKind` | `TaskPassed \| TaskFailed \| TaskBlocked \| AllTasksPassed` |
| **deep-research** | `InformationSeekingKind` | `FindingsAdded \| Sufficient` |
| **deep-interview** | `ClarificationKind` *(HUMAN_GATED)* | `CoverageUpdated \| HumanConfirmed` |
| **cyclus-autoresearch** | `MetricOptimizationKind` | `Accepted \| Discarded` |
| *(future)* | `SelectionKind` | `GenerationComplete \| Converged` |

**`ClarificationKind.HUMAN_GATED = True`** is the structural fact that makes
deep-interview different from every other skill: the scheduler never marks it
terminal. Only an explicit human `complete()` call ends it. This is not a
configuration choice or a prose rule — it is a type property.

Cyclus's `cyclus-loop-design` deliberation (the design skill that produces new loop
specs) determines which kind a new spec belongs to. The kind determines
everything else: which spec fields are required, which turn results are valid,
which terminal states are possible.

---

## The Work-Queue Interface (Four Operations)

Saturate's published contract. Cyclus is a **producer** — it calls `post()`.
Workers call `claim()`, `write_state()`, `complete()`.

```
post(spec: DesignedWork, submitted_by: Attribution)  →  ScheduledTask
claim()                                              →  Option[ClaimedTask]
write_state(task: ClaimedTask, state: LoopState)     →  ActiveTask
complete(task: ClaimedTask, output: LoopOutput)      →  TerminalTask
```

The worker does not know whether it is talking to the Cyclus internal queue,
Kanban, or Saturate's distributed fabric. That is the whole interface.

**Serial and parallel are scheduling properties, not architectural categories.**
`depends_on` expresses serial constraints. No `depends_on` = freely parallel.

---

## Execution Backends (Progressive)

Saturate's interface is the contract. Three concrete backends implement it,
each adding capability without requiring skill rewrites:

| Backend | When | What it provides |
|---------|------|-----------------|
| **File-based** | Always works; zero config; NFS-safe | Atomic directory operations — `pending/`, `active/`, `done/` subdirs; `claim()` = `os.rename()`; no database, no WAL, no journal; works on Azure Files, NFS, any filesystem |
| **Kanban** (Hermes v0.18.0) | If Hermes Kanban is enabled | Native Hermes durable board; `kanban_create/next/comment/complete` implement the four operations; HITL gates via `kanban_block`; visual surface on top of the same file semantics |
| **Saturate** | When configured | Distributed fleet; PostgreSQL with `SELECT FOR UPDATE SKIP LOCKED` for concurrent workers; multi-node; the production backend for N parallel workers |

**Why not SQLite for Tier 1?** SQLite WAL mode corrupts on NFS-mounted
filesystems — the exact reason Hermes users on Azure Files or shared mounts
disable Kanban. Since Cyclus's primary target is Hermes (which frequently runs
on NFS-backed storage), SQLite is the wrong Tier 1 foundation. Atomic file
renames are NFS-safe by POSIX guarantee.

Cyclus detects which backend is available at runtime. The skill prose is written
against the four-operation interface — a backend swap is a configuration change,
not a skill rewrite.

---

## Hermes-Native Loop Patterns

Cyclus is Hermes-native. The full loop engineering stack runs on Hermes
primitives with no extra infrastructure:

| Loop primitive | Hermes mechanism |
|---|---|
| Scheduling / heartbeat | `hermes cron create "0 7 * * 1-5" --skill cyclus-ralph --workdir "$PWD"` |
| Run-until-done | Two cron jobs chained via `hermes cron edit --context-from <upstream-id>` |
| Worktrees | `git worktree` inside the cron job; `--workdir` pins per-job cwd |
| Skills | `SKILL.md` under `~/.hermes/skills/` or project `.hermes/skills/` |
| Sub-agents (maker/checker) | `delegate_task(role='leaf', toolsets=[...])` |
| State/memory | `STATE.md` in `--workdir`; `hermes memory` for cross-session facts |
| Channel delivery | `--deliver telegram\|slack\|local` on any cron job |

### The `--context-from` chain (L2 maker/checker split)

```bash
# Proposer: one cyclus-ralph turn, writes proposed diff to STATE.md
PROPOSER=$(hermes cron create "0 7 * * 1-5" \
  --name "cyclus-ralph proposer" --skill cyclus-ralph \
  --workdir "$PWD" --deliver local \
  "Run one turn. Write proposed patch as fenced diff. Update STATE.md. Do not apply." \
  | tail -1)

# Verifier: receives proposer stdout, applies patch in worktree, runs eval
hermes cron create "5 7 * * 1-5" \
  --name "cyclus-ralph verifier" --skill cyclus-ralph-driver \
  --workdir "$PWD" --deliver local \
  "Apply injected patch in isolated worktree. Run eval. Commit if improved. Update STATE.md."

hermes cron edit <verifier-id> --context-from "$PROPOSER"
```

The upstream job's stdout is injected into the downstream prompt on every tick.
No new infrastructure — this is `--context-from` doing inter-job pipeline.

### L1 defaults (always start here)

All `spec.md` files default to `level: L1` until trust is earned:

- `--deliver local` — output stays in `~/.hermes/cron/output/`, not in any channel
- Workers write proposed diffs to `write_state()` only — nothing touches the repo
- Human reads `STATE.md` and local output before enabling L2
- Kill switch: set `loop-pause-all: true` in `STATE.md` and the skill short-circuits

**Anti-pattern #4 (Greyling):** L3 before L1 quality. Never auto-commit until
the eval command, baseline score, and improvement direction are confirmed correct.

---

## The Typed Spec: The Handoff File

Cyclus's `cyclus-loop-design` deliberation produces a typed YAML spec for the
declared loop kind. The spec is Saturate's input — read-only during execution.

Each kind has its own required fields. A `ConsensusSpec` carries `roles` and
`consensus_fn`; a `MetricOptimizationSpec` carries `metric` and `correctness`.
There is no generic loop spec — the kind determines the schema.

```yaml
# Example: MetricOptimizationSpec (cyclus-autoresearch)
kind:           metric-optimization
goal:           Reduce CI build time by at least 20%
metric:
  command:      npm run build
  extract:      wall_clock
  direction:    minimize
correctness:
  command:      npm test
max_turns:      100
budget_tokens:  500000
stagnation_n:   10
memory:         ./output/build-optimizer/
```

```yaml
# Example: ConsensusSpec (ralplan)
kind:          consensus
goal:          Produce an implementation plan for X
roles:         [planner, architect, critic]
consensus_fn:  all-approve
max_rounds:    3
memory:        .omh/plans/
```

A spec without all required fields for its kind is not schedulable.
The `cyclus-loop-design` deliberation enforces this before handoff.

---

## The Forward Arc

```
Cyclus v18.0.0   Retire bespoke plumbing (omh_state, omh_delegate, hooks)
              Skills written against the four-operation interface
              Cyclus internal queue as default backend; Kanban if enabled

Cyclus v18.1.0   Complete Python deletion; all skills fully re-grounded

Cyclus v18.x     Arc 1 — cyclus_measure (MetricOptimizationKind measurement primitive)
              Arc 2 — cyclus-autoresearch (first MetricOptimizationKind skill)
              Arc 3 — cyclus-loop-design (deliberation that produces typed specs)

Saturate      The Tier 3 backend — typed loop execution at fleet scale
              Implements the four-operation interface over SQLite → PostgreSQL → Nomad

Continuum     The cognitive presence that surveys the Saturate fleet,
              identifies what to spawn next, directs long-horizon work
```

The three projects compose without coupling:
- Cyclus produces typed specs; Saturate runs them; Continuum directs the fleet
- Each communicates through files and the four-operation queue interface
- None needs to know how the others are built

---

*Cyclus designs work. Saturate executes it. The handoff is a typed spec.*

⚒️
