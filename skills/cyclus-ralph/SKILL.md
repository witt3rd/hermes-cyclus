---
name: cyclus-ralph
description: "execute plan: 1 task/call, verify evidence, iron law"
version: 2.0.0
metadata:
  hermes:
    requires_toolsets: [terminal, omh]
    tags: [execution, verification, persistence, iron-law, loop]
    category: omh
---

# OMH Ralph — Verified Execution (v2)

> **Requires the OMH plugin.** Install `plugins/omh/` from this repo to
> `~/.hermes/plugins/omh/`.

**Loop kind: `TaskExecutionKind`.** This skill implements a `TaskExecutionKind` loop.
Each invocation does one unit of work (one task) and exits cleanly. Loop state
is tracked in `.omh/queue.db` via the `cyclus_queue` tool.

## When to Use

- You have a plan (from cyclus-ralplan or manual) and need verified execution
- The user says: "ralph", "don't stop", "until done", "must complete", "keep going"
- You need guaranteed verification — not just "looks done" but evidence-backed completion
- Multi-step implementation where each task must be independently verified

## When NOT to Use

- No plan or spec exists (use cyclus-deep-interview and/or cyclus-ralplan first)
- Trivial single-file changes (just do them directly)
- The user explicitly wants to skip verification

## Architecture: One Task Per Invocation

Each ralph invocation does ONE unit of work and exits. The caller re-invokes for
the next task. This eliminates context window exhaustion and makes every invocation
a clean checkpoint.

```
Invocation N:  claim item → read state → pick task → execute → verify → write_state → release → EXIT
Invocation N+1: claim item → read state → pick next task → execute → verify → write_state → release → EXIT
...
Final invocation: all tasks pass → architect review → complete → EXIT
```

## Procedure

### Step 0: Resolve Instance and Claim Work Item

Ralph and autopilot mutate a shared `.omh/plans/` plan. Two sessions
running ralph against the same plan would race on task state
and produce non-deterministic outcomes. Use per-instance claim to make concurrent plans safe.

1. **Resolve `instance_id`** from the plan path:
   - Default plan source: `.omh/plans/ralplan-*.md` or `.omh/plans/ralph-plan.md`.
   - `instance_id = basename(plan_path) without ".md"` (engine slugifies).
   - If no plan exists yet (Step 2 will choose), use `instance_id="default"`.
2. **Claim the work item** before reading/writing state:
   ```
   result = cyclus_queue(action="claim", mode="ralph", instance_id="{instance_id}")
   ```
   - `result.status="claimed"`: continue. `result.item.state_path` holds the path to the
     intermediate state file.
   - `result.status="not_found"`: no work item exists yet — call
     `cyclus_queue(action="post", mode="ralph", instance_id="{instance_id}", kind="TaskExecutionKind", name="{plan description}")`
     first, then claim again.
   - `result.status="running"`: another session holds this item (fresh heartbeat). Report
     this to the user (check `cyclus_queue(action="status", mode="ralph", instance_id="{instance_id}")`
     for metadata). Offer: wait / signal cancel
     (`cyclus_queue(action="cancel", mode="ralph", instance_id="{instance_id}")`)
     and retry on next invocation / pick a different plan.
3. **Pass `instance_id` to every subsequent `cyclus_queue` call in this invocation.**
4. **Release the item at every clean exit point** (success, blocked, max-iterations):
   ```
   cyclus_queue(action="release", mode="ralph", instance_id="{instance_id}")
   ```
   This resets the item to PENDING so the next invocation can claim immediately.
   On crash (no release called), heartbeat-based reclaim fires after 300 seconds
   automatically — no manual unlock needed.

> **State file.** All intermediate state is read/written via `state_path` (a JSON file
> in the project). Read: `read_file(result.item.state_path)`. Write:
> `cyclus_queue(action="write_state", mode="ralph", instance_id="{instance_id}", state={...})`.

### Step 1: Read State

```
state_path = result.item.state_path  # from claim result
state = read_file(state_path)        # JSON; empty dict on first invocation
```

- **Empty / does not exist**: Fresh start — go to Step 2 (Planning Gate).
- **`state.active=true`**: Resume — go to Step 3.
- **`state.phase="complete"`**: Report completion. Ask if user wants fresh start.
- **`state.phase="blocked"`**: Report blockers. Ask if issues are resolved.
- **`state.active=false`, `phase="cancelled"`**: Report cancellation. Offer resume.

Check for cancel signal:
```
item_status = cyclus_queue(action="status", mode="ralph", instance_id="{instance_id}")
```
If `item_status.cancel_requested=1`: call
`cyclus_queue(action="complete", mode="ralph", instance_id="{instance_id}", terminal_state="Cancelled")`
and exit.

Check staleness: if `state.stale=true`, warn the user and offer to continue or fresh start.

