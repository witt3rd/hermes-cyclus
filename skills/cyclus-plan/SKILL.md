---
name: cyclus-plan
description: "ConsensusKind: Planner+Architect+Critic deliberate to produce a verified implementation plan"
version: 3.0.0
metadata:
  hermes:
    tags: [planning, multi-agent, consensus, architecture, cyclus]
    category: cyclus
    requires_toolsets: [terminal, file]
---

# cyclus-plan

**Loop kind:** `ConsensusKind`  
**Turn results:** `RoundComplete | ConsensusReached`  
**Terminal states:** `ConsensusTerminalReached | Deadlocked`  
**Max rounds:** 3

---

## When to Use

- Before implementing anything that touches multiple files or components
- When architectural decisions need adversarial validation
- When the user says: "plan this", "let's think this through", "design first"
- When `cyclus-interview` has clarified the requirements and you have a clear goal

Don't use when:
- Trivial single-file changes (just do them)
- Goal is still ambiguous — use `cyclus-interview` first
- User explicitly wants to skip planning

---

## Dispatcher Prep (do this before Phase 1)

Quality is born in prep. The Planner/Architect/Critic triangle converges on internal
consistency — it will produce coherent output about *whatever you point it at*, including
the wrong frame. The dispatcher is the only role with the vantage to prevent this.

### 1. Carve principles first

Ralplan without principles produces plausibly-reasoned nonsense. If no `PRINCIPLES.md`
exists, draft a short one (≤15 entries, each naming the failure it prevents) before
dispatching. Even a rough draft beats unprincipled planning.

### 2. Author a context package (~500 words)

Not a prompt — a living document. Read the relevant source before writing it:
- Project structure, active conventions, constraints
- Adjacent mechanisms the plan must not duplicate
- Any design decisions already made (don't let subagents re-debate them)
- The user's lived context (half of requirements only the user knows)

If the package exceeds ~1000 words, it's bloated. Cut to the load-bearing facts.

### 3. Verify ground truth

Read the actual source, not summaries. If designing against another system, pass
file paths to subagents so they read the implementation directly. Summaries lose
critical field names, state schemas, and design patterns.

---

## Procedure

### Phase 0: Gather context

1. Read relevant files to understand codebase structure and conventions
2. Summarize into a brief (~500 words) — this is the context package all subagents receive
3. Post and claim the work item:
   ```
   cyclus_queue(action="post", mode="plan", instance_id="{slug}", kind="ConsensusKind", name="Plan: {goal}")
   cyclus_queue(action="claim", mode="plan", instance_id="{slug}")
   ```

### Phase 1: Planning loop (max 3 rounds)

Load all role prompts via `skill_view` before dispatching — never inline them:
```
planner_prompt  = skill_view(name="cyclus-plan", file_path="references/role-planner.md")
architect_prompt= skill_view(name="cyclus-plan", file_path="references/role-architect.md")
critic_prompt   = skill_view(name="cyclus-plan", file_path="references/role-critic.md")
```
If any `skill_view` call returns empty, abort: "Role prompt unavailable."

**Round 1 — Sequential (Planner → Architect → Critic):**

```python
# Step 1: Planner
delegate_task(
    goal="Create an implementation plan for: {goal}\n\n{detailed_requirements}",
    context="# Project Context\n\n{context_package}\n\n## Role\n\n{planner_prompt}"
)

# Step 2: Architect review
delegate_task(
    goal="Review this plan for architectural soundness:\n\nPLAN:\n{planner_output}",
    context="# Project Context\n\n{context_package}\n\n## Role\n\n{architect_prompt}"
)

# Step 3: Critic challenge
delegate_task(
    goal="Challenge this plan:\n\nPLAN:\n{plan_summary}\n\nARCHITECT:\n{architect_verdicts}",
    context="# Project Context\n\n{context_package}\n\n## Role\n\n{critic_prompt}"
)
```

**Consensus check:** All three APPROVE → proceed to output.
Any REQUEST_CHANGES → collect all feedback (label A1/A2/C1/C2/W1), go to Round 2.
Any REJECT → surface to user.

**Round 2+ — Planner revises; Architect + Critic re-review in parallel:**

```python
# Planner revises with ALL feedback
delegate_task(goal="Revise plan addressing: A1: {}, C1: {}", context="{context_package}\n\n{planner_prompt}")

# Parallel re-review (saves ~100s vs sequential)
delegate_task(tasks=[
    {"goal": "Re-review revised plan:\n{revised}\n\nPrior concerns: {architect_concerns}", "context": "{context_package}\n\n{architect_prompt}"},
    {"goal": "Re-review revised plan:\n{revised}\n\nPrior concerns: {critic_concerns}",   "context": "{context_package}\n\n{critic_prompt}"},
])
```

Write state after each phase:
```
cyclus_queue(action="write_state", mode="plan", instance_id="{slug}", state={
    "goal": "...", "round": N, "phase": "planner|architect|critic|complete",
    "consensus": false, "plan_file": ".cyclus/plans/plan-{slug}.md"
})
```

### Phase 2: Output

Write the consensus plan to `.cyclus/plans/plan-{slug}.md`:
1. Consensus status (rounds, verdicts per round)
2. Revision summary (what changed and why)
3. Final plan (tasks with dependencies, acceptance criteria)
4. Risks and open questions

Use descriptive slugs: `plan-auth-refactor.md` not `plan-20260707.md`.

Summarize key design decisions to the user.

Complete the work item:
```
cyclus_queue(action="complete", mode="plan", instance_id="{slug}", terminal_state="ConsensusReached")
```

**Deliberate mode:** When the user requests ADR format, load `references/adr-template.md`
and have the Architect produce Architecture Decision Record output.

---

## Pitfalls

**P1 — No principles.** Dispatching without principles produces coherent-but-wrong plans. Carve principles first.

**P2 — Stale source.** Subagents inherit summaries instead of reading actual code. Pass file paths, not summaries.

**P3 — Inline role prompts.** Always load via `skill_view` — never hardcode role text in the goal string.

**P4 — Sequential Round 2+ reviews.** Architect and Critic are independent in re-review; run them in parallel.

**P5 — Vague feedback labels.** Label all feedback A1/A2/C1/C2/W1 so the Planner can address each explicitly.

**P6 — Round bloat.** Cap at 3 rounds. If no consensus, output with caveats rather than loop indefinitely.

**P7 — Ambiguous goal.** If requirements are unclear, stop and suggest `cyclus-interview` first.

**P8 — Critic as blocker.** Minor issues should be APPROVE with reservations, not REJECT. The Critic challenges, not vetoes.

**P9 — Dispatcher skips context package.** Subagents must receive project context, not just the plan text.

---

## References (internal — not user-facing skills)

- `references/role-planner.md` — Planner role prompt (load via `skill_view` before dispatch)
- `references/role-architect.md` — Architect role prompt
- `references/role-critic.md` — Critic role prompt
- `references/adr-template.md` — Architecture Decision Record template for deliberate mode
- `references/brief-template.md` — Context package template
- `references/orchestrator-review-template.md` — Final review checklist

