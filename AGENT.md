# AGENT.md — hermes-cyclus contributor guidance

## What this repo is

hermes-cyclus is a [Hermes Agent](https://github.com/NousResearch/hermes-agent) plugin
that provides loop engineering primitives — typed deliberation skills mapped to the
[Saturate](https://github.com/witt3rd/saturate) loop taxonomy.

The plugin name is `cyclus`. Tool prefix is `cyclus_`. Skill prefix is `cyclus-`.

## Repository layout

```
DOCTRINE.md           founding doctrine — what Cyclus is and is for
ARCHITECTURE.md       loop taxonomy, queue interface, Saturate handoff contract
PRINCIPLES.md         load-bearing design constraints for contributors
README.md             user-facing overview
LICENSE               MIT
cyclus/       the plugin
  __init__.py         Hermes entry point — register()
  queue.py            six-operation SQLite queue (the always-available backend)
  cyclus_config.py    config helpers
  tools/
    queue_tool.py     cyclus_queue Hermes tool handler
    evidence_tool.py  cyclus_evidence Hermes tool handler
  references/         15 role prompts (role-executor.md, role-planner.md, ...)
  skills/             deliberation skill SKILL.md files (cyclus-ralph, cyclus-ralplan, ...)
  tests/              pytest suite (uv run pytest cyclus/tests/)
  templates/          .cyclus/ directory scaffolding
```

## Development

```bash
uv sync
uv run pytest cyclus/tests/ -q   # must pass before any commit
```

## Doctrine and Principles

Read `DOCTRINE.md` before `PRINCIPLES.md`. Doctrine names what Cyclus is and
is for — it is stable and rarely changes. Principles descend from doctrine
and name what matters when designing the system; the nine principles are
non-negotiable constraints — every PR is evaluated against them. If a
proposal conflicts with a principle, the principle wins unless rectified.
If a principle conflicts with doctrine, doctrine wins — that should never
happen, and if it does, the principle is what needs fixing.

## Queue interface

Skills write against the six-operation `cyclus_queue` tool — not against any backend's
native API. The backend (SQLite / Kanban / Saturate) is runtime configuration. Do not
add Kanban-specific calls (`kanban_show`, `kanban_complete`) to skill prose.

## Loop kinds

Every skill maps to a Saturate loop kind. New skills must declare their kind in the
SKILL.md header. See `ARCHITECTURE.md` for the full taxonomy.

## Commit style

Conventional commits. `feat`, `fix`, `docs`, `test`, `chore`.
No direct commits to `main` — branch + PR.

## License

MIT. See `LICENSE`.
