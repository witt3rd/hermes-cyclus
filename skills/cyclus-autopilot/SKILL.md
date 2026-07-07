---
name: cyclus-autopilot
description: "pipeline: interview→plan→execute→QA→verify (idea→code)"
version: 3.0.0
metadata:
  hermes:
    requires_toolsets: [terminal, omh]
    tags: [autopilot, pipeline, autonomous, end-to-end, composition]
    category: omh
---

# OMH Autopilot — End-to-End Autonomous Pipeline

## Loop Kind

This skill implements a `TaskExecutionKind` loop (multi-phase pipeline).

## When to Use

- End-to-end feature implementation from idea to verified, reviewed code
- The user says: "autopilot", "build me", "handle it all", "e2e this"

## When NOT to Use

- Single-file changes or trivial tasks (just do them)
- You want to stay in one continuous session (autopilot is multi-session)
- You only need planning (cyclus-ralplan) or execution (cyclus-ralph)

## Prerequisites

- The `omh` plugin must be installed (`~/.hermes/plugins/omh/`)

## Architecture: One Phase Step Per Invocation

Each autopilot invocation reads state, does ONE unit of work, exits. The caller re-invokes.
This preserves fresh context at every level — including during the ralph loop.

```
Invocation 1:   Phase 0 — requirements (or skip)
Invocation 2:   Phase 1 — planning (or skip)
Invocations 3-N: Phase 2 — ralph iterations (one per call)
Invocation N+1: Phase 3 — QA cycle         [FRESH SESSION]
Invocation M:   Phase 4 — validation round  [FRESH SESSION]
Final:          Phase 5 — cleanup → complete
```

See `references/caller-examples.md` for how to drive the loop.

## Procedure

### Step 0: Resolve Instance and Claim

Autopilot drives a goal through spec → plan → ralph → QA → validation.
Two autopilot sessions on the same goal would race on state simultaneously.
Use per-instance queue claims for mutual exclusion.

1. **Resolve `instance_id`** in this order:
   - If a confirmed spec exists at `.omh/specs/{name}-spec.md`, use
     `instance_id = "{name}"`.
   - Else if a plan exists at `.omh/plans/ralplan-{slug}.md`, use
     `instance_id = "{slug}"`.
   - Else derive from the goal: `instance_id = kebab(goal)[:60]`.
2. **Post the work item** (idempotent — safe to call on every invocation):
   ```
   cyclus_queue(action="post", mode="autopilot", instance_id="{instance_id}",
             kind="TaskExecutionKind", name="{goal}")
   ```
3. **Claim the work item**:
   ```
   result = cyclus_queue(action="claim", mode="autopilot", instance_id="{instance_id}")
   ```
   - `status="claimed"`: proceed; read current phase from the work item's state file.
   - `status="running"`: the item is held by another active session.
     Report the holder (check `cyclus_queue(action="status", mode="autopilot", instance_id=...)` for details),
     offer wait/cancel/different goal.
   - `status="not_found"`: unexpected — `post()` first, then `claim()`.
4. **Pass `instance_id` to every `cyclus_queue` call** in this invocation
   (autopilot, ralph, ralph-tasks modes).
5. **Release at every exit point** (paused, blocked, exception):
   ```
   cyclus_queue(action="release", mode="autopilot", instance_id="{instance_id}")
   ```
   For terminal exits (Phase 5 cleanup complete, permanent block), call `complete()`
   instead of `release()`.

### On Every Invocation: Dispatch

After claiming, read the current `phase` from the work item's `state_path` file:

- **No state yet** (fresh item, `state_path` is empty or absent): Fresh start → Smart Detection (below)
- **Found**: Dispatch to current phase handler based on `state.phase`
- Check staleness: if state was last updated many hours ago, warn and offer
  fresh start

### Smart Detection (Fresh Start)

When autopilot state is absent, detect artifacts:

1. Confirmed spec in `.omh/specs/*-spec.md` → create state at Phase 1
2. Consensus plan in `.omh/plans/ralplan-*.md` → create state at Phase 2
3. Ralph complete — check `cyclus_queue(action="status", mode="ralph", instance_id="{instance_id}")`;
   if `status="COMPLETE"` → create state at Phase 3
