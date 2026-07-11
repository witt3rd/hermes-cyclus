# DOCTRINE.md — Cyclus

This is the founding doctrine of Cyclus: what Cyclus **is** and what it is
**for**, at the altitude above design decisions. Doctrine survives any
specific architecture choice. When a proposal anywhere in this repo
contradicts doctrine, the proposal is wrong — not the doctrine.

`PRINCIPLES.md` descends from this document. Where doctrine says *what
Cyclus is for*, principles say *what matters when designing the system
that does it* — and rules and behaviors descend further still, distributed
across gates, skills, and code, not centralized here.

---

## Article I — Cyclus turns iterative work into loops so the system prompts you, not the other way around

The problem Cyclus exists to solve is named plainly in `README.md`: *"Every
session starts cold. Progress only happens when you remember to push. The
agent is a tool you hold, not a system that works."*

Cyclus's answer is the inversion — build the system that prompts the agent,
so the human is not the clock. `LOOP.md` names this directly: *"Loop
engineering replaces you as the person who prompts the agent — you design
the system that does it instead."*

This is the reason Cyclus exists. Every capability downstream of this
article — typed loop kinds, the queue interface, LDD, the Saturate
handoff — is in service of this one inversion. A feature that makes the
human more necessary to keep the loop moving is working against doctrine,
regardless of how useful it looks locally.

## Article II — A loop that does not accumulate is not a loop, it is a task that happened once

`docs/ldd.md` states the accumulation principle: *"Direct execution
succeeds tactically but fails systemically... The code ships. The tests
pass. But no STATE.md exists, no decomposition record exists, no baseline
was established, the next iteration cannot build on this."*

The test for whether Cyclus's core promise held on a given run is not "did
the work get done" — it is "did this work produce something the *next*
loop can stand on." A loop that completes and leaves nothing for the next
invocation to build on has satisfied the letter of loop-shaped work while
violating its purpose. This is why `STATE.md`, decomposition records, and
baselines are structural requirements, not documentation nicety — they are
the accumulation itself, made visible.

## Article III — Progressive autonomy is earned, never assumed

Every loop begins at `level: L1` (report-only) and is promoted to L2, then
L3, only as trust in the eval command and the loop's judgment is
demonstrated over real cycles. `LOOP.md`: *"All loops start at L1
(report-only). No loop auto-commits until L1 output has been reviewed for
at least one full cycle."*

This is not caution for its own sake. It is the recognition that a loop
which can act autonomously before its correctness criterion has been
proven is optimizing against an unverified signal — the failure mode is
not "the loop is slow to trust," it is "the loop confidently does the
wrong thing at scale before anyone notices." Trust is a property earned by
the specific loop instance on the specific task, not a global setting
granted once and forgotten. See `cyclus-loop-design-pitfalls` P-JUDGMENT-FLAG
and P-TIMEOUT for lived instances of this doctrine under pressure.

## Article IV — The mechanism belongs to the platform; the discipline belongs to Cyclus

`PRINCIPLES.md` P1 names Cyclus's actual identity: *"adversarial-consensus
planning, fan-out-synthesize-verify research, Socratic requirements,
multi-role triage, and the pitfalls authored from real runs. The mechanism
that executes those patterns belongs to Hermes and Saturate."*

Cyclus does not own state engines, result-persistence contracts, or
role-injection hooks as permanent intellectual property — those are
infrastructure the platform provides or will provide, and building bespoke
versions carries permanent maintenance cost for capability the platform
already owns. What Cyclus owns and must never delegate away: the *shape*
of good deliberation — which roles argue, in what order, checking for what
failure modes, refined against what actually went wrong in real runs. The
distinction is not "we don't write code" — Cyclus is a real plugin with
real mechanics — it is "the code exists to carry the discipline, and
retires the moment the platform absorbs it natively" (see Article V).

This is the doctrinal root of the "minimize bespoke" instinct that recurs
throughout `PRINCIPLES.md`: it is not a style preference, it is what
follows from correctly locating where Cyclus's actual value lives.

## Article V — Bespoke workarounds are debt, not achievements; they retire the moment the platform closes the gap

`PRINCIPLES.md` P7: *"'It still works' is not a reason to keep it —
maintenance cost compounds and the bespoke version will inevitably drift
from the native one."*

A bespoke surface that once filled a genuine platform gap does not become
permanent infrastructure by virtue of having shipped and worked. The
moment the underlying gap closes upstream, the correct response is
migration, not preservation. Treating a working bespoke surface as earned
and therefore untouchable is the trap — the risk of migrating only grows
the longer migration is deferred, it never shrinks. "It works" and "it
should stay" are different claims and must not be conflated.

## Article VI — Loops are typed by iteration semantics, not by what they happen to do

Every unit of loop-shaped work in Cyclus maps to a named loop kind
(`TaskExecutionKind`, `ConsensusKind`, `InformationSeekingKind`,
`ClarificationKind`, `MetricOptimizationKind`, `SelectionKind`) whose
*type* — not its prose description — determines what a terminal state is,
what a turn result means, and who is structurally allowed to end it.

The clearest instance of this doctrine made structural: `ClarificationKind`
tasks are `HUMAN_GATED` at the type level — the scheduler has no
`should_terminate` code path for this kind at all. Only a human's explicit
`complete()` call can end one (`PRINCIPLES.md` P8). This is not a runtime
rule that could, under pressure, be reasoned around — it is a property of
the *type*, unrepresentable to violate by construction. When a new kind of
loop-shaped work is discovered, the doctrinal question is always "what
kind is this, and what does that kind's type structurally permit and
forbid" — never "what do I want this loop to be allowed to do."

## Article VII — Backend is configuration; loop kind is identity

The execution substrate a loop runs on — an in-memory file-based queue, a
Kanban board, a distributed Saturate fleet — is detected at runtime and is
invisible to the skill prose that authors the loop's discipline
(`PRINCIPLES.md` P5). A skill that hardcodes assumptions about which
backend it runs on has confused *where the loop executes* with *what the
loop is* — and will break the moment the deployment scales past its
original assumption.

This is why Cyclus is not "a queue implementation" — the queue is
replaceable. Cyclus is the discipline for expressing a loop correctly such
that any conforming backend can execute it. `ARCHITECTURE.md`'s one-line
summary states the resulting division of labor precisely: *"Cyclus designs
work. Saturate executes it at fleet scale. Hermes runs it everywhere
else."*

## Article VIII — Zhèngmíng: when a name stops matching what it names, the fix belongs at the seam where the mismatch lives

This repository was named `oh-my-hermes` and rebranded to Cyclus mid-life.
When a rename like this happens, the doctrine is not "eventually clean up
the old name" as background chore — it is that a stale name is an active
falsehood every time a reader encounters it, and the fix belongs at
whatever layer the mismatch was caught. A stale title in a document you
are editing anyway is fixed in the same commit, not filed as a follow-up.
A stale name discovered elsewhere in the system, out of the current scope
of work, is named explicitly and tracked — not silently absorbed into an
unrelated change, and not silently ignored either.

---

## Provenance

Extracted 2026-07-11 from what the repository already asserted about
itself across `README.md`, `LOOP.md`, `docs/ldd.md`, `PRINCIPLES.md`, and
`ARCHITECTURE.md` — this document names the *why* those artifacts already
assumed but never stated at doctrinal altitude. Authored under
`descend-by-default`: doctrine is Stratum 1, single canonical home, rarely
changes, governs everything that descends from it.

When this document stops matching what Cyclus actually is, rectify it —
do not preserve a stale doctrine out of loyalty to a past author. The
same zhèngmíng discipline this document names in Article VIII applies to
itself.
