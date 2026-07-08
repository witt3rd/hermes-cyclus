# hermes-cyclus — Architecture

> **Status:** Active — 2026-07-08
> **Companion:** [`loop-spec`](https://github.com/witt3rd/loop-spec) · [`saturate`](https://github.com/witt3rd/saturate)

---

## One-Line Summary

> **Cyclus designs work. Saturate executes it at fleet scale. Hermes runs it everywhere else.**

---

## Three Decisions

Every Cyclus loop requires three independent decisions. They are orthogonal — any
combination is valid.

### Decision 1: Loop Kind (what work gets done)

| Kind | Use when | Skill |
|------|----------|-------|
| **`/goal`** *(Hermes primitive)* | Open-ended goal, no plan needed. Judge decides when done. | — (built-in) |
| **`TaskExecutionKind`** | Structured plan with per-task evidence requirements. More disciplined than `/goal`. | cyclus-loop |
| **`ConsensusKind`** | Multi-role deliberation (Planner + Architect + Critic + DRI) to produce a plan or decision. | cyclus-plan |
| **`InformationSeekingKind`** | Research until a sufficiency threshold is reached. | cyclus-research |
| **`ClarificationKind`** | Elicit requirements from a human. **HUMAN_GATED** — only an explicit human `complete()` ends it. `/goal` cannot do this. | cyclus-interview |
| **`MetricOptimizationKind`** | hypothesis → measure → keep/revert until metric target is reached. | cyclus-autoresearch *(Arc 2)* |
| **`SelectionKind`** | Generate N candidates, rank by fitness, keep top-k, repeat. | *(future)* |

**`/goal` vs cyclus skills:** `/goal` is the simplest loop — use it when the goal is
open-ended and you don't need plan discipline. Cyclus skills add structure on top:
committed plans, per-task evidence contracts, typed terminal algebras, HITL gates.
When Kanban dispatches a cyclus-loop worker with `goal_mode=True`, the Kanban judge
checks whether the plan is complete — `/goal` IS the judge.

**Typical flow:** cyclus-plan produces a plan → cyclus-loop executes it.
Or: cyclus-interview clarifies requirements → cyclus-plan designs → cyclus-loop executes.

---

### Decision 2: Worker Topology (how many workers at once)

| Topology | Workers | Use when |
|----------|---------|----------|
| **Serial** | 1 at a time | Default for all loop kinds. Each turn builds on the previous. |
| **Swarm** | N in parallel | `MetricOptimizationKind` and `SelectionKind` only. Workers try different hypotheses simultaneously; verifier picks the best; loop continues from the winner. |

Swarm is not a different architecture — it is the serial pattern with `N > 1` at
the dispatch step. The verifier/synthesizer is the loop controller in both topologies.

---

## Swarm Isolation Strategy (decided)

When N workers each propose a change to the same `target_files`, they must not
collide. Every mature parallel optimization system (Ray Tune, Island-model GAs,
CMA-ES) converges on the same invariant:

> **The scheduler is the single writer to canonical state. Workers are proposers only.**

### For text / code / config / prompt artifacts

Create a **loop-scoped ephemeral git repo** (even if the outer project has no git):

```bash
# Create the loop repo with an initial empty commit (required before worktrees)
git init /tmp/loop-{id}/
git -C /tmp/loop-{id}/ commit --allow-empty -m "loop root"

# Each worker gets an isolated worktree on its own branch
git -C /tmp/loop-{id}/ worktree add worker-A -b worker/A
git -C /tmp/loop-{id}/ worktree add worker-B -b worker/B
git -C /tmp/loop-{id}/ worktree add worker-C -b worker/C
```

- Each worker has a fully isolated working directory on its own branch
- Workers write their proposed change to their worktree — never to canonical
- Verifier applies each proposal to a fresh copy of canonical, measures, picks winner
- Dispatcher cherry-picks the winning worktree into canonical, `git worktree remove` the rest
- The loop repo is reaped when the loop ends

Benefits: diff, merge, rollback, audit trail, O(1) isolation via shared object store.
The loop repo is orthogonal to the project's own git history.

### For binary / structured artifacts (model weights, compiled outputs)

Per-worker staging directories — no git needed:

```
staging/{worker_id}/artifact   ← worker writes here
canonical/artifact             ← scheduler writes here (only)
```

Workers write to `staging/{worker_id}/`. Scheduler applies each to a fresh copy of
canonical, measures, promotes the winner atomically.

### Long-term: BranchFS (arXiv:2602.08199)

Copy-on-write OS primitives with sub-350µs branch creation, first-commit-wins
semantics, and artifact-type-agnostic isolation. The correct Saturate fleet
primitive when available.

### GC

N workers × M iterations = N×M ephemeral artifacts. Build the reaper into the loop,
not as an afterthought. `loop-spec`'s `output_dir` field is the hook for cleanup.

```
Serial:  Dispatcher → Worker → (timeout) → Worker → ... → DONE

Swarm:   Dispatcher ──┬── Worker A (hypothesis α) ──┐
                      ├── Worker B (hypothesis β) ──┼──► Verifier → winner → new baseline
                      └── Worker C (hypothesis γ) ──┘
```

---

### Decision 3: Backend (what dispatches and reclaims workers)

| Backend | When | Swarm | Dispatcher |
|---------|------|-------|------------|
| **File** | Zero config. Always available. | ✅ via `delegate_task(tasks=[...])` batch | Parent agent (driver skill) |
| **Kanban** | Unattended loops, overnight, HITL gates. Hermes v0.18.0+. | ✅ via `hermes kanban swarm` | Hermes gateway (built-in) |
| **Saturate** | Multi-machine fleet, concurrent workers. | ✅ via `BatchKind + SpawnPolicy` | Saturate scheduler (built-in) |

**The backend is a deployment detail, not a skill concern.** Skills call `cyclus_queue`
and never touch backend APIs directly. `queue_tool.py` detects the active backend via
environment variables and routes accordingly.

---

## The Dispatcher and the Worker

Every backend separates two roles:

**The dispatcher** is the loop controller. It:
- Assigns tasks to workers
- Detects stale workers and reclaims them immediately
- For swarm: fans out N workers and collects results via the verifier
- Decides when the loop is done (terminal condition check)

**The worker** saturates compute. It:
- Does as much work as possible before context runs out
- Writes state after every iteration (`cyclus_queue write_state`)
- If terminal: calls `cyclus_queue complete` and exits
- If context limit approaching: writes state and exits cleanly (dispatcher reclaims)

The worker never manages the loop. It never waits. It never checks "should I keep
going?" — that is the dispatcher's job.

---

## File Backend: Driver Skills

Without a built-in dispatcher, a parent agent drives the loop.

**Serial (driver skill as dispatcher):**
```
cyclus-loop-dispatcher (parent):
  loop:
    delegate_task(cyclus-loop worker, context=current_task)  ← blocks until done
    read result
    if not terminal: loop again
    if terminal: stop
```

**Swarm (driver skill + batch delegation):**
```
cyclus-autoresearch-driver (parent):
  loop:
    delegate_task(tasks=[
      {worker, context={...hypothesis_seed: "basin A"}},
      {worker, context={...hypothesis_seed: "basin B"}},
      {worker, context={...hypothesis_seed: "basin C"}},
    ])  ← runs N workers concurrently, blocks until all return
    pick best result (verifier logic inline)
    commit winner, revert losers
    update state
    if not terminal: loop again
```

`delegate_task(tasks=[...])` runs up to `delegation.max_concurrent_children` workers
in parallel (default 3, configurable). This is file-backend swarm.

**Driver skills exist only for the file backend.** Kanban and Saturate have built-in
dispatchers — driver skills are not needed when those backends are active.

---

## Kanban Backend: Gateway as Dispatcher

```bash
# Serial
hermes kanban create "optimize fn_min to 1.49" \
  --assignee forge --goal

# Swarm
hermes kanban swarm  # root + N parallel workers + gated verifier + synthesizer
```

Key config for fast loops:
```yaml
kanban:
  dispatch_stale_timeout_seconds: 600   # reclaim after ~10 min
  dispatch_interval_seconds: 10         # check for stale tasks every 10s
```

Worker skill behaviour in Kanban mode (`HERMES_KANBAN_TASK` set):
1. `kanban_show` — reads task body (spec path, state path)
2. Reads state from state_path — picks up where last worker stopped
3. Checks terminal conditions — if done, `kanban_complete()` and exit
4. Iterates as fast as possible, writing state after each iteration
5. `kanban_heartbeat()` periodically to prevent premature reclaim
6. Approaching context limit: write state cleanly, exit — Kanban reclaims

HITL gate:
```python
kanban_block(reason="needs_input",
             message="Plateau at 1.44. Try a different algorithm family?")
# Human comments → dispatcher re-dispatches with context injected
```

---

## Saturate Backend: Scheduler as Dispatcher

Saturate's `SaturateTask` carries `spawned_by` and `depends_on` — hierarchy is a
dependency graph, not a type distinction. Serial and swarm are scheduling properties.

**Swarm via BatchKind:**
```python
queue.post(BatchSpec(
    workers=N,
    child_kind=MetricOptimizationKind,
    child_spec=spec,
    synthesizer=SynthesizerSpec(strategy="best_metric"),
))
# Scheduler spawns N child tasks automatically via SpawnPolicy
```

The `spawn` field in `MetricOptimizationSpec` declares whether a stagnated serial
loop may spawn children to try N hypotheses in parallel — graduating to swarm
automatically when stuck.

---

## The Loop Spec (Source of Truth)

The canonical schema lives at [`witt3rd/loop-spec`](https://github.com/witt3rd/loop-spec).
All three backends read the same spec. The spec is **read-only during execution**.

```yaml
kind: MetricOptimizationKind
name: function_minimization
level: L2                        # L1=propose-only, L2=apply+confirm, L3=autonomous
direction: higher_is_better
metric: combined_score
baseline: 1.404
terminal:
  target_score: 1.49
  max_iterations: 20
  plateau_count: 5
evaluate: |
  cd /path/to/project && python3 evaluator.py
correctness: |
  cd /path/to/project && uv run pytest tests/ -q
target_files:
  - path/to/optimized_file.py
executor:
  type: hermes
  profile: forge
output_dir: .cyclus/state/kanban--function-minimization/
```

Maturity levels: **L1** (propose only) → **L2** (apply + confirm) → **L3** (autonomous).
All specs start at L1. Trust is earned through demonstrated L1 behaviour.

`load_spec()` is the planning gate — every cyclus-loop run validates the spec
before parsing the plan. A `ValidationError` halts immediately.

---

## State Persistence

Runtime state lives in `.cyclus/` in the user's project — committed following the
`.omh/` pattern:

```
.cyclus/
  plans/          ← committed (plans, specs — durable artifacts)
  queue/
    pending/      ← gitignored (runtime JSON)
    active/       ← gitignored (runtime JSON)
    done/         ← gitignored (runtime JSON)
  state/          ← gitignored (per-loop state.json, turns.jsonl)
```

`.cyclus/.gitignore` excludes runtime state. Plans are tracked.

---

## cyclus_queue: The Backend-Agnostic Interface

Skills never call `kanban_*` or Saturate APIs directly. They call `cyclus_queue`:

```python
cyclus_queue(action="write_state", mode="loop", instance_id="my-plan",
             state={"iteration": 3, "best_score": 1.47})
```

`queue_tool.py` detects the active backend and routes:
- `HERMES_KANBAN_TASK` set → `kanban_heartbeat` + `kanban_comment`
- `SATURATE_TASK` set → Saturate API *(future)*
- default → file-based queue in `.cyclus/`

---

## Cyclus Skills → Loop Kinds

| Skill | Loop kind | Serial | Swarm | Driver skill (file backend) |
|-------|-----------|--------|-------|----------------------------|
| cyclus-loop | `TaskExecutionKind` | ✅ | ✅ *(different tasks in parallel)* | cyclus-loop-dispatcher |
| cyclus-plan | `ConsensusKind` | ✅ | — | cyclus-plan-dispatcher |
| cyclus-research | `InformationSeekingKind` | ✅ | — | *(uses delegate_task internally)* |
| cyclus-interview | `ClarificationKind` *(HUMAN_GATED)* | ✅ | — | *(interactive only)* |
| cyclus-autoresearch | `MetricOptimizationKind` | ✅ | ✅ | *(Arc 2)* |

---

## The Forward Arc

```
loop-spec v0.1   Schema + Python reference implementation (shipped)

Cyclus v18.0.0   File-based queue, typed specs, load_spec() planning gate (shipped)
                 cyclus_queue backend abstraction (shipped)
                 Kanban backend routing (shipped)

Arc 1            L1/L2/L3 maturity enforcement in example specs
Arc 2            cyclus-autoresearch — MetricOptimizationKind worker skill
                 File-backend swarm driver
Arc 3            cyclus-loop-design — deliberation → typed spec

Saturate         Tier 3 backend — fleet execution at scale
                 BatchKind + SpawnPolicy for distributed swarm

Continuum        Cognitive presence — surveys the Saturate fleet,
                 identifies what to spawn next, directs long-horizon work
```

---

*Cyclus designs work. Saturate executes it. The handoff is a typed spec.*

⚒️