Increment `state.iteration`. If `iteration > max_iterations` (default 100):
write `phase="blocked"` via `write_state`, release, report "Max iterations reached", exit.

### Step 2: Planning Gate

**Step 2 (pre-check): Validate spec.yaml if present**

Before checking for plan files, look for a spec.yaml at:
- `.cyclus/plans/{instance_id}-spec.yaml`, OR
- A path recorded in the work item's state

If found:
1. Run: `python -c "from cyclus.specs import load_spec; load_spec('{path}')"`
   (via terminal tool or cyclus_evidence with a single command)
2. If it exits nonzero (ValidationError or ValueError): **halt immediately.**
   Report the exact error to the user. Do NOT proceed to plan parsing.
3. If it exits 0 or no spec.yaml is found: continue to plan source checks below.

Ralph MUST NOT execute without a plan. Check sources in order:

1. `cyclus_queue(action="status", mode="ralph", instance_id="{instance_id}")` — if tasks are
   already loaded in `state_path`, skip to Step 3
2. `.omh/plans/ralplan-*.md` — parse into task list, write via `write_state`
3. `.omh/plans/ralph-plan.md` — parse into task list, write via `write_state`
4. Nothing found → tell user: "No plan found. Run `cyclus-ralplan` first."

**Plan parsing rules:**
- Extract numbered tasks with titles, descriptions, and acceptance criteria
- Reject generic criteria like "implementation is complete" — must be testable
- Enforce atomicity: split multi-part tasks into separate entries
- Assign priorities by dependency order (no-dependency tasks first)
- Set all tasks to `passes: false`

Write initial state:
```
cyclus_queue(action="write_state", mode="ralph", instance_id="{instance_id}", state={
  "active": true, "phase": "execute", "iteration": 0,
  "session_id": "<uuid>", "max_iterations": 100,
  "task_prompt": "<original user request>",
  "current_task_id": null,
  "started_at": "<ISO 8601 timestamp>",
  "project_path": "<absolute path to project root>",
  "files_modified": [],
  "error_history": [],
  "completed_task_learnings": [],
  "tasks": [{...parsed task list...}]
})
```

Also check cancel signal: if `cyclus_queue(action="status", mode="ralph", instance_id="{instance_id}")`
returns `cancel_requested=1`, call
`cyclus_queue(action="complete", mode="ralph", instance_id="{instance_id}", terminal_state="Cancelled")`
and exit.

### Step 3: Pick Next Task

Read task list from state file:
```
state = read_file(state_path)
tasks = state["tasks"]
```

1. If ALL tasks have `passes: true` → go to Step 7 (Final Review)
2. Find eligible tasks: `passes=false` AND all dependencies met
3. If no eligible task but incomplete tasks remain → dependency deadlock → write state with
   `phase="blocked"` via `write_state`, release, exit
4. Among eligible tasks, pick by priority (lowest number first)

**Parallel execution:** if 2-3 independent tasks are eligible (no shared file
footprint, no dependency between them), batch them into one `delegate_task` call.

### Step 4: Execute

Before delegating, load the role prompt:
```
executor_prompt = skill_view(name="cyclus-ralph", file_path="references/role-executor.md")
```
If `skill_view` returns empty or raises, abort: "Role prompt unavailable — cannot dispatch
without role context."

Delegate to an executor subagent:
```
delegate_task(
    goal="Implement this task:\n\n{task.title}\n{task.description}\n\nAcceptance Criteria:\n{task.acceptance_criteria}",
    context="## Role\n{executor_prompt}\n\nProject Context:\n{tech stack, conventions, relevant paths}\n\nPrevious Feedback (if retry):\n{task.verifier_verdict}\n\nLearnings from prior tasks:\n{state.completed_task_learnings}"
)
```

Parse the executor's response: **COMPLETE** → Step 5, **PARTIAL** → Step 5,
**BLOCKED** → record blocker, add discovered task if needed, write state via `write_state`,
release, exit.

Also check cancel signal after executor completion: if `cyclus_queue(action="status", ...)`
returns `cancel_requested=1`, call
`cyclus_queue(action="complete", ..., terminal_state="Cancelled")` and exit.

### Step 5: Verify

**Part A: Gather evidence**

```
evidence = cyclus_evidence(commands=[
    "{project build command}",
    "{project test command}",
    "{project lint command}"
])
```

Use the project's actual build/test/lint commands. The tool captures output,
enforces timeouts, and returns `{results, all_pass, summary}`.

**Part B: Delegate to verifier**

Before delegating, load the role prompt:
```
verifier_prompt = skill_view(name="cyclus-ralph", file_path="references/role-verifier.md")
```
If `skill_view` returns empty or raises, abort: "Role prompt unavailable — cannot dispatch
without role context."

