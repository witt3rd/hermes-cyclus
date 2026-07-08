---
name: cyclus-research
description: parallel web research; subagents→synthesis→cite-verify
version: 2.0.0
metadata:
  hermes:
    tags: [research, web, synthesis, parallel, omh]
    category: omh
    requires_toolsets: [terminal, omh, web]
---

# OMH Deep Research — Multi-Phase Web Research with Citation Verification

## Loop Kind

This skill implements an `InformationSeekingKind` loop.  
Turn results: `FindingsAdded | Sufficient`.  
Terminal states: `InformationSufficient | InformationExhausted | Cancelled`.

**SufficiencyFn:** At each round, evaluate whether gaps have closed using the
gap-tracking state stored in the work item. The `Sufficient` terminal is reached
when the gap list is empty or the evaluator judges evidence sufficient.

## When to Use

- The user asks for "deep research on", "a research report about",
  "comprehensive research", "investigate X", "what's known about Y"
- cyclus-interview encounters an unfamiliar domain and needs background
- cyclus-plan needs external context before it can plan responsibly
- The user's question requires synthesizing 3+ web sources into one
  coherent answer, not a single search

## When NOT to Use

- A confirmed report already exists at `.omh/research/{slug}-report.md`
  with `status: confirmed` for this topic — view it instead
- The question is answerable by a single web_search call
- The user wants real-time / current-events data only (this skill
  emphasizes durable synthesis, not freshness)
- No `web` toolset is available in this Hermes install (see Prerequisites)

## Prerequisites

This skill fail-fasts if any of the following are missing:

- **`web` toolset** — provides `web_search` AND `web_extract`. If either
  is unavailable, print:
  ```
  cyclus-research requires the `web` toolset (web_search + web_extract); aborting.
  ```
  and exit before doing any work.
- **`cyclus_queue` tool** — always available (zero-config embedded SQLite backend).
  Use `cyclus_queue` for all state tracking; no manual JSON fallback is needed or
  supported.
- **Write access** to `.omh/` for state, plan, findings, report, log.

Hermes discovery: `hermes skills list | grep cyclus-research` should
return this skill once installed.

### Installation (symlink for Hermes discovery)

```
mkdir -p ~/.hermes/skills/omh && ln -snf <repo>/plugins/omh/skills/cyclus-research ~/.hermes/skills/omh/cyclus-research
```

Parent dir creation MUST precede the symlink.

## Architecture

Five invocation phases, exit-safe between any two:

| # | Phase     | Reads                                  | Writes                                                       | Subagents |
|---|-----------|----------------------------------------|--------------------------------------------------------------|-----------|
| 1 | decompose | user query                             | `{slug}-plan.md`, state.phase=search                         | none      |
| 2 | search    | plan, state, findings/                 | new findings file(s), state.completed_subtopics, phase       | 1-3 researcher subagents (parallel; role loaded via skill_view) |
| 3 | gap_check | all findings                           | optional `_followup.md` OR direct phase flip                 | 0 or 1 researcher subagent (role loaded via skill_view) |
| 4 | synthesize| all findings (parent inlines)          | `{slug}-report.md` `status: draft`, phase=verify             | 1 synthesist subagent (role loaded via skill_view) |
| 5 | verify    | report + findings (parent inlines)     | confirmed frontmatter / state mutate / blocked               | 1 verifier subagent (role loaded via skill_view) |

**Per-instance state.** Each research session lives in the OMH queue under
`mode="research"` and `instance_id="{slug}"` (the slug minted in Phase 1).
Intermediate state is written to the `state_path` file via
`cyclus_queue(action="write_state", ...)`. Multiple topics can be in flight
concurrently — the slug IS the instance_id, and every subsequent
`cyclus_queue(...)` call passes `instance_id="{slug}"`. Per-session
artifacts (plan, findings, report) are slug-keyed under `.omh/research/`.
The earlier `research-{id}.json` and `research-state.json` (singleton)
wordings from older specs are superseded.

**Parent owns the filesystem.** All web tool use happens inside delegated
subagents. The parent reads findings files and inlines their contents
into synthesist's and verifier's `context` field. Subagents return
text only.

