---
name: cyclus-triage
description: "Multi-role consensus triage of an issue backlog."
version: 0.1.0
metadata:
  hermes:
    tags: [triage, multi-agent, consensus, backlog]
    category: omh
    requires_toolsets: [terminal, omh, delegation]
---

# Cyclus Triage — Consensus Backlog Grooming

> **v0.1 status:** This skill is **deliberately small**. It ships with two roles (Maintainer, Skeptic) and is being battle-tested before more roles are added. The full design hypothesis (Maintainer / Operator / Architect / Member-advocate / Skeptic) lives in [witt3rd/hermes-cyclus#9](https://github.com/witt3rd/hermes-cyclus/issues/9). The next concrete milestone (Operator role for version-cut planning pressure) is tracked at [witt3rd/hermes-cyclus#11](https://github.com/witt3rd/hermes-cyclus/issues/11). Roles will be added as lived rounds surface real tensions that the current set cannot represent. The discipline here is *learn through use, then expand* — the inverse of authoring all five roles up-front against imagined friction.

## When to Use

- Periodically grooming an issue backlog (default cadence: before each version cut, when ≥10 issues have accumulated since the last pass, or when a major refactor/migration just landed and may have moved issue premises)
- After a fast-moving development arc (multiple migrations or refactors in days/weeks) that may have superseded several open issues
- When the user says: "triage", "groom the backlog", "walk the issues", "what's stale"

## When NOT to Use

- A single ambiguous issue that needs design (use `cyclus-interview` then `cyclus-plan`)
- A backlog that's never been groomed and has hundreds of issues (do a manual first-pass cull first; this skill is for keeping a curated backlog honest, not for archaeology on a rotted one)
- Closing during active dev (don't mix the two-mode discipline — capture during dev, decide during grooming; see the host project's `docs/triage/PROCESS.md` if it has one)

## Prerequisites

- A target repo with an issue backlog (GitHub Issues; pluggable for other backlogs eventually)
- Optional: a GitHub Project for version + cluster + status targeting (the run will write back to it)
- Optional: prior triage docs under `docs/triage/` for delta-since-last-pass framing
- The `delegate_task` tool must be available

## Procedure

### Phase 0: Ground-truth pre-flight

Before dispatching any roles, the orchestrator gathers:

1. **Repo HEAD.** Note the commit ref. Verdicts will anchor against this.
2. **Issue inventory.** `gh issue list --state open --limit <N>`. Note count, label distribution, age distribution.
3. **Recent migrations / refactors.** Read commit log for the last N weeks. The orchestrator must know what surfaces have moved before dispatching — otherwise the Maintainer will discover this in-flight and waste a round.
4. **Existing project board state** (if any). Read target version, cluster, status fields for context.
5. **Prior triage doc** (if any). The most recent `docs/triage/YYYY-MM-DD-*.md` is delta-since-last-pass anchor.

Phase 0's output is a ~500-word context package that all subagents will receive. Same shape as `cyclus-plan` Phase 0.

### Phase 1: Role passes (sequential, parallel where possible)

**v0.1 ships two roles.** Future versions will add Operator, Architect, Member-advocate.

#### Step 1 — Maintainer pass

```
# v18: load role prompt before delegating
triage_maintainer_prompt = skill_view(name="cyclus-triage", file_path="references/role-triage-maintainer.md")
delegate_task(
    goal="Vet each issue in the attached inventory against current code. Produce a per-issue verdict (stale/recast/live/partial-stale/out-of-scope) with code-anchored reasoning. Repo HEAD: <ref>. Inventory: <list>",
    context="## Role\n{triage_maintainer_prompt}\n\n# Project context\n\n<context-package>\n\n# Inventory\n\n<full issue bodies, not just titles>"
)
```

The Maintainer's pass is **per-issue**. Output is structured (one block per issue with verdict + anchor + reasoning + close-comment-or-recast-spec).

#### Step 2 — Skeptic pass (after Maintainer; needs Maintainer's verdicts as input)

```
# v18: load role prompt before delegating
triage_skeptic_prompt = skill_view(name="cyclus-triage", file_path="references/role-triage-skeptic.md")
delegate_task(
    goal="For each LIVE issue from the Maintainer pass, apply skeptical pressure: keep/drop/dedup/refile-smaller/wait-for-recurrence. Stale/out-of-scope issues do not need skeptical review.",
    context="## Role\n{triage_skeptic_prompt}\n\n# Project context\n\n<context-package>\n\n# Maintainer verdicts\n\n<Maintainer's structured output>\n\n# Full inventory (for cross-reference)\n\n<full issue bodies>"
)
```

The Skeptic only reviews issues the Maintainer marked live or recast. Stale/out-of-scope are already moving to close; double-pressure on them wastes the role's attention.

#### Step 3 — Orchestrator distillation

The orchestrator combines Maintainer + Skeptic verdicts. **The matrix below is authoritative** — every Maintainer × Skeptic combination resolves to a specific disposition. Combinations not enumerated here are the only cases that escalate to user as a true conflict.

The Maintainer verdict `partial-stale` (issue contains multiple sub-claims; some stale, some live) is treated identically to `recast` for matrix purposes — both signal "body needs surgery, possibly extensive." Maintainer output should still distinguish them so the recast spec can name which sub-claims are stale vs live, but the disposition resolution is the same.

| Maintainer | Skeptic | Resolved disposition |
|------------|---------|----------------------|
| stale | (not run) | close — Maintainer pointer-comment |
| out-of-scope | (not run) | close — refile-target named |
| recast / partial-stale | keep | recast body, keep open |
| recast / partial-stale | drop / wait-for-recurrence | close — Skeptic pointer-comment (the body needs work AND the underlying friction may not be load-bearing; combined verdict is "not worth the surgery") |
| recast / partial-stale | dedup | close + comment-on-covering-issue |
| recast / partial-stale | refile-smaller | close + reopen-as-smaller |
| live | keep | live |
| live | drop / wait-for-recurrence | close — Skeptic pointer-comment |
| live | dedup | close + comment-on-covering-issue |
| live | refile-smaller | close + reopen-as-smaller |

The matrix is exhaustive over the verdict types in this skill (v0.1). When future versions add roles or new verdict types, the matrix expands; conflicts surface only when a *new* combination doesn't have a resolution.

**The escalation case** (rare in v0.1): if a Skeptic returns `needs lived signal` (the role's escape hatch when verdict cannot be determined) — or any other unresolved value the role catalog doesn't enumerate — that's a true escalation. The orchestrator surfaces these to user as specific decision questions. The orchestrator's job is to distill, not to decide for the user when the matrix doesn't resolve.

### Phase 2: Output

The orchestrator produces:

1. **Triage doc** at `docs/triage/YYYY-MM-DD-<descriptor>.md` (in the host repo, not in this skill repo) using the host project's template. If no template exists, use the structure documented in `references/triage-doc-template.md`.
2. **Verdict execution plan** — list of closures (with body files staged at `/tmp/closeN.md`), recasts (with proposed body diffs), refile-smaller drafts.
3. **Project board updates** (if a project is configured) — target-version moves, cluster updates, status changes.

The orchestrator **stages, does not execute** by default. The user sign-off gate happens between Phase 2 and execution. See `references/orchestrator-review-template.md`.

### Phase 3: Execution (user-gated)

After user approval:

1. Post pointer-comments and close stale/dropped issues
2. Post recast PRs (or comments with proposed body changes)
3. Update project board fields
4. Commit the triage doc with appropriate authorship

## Roles in v0.1

| Role | Reference | Pressure |
|------|-----------|----------|
| Triage Maintainer | `references/role-triage-maintainer.md` | Code-anchored ground truth: is the premise live? |
| Triage Skeptic | `references/role-triage-skeptic.md` | Pruning: does this earn its slot? |

Roles **planned for v0.2+** (witt3rd/hermes-cyclus#9):

- **Operator** — version-cut planning: smallest defensible vN+1
- **Architect** — cross-cutting: which issues are symptoms of one root
- **Member-advocate** — lived experience: what hurts the user/principal/being now

These will be added when lived rounds surface tensions the current two cannot represent. Resist authoring them ahead of evidence.

## Output Quality Bar

A run is done when:

1. Every open issue has a Maintainer verdict (no skipped issues)
2. Every live/recast issue has a Skeptic verdict
3. Every stale/dropped issue has a pointer-comment ready to post
4. Every recast issue has a specific body-surgery spec (not "rewrite the body")
5. Conflicts are escalated to user, not silently resolved
6. The triage doc names what this round did NOT do (deferred work)

## Pitfalls (v0.1, will grow)

### T1 — Don't dispatch Maintainer without ground-truth Phase 0

Maintainer's job is to anchor against current code. If the orchestrator hasn't already mapped recent migrations/refactors, the Maintainer discovers them in-flight and wastes attention re-deriving what Phase 0 should have given.

### T2 — Skeptic only reviews live + recast

Issues the Maintainer marked stale or out-of-scope are already moving to close. Sending them to Skeptic produces noise (Skeptic will say "drop" on stale issues, which adds nothing).

### T3 — Stage, don't execute by default

Triage closes are durable on the issue tracker. Always stage closures with body files at `/tmp/closeN.md` and let the user approve before executing the actual close commands. The skill that runs the close after approval should loop in shell with `--comment "$(cat /tmp/closeN.md)"` (multi-paragraph quoted bodies through `terminal()` from `execute_code` fail silently — lesson from janus round 1).

### T4 — The matrix resolves; only un-enumerated cases escalate

The verdict-combination matrix in Phase 1 Step 3 is **authoritative** — `live` + `drop` resolves to "close — Skeptic pointer-comment", not to "user conflict." The matrix encodes our considered judgment that "Maintainer says live, Skeptic says drop" means *the issue is real but not worth the slot it consumes*; closing with a clear pointer-comment that invites refile-on-recurrence is the correct disposition, not a user-decision question.

True escalations are: the Skeptic returns `needs lived signal` (escape hatch), the Maintainer returns `needs investigation` (escape hatch), or some future role's verdict produces a combination the matrix doesn't enumerate. These are rare in v0.1 and surface to user as specific decision questions, not as "there are some conflicts."

The dispatcher should also feel free to **override the matrix** for individual issues when their own bar applied to the verdict produces a different read — but that's a dispatcher-judgment call, not a matrix conflict. Note overrides explicitly in the orchestrator review (`cyclus-plan-dispatcher` P25 — skepticism over deference applies here too).

### T5 — A round produces a durable doc

The triage doc under `docs/triage/YYYY-MM-DD-*.md` is the round's audit trail. It names what was decided, what was deferred, and what the round taught. A round without a doc didn't happen.

### T6 — Resist the pressure to ship missing roles up-front

This skill is v0.1 deliberately. The OMH#9 design names five roles; only two ship today. Adding Operator / Architect / Member-advocate before lived rounds surface real tensions for them is the "imagined friction" failure mode. Wait for evidence.

---

## Dispatcher Pre-flight (do this before Phase 0)

### Audit the backlog

- **<10 issues** → decide manually; triage overkill
- **>100 issues** → backlog has rotted; manual cull first
- **<2 weeks since last grooming AND no major refactor** → probably skip
- **Recent migrations/refactors** → this is the load-bearing check. What surfaces moved since issues were filed? High movement = high-leverage triage run.

### Identify the trigger

| Trigger | What it means |
|---------|---------------|
| About to cut vN+1 | Output targets version field. Maintainer dominates. |
| Just shipped major migration | Cleanup pass. Mostly closures. |
| Backlog feels heavy | Skeptic's pressure dominates. |
| Periodic hygiene | Low priority. Defer until a real trigger exists. |

The trigger shapes how you weight role outputs. Name it before dispatching.

### Verify infrastructure

Does the project have:
- `docs/triage/PROCESS.md` (two-mode discipline: quick-file vs grooming)?
- A GitHub Project with version + cluster fields?
- A prior triage doc to delta against?

If not, propose authoring these first — triage produces dated docs and board updates; without the infrastructure, output evaporates.

### Dispatcher's job during the run

- **Phase 0:** Author the context package yourself (~500 words). Don't delegate it — the package shapes both roles' work and a bad package wastes both passes.
- **Phase 1:** Maintainer first; Skeptic only on Maintainer's live + recast output. Don't run them parallel-from-scratch — the Skeptic needs Maintainer's verdicts.
- **Phase 2:** You produce the resolution table. Conflicts → specific decision question to user, not generic "there's some disagreement." Format each as: "Maintainer says X for reason A; Skeptic says Y for reason B; my recommendation is Z."
- **Phase 3:** User-gated execution. Read every close comment before posting. A wrongly-closed issue is harder to recover than a wrongly-kept one.

### Pre-flight pitfalls

**T1 — Skipping ground-truth pre-flight.** Bad ground truth produces stale verdicts that look authoritative. Spend 10 minutes mapping recent migrations before dispatching.

**T2 — Writing the triage doc before the run.** Don't validate pre-decided verdicts. Write the doc *from* the run output.

**T3 — Scope creep.** If a role surfaces "we should redesign X" — that's a ralplan, not triage. Note in deferred section.

**T4 — Rubber-stamping closures.** Read every close comment. Ratify each verdict, don't rubber-stamp.

**T5 — Vague conflict presentation.** Frame conflicts as specific decision questions with your recommendation, not as "there's some disagreement."

**T6 — Running too often.** If dispatching weekly, the problem is upstream (filing discipline, backlog size), not triage frequency.

---

## References (internal — not user-facing skills)

- `references/role-triage-maintainer.md` — Maintainer role prompt (load via `skill_view`)
- `references/role-triage-skeptic.md` — Skeptic role prompt
- `references/triage-doc-template.md` — Round doc structure
- `references/orchestrator-review-template.md` — Pre-execution review checklist

## See Also

- [`witt3rd/hermes-cyclus#9`](https://github.com/witt3rd/hermes-cyclus/issues/9) — design tracking issue

