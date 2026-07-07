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
| **Cyclus internal queue** | Always works; zero config | Embedded SQLite (single-node); matches Saturate's schema; full lifecycle and audit trail; no Hermes dependency |
| **Kanban** (Hermes v0.18.0) | If Hermes Kanban is enabled | Native Hermes durable board; `kanban_create/next/comment/complete` implement the four operations; HITL gates via `kanban_block` |
| **Saturate** | When configured | Distributed Ray/Nomad fleet; multi-node; full typed loop execution at scale; the production backend |

Cyclus detects which backend is available at runtime. The skill prose is written
against the four-operation interface — a backend swap is a configuration change,
not a skill rewrite.

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