4. Nothing → create state at Phase 0

Check for active ralph: `cyclus_queue(action="status", mode="ralph", instance_id="{instance_id}")` →
if `status` is `RUNNING` or `PENDING`, warn about existing session.

Initialize state via `cyclus_queue(action="write_state", mode="autopilot", instance_id="{instance_id}", state={...})`:

```
{
    "phase": "requirements", "goal": "...", "ralph_iteration": 0,
    "qa_cycle": 0, "max_qa_cycles": 5, "validation_round": 0,
    "max_validation_rounds": 3, "validation_verdicts": {},
    "skip_qa": false, "skip_validation": false, "pause_after_phase": null
}
```

### Phase 0: Requirements

**Goal**: Ensure a confirmed spec exists.

1. Check `.omh/specs/*-spec.md` with `status: confirmed` → found? Set `spec_file`, advance to Phase 1:
   `cyclus_queue(action="write_state", mode="autopilot", instance_id="{instance_id}", state={..., "phase": "planning", "spec_file": "<path>"})`,
   then `cyclus_queue(action="release", mode="autopilot", instance_id="{instance_id}")`, exit.
2. Not found — assess input:
   - **Concrete** (file paths, function names, specific tech): generate inline spec, advance
   - **Vague**: Load `cyclus-deep-interview` and follow it. **This phase is interactive.**
3. Update state: `phase: "planning"`, `spec_file: "<path>"`. Call `write_state(...)`, `release()`, exit.

**For fully autonomous runs**: run `cyclus-deep-interview` separately first.

### Phase 1: Planning

**Goal**: Ensure a consensus plan exists.

1. Check `.omh/plans/ralplan-*.md` → found? Set `plan_file`, advance to Phase 2:
   call `cyclus_queue(action="write_state", mode="autopilot", instance_id="{instance_id}", state={..., "phase": "execution", "plan_file": "...", "ralph_iteration": 0})`,
   then `cyclus_queue(action="release", mode="autopilot", instance_id="{instance_id}")`, exit.
2. Not found: Load `cyclus-ralplan`, follow its procedure with the spec as input.
3. Update state: `phase: "execution"`, `plan_file`, `ralph_iteration: 0`.
   Call `write_state(...)`, `release()`, exit.

Each phase transition follows the pattern: `write_state({phase: "next_phase", ...})` →
`release()` → exit. The fresh session on re-invocation picks up cleanly via `claim()` + phase dispatch.

### Phase 2: Execution (Ralph Iterations)

Each invocation performs **exactly ONE ralph iteration**:

1. Load the ralph skill and run one iteration via `delegate_task`:
   ```
   ralph_skill = skill_view(name="cyclus-ralph")
   delegate_task(
     goal="Follow the cyclus-ralph skill procedure: read state, pick the next incomplete task, execute it, verify, update state, exit.",
     context="<current ralph state + plan file contents>\n\n## Ralph Skill Procedure\n{ralph_skill}"
   )
   ```
2. After ralph completes its step, check ralph status:
   ```
   ralph = cyclus_queue(action="status", mode="ralph", instance_id="{instance_id}")
   ```
   - `status` is `PENDING` or `RUNNING` (still active) → increment `ralph_iteration`,
     call `write_state({..., "ralph_iteration": N})`, call `release()`, exit (caller re-invokes).
   - `status` is `COMPLETE` → advance:
     call `write_state({..., "phase": "qa"})`, call `release()`, exit.
   - `status` is `BLOCKED` or `CANCELLED` → set autopilot `phase: "blocked"`,
     call `write_state({..., "phase": "blocked"})`, call `release()`, report, exit.

### Phase 3: QA Cycling

Each invocation performs **ONE QA cycle**. Starts in fresh session.

If `skip_qa: true` → advance to Phase 4: `write_state({..., "phase": "validation"})`, `release()`, exit.

1. Gather evidence using the project's actual build/test/lint commands (check for
   Makefile, package.json, Cargo.toml, pyproject.toml, etc. to determine the right commands):
   ```
   evidence = cyclus_evidence(commands=["<build>", "<test>", "<lint>"])
   ```
