# Cyclus Principles

These are the load-bearing constraints for Cyclus design and implementation.
Each principle names the failure it prevents. Subagents in any consensus-plan
run must honor all of them unless explicitly contesting one with principled grounds.

These principles descend from `DOCTRINE.md` — read that first. Doctrine says
what Cyclus is *for*; these principles say what matters when *designing the
system* that does it. When a principle and a proposal conflict, the principle
wins unless the principle itself is rectified. When a principle and doctrine
conflict, doctrine wins — that should never happen, and if it does, the
principle is wrong.

---

## P1 — Cyclus uniquely owns the deliberation patterns; not the plumbing

Cyclus's identity is adversarial-consensus planning (cyclus-plan),
fan-out-synthesize-verify research (cyclus-research), Socratic requirements
(cyclus-interview), multi-role triage, and the pitfalls authored from real
runs. The mechanism that executes those patterns belongs to Hermes and Saturate.

**Failure it prevents:** building bespoke infrastructure (state engines,
result-persistence contracts, role-injection hooks) that the platform already
provides or will provide — at permanent maintenance cost.

## P2 — Cyclus major version tracks the Hermes feature line

Cyclus v18 targets Hermes v0.18.x and uses its native primitives. A skill or
plugin behavior that assumes Kanban, background delegation, or the verification
ledger does not work on a prior Hermes. The dependency is real; the version
string makes it legible.

**Failure it prevents:** Cyclus running on a Hermes version that lacks the
primitives it assumes, silently failing or requiring undocumented workarounds.

## P3 — Native primitive over bespoke; bespoke only where the invariant genuinely diverges

Before authoring any plugin code, ask: does Hermes v0.18.0 or Saturate provide
this? If yes, use it. If upstream "almost does" with minor differences, adopt +
configure. Author bespoke only where the invariant requires something the
platform structurally cannot provide.

**Failure it prevents:** the reimplementation reflex — building a parallel
state engine, a parallel result-transport layer, a parallel role-dispatch
system, each carrying permanent maintenance cost that upstream absorbs for free.

## P4 — Role prompts are authored value; injection mechanisms are not

The 15 role prompts (executor, verifier, architect, critic, planner,
researcher, synthesist, skeptic, analyst, triage-maintainer, triage-skeptic,
code-reviewer, security-reviewer, test-engineer, debugger) were refined
through real runs. They are Cyclus's primary intellectual property.

The *mechanism* that injects them (the `[cyclus-role:NAME]` marker passed
in the goal string) is how roles travel. Role prompts are loaded explicitly
via `skill_view(name=..., file_path="references/role-NAME.md")` by the
parent before each `delegate_task` call — never injected by a hook or
catalog loader.

**Failure it prevents:** deleting role prompts as part of bespoke-deletion
(wrong) or keeping bespoke injection machinery (wrong).

## P5 — Every Cyclus skill is a Saturate loop kind; backend is runtime configuration

Every Cyclus skill maps to a Saturate loop kind (`ConsensusKind`,
`TaskExecutionKind`, `InformationSeekingKind`, `ClarificationKind`,
`MetricOptimizationKind`, `SelectionKind`). The kind determines iteration
semantics, turn result types, terminal states, and spec schema. Skills are
written against the four-operation queue interface (`post`, `claim`,
`write_state`, `complete`). The execution backend — Cyclus's own file-based
queue, Kanban if enabled, Saturate if configured — is detected at runtime by
the plugin and is invisible to skill prose.

**Failure it prevents:** writing skill prose against a specific backend's API
such that switching backends requires rewriting skills. The backend is
configuration; the loop kind is identity.

## P6 — Skills encode discipline; plugin code enables it

A SKILL.md carries the orchestration discipline: when to delegate, which
roles to use, how to interpret results, what pitfalls to avoid. Plugin Python
code provides the mechanical substrate: queue interface, evidence running,
hooks. The discipline stays in skills (portable, authorable, testable in
prose); the substrate stays in the plugin (executable, versioned, testable
in Python).

**Failure it prevents:** encoding discipline in plugin code (unmaintainable,
no-edit-without-redeploy) or encoding mechanics in skill prose (fragile,
context-hungry, re-derived each invocation).

## P7 — Bespoke workarounds retire when the upstream gap closes

When a bespoke surface was authored to work around a Hermes limitation, and
v0.18.0 closes that limitation natively, the bespoke surface retires with a
migration. "It still works" is not a reason to keep it — maintenance cost
compounds and the bespoke version will inevitably drift from the native one.

**Failure it prevents:** carrying a parallel implementation of a native
primitive indefinitely because "the migration seems risky" — the risk grows
with time, not shrinks.

## P8 — `ClarificationKind.HUMAN_GATED` is a structural property, not a configuration

`cyclus-interview` maps to `ClarificationKind`. The scheduler structurally
cannot mark a `ClarificationKind` task terminal — there is no
`should_terminate` overload for it. Only an explicit human `complete()` call
ends it. This is not a runtime rule or a prose instruction; it is a type
property that holds across all backends.

**Failure it prevents:** re-architecting `cyclus-interview` onto a durable
queue model with a synthetic done-criterion, violating the fundamental
property that only the human decides when requirements deliberation is
complete.

## P9 — Cyclus's job is `WorkSpec → DesignedWork`; Saturate's job is execution

Cyclus's single responsibility in the arc is the type transformation:
`WorkSpec → DesignedWork`. A `DesignedWork` carries proof-of-deliberation —
the goal is verifiable, the loop kind is declared, terminal states are named,
blast radius is documented. Saturate never needs to know how deliberation
happened; it needs a conforming typed spec. Cyclus never needs to know how
Saturate executes; it needs to produce the spec correctly.

**Failure it prevents:** Cyclus reaching into execution concerns (scheduler
config, fleet topology, backend selection) or Saturate reaching into
deliberation concerns (goal verification, blast radius review). Neither
crosses the line.

---

*Authored 2026-07-06 for the v18 re-grounding (at the time the project was
still named OMH; renamed to Cyclus within the same cycle). Revised same day
after loop taxonomy co-design with Saturate. Rectified 2026-07-11 —
OMH → Cyclus naming, stale skill names (`ralplan`/`deep-research`/
`deep-interview` → `cyclus-plan`/`cyclus-research`/`cyclus-interview`),
`DOCTRINE.md` cross-reference added, stale `docs/v18/` pointers removed
(that design work now lives in this file and `ARCHITECTURE.md`).*
