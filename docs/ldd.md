# Loop-Driven Development (LDD)

LDD is the discipline that makes loop engineering produce good outcomes rather
than just loop-shaped activity. It is to loop engineering what TDD is to
software development — not a tool, a *discipline*. The order matters. The
gates are structural, not advisory.

> **The LDD invariant:** A timeout is not a reason to bypass the loop. It is
> a signal that your decomposition needs work. The correct response is always
> to decompose smaller, never to execute directly.

---

## The analogy to TDD

| TDD | LDD |
|-----|-----|
| Write the failing test first | Declare the loop kind and spec first |
| Red before green, full stop | SPECIFY before DISPATCH, full stop |
| Failing test → fix the implementation | Timeout → fix the decomposition |
| Skip the test → technical debt | Bypass the loop → no accumulation |
| `pytest` refuses if no tests | Planning gate refuses if spec is malformed |

The critical insight: **direct execution that bypasses the loop produces work
that does not accumulate.** Even when it succeeds, it leaves no STATE.md, no
decomposition record, no baseline, no lessons-learned for the next iteration.
The work is done but the loop cannot build on it. You are always starting over.

---

## The six-step LDD cycle

### 1. RECOGNIZE

*Is this loop-shaped work? Which loop kind?*

Not all work is loop-shaped. The test: can you define a terminal condition
that is verifiable without human judgment? If yes, it's loop-shaped.

| If the work is... | Loop kind | Terminal condition |
|---|---|---|
| A plan to execute with verification | `TaskExecutionKind` | All tasks pass |
| A design decision needing adversarial deliberation | `ConsensusKind` | All roles approve |
| Research that needs to reach sufficiency | `InformationSeekingKind` | Gap check passes |
| A metric to optimize | `MetricOptimizationKind` | Score exceeds target |
| Requirements that need human confirmation | `ClarificationKind` | Human says done |
| Active pairing session, trivially small | *not loop-shaped* | Direct is correct |

If it doesn't fit a loop kind, do it directly and say so explicitly. The
declaration is the discipline — not the loop.

### 2. SPECIFY

*What does done look like? What is the metric? What are the terminal
conditions?*

Write the `spec.yaml` before touching the work. The spec must declare:

```yaml
kind: TaskExecutionKind          # or MetricOptimizationKind, etc.
name: queue-rewrite
level: L1                        # L1 | L2 | L3
metric: all_tasks_pass           # or combined_score, coverage_percent, etc.
terminal:
  target_score: 1.0
  max_iterations: 50
  plateau_count: 5
```

The spec is machine-validated by the planning gate. A malformed spec — missing
`kind`, missing `level`, missing terminal conditions — cannot be dispatched.
This is the structural enforcement. Not a guideline. Not a warning. A gate.

### 3. DECOMPOSE

*What are the tasks? Does each fit in one delegation budget (~600s)?*

This is the step most often skipped — and the one that causes timeouts.

**The decomposition test:** Can you describe each task's acceptance criteria in
< 200 words, in a way that a subagent with no prior context can implement and
verify in under 10 minutes? If not, split the task.

**The queue rewrite failure:** "Replace queue.py SQLite with file-based ops"
was one task in the spec but contained: understand existing interface → design
new implementation → write 400 lines → run tests → fix failures → commit. That
is 5 tasks. The timeout was not a dispatcher failure — it was a decomposition
failure. The discipline response: decompose to 5 tasks and re-dispatch. Not:
implement directly and rationalize it as "cleaner."

Budget-sized tasks:
- Can be stated as a single acceptance criterion
- Touch at most 2-3 files
- Have no ambiguous dependencies on undone work
- Complete in a single subagent invocation

### 4. DECLARE

*Write the mode to STATE.md before touching the work.*

```markdown
## Current mode (declared 2026-07-07 07:05)

Mode: loop-work
Loop kind: TaskExecutionKind
Instance: queue-rewrite
Reason: Implementing issue #5 — 5 decomposed tasks, each budget-sized
```

The declaration is the accountability surface. If you execute directly without
a declaration, the absence is visible. If you declare `loop-work` and then
bypass the loop, the contradiction is visible.

**Legitimate bypass modes** (declare explicitly):

- `active-pairing` — you and the member are both present; direct execution is
  correct *for this session*; the work still gets committed with attribution
- `too-small` — single-line fix, trivially obvious, no decomposition needed;
  name the size criterion explicitly

**Not a legitimate bypass mode:**
- `loop-failed` — the loop timed out or the subagent failed; the correct
  response is DECOMPOSE SMALLER, not bypass

### 5. DISPATCH