**Roles are loaded via skill_view, never inlined.** Before each delegation,
load the role prompt:
```
role_prompt = skill_view(name="cyclus", file_path="references/role-{name}.md")
```
Pass the loaded text in the delegation's `context` field under a `## Role`
heading. If `skill_view` returns empty or raises, abort with:
"Role prompt unavailable — cannot dispatch without role context."

## Procedure

### Phase 0: Check for Existing State and Sentinel

Before starting any new research session:

1. **Mint a candidate slug** for the new request (see Phase 1 rule).
   Call this `new_slug`. We need it to disambiguate enumeration below.
2. **Discover existing research instances** — scan `.omh/research/*-plan.md`
   files to find known slugs. For each slug, call
   `cyclus_queue(action="status", mode="research", instance_id="{slug}")` to
   read its queue status. Items with `status` of `PENDING`, `RUNNING`, or
   `BLOCKED` are considered active.
3. **For each active entry**, check for cancellation:
   if the status result shows `cancel_requested=1`, log
   `CANCELLED slug={slug}` and call
   `cyclus_queue(action="complete", mode="research", instance_id="{slug}", terminal_state="Cancelled")`.
4. **Sentinel self-heal (recovery from crash between confirm and complete).**
   For each remaining active entry whose
   `.omh/research/{slug}-report.md` has frontmatter `status: confirmed`,
   the previous run crashed after writing the sentinel but before calling
   `complete()`. Treat as completed: log
   `REPORT_CONFIRMED_RECOVERED slug={slug}`, then call
   `cyclus_queue(action="complete", mode="research", instance_id="{slug}", terminal_state="InformationSufficient")`.
5. **Topic-match resume** — if any remaining active entry's `topic` in its
   state file matches the new request, jump directly to Phase 2/3/4/5 for
   THAT slug (use its existing `instance_id`); do not mint `new_slug`.
6. **Already-confirmed for this topic** — if a `{slug}-report.md`
   exists with `status: confirmed` matching the new topic, prompt:
   refresh (mint a new slug and re-run) / view existing report / cancel.
7. **No conflict** — proceed to Phase 1 with `new_slug`. Concurrent
   active research on different topics is permitted; do not block.

### Phase 1: Decompose

1. **Cancel check**: call `cyclus_queue(action="status", mode="research", instance_id="{slug}")`;
   if `cancel_requested=1`, call
   `cyclus_queue(action="complete", mode="research", instance_id="{slug}", terminal_state="Cancelled")`
   and exit.
2. **Mint a slug** — concrete rule:
   `slug = kebab(topic)[:40] + '-' + YYYYMMDD + '-' + random4`
   where `random4` is 4 lowercase-hex chars.
   `kebab()` = lowercase, replace runs of non-alphanumeric with `-`,
   strip leading/trailing `-`, truncate to 40 chars.
3. Decompose the user's topic into 3-5 subtopics. For each subtopic,
   draft 2-3 candidate search queries.
4. **Write the plan** atomically (tmp → fsync → rename) to
   `.omh/research/{slug}-plan.md` with frontmatter:
   ```
   ---
   status: planning
   topic: {original user topic}
   slug: {slug}
   subtopics:
     - name: {subtopic 1 name}
       queries: [{q1}, {q2}, {q3}]
     - ...
   ---
   ```
5. **Post, claim, and initialize state**:
   - `cyclus_queue(action="post", mode="research", instance_id="{slug}", kind="InformationSeekingKind", name="{topic}")`
   - `cyclus_queue(action="claim", mode="research", instance_id="{slug}")`
   - `cyclus_queue(action="write_state", mode="research", instance_id="{slug}", state={...})`:
     ```
     {
       "phase": "search",
       "slug": "{slug}",
       "topic": "{topic}",
       "subtopic_count": N,
       "completed_subtopics": [],
       "started_at": "{ISO-8601}",
       "session_id": "{uuid4}",
       "synthesis_attempts": 0
     }
     ```
   - `cyclus_queue(action="release", mode="research", instance_id="{slug}")`
6. Log `STARTED slug={slug}` and `PLAN_WRITTEN slug={slug} subtopics=N`.
7. Exit. Re-invocation will pick up at Phase 2 via the Phase 0 resume path.

