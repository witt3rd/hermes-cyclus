---
name: cyclus-loop
description: "TaskExecutionKind: execute a plan to completion with per-task verification"
version: 3.0.0
metadata:
  hermes:
    requires_toolsets: [terminal, file]
    tags: [execution, verification, loop, plan, task, kanban, saturate]
    category: cyclus
---

# cyclus-loop

**Loop kind:** `TaskExecutionKind`  
**One skill, two roles** — auto-detected from environment.

```
HERMES_KANBAN_TASK set   →  Worker role  (Kanban/Saturate dispatched you)
SATURATE_TASK_ID set     →  Worker role  (Saturate dispatched you)
Neither set              →  Dispatcher role  (you drive the loop)
```

---

## When to Use

Use `cyclus-loop` when:
- You have a plan (from `cyclus-plan` or hand-authored) and need verified execution
- Each task must produce evidence before the next task begins
- Some tasks can run in parallel (disjoint file sets)
- You want clean checkpoints — no context bloat across many tasks

Don't use when:
- No plan exists — use `cyclus-plan` first (or `cyclus-interview` to clarify requirements)
- The change is trivially small — just do it directly
- Verification is explicitly not needed

---

## Dispatcher Role (no Kanban/Saturate env)

You are the loop driver. You manage iterations until the plan is complete.

### Detection
```python
import os
is_worker = bool(os.environ.get("HERMES_KANBAN_TASK") or os.environ.get("SATURATE_TASK_ID") or os.environ.get("SATURATE_TASK"))
# if is_worker is False → you are the dispatcher
```

### The dispatch arc

```
iter 1: read plan → pick eligible tasks → dispatch workers (parallel where safe)
         → gather evidence → mark passes/fails → write_state → exit

iter 2: re-invoked → read state → pick next batch → same cycle

iter N: all tasks pass → complete
```

**Iteration = one `delegate_task` round.** The dispatcher exits after each round and
is re-invoked (by Kanban reclaim, by the user, or by a parent agent). State persists
across invocations via `cyclus_queue`.

### Step 1 — Claim the work item

```
result = cyclus_queue(action="claim", mode="loop", instance_id="{plan_slug}")
```
- `claimed` → continue, use `result.item.state_path`
- `not_found` → post first: `cyclus_queue(action="post", mode="loop", instance_id=..., kind="TaskExecutionKind", name=...)`
- `running` → another session holds it; report to user

Release at every clean exit:
```
cyclus_queue(action="release", mode="loop", instance_id="{plan_slug}")
```

### Step 2 — Validate the plan spec

```python
uv run python -c "from loop_spec import load_spec; load_spec('{spec_path}')"
```
Halt on `ValidationError` — do not proceed with a malformed spec.

### Step 3 — Read state and pick the batch

Read `state_path` from the claimed item. State schema:
```json
{
  "tasks": [{"id": "t1", "title": "...", "passes": false, "tries": 0, "files": [...]}],
  "iteration": 0,
  "complete": false
}
```

Eligible = `passes: false` AND all dependencies met.

Batch selection:
- Tasks with **disjoint file sets** → parallel batch (up to 3 via `delegate_task(tasks=[...])`)
- Tasks with **overlapping files** → serial (one at a time)

Load executor template from references if dispatching workers:
→ `references/executor-goal-template.md`
→ `references/verifier-goal-template.md`

### Step 4 — Dispatch workers

```python
# Serial
delegate_task(goal="...", context="task: {task}, plan: {plan_path}", toolsets=["terminal","file"])

# Parallel batch
delegate_task(tasks=[
    {"goal": "...", "context": "task: {t1}"},
    {"goal": "...", "context": "task: {t2}"},
])
```

Each worker is a leaf agent. Load `references/executor-goal-template.md` to
construct the worker goal. After workers return, dispatch verifiers using
`references/verifier-goal-template.md`.

### Step 5 — Collect evidence and advance state

For each task result:
- **Passes** → mark `passes: true` in state, record learning
- **Fails** → increment `tries`, record error fingerprint
- **Blocked** → surface to user via `cyclus_queue(action="cancel", ...)` or pause

Write updated state:
```
cyclus_queue(action="write_state", mode="loop", instance_id="{plan_slug}", state={...})
```

### Step 6 — Check terminal condition

All tasks `passes: true` → final architect review (load `references/architect-final-review-template.md`)
→ `cyclus_queue(action="complete", mode="loop", instance_id=..., terminal_state="PlanComplete")`

Not done → release and exit (next invocation continues):
```
cyclus_queue(action="release", mode="loop", instance_id=...)
```

---

## Worker Role (Kanban or Saturate dispatched you)

You received a single task to execute and verify. Do it and report back.

