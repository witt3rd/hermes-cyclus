# MetricOptimizationKind — Anti-Patterns and Failure Modes

This catalog documents design mistakes and runtime failure classes specific to
`MetricOptimizationKind` loops in Cyclus. These are especially consequential when
running loops unattended or distributed across Saturate workers.

Adapted from Cobus Greyling's [loop-engineering](https://github.com/cobusgreyling/loop-engineering)
catalog for the Cyclus context.

---

## Anti-Patterns (design mistakes)

These are mistakes in loop specification or worker design that allow failures to occur.
Fix them before the loop runs.

### 1. Same worker proposes and verifies

The worker that generated the hypothesis grades its own improvement. Self-scoring
is not a check — it is rationalization in a loop.

**Fix:** Use a separate verifier sub-agent or a different model for the score check.
The verifier must be independent of the proposer.

### 2. No iteration cap

`MetricOptimizationKind` loops with only a `target_score` terminal condition can run
forever if the target is unreachable or the metric never converges.

**Fix:** Always set `max_iterations` in the loop spec. This is a hard safety ceiling,
not a goal.

### 3. No plateau detection

Loops that stall — proposing changes that never improve the metric — waste compute
and block other work from the queue.

**Fix:** Always set `plateau_count`. When N consecutive iterations produce no
measurable improvement, the loop terminates and surfaces the result for human review.

### 4. L3 before baseline established

Auto-committing (`level: L3`) before validating that the eval command, baseline
score, and improvement direction are correct is premature. A miscalibrated eval at
L3 writes bad code to the repo automatically.

**Fix:** Run at `level: L1` (proposal-only, no commits) first. Verify that the
eval command works, the baseline score is sane, and improvements go in the right
direction. Promote to L3 only after L1 confirms the loop is healthy.

### 5. Eval command modifies repo state

Evaluators must be read-only. If the eval script touches files — writing outputs,
updating state, modifying the program it measures — concurrent workers corrupt each
other's baseline and produce incoherent results.

**Fix:** Eval commands must read input, compute a metric, and emit JSON. Nothing
else. Enforce this with code review on any eval script before wiring it into a spec.

### 6. No loop budget

When N Saturate workers run the same loop in parallel, each worker's token and
compute cost multiplies by N. A loop without a budget cap can exhaust resources
across the whole fleet.

**Fix:** Set `budget_tokens` in the loop spec (tracked in
[loop-spec #4](https://github.com/witt3rd/loop-spec/issues/4)). This is especially
critical for distributed execution — unattended loops at scale need a hard cost ceiling.

### 7. Verifier theater

Marking a hypothesis as improved without actually running the eval command. This
happens when a verifier agent reasons about whether the change *should* improve the
metric rather than measuring whether it *did*.

**Fix:** The eval must run. Its output — parsed via the `metric:` field configured
in the loop spec (e.g., `json:combined_score`, `json:coverage_percent`) — is the
only valid measurement. Any verification step that does not invoke the eval command
and parse its output is theater. Treat missing or malformed eval output as a crash,
not a score.

---

## Failure Modes (runtime failures)

These are failures that occur at loop execution time, even when the spec is well-formed.

### Infinite improvement loop

**What happens:** The metric improves on every iteration with no sign of converging.
Usually caused by the eval overfitting to the program changes — the eval measures
something the worker can game indefinitely.

Note: `plateau_count` will *not* trigger here because the score keeps improving.
The hard ceiling is `max_iterations`.

**Mitigation:**
- Always set `max_iterations` as a hard ceiling — it fires regardless of whether
  the score is improving or stalling.
- Use a held-out validation set that the eval also scores but the worker cannot see.
- Flag suspiciously long improvement streaks (e.g., >10 consecutive improvements
  without any near-miss iterations) for human review.
- Periodic human review gates at checkpoints.

### Eval corruption

**What happens:** The eval command fails silently and returns stale or malformed JSON.
The loop records the stale score as a real measurement, contaminating the baseline.

**Mitigation:**
- Validate JSON schema on every eval output before accepting the score.
- Treat a missing or malformed value for the configured `metric:` key (e.g.,
  `combined_score`, `coverage_percent`) as a crash — not a valid measurement.
- Treat empty output or non-zero exit code as a crash.
- Log eval stderr separately so silent failures surface in the audit trail.

### Worker collision

**What happens:** Two workers claim different tasks but apply conflicting diffs to
the same file. Neither worker knows about the other's changes. Whichever commits last
overwrites the first, and the baseline state becomes incoherent.

**Status:** Design decision made (see [#1](https://github.com/witt3rd/hermes-cyclus/issues/1)):
per-worker staging directories with optional git worktrees. Implementation tracked in Arc 2.

**Mitigation until resolved:** Run at `level: L1` (no commits). No file isolation
problem exists at L1 because workers propose but do not write. Promote to L2/L3
only after the isolation strategy is implemented.

### Baseline drift

**What happens:** A winning commit at `level: L3` modifies the canonical
`initial_program.py` (or equivalent baseline file). The *next* worker's baseline is
now a different program than the loop started with. Over many iterations, the program
drifts far from the original starting point.

**Is this a bug?** At `level: L3`, intentional improvement accumulation is the
design goal — each winning commit becomes the new baseline, so the program evolves.
This is correct behavior.

**When it becomes a problem:** If the loop spec assumes a fixed baseline (e.g., for
reproducibility or comparison against a fixed reference), baseline drift violates
that assumption silently.

**Mitigation:**
- Document in the loop spec whether baseline drift is intentional (`accumulating`)
  or disallowed (`fixed`).
- For fixed-baseline loops, run at `level: L1` or `L2` and apply commits manually
  after human review.
- Tag the baseline commit before the loop starts so drift can be measured.

---

## References

- **Cobus Greyling — loop-engineering catalog:**
  <https://github.com/cobusgreyling/loop-engineering>
  The primary reference for anti-patterns and failure modes adapted here.

- **loop-spec (Cyclus loop specification format):**
  <https://github.com/witt3rd/loop-spec>
  Defines `max_iterations`, `plateau_count`, `level`, `metric`, and other spec fields
  referenced in this document.

- **Issue #1 — Worker isolation strategy (decided):**
  <https://github.com/witt3rd/hermes-cyclus/issues/1>
  Tracks the file-isolation design decision referenced in the Worker Collision section.

- **loop-spec #4 — Loop budget (`budget_tokens`):**
  <https://github.com/witt3rd/loop-spec/issues/4>
  Tracks the budget enforcement mechanism referenced in Anti-Pattern #6.