### Phase 2: Search (parallel batched, re-entrant)

This phase is **re-entrant**: it dispatches one batch of up to 3
researcher subagents per invocation, then exits. Re-invoke to dispatch
the next batch. Re-entry is driven by `state.completed_subtopics`.

1. **Claim the work item**:
   `cyclus_queue(action="claim", mode="research", instance_id="{slug}")`.
   Check `cancel_requested` in the result; if set, call
   `cyclus_queue(action="complete", terminal_state="Cancelled")` and exit.
   Read current state from the `state_path` in the claimed item.
2. Read state and the `{slug}-plan.md` frontmatter.
3. Compute `pending = [s for s in plan.subtopics if s.name not in state.completed_subtopics]`.
4. Take the next `batch = pending[:3]` (up to 3 in parallel).
5. **Load the researcher role and dispatch ONE batch call**:
   ```
   researcher_prompt = skill_view(name="cyclus", file_path="references/role-researcher.md")
   delegate_task(tasks=[
     {
       "goal": "<self-contained: topic, subtopic name, exact queries to run, output template>",
       "context": "<plan excerpt for this subtopic; no other subagent's findings>\n\n## Role\n{researcher_prompt}",
     },
     ...up to 3...
   ])
   ```
   Each task's `goal` is fully self-contained — no inter-subagent dependencies.
6. **(Strict write-order — NEVER reverse this order):**
   1. Write all findings file(s) for this batch atomically
      (tmp → fsync → rename). Each file lands at
      `.omh/research/{slug}-findings/{subtopic-slug}.md` with
      frontmatter capturing `subtopic`, `source_urls`, and credibility
      tags pulled from the subagent's returned SOURCES block.
   2. Update `state.completed_subtopics` (extend the list) and persist via
      `cyclus_queue(action="write_state", mode="research", instance_id="{slug}", state=...)`.
   3. `cyclus_queue(action="release", mode="research", instance_id="{slug}")`.
   4. Exit.
7. **Phase transition.** On the next invocation, Phase 0 routes back
   here. If `pending` becomes empty after the write, set
   `state.phase = "gap_check"` BEFORE releasing (order: findings →
   completed_subtopics → phase flip → write_state → release → exit).
8. Log `BATCH_COMPLETE batch=N subtopics=[name1,name2,...]` per batch.

**Pitfalls specific to Phase 2:**

- **Dedup across subtopics.** Two researchers may surface the same URL.
  The synthesist (Phase 4) handles cross-subtopic dedup via global
  Sources renumbering; Phase 2 does NOT need to dedup across files.
- **Slug for findings filename.** Use `kebab(subtopic.name)[:60]`. If
  two subtopics kebab to the same slug, append `-2`, `-3`, etc.
- **Parent never calls `web_search` or `web_extract` directly.** All
  web tool use is inside the delegated researcher subagents. The parent's
  job is dispatch and disk.

### Phase 3: Gap Check (TWO branches only)

The parent skill never calls `web_search` or `web_extract` directly;
all web tool use happens inside delegated subagents.

1. **Claim the work item**:
   `cyclus_queue(action="claim", mode="research", instance_id="{slug}")`.
   Check `cancel_requested`; if set, call `complete(terminal_state="Cancelled")` and exit.
2. Read all `.omh/research/{slug}-findings/*.md` files. From each, extract
   the `GAPS:` bullet list. Concatenate, then **dedup lexically**
   (case-insensitive trim-compare; preserve first occurrence).
3. **TWO branches only:**

   - **(a) 0 gaps** — **SufficiencyFn satisfied.** Set `state.phase = "synthesize"`,
     call `cyclus_queue(action="write_state", mode="research", instance_id="{slug}", state=...)`
     with updated state, call `cyclus_queue(action="release", mode="research", instance_id="{slug}")`,
     log `GAP_CHECK_COMPLETE gaps=0`, exit.

   - **(b) ≥1 gap** — Load researcher role and delegate ONE subagent:
     ```
     researcher_prompt = skill_view(name="cyclus", file_path="references/role-researcher.md")
     delegate_task(
       goal="<self-contained: research the following gaps: {deduped_gap_list}>",
       context="<deduped gap list>\n\n## Role\n{researcher_prompt}"
     )
     ```
     Parent writes the returned text to
     `.omh/research/{slug}-findings/_followup.md` (atomic). Set
     `state.phase = "synthesize"`, call `write_state` with updated state,
     call `release`, log `GAP_CHECK_COMPLETE gaps=N`, exit.

   No threshold tiers. No N-versus-M gap branching. No inline
   web_search branch. Two branches only — that is the contract.

