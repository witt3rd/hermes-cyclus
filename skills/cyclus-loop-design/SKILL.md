---
name: cyclus-loop-design
description: "Design a well-formed Cyclus loop: RECOGNIZE→SPECIFY→DECOMPOSE via Planner+Architect+Critic consensus (≤3 rounds)"
version: 1.0.0
metadata:
  hermes:
    tags: [loop-design, ldd, consensus, planning, meta-loop]
    category: cyclus
    requires_toolsets: [terminal, file]
---

# cyclus-loop-design — The LDD Meta-Loop

> **Loop kind:** `ConsensusKind`
> Turn results: `RoundComplete | ConsensusReached`
> Terminal states: `ConsensusReached | Deadlocked`
> Max rounds: 3

This skill is the structural expression of Loop-Driven Development (LDD).
It produces a validated `spec.yaml` and a ralph-shaped `plan.md` that the
`cyclus-ralph` planning gate will accept. Nothing gets dispatched until this
skill approves the loop design.

**This skill is itself a loop.** The discipline that enforces well-formed loops
is produced by running a ConsensusKind loop. LDD all the way down.

Read `docs/ldd.md` before using this skill.

---

## When to use

- Before dispatching ANY loop that isn't trivially obvious
- When you have a goal but no `spec.yaml`
- When a `cyclus-ralph` run timed out (decompose smaller via this skill first)
- When the user says: "design a loop", "loop-design", "spec this out", "LDD"

## When NOT to use

- Active pairing session + trivially small change (declare `active-pairing` in STATE.md, proceed directly)
- A loop spec already exists and has been validated

---

## Procedure

### Phase 0: Gather context

Before designing the loop, understand the work:

1. Read `STATE.md` — what has already been tried? What is the current baseline?
2. Read any relevant issue, spec, or design doc linked in the goal
3. Check existing specs in `.cyclus/plans/` for similar loops
4. Summarize in ~300 words: what the work is, what constraints exist, what
   done looks like

### Phase 1: Design loop (≤3 rounds)

**Round 1 — Sequential: Planner → Architect → Critic**

**Step 1 — Loop Planner**

Load role prompt:
```
planner_prompt = skill_view(name="cyclus-loop-design",
                             file_path="references/role-loop-planner.md")
```
If empty, abort: "Role prompt unavailable."

```
delegate_task(
    goal="Design a Cyclus loop for this goal:\n\n{goal}\n\n"
         "Produce: (1) spec.yaml fields, (2) decomposed task list.",
    context="## Role\n\n{planner_prompt}\n\n"
            "## Context\n\n{gathered_context}\n\n"
            "## Spec template\n\n{spec_template}"
)
```

**Step 2 — Loop Architect**

Load role prompt:
```
architect_prompt = skill_view(name="cyclus-loop-design",
                               file_path="references/role-loop-architect.md")
```

```
delegate_task(
    goal="Stress-test this loop design:\n\n{planner_output}",
    context="## Role\n\n{architect_prompt}\n\n"
            "## Context\n\n{gathered_context}"
)
```

**Step 3 — Loop Critic**

Load role prompt:
```
critic_prompt = skill_view(name="cyclus-loop-design",
                            file_path="references/role-loop-critic.md")
```

```
delegate_task(
    goal="Check this loop design for LDD anti-patterns:\n\n"
         "PLANNER OUTPUT:\n{planner_output}\n\n"
         "ARCHITECT REVIEW:\n{architect_output}",
    context="## Role\n\n{critic_prompt}\n\n"
            "## Context\n\n{gathered_context}"
)
```

**Step 4 — Consensus check**

- All three APPROVE → consensus reached, go to Phase 2
- Any REQUEST_CHANGES → collect feedback with IDs (A1/A2/C1/C2), go to Round 2
- Any REJECT → surface to user, ask whether to continue

**Round 2+ — Planner revises; Architect + Critic re-review in parallel**

Architect and Critic are independent in re-review — batch them:

```
delegate_task(tasks=[
    {
        "goal": "Re-review revised loop design:\n{revised_design}\n\nPrior concerns: {architect_concerns}",
        "context": "## Role\n\n{architect_prompt}\n\n## Context\n\n{gathered_context}"
    },
    {
        "goal": "Re-check revised loop design for anti-patterns:\n{revised_design}\n\nPrior concerns: {critic_concerns}",
        "context": "## Role\n\n{critic_prompt}\n\n## Context\n\n{gathered_context}"
    }
])
```

### Phase 2: Write output

Write two files:

**`spec.yaml`** at `.cyclus/plans/{slug}-spec.yaml`:

```yaml
kind: {LoopKind}
name: {slug}
level: L1            # always L1 until trust is established
metric: {metric}     # if MetricOptimizationKind
direction: {dir}
baseline: {baseline}
terminal:
  target_score: {score}
  max_iterations: {n}
  plateau_count: {p}
evaluate: |
  {eval_command}
target_files:
  - {file1}
```

**`plan.md`** at `.cyclus/plans/{slug}-plan.md`:

Ralph-shaped task list. Each task must have:
- Title (one line)
- Description (< 200 words — if longer, split the task)
- Acceptance criteria (testable, specific)
- Files owned (explicit list)
- Dependencies (which tasks must land first)

Report to the user:
- The loop kind chosen and why
- The decomposition (N tasks, estimated budget per task)
- Any anti-patterns caught and how they were resolved
- The exact `cyclus-ralph` invocation to dispatch

---

## Verdicts

Each role returns one of:

- **APPROVE** — design is sound, proceed
- **REQUEST_CHANGES** — specific concerns (labeled A1/C1 etc.), fixable in next round
- **REJECT** — fundamental problem, cannot proceed without user input

Consensus = all three APPROVE in the same round.

If no consensus after 3 rounds: write the output with caveats, surface the
open disagreements to the user. Do not block indefinitely.

---

## Output files

| File | Purpose |
|------|---------|
| `.cyclus/plans/{slug}-spec.yaml` | Machine-validated loop spec (Pydantic gate) |
| `.cyclus/plans/{slug}-plan.md` | Ralph-shaped task list |
| `STATE.md` update | Mode declaration: `loop-work`, instance, declared at timestamp |

---

## Pitfalls

- **Load role prompts via `skill_view` before every `delegate_task` call.**
  If `skill_view` returns empty, abort. Never inline role prompts.

- **Round 2+ Architect and Critic are independent — run in parallel.**
  Saves 60-90s per round.

- **The Architect's job is decomposition, not architecture.**
  cyclus-loop-design is not about system architecture (that's cyclus-ralplan).
  It's about whether the *loop* is well-formed: right kind, budget-sized tasks,
  verifiable terminal conditions.

- **The Critic checks LDD anti-patterns, not code quality.**
  L3-before-L1, no plateau detection, eval that modifies repo state, task
  descriptions > 200 words — these are the Critic's targets.

- **level: L1 always in initial output.**
  The Planner must never propose L2 or L3 on first design. Trust is earned
  by running at L1 first. The Architect and Critic must reject any spec that
  starts at L2 or L3.

- **Every task must fit in one delegation budget (~600s).**
  The Architect's primary job: count the words in each task description and
  trace the acceptance criteria. If a task description exceeds 200 words or
  acceptance criteria require more than one verifiable state transition, it
  must be split. This is the decomposition failure that caused the queue-rewrite
  timeout (session 2026-07-07) — it must not repeat.

- **Do not design loops for active-pairing-session work.**
  If you and the member are both present and the work is trivially obvious,
  declare `active-pairing` in STATE.md and proceed directly. cyclus-loop-design
  is for autonomous, recurring, or complex work.