### Detection
```python
import os
task_id = os.environ.get("HERMES_KANBAN_TASK") or os.environ.get("SATURATE_TASK_ID") or os.environ.get("SATURATE_TASK")
# task_id is set → you are a worker
```

### Your job — the iron law

1. **Read the task envelope** — `cyclus_queue(action="claim", mode="loop", instance_id=...)` (Kanban already claimed, this heartbeats)
2. **Do exactly the task specified** — no more, no less
3. **Stay inside the declared file scope**
4. **Verify** — run the acceptance criteria command; collect output as evidence
5. **Commit once** — exact message format: `loop(task-{id}): {title} — {one-line-result}`
6. **Report** — structured result with evidence path

**Never expand scope.** If you discover adjacent work, note it in state and stop.
**Never self-verify your own implementation** — the dispatcher dispatches a separate verifier.

### Evidence format

```json
{
  "task_id": "t1",
  "passes": true,
  "evidence_command": "uv run pytest tests/test_foo.py -q",
  "evidence_output": "3 passed in 0.12s",
  "commit": "abc1234",
  "learning": "optional one-line lesson for future tasks"
}
```

### Heartbeat

Call `cyclus_queue(action="write_state", ...)` after each meaningful step to prevent
the dispatcher from reclaiming the task prematurely.

---

## References (internal — not user-facing skills)

- `references/executor-goal-template.md` — goal template the dispatcher injects into worker `delegate_task` calls
- `references/verifier-goal-template.md` — goal template for verifier workers  
- `references/architect-final-review-template.md` — final review prompt for the architect gate
- `references/sibling-executor-preemption.md` — how parallel workers handle file conflicts
- `references/sibling-isolation-pattern.md` — worktree isolation for parallel tasks

---

## Pitfalls

**P1 — Scope creep.** Workers implement adjacent improvements not in their task. Iron law: if it's not in the task, don't do it.

**P2 — Self-verification.** The executor verifies their own implementation. Always dispatch a separate verifier agent.

**P3 — Stale state.** Reading state from before a crash/timeout without checking the heartbeat timestamp. Always validate state freshness on claim.

**P4 — Parallel conflict.** Two workers modify the same file. Batch only tasks with disjoint file sets.

**P5 — Missing spec validation.** Dispatching without running `load_spec()`. The spec gates the loop — always validate first.

**P6 — Cron/no-user session: delegate_task results don't arrive in-session.** When the dispatcher runs as a scheduled cron job with no user present, `delegate_task` subagents run in the background and their results only re-enter the conversation when they finish — which may be after the cron session ends. **Implement tasks directly in the dispatcher session instead of delegating them.** The dispatcher *is* the worker in a cron context. Signal: `HERMES_CRON_SESSION=1` env var, or goal prompt says "You are running as a scheduled cron job."

**P7 — `node --watch` parent/child: SIGHUP kills the parent, not just reloads.** Node's `--watch` flag spawns a child process for each reload; the parent process is the watcher. Sending SIGHUP to the parent terminates the whole watcher, taking the server down. To trigger a hot reload, `touch` a watched source file instead. Never `kill -HUP` a `node --watch` parent.

**P8 — npm package name mismatch: `@livekit/client` does not exist.** The correct npm package is `livekit-client` (unscoped). `@livekit/client` returns 404. Imports use `from "livekit-client"`. Always `npm view <package>` before assuming a scoped name exists.

**P9 — YAML `depends_on` does not auto-wire Kanban parents.** When the plan spec declares `depends_on: [T3]` for T4, that is human-readable intent only — the Kanban board does NOT enforce it automatically. To actually block T4 until T3 reaches `done`, pass `parents=[t3_kanban_id]` when calling `kanban_create` for T4. Workflow: create T3's card first → capture its `task_id` → create T4 with `parents=[t3_task_id]`. If two tasks own the same file (serial by necessity), this parent wiring is the only thing preventing the dispatcher from dispatching them concurrently in a future iteration.

**P10 — Tasks that verify against a live server will time out if the server is down.** A subagent dispatched to write an acceptance test will spend its entire 600s budget retrying the test runner if the server is not up. Fix: split "write test" and "run test" into separate tasks, OR state explicitly in the task goal that the agent should write the test and commit without running it (server is down). Do server-dependent verification directly in the dispatcher session where you control the server. Symptom: subagent returns `status=timeout` at exactly 600s with 20+ API calls — root cause is almost always a blocking network call with no timeout guard. Pattern that works: T1 writes the acceptance scenario and commits it (no server required); the dispatcher runs the terminal gate directly after the implementation tasks land. The scenario file survives a T1 timeout — do T1 in-session and continue; the spec-first work outlasts any individual worker failure. (Lived: Sub-PR D, spire-ui, 2026-07-13.)