### Phase 4: Synthesize (parent inlines findings; parent writes report)

1. **Claim the work item**:
   `cyclus_queue(action="claim", mode="research", instance_id="{slug}")`.
   Check `cancel_requested`; if set, call `complete(terminal_state="Cancelled")` and exit.
2. **Parent INLINES findings.** Read ALL files under
   `.omh/research/{slug}-findings/` (including `_followup.md` if
   present). Concatenate their full contents into the delegation's
   `context` field. The synthesist subagent has no filesystem access.

   **Budget escape (verified safe).** If the concatenated payload
   exceeds the orchestrator's tool-arg budget (≈40KB+ across 5+
   findings files is a soft threshold), the parent MAY summarize
   each findings file's SYNTHESIS section while preserving:
     - The full SOURCES `[N]` block verbatim (titles + URLs + tags + dates)
     - All GAPS sections verbatim
     - The `_followup` block verbatim (it is usually the smallest and
       most claim-dense)
   Do NOT drop or paraphrase any URL, citation tag, or numeric claim.
   Dogfooded 2026-04: a 5-subtopic + 1-followup run with summarized
   SYNTHESIS bodies + verbatim source lists passed verification at
   high confidence with all 28 globally-renumbered citations intact.
   When in doubt, prefer full inline; summarize only when forced.
3. **Load synthesist role and dispatch ONE task**:
   ```
   synthesist_prompt = skill_view(name="cyclus", file_path="references/role-research-synthesist.md")
   delegate_task(
     goal="<self-contained: produce report per synthesist role template; topic={topic}; reference inlined plan + findings>",
     context="<plan frontmatter + every findings file content, fully inlined>\n\n## Role\n{synthesist_prompt}",
   )
   ```
4. **Retry context.** If `state.synthesis_attempts > 0`, append the
   prior verifier's REQUEST_CHANGES feedback (stored in
   `state.last_verifier_feedback`) to the goal as:
   ```
   Address these prior verifier findings:
   {feedback}
   ```
5. **Parent always overwrites** `.omh/research/{slug}-report.md` with
   the returned text. Frontmatter starts at `status: draft`. NO `-v2`
   suffixing. Prior verdicts live only in state, not on disk.
6. **C3 propagation.** Parent does NOT edit the returned report. Any
   `(insufficient sources for this subtopic)` strings remain verbatim.
7. Set `state.phase = "verify"`, call
   `cyclus_queue(action="write_state", mode="research", instance_id="{slug}", state=...)`,
   call `cyclus_queue(action="release", mode="research", instance_id="{slug}")`,
   log `REPORT_DRAFT`, exit.

### Phase 5: Verify (parent inlines; 3-strike gate; ordered confirm)

1. **Claim the work item**:
   `cyclus_queue(action="claim", mode="research", instance_id="{slug}")`.
   Check `cancel_requested`; if set, call `complete(terminal_state="Cancelled")` and exit.
2. **Parent INLINES report + findings.** Read `{slug}-report.md` AND
   all `{slug}-findings/*.md` files. Concatenate BOTH into the
   verifier delegation's `context` field. Verifier subagent has no
   filesystem access.
3. **Tools allowlist (A5).** When dispatching, pass a tools allowlist
   EXCLUDING write/edit/filesystem tools where Hermes supports
   per-call tool scoping. If Hermes lacks per-call scoping, document
   in Known Gaps and rely on the prose READ-ONLY contract in
   `role-research-verifier.md`.
4. **Load verifier role and dispatch ONE task**:
   ```
   verifier_prompt = skill_view(name="cyclus", file_path="references/role-research-verifier.md")
   delegate_task(
     goal="<self-contained: verify report per verifier role; topic={topic}>",
     context="<report + all findings files, fully inlined>\n\n## Role\n{verifier_prompt}",
   )
   ```
   Parse the returned VERDICT.

