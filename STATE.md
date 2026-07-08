# Cyclus — Loop State

> Durable memory across cron ticks. Read at the start of every loop run.
> Updated by the loop. Human reviews weekly.

**Last run:** —  
**Kill switch:** `loop-pause-all: false`

---

## High Priority

*(empty — loops not yet started)*

## Watch List

*(empty)*

## Active Loops

| Loop | Pattern | Level | Status |
|------|---------|-------|--------|
| function-minimization | MetricOptimizationKind | L1 | 🔲 not started |
| test-coverage | MetricOptimizationKind | L1 | 🔲 not started |
| queue-rewrite (issue #5) | TaskExecutionKind | L1 | ✅ complete (branch fix/5-file-based-queue) |
| **spec-yaml-pydantic-gate (issue #7)** | **TaskExecutionKind** | **L1** | **🔄 designed, ready to dispatch** |

## Current mode (declared 2026-07-07 07:30 PDT)

Mode: loop-work
Loop kind: TaskExecutionKind
Instance: spec-yaml-pydantic-gate
Issue: https://github.com/witt3rd/hermes-cyclus/issues/7
Plan: .cyclus/plans/spec-yaml-pydantic-gate-plan.md
Spec: .cyclus/plans/spec-yaml-pydantic-gate-spec.yaml
Designed via: cyclus-loop-design (meta-loop, Round 1 consensus)

## Human Inbox

*(Items the loop cannot resolve — requires human decision)*

---

## Loop Run Log

| Date | Loop | Turns | Best Score | Outcome |
|------|------|-------|-----------|---------|
| — | — | — | — | — |

---

## Lessons Learned

*(Accumulated by loop workers across runs — do not edit manually)*

---

## Foreclosed Avenues

*(Approaches tried and rejected — workers must not repeat these)*

---

*Kill switch: set `loop-pause-all: true` above. Every loop skill checks this
before acting and short-circuits cleanly if set.*