*Run the loop. One task per invocation. Claim, execute, verify, write_state,
release, exit.*

This is what `cyclus-ralph` does. The discipline here is the iron law: one
task per invocation. The orchestrator stays at altitude — picking batches,
encoding learnings, gathering evidence, dispatching verifiers. It does not
drop into the work.

**If a subagent times out:**
1. Read the timeout as a decomposition failure signal
2. Split the timed-out task into 2-3 smaller tasks
3. Update the spec and plan
4. Re-dispatch the smaller tasks
5. Never: implement the timed-out work directly

### 6. INTERPRET

*What does the loop's output mean? What is the next move?*

| Outcome | Signal | Response |
|---------|--------|----------|
| Task passes | Decomposition was right | Advance to next task |
| Task fails (verifier) | Implementation was wrong | Retry with feedback |
| Task times out | Task was too large | Decompose smaller |
| 3 strikes | Fundamental problem | Surface to human |
| Plateau (N consecutive rejections) | Strategy needs to change | Shift exploration |
| Score improves | Loop is working | Continue |
| Score regresses | Wrong direction | Revert, try different approach |

---

## The accumulation principle

This is the deeper reason LDD matters beyond any individual task.

**Direct execution succeeds tactically but fails systemically.** When you
implement queue.py directly in a pairing session:
- The code ships ✅
- The tests pass ✅
- No STATE.md exists ❌
- No decomposition record exists ❌
- No baseline was established ❌
- The next iteration cannot build on this ❌

The loop exists to produce *accumulation*, not just completion. A loop that
runs produces: a STATE.md with lessons learned, a decomposition record that
can be reused, a baseline for the next metric comparison, a trail of what was
tried and discarded. This accumulation is what makes the system smarter over
time rather than just faster at one-off tasks.

**The test:** Did this work produce something the *next loop* can stand on?
If yes, the discipline was followed. If no, the discipline was violated —
regardless of whether the immediate task succeeded.

---

## The meta-loop

`cyclus-loop-design` is the skill that produces well-formed loop specs. It is
itself a `ConsensusKind` loop:

- **Planner** proposes the loop kind, spec fields, decomposed tasks
- **Architect** stress-tests the decomposition — are tasks budget-sized? are
  terminal conditions verifiable? is the metric meaningful?
- **Critic** checks for anti-patterns — L3 before L1 established, no plateau
  detection, eval command that modifies repo state

The Planner/Architect/Critic cycle runs until all three approve the spec. The
output is a validated `spec.yaml` that the planning gate will accept. You
cannot bypass this cycle by writing a spec directly — the gate enforces it.

This is the recursion: **the tool that enforces loop discipline is itself a
loop.** LDD all the way down.

---

## LDD vs direct execution: when each is right

| Situation | Mode | Why |
|-----------|------|-----|
| Pairing session, both present, trivial change | Direct | Speed + presence; attribution still happens |
| Pairing session, large work | Loop | Accumulation matters even with both present |
| Unattended work | Loop | Always |
| Loop times out | Decompose + loop | The timeout is the signal |
| Subagent fails 3 times | Surface to human | Fundamental problem, not a tool problem |
| Spec is malformed | Fix the spec | Never bypass the gate |

---

## Anti-patterns

These are the failure modes that look like progress but aren't:

1. **Bypass-after-timeout** — loop fails, implement directly, rationalize as
   "cleaner." The work succeeds. The accumulation doesn't happen.

2. **Spec-as-afterthought** — dispatch the loop, then write the spec to match
   what was dispatched. The gate is theater.

3. **L3-before-L1** — auto-commit before the eval command has been verified to
   produce meaningful output. The loop optimizes the wrong thing.

4. **Undeclared mode** — work directly without declaring `active-pairing` or
   `too-small`. The bypass is invisible.

5. **Task-too-large** — dispatch a task that requires reading 500 lines,
   designing a solution, writing 400 lines, running tests, and fixing failures.
   The timeout is guaranteed. The response is decomposition, not a larger
   timeout budget.

---

## The planning gate (structural enforcement)

Every `cyclus-ralph` invocation checks:

1. Does `spec.yaml` exist and parse as valid YAML?
2. Do all required fields for this loop kind pass Pydantic validation?
3. Are all tasks in the plan budget-sized (< 200 word description)?
4. Is `level` declared?

If any check fails, `cyclus-ralph` halts with a specific error naming what is
missing. It does not proceed with a warning. It does not suggest the work be
done directly. It names the fix and stops.

This is the structural expression of LDD: the discipline is not optional, and
the system will not pretend otherwise.

---

*"A timeout is not permission to bypass. It is a signal to decompose."*

⚒️