5. **On VERDICT: PASS — STRICT ORDER (NEVER reverse):**
   1. Write `{slug}-report.md` with frontmatter `status: confirmed` (atomic; idempotent sentinel; THIS is the source-of-truth and must land FIRST).
   2. Append `REPORT_CONFIRMED slug={slug}` to the event log.
   3. Call `cyclus_queue(action="complete", mode="research", instance_id="{slug}", terminal_state="InformationSufficient")`.
   4. Print summary to user; exit.

   Phase 0 self-heals if a crash occurs between step 1 and step 3 (it
   detects the confirmed sentinel and completes the orphan queue item).

6. **On VERDICT: FAIL with `state.synthesis_attempts < 3`:**
   - Increment `state.synthesis_attempts`.
   - Store the verifier's REQUEST_CHANGES verdict (full body) in
     `state.last_verifier_feedback`.
   - Set `state.phase = "synthesize"`.
   - Call `cyclus_queue(action="write_state", mode="research", instance_id="{slug}", state=...)`.
   - Call `cyclus_queue(action="release", mode="research", instance_id="{slug}")`.
   - Log `VERIFY_FAIL slug={slug}` and `SYNTHESIS_RETRY attempt={N}`.
   - Exit. Re-invocation re-runs Phase 4 with feedback context.

7. **On VERDICT: FAIL with `state.synthesis_attempts == 3`:**
   - Set `state.phase = "blocked"`.
   - Call `cyclus_queue(action="write_state", mode="research", instance_id="{slug}", state={..., "phase": "blocked"})`.
   - Call `cyclus_queue(action="release", mode="research", instance_id="{slug}")`.
   - Surface the verifier's gap list to the user.
   - Log `VERIFY_FAIL slug={slug}` and `BLOCKED_RETRIES_EXHAUSTED slug={slug}`.
   - Exit. The work item remains claimable so the user can inspect or escalate
     (Phase 0 will not auto-restart a blocked session).

## Logging

Append-only events to `.omh/logs/research-{session_id}.log`. Events are
decisions and phase transitions only — never findings content (matches
the cyclus-interview convention).

Documented event vocabulary:

- `STARTED slug={slug}`
- `PLAN_WRITTEN slug={slug} subtopics=N`
- `BATCH_COMPLETE batch=N subtopics=[...]`
- `GAP_CHECK_COMPLETE gaps=N`
- `REPORT_DRAFT`
- `VERIFY_PASS`
- `VERIFY_FAIL`
- `SYNTHESIS_RETRY attempt=N`
- `BLOCKED_RETRIES_EXHAUSTED slug={slug}`
- `REPORT_CONFIRMED slug={slug}`
- `REPORT_CONFIRMED_RECOVERED slug={slug}`
- `BLOCKED slug={slug}`
- `CANCELLED`

## Sentinel

Downstream skills (cyclus-interview, cyclus-plan, cyclus-autopilot) detect
a completed research session by:

```
.omh/research/{slug}-report.md  with frontmatter `status: confirmed`
```

This file is the durable contract. Queue state is intermediate tracking;
the sentinel file written before `complete()` is the source of truth.

## Pitfalls

- **Never call `web_search` or `web_extract` from the parent.** All web
  tool use happens inside delegated researcher subagents.
- **Load role text via `skill_view` before each delegation; pass in context.**
  Role bodies live in `plugins/omh/references/role-*.md`. Never inline
  role text in the skill body itself.
- **Phase boundaries are commit points.** Each phase MUST call `write_state`,
  call `release()`, and exit cleanly after its outputs. Long-running phases
  that span multiple delegations are not exit-safe.
- **One active research session per project.** Phase 0 enforces this.
  Don't create parallel research states.
- **Slug collisions are user-visible.** The `random4` suffix keeps
  same-topic same-day re-runs from clobbering each other.

## Known Gaps

- **Persistence to wiki / fact_store / memory** is not yet integrated.
  The sentinel report is the only durable interface in v1. (Q2)
- **Per-call subagent tool scoping for research-verifier**
  may be unavailable depending on Hermes install; READ-ONLY contract is
  enforced by prose in `role-research-verifier.md` in that case. (A5)
