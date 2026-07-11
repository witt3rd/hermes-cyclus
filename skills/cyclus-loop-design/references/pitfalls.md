# cyclus-loop-design — Earned Pitfalls

These are lived failures from real `cyclus-loop-design` runs — each one cost
real time or real trust before the rule was named. Read this alongside the
main `SKILL.md` "Pitfalls" section, which covers the Planner/Architect/Critic
mechanics; this file covers failures that surfaced downstream of a design
that looked correct on paper.

---

## P-MOCK: Mocked e2e tests give false confidence (2026-07-09)

**What happened:** A live-e2e loop designed to prove Saturate integration used
`subprocess.run` mocks for the actual hermes invocations and declared "done."
Seven real integration bugs remained unfound behind the mock — phantom env var
names, a file-name mismatch, an import that didn't exist, missing context
injection, and environment leakage across a nested dispatch. The member had
to push back twice before the loop actually ran with real hermes calls.

**Rule:** When the goal is "make X work end-to-end," acceptance criteria must
include at least one real invocation — no mocking of the system under test.
Mocked tests prove structural wiring; only real invocations prove integration.
Cap real invocations at `max_iterations: 1` for speed, but don't skip them.
The Architect's job includes catching a plan whose only verification path
is mocked.

---

## P-GOAL: "Iterate until working" terminal condition must be in the task body (2026-07-09)

**What happened:** A loop completed all its decomposed tasks (good structural
work) but stopped short of the stated goal ("run until all examples work").
The worker declared done when the tasks were done, not when the goal was
achieved.

**Rule:** When the goal includes a terminal condition ("keep going until X
works"), that condition must appear verbatim in the dispatched task body —
not just in the plan's header. The task body is what the worker reads at
wake. Tasks completing ≠ goal achieved. The Planner must copy the terminal
condition into every task that could plausibly be the last one.

---

## P-BRANCH: Autonomous fix loops need direct-commit branches upfront (2026-07-09)

**What happened:** A loop designed to autonomously find and fix bugs across
multiple iterations was blocked mid-run by PR approval requirements on the
default branch — something that should have been anticipated at design time,
not discovered mid-dispatch.

**Rule:** When designing a loop that will find and fix bugs across multiple
iterations, set up a feature branch with direct-commit access *before*
dispatching. This is a Phase 0 action (see SKILL.md "Phase 0: Gather
context") — the Planner should name the branch strategy explicitly in its
output, not leave it implicit.

---

## P-COMPLETION: Kanban/queue tasks with no delivery mechanism leave the operator polling (2026-07-09)

**What happened:** A Kanban goal-mode task completed cleanly into the
database with zero notification back to the operator, who had to ask "is it
running?" multiple times because there was no signal a loop had finished.

**Workaround (immediate):** Add a `send_message` (or equivalent notification)
call to the task body as the last step before the completion call.

**Proper fix:** This is the same escalation/delivery-channel gap named in the
outer-loop design work — file it as an issue against the execution backend
(Kanban, Saturate) rather than routing around it silently every time.

---

## P-TIMEOUT: A subagent timing out with zero real artifacts means take it directly, not wait longer (2026-07-10)

**What happened:** The final task of a multi-task loop was delegated to a
subagent. It timed out (600s) with dozens of API calls but zero diff, zero
new state — a clean timeout with no partial progress to build on. This is
distinct from an earlier partial timeout in the same loop that at least left
usable state behind.

**Diagnostic before deciding what to do:** confirm the subagent left
*nothing* (check for uncommitted diffs, new rows, new files at the expected
paths) before deciding to redo the work directly rather than re-dispatching.
A timeout with real partial progress should usually be re-dispatched with
narrower scope; a timeout with zero artifacts is cheaper to redo directly
than to diagnose why the subagent stalled.

**Rule:** when a subagent times out on the final/closing task of a loop,
check for real artifacts first. Zero artifacts → take the task directly
rather than re-dispatching blind. Some artifacts → narrow the scope and
re-dispatch; don't discard the partial progress.

---

## P-JUDGMENT-FLAG: A closing task that discovers unresolved upstream governance questions must flag them explicitly, not silently resolve them (2026-07-10)

**What happened:** During the final closure task of a loop, a downstream
artifact (a spec file authored by an earlier task) diverged from what the
design-consensus round (Planner/Architect/Critic/DRI) had ratified — the
artifact said `level: L1`, the ratified decision said `level: L2`. The
closing task had to decide whether to "fix" the artifact to match the
ratified decision, leave it as-is, or ask.

**Rule:** a closing/verification task's job is to verify and report, not to
silently resolve open governance forks it discovers along the way. When a
loop closure surfaces a divergence between what was designed and what was
built: ask the human if there's time; if not, make the conservative,
reversible call and **name it as a judgment call, distinctly, in the closing
report** — not folded silently into "everything passed."