```
delegate_task(
    goal="Verify whether this task's acceptance criteria are met:\n\n{task.title}\n{task.acceptance_criteria}\n\nExecutor Report:\n{task.executor_report}",
    context="## Role\n{verifier_prompt}\n\nEvidence:\n{evidence.results}"
)
```

Parse the verifier's response:
- **APPROVE / PASS**: Set `task.passes = true`. Append to learnings:
  `{task_id, summary, files_changed, gotchas}`. Append to `.omh/logs/ralph-progress.md`.
- **REQUEST_CHANGES / FAIL**: Record `task.verifier_verdict`. Check 3-strike rule (Step 6).

Write updated state via `cyclus_queue(action="write_state", mode="ralph", instance_id="{instance_id}", state={...})`.
Also check cancel signal: if `cancel_requested=1`, call
`cyclus_queue(action="complete", ..., terminal_state="Cancelled")` and exit.

### Step 6: Error Handling

**3-Strike Circuit Breaker:** Construct error fingerprint `{task_id, category, error_key}`.
Add to `task.error_fingerprints`. If 3 fingerprints share the same `category + error_key`:
mark task blocked, log the error, continue to next eligible task on next invocation.
If ALL remaining tasks are blocked: write state with `phase="blocked"` via `write_state`,
release, exit.

**Cancel detection** (if user says "stop", "cancel", "abort"):
```
cyclus_queue(action="cancel", mode="ralph", instance_id="{instance_id}", reason="user request")
```
Then call `cyclus_queue(action="complete", mode="ralph", instance_id="{instance_id}", terminal_state="Cancelled")`
and exit with resume instructions.

### Step 7: Final Review

When all tasks have `passes: true`:

Before delegating, load the role prompt:
```
architect_prompt = skill_view(name="cyclus-ralph", file_path="references/role-architect.md")
```
If `skill_view` returns empty or raises, abort: "Role prompt unavailable — cannot dispatch
without role context."

```
evidence = cyclus_evidence(commands=["{build command}", "{test command}"])

delegate_task(
    goal="Review the complete implementation for architectural soundness.\n\nOriginal Plan:\n{source plan text}\n\nTasks Completed:\n{summary of all tasks + learnings}",
    context="## Role\n{architect_prompt}\n\nEvidence:\n{evidence.results}\n\nFiles Changed Across All Tasks:\n{aggregate file list}"
)
```

- **APPROVE**: Call `cyclus_queue(action="complete", mode="ralph", instance_id="{instance_id}", terminal_state="PlanComplete", output={"tasks_completed": N, "files_modified": [...], "progress_log": ".omh/logs/ralph-progress.md"})`. Keep progress log.
- **REQUEST_CHANGES**: Add new tasks with `discovered: true`, write updated state via `write_state`,
  set `phase="execute"`, release, continue on next invocation.

### Step 8: Update State and Exit

After every action, write intermediate state:
```
cyclus_queue(action="write_state", mode="ralph", instance_id="{instance_id}", state={...updated state...})
```

At every clean exit point (not crash), release the item:
```
cyclus_queue(action="release", mode="ralph", instance_id="{instance_id}")
```

Exit cleanly. The caller re-invokes for the next iteration.

## Pitfalls

- **Never skip the planning gate.** No plan = no execution.
- **Never trust executor claims without verifier evidence.** The verifier must see `cyclus_evidence` output.
- **Don't run evidence inside the verifier delegation.** Gather evidence BEFORE delegating.
- **Don't conflate verifier and architect.** Different jobs, different prompts, different phases.
- **Respect the 3-strike rule.** Same error 3 times → surface the fundamental issue.
- **Feed learnings forward.** Include `completed_task_learnings` in every executor delegation.
- **Role prompts must be loaded via skill_view before delegating — not injected automatically in v18.** Use `skill_view(name="cyclus-ralph", file_path="references/role-{role}.md")`. If `skill_view` returns empty, abort the delegation — a role-less subagent produces garbage results. Available roles: executor, verifier, architect.
- **Call release() at clean exit so the next invocation can claim immediately.** Without `release()`, the next `claim()` waits up to 300 seconds (heartbeat timeout) before reclaiming. On crash, heartbeat-based reclaim handles recovery automatically — no manual unlock needed.
- **Spec gate fires before plan parsing.** If `spec.yaml` is present and `load_spec()` raises, stop. A malformed spec will corrupt every subsequent iteration; fail loudly at the gate rather than silently producing wrong output.

## Sentinel Convention

Other skills detect ralph status:
- `cyclus_queue(action="status", mode="ralph", instance_id="{instance_id}")` → returns item dict
  with `status`, `terminal_state`, `cancel_requested` fields; returns `{"found": false}` if
  no item exists
- `terminal_state="PlanComplete"` → ralph finished successfully
- `status="BLOCKED"` → ralph needs intervention