2. If `evidence.all_pass` → advance: `write_state({..., "phase": "validation"})`, `release()`, exit.
3. If failures:
   - Increment `qa_cycle`. Check 3-strike on `qa_error_history`. If triggered →
     `write_state({..., "phase": "blocked"})`, `release()`, exit.
   - If `qa_cycle > max_qa_cycles` (default 5) →
     `write_state({..., "phase": "blocked"})`, `release()`, exit.
   - Delegate diagnosis to architect subagent (read-only).
   - Delegate fix to executor subagent.
   - Update state via `write_state(...)`, call `release()`, exit (next invocation re-runs QA).

### Phase 4: Multi-Reviewer Validation

Each invocation performs **ONE validation round**. Starts in fresh session.

If `skip_validation: true` → advance to Phase 5: `write_state({..., "phase": "cleanup"})`, `release()`, exit.

1. Gather evidence using the project's actual build/test commands:
   ```
   evidence = cyclus_evidence(commands=["<build>", "<test>"])
   ```
2. Load review role prompts and delegate 3 parallel reviews (exactly 3 = Hermes concurrent limit):
   ```
   architect_prompt = skill_view(name="cyclus", file_path="references/role-architect.md")
   security_prompt = skill_view(name="cyclus", file_path="references/role-security-reviewer.md")
   code_prompt = skill_view(name="cyclus", file_path="references/role-code-reviewer.md")
   delegate_task(tasks=[
       {goal: "Architectural review:\n{spec + plan}", context: "{evidence}\n\n## Role\n{architect_prompt}"},
       {goal: "Security review:\n{changed files list}", context: "{evidence}\n\n## Role\n{security_prompt}"},
       {goal: "Code quality review:\n{changed files list}", context: "{evidence}\n\n## Role\n{code_prompt}"}
   ])
   ```
3. Record verdicts in `validation_verdicts` and call `write_state(...)`.
4. All APPROVE → advance to Phase 5: `write_state({..., "phase": "cleanup"})`, `release()`, exit.
5. Any REQUEST_CHANGES → delegate fix to executor, increment `validation_round`,
   call `write_state(...)`, `release()`, exit.
6. If `validation_round > max_validation_rounds` (default 3) →
   `write_state({..., "phase": "blocked"})`, `release()`, exit.

### Phase 5: Cleanup

1. Set `phase: "cleanup"` first via `write_state(...)` (safety — if interrupted, re-invocation retries cleanup).
2. Call `complete()` for all queue items associated with this run:
   ```
   cyclus_queue(action="complete", mode="autopilot", instance_id="{instance_id}", terminal_state="PlanComplete")
   cyclus_queue(action="complete", mode="ralph", instance_id="{instance_id}", terminal_state="PlanComplete")
   cyclus_queue(action="complete", mode="ralph-tasks", instance_id="{instance_id}", terminal_state="PlanComplete")
   ```
3. Preserve: `.omh/logs/`, `.omh/plans/`, `.omh/specs/`
4. Report completion summary: goal, phases completed, ralph iterations, QA cycles, validation rounds

## State Management

All state via `cyclus_queue(action="write_state", ...)`. Atomic writes and heartbeat tracking
are handled by the queue. After each `claim()`, read the state from the `state_path` field
of the claimed item to restore phase and progress.

## Sentinel Convention

```
cyclus_queue(action="status", mode="autopilot", instance_id="{instance_id}")
→ item dict with status (PENDING|RUNNING|COMPLETE|BLOCKED|CANCELLED) and state_path
```

Read `state_path` for `{phase, goal, ralph_iteration, ...}`.

## Pitfalls

- **Don't loop ralph in a single session.** Each ralph iteration is a separate invocation. Context exhaustion is real.
- **Don't reimplement ralph.** Load the skill via `skill_view`, follow its procedure.
- **Phase boundaries = fresh sessions.** Call `release()` at the end of each phase before
  exiting. The next invocation claims fresh and reads the current phase from state.
- **Don't skip QA.** Ralph verifies per-task. QA catches integration issues.
- **Phase 0 is interactive** if no spec exists. Pre-create specs for automated runs.
- **3 subagent limit.** Phase 4 uses all 3 slots for parallel review.
