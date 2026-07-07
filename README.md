# hermes-cyclus

**Loop engineering primitives for [Hermes Agent](https://github.com/NousResearch/hermes-agent).**

Every skill in hermes-cyclus is a loop — a unit of autonomous, iterative work
that runs until a declared terminal condition is met. Cyclus maps each skill to a
typed loop kind from the [Saturate](https://github.com/witt3rd/saturate) taxonomy,
writes skill prose against a backend-agnostic four-operation queue interface, and
provides the deliberation patterns that produce well-specified loops worth running.

## Loop kinds

| Skill | Loop kind | What one turn does |
|-------|-----------|--------------------|
| `cyclus-ralph` | `TaskExecutionKind` | Execute one task from a plan, verify, advance |
| `cyclus-autopilot` | `TaskExecutionKind` | Drive a multi-phase project pipeline |
| `cyclus-ralplan` | `ConsensusKind` | Run one adversarial deliberation round |
| `cyclus-deep-research` | `InformationSeekingKind` | Search, gap-check, advance toward sufficiency |
| `cyclus-deep-interview` | `ClarificationKind` *(HUMAN_GATED)* | Elicit requirements; only human confirms done |
| `cyclus-triage` | `BatchKind` | Fan-out Maintainer + Skeptic passes on an issue backlog |

## Queue backends

Cyclus detects the execution backend at runtime — no code changes when you scale up:

```
cyclus_queue   (always available, zero config)   →  embedded SQLite
               (if omh_backend = "kanban")        →  Hermes Kanban board
               (if SATURATE_URL is set)           →  Saturate distributed fleet
```

## Queue interface

Six operations, identical to Saturate's four-operation contract plus `release` and `cancel`
for multi-invocation loop orchestration:

```
post(mode, instance_id, kind, name, ...)  →  submit a work item
claim(mode, instance_id)                  →  ClaimResult{claimed|not_found|running}
release(mode, instance_id)               →  return to PENDING after clean exit
write_state(mode, instance_id, state)    →  record iteration progress + heartbeat
cancel(mode, instance_id)               →  set cancel_requested sentinel
complete(mode, instance_id, terminal)   →  mark done, attach output
status(mode, instance_id)               →  read-only current state (no heartbeat update)
```

## Installation

```bash
uv add hermes-cyclus
```

Add to your Hermes profile:

```yaml
plugins:
  - hermes-cyclus
```

## Architecture

See [`ARCHITECTURE.md`](ARCHITECTURE.md) for the full design: the loop taxonomy,
typed FP-style interfaces, the OMH→Saturate handoff contract, and the forward arc
toward distributed loop execution.

## Prior art and influences

**[Loop Engineering](https://cobusgreyling.substack.com/p/loop-engineering)** — Cobus Greyling.
The canonical reference implementation: 7 named patterns, starters for 8 tools
(including Hermes), an npm toolchain (`loop-init`, `loop-audit`, `loop-cost`,
`loop-worktree`), anti-patterns catalog, failure modes catalog, and multi-loop
coordination docs. Hermes is a first-class citizen in their primitives matrix.
The L1/L2/L3 maturity model, loop budget concept, and kill switch pattern all
trace here. Repository: [`cobusgreyling/loop-engineering`](https://github.com/cobusgreyling/loop-engineering).

**[Loop Engineering (essay)](https://addyosmani.com/blog/loop-engineering/)** — Addy Osmani
(Director of Engineering, Google DeepMind). Independent convergence on the same
five-primitive architecture Cyclus implements. His framing —
*"build it like someone who intends to stay the engineer, not just the person who
presses go"* — is a load-bearing design principle. Full annotated copy in
[`docs/AddyOsmani_com_-_Loop_Engineering.md`](docs/AddyOsmani_com_-_Loop_Engineering.md).

**[Autoloop](https://github.com/githubnext/autoloop)** — GitHub Next. The example
programs in [`examples/`](examples/) are adapted from Autoloop's use cases
(function minimization, circle packing, autoresearch). Autoloop runs sequentially
on GitHub Agentic Workflows; Cyclus + Saturate makes the population concurrent.

**[Karpathy's autoresearch](https://github.com/karpathy/autoresearch)** — the
`MetricOptimizationKind` loop kind (run until a metric improves) traces directly
to Karpathy's formulation. The `examples/autoresearch/` program is based on it.

## License

MIT — see [`LICENSE`](LICENSE).
