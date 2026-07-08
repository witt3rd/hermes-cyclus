# hermes-cyclus

## The Problem

You spend your time prompting AI coding agents one turn at a time. Every
session starts cold. Progress only happens when you remember to push. The
agent is a tool you hold, not a system that works.

## The Solution

hermes-cyclus turns iterative work into **loops** — scheduled, autonomous,
accumulating — so the system prompts the agent instead of you.

```bash
# Before: you prompt manually, every time
hermes "improve test coverage"

# After: the loop runs every morning, proposes improvements, updates STATE.md
hermes cron create "0 9 * * 1-5" --skill cyclus-loop --workdir "$PWD" \
  "Run one test-coverage turn. Propose one improvement. Update STATE.md."
```

## Why use this?

- **Work advances while you sleep.** `hermes cron` fires on a schedule.
  Each tick does one unit of work and updates `STATE.md`. You check in
  when you want, not when the agent needs you.

- **Hermes-native, zero extra infrastructure.** Built on skills, cron,
  and `delegate_task` — primitives already in every Hermes installation.
  File-based queue (NFS-safe, no database) works on Azure Files, shared
  mounts, everywhere Hermes runs.

- **Progressive autonomy — earn trust before granting it.** Start at
  `level: L1` (propose only, nothing committed). Graduate to L2 (draft
  PR) when the loop proves reliable. L3 (autonomous commits) only after
  you trust the eval command.

- **Typed loop kinds.** Every skill maps to a loop kind from the Saturate
  taxonomy — `TaskExecutionKind`, `ConsensusKind`, `MetricOptimizationKind`,
  etc. The kind determines what one turn does, what terminal states are
  valid, and whether human confirmation is required.

---

## Getting started

**New here?** Read [`docs/tutorial.md`](docs/tutorial.md) first. It answers:

- What is `hermes cron` for, and why does it matter?
- What is the difference between in-session work and a loop?
- How do L1/L2/L3 maturity levels work in practice?
- How do I run my first loop, step by step?
- What is `STATE.md` and why does the loop need it?

**Building loops that work?** Read [`docs/ldd.md`](docs/ldd.md) — Loop-Driven
Development. Why the discipline matters, the six-step cycle (RECOGNIZE →
SPECIFY → DECOMPOSE → DECLARE → DISPATCH → INTERPRET), and why a timeout
means decompose smaller, never bypass.

---

## Loop kinds

| Skill | Loop kind | What one turn does |
|-------|-----------|------------|
| `cyclus-loop` | `TaskExecutionKind` | Execute one task from a plan, verify, advance |
| `cyclus-autopilot` | `TaskExecutionKind` | Drive a multi-phase project pipeline |
| `cyclus-plan` | `ConsensusKind` | Run one adversarial deliberation round |
| `cyclus-research` | `InformationSeekingKind` | Search, gap-check, advance toward sufficiency |
| `cyclus-interview` | `ClarificationKind` *(HUMAN_GATED)* | Elicit requirements; only human confirms done |
| `cyclus-triage` | `BatchKind` | Fan-out Maintainer + Skeptic passes on an issue backlog |

## Queue backends

Cyclus detects the execution backend at runtime — no code changes when you scale up:

```
File-based  (always available, NFS-safe, zero config)  →  atomic dir ops: pending/ active/ done/
            (if omh_backend = "kanban")                →  Hermes Kanban board (visual surface)
            (if SATURATE_URL is set)                   →  Saturate distributed fleet
```

**Why not SQLite?** SQLite WAL mode corrupts on NFS — the reason Hermes users
on Azure Files or shared mounts disable Kanban. Cyclus Tier 1 uses atomic
`os.rename()` instead: POSIX-guaranteed NFS-safe, zero dependencies.

## Queue interface

Eight operations — seven core plus `dispatch` for the push model:

```
post(mode, instance_id, kind, name, ...)  →  submit a work item
claim(mode, instance_id)                  →  ClaimResult{claimed|not_found|running}
release(mode, instance_id)               →  return to PENDING after clean exit
write_state(mode, instance_id, state)    →  record iteration progress + heartbeat
cancel(mode, instance_id)               →  set cancel_requested sentinel
complete(mode, instance_id, terminal)   →  mark done, attach output
status(mode, instance_id)               →  read-only current state
dispatch(mode, instance_id, ...)        →  post if needed, return worker context (push model)
```

## Installation

```bash
uv add hermes-cyclus
```

Add to your Hermes profile (`config.yaml`):

```yaml
plugins:
  - hermes-cyclus
```

Or symlink for live development:

```bash
ln -s /path/to/cyclus ~/.hermes/profiles/forge/plugins/cyclus
```

## Architecture

See [`ARCHITECTURE.md`](ARCHITECTURE.md) for the full design: the loop taxonomy,
typed FP-style interfaces, the Hermes-native loop patterns (`--context-from`
chaining, `STATE.md` as loop spine), and the forward arc toward distributed
execution via [Saturate](https://github.com/witt3rd/saturate).

---

## Prior art and influences

See [`docs/resources/`](docs/resources/) for annotated copies of the key
references, including Greyling's loop-engineering patterns, Osmani's essay,
and a full transcript of Karpathy's *Skill Issue* talk. The
[`docs/resources/README.md`](docs/resources/README.md) has full citations.

## License

MIT — see [`LICENSE`](LICENSE).
