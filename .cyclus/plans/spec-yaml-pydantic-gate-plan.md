# Ralph Plan: spec-yaml-pydantic-gate

> Consensus reached: Round 1 (Planner APPROVE, Critic APPROVE, Architect REQUEST_CHANGES → revisions applied)
> Loop design via: cyclus-loop-design (ConsensusKind meta-loop)

## Goal

Implement issue #7: migrate loop specs from spec.md (markdown + YAML frontmatter) to
spec.yaml (pure YAML), define Pydantic validation models, wire planning gate into
cyclus-ralph Step 2.

## Tasks

---

### Task 1 — Define Pydantic models + load_spec() in cyclus/specs.py

**Files owned:** `pyproject.toml`, `cyclus/specs.py`

**Description:**
Add `pydantic>=2.0` to pyproject.toml dependencies. Run `uv sync`. Create
`cyclus/specs.py` with these models and exact required fields:

- `TerminalConditions(BaseModel)`: max_iterations: int=100, plateau_count: int=10,
  target_score: float|None=None
- `LoopSpec(BaseModel)`: kind: str, name: str, level: Literal['L1','L2','L3']='L1',
  terminal: TerminalConditions=TerminalConditions()
- `MetricOptimizationSpec(LoopSpec)`: metric: str, direction: Literal['higher_is_better',
  'lower_is_better'], baseline: float|None=None, evaluate: str|None=None,
  target_files: list[str]=[]
- `TaskExecutionSpec(LoopSpec)`: target_files: list[str]=[]
- `ConsensusSpec(LoopSpec)`: stub (no extra fields)
- `InformationSeekingSpec(LoopSpec)`: stub
- `ClarificationSpec(LoopSpec)`: HUMAN_GATED: ClassVar[bool] = True

Add `load_spec(path: str | Path) -> LoopSpec` that:
- Reads YAML file at path (raises FileNotFoundError if absent)
- Dispatches to correct subclass by `kind` field
- Raises `pydantic.ValidationError` on invalid fields
- Raises `ValueError` for unknown kind string

**Acceptance criteria:**
- `PYTHONPATH=. uv run python -c "from cyclus.specs import load_spec; print('ok')"` exits 0
- `PYTHONPATH=. uv run pytest tests/ -q` — all 86+ existing tests still pass
- `load_spec` with `kind: BogusKind` raises `ValueError`

**Dependencies:** none
**Estimated budget:** < 400s

---

### Task 2 — Write tests/test_spec_validation.py

**Files owned:** `tests/test_spec_validation.py`

**Description:**
Create pytest file covering `cyclus/specs.py`. Use `tmp_path` fixture for file-based
tests. No network, no external deps beyond pydantic + pyyaml. Test cases:
1. Valid MetricOptimizationSpec via `load_spec()` on temp YAML file — returns correct type
2. Valid TaskExecutionSpec via `load_spec()` — returns correct type
3. Missing `kind` field → `pydantic.ValidationError`
4. Missing `terminal` (or max_iterations under terminal) — still valid (defaults apply)
5. Unknown kind string → `ValueError`
6. `load_spec` on nonexistent path → `FileNotFoundError`
7. `load_spec` on malformed YAML (e.g. `{bad: [yaml`) → exception (not silent)
8. `ClarificationSpec.HUMAN_GATED is True`

**Acceptance criteria:**
- `PYTHONPATH=. uv run pytest tests/test_spec_validation.py -v` — all green, zero skips
- `PYTHONPATH=. uv run pytest tests/ -q` — full suite still passes (no regressions)

**Dependencies:** Task 1
**Estimated budget:** < 350s

---

### Task 3a — Migrate examples/function_minimization: spec.md → spec.yaml + README.md

**Files owned:** `examples/function_minimization/spec.yaml` (create),
`examples/function_minimization/README.md` (create),
`examples/function_minimization/spec.md` (delete)

**Description:**
1. Read `examples/function_minimization/spec.md`
2. Extract frontmatter fields → spec.yaml (pure YAML, no `---` delimiters)
3. Promote from prose:
   - `evaluate:` = the bash code block under `## Evaluate` heading — verbatim as
     YAML literal block string (pipe `|`)
   - `target_files:` = bulleted list under `Workers may ONLY modify:` — as YAML sequence
4. Write all prose (everything after frontmatter) → `README.md` with `# Function Minimization` as H1
5. Delete `spec.md`
6. Validate: `PYTHONPATH=. uv run python -c "from cyclus.specs import load_spec; s=load_spec('examples/function_minimization/spec.yaml'); print(s.name)"` exits 0

Baseline for function_minimization is `1.42` (measured). target_score is `1.3`.

**Acceptance criteria:**
- `examples/function_minimization/spec.md` does not exist
- `examples/function_minimization/spec.yaml` exists and is valid YAML
- `load_spec('examples/function_minimization/spec.yaml')` returns without error
- `PYTHONPATH=. uv run pytest tests/ -q` still passes

**Dependencies:** Task 1, Task 2
**Estimated budget:** < 300s

---

### Task 3b — Migrate examples/circle_packing: spec.md → spec.yaml + README.md

**Files owned:** `examples/circle_packing/spec.yaml` (create),
`examples/circle_packing/README.md` (create),
`examples/circle_packing/spec.md` (delete)

**Description:**
Same procedure as Task 3a, applied to circle_packing.
- `evaluate:` = bash code block under `## Evaluate` — verbatim as YAML literal block string
- `target_files:` = files listed under `Workers may ONLY modify:`
- Baseline is `0.0`; target_score is `1.0` (matching AlphaEvolve)
- Validate via `load_spec('examples/circle_packing/spec.yaml')`

**Acceptance criteria:**
- `examples/circle_packing/spec.md` does not exist
- `examples/circle_packing/spec.yaml` exists and loads cleanly
- `PYTHONPATH=. uv run pytest tests/ -q` still passes

**Dependencies:** Task 1, Task 2
**Estimated budget:** < 300s

---

### Task 3c — Migrate examples/test_coverage: spec.md → spec.yaml + README.md

**Files owned:** `examples/test_coverage/spec.yaml` (create),
`examples/test_coverage/README.md` (create),
`examples/test_coverage/spec.md` (delete)

**Description:**
Same procedure as Task 3a, applied to test_coverage.
- metric: `coverage_percent`, direction: `higher_is_better`, baseline: `77.93`
- `evaluate:` = the uv+pytest+coverage command from `## Evaluate` section
- No `target_files:` (workers add to `tests/` — not listed as fixed paths)
- Validate via `load_spec('examples/test_coverage/spec.yaml')`

**Acceptance criteria:**
- `examples/test_coverage/spec.md` does not exist
- `examples/test_coverage/spec.yaml` exists and loads cleanly
- `PYTHONPATH=. uv run pytest tests/ -q` still passes

**Dependencies:** Task 1, Task 2
**Estimated budget:** < 300s

---

### Task 4 — Wire load_spec() planning gate into cyclus-ralph Step 2

**Files owned:** `skills/cyclus-ralph/SKILL.md`

**Description:**
Update Step 2 to add a spec validation gate as the *first check* before any plan
parsing. Insert subsection "Step 2 (pre-check): Validate spec.yaml" with:

```
If a `spec.yaml` exists at `.cyclus/plans/{slug}-spec.yaml` or project root:
  1. Run load_spec() on it: python -c "from cyclus.specs import load_spec; load_spec('{path}')"
  2. If it raises (ValidationError or ValueError): halt immediately.
     Report the exact error. Do NOT proceed.
  3. If it exits 0 or no spec.yaml exists: continue to plan source checks.
```

The gate is conditional — ralph works without a spec.yaml. Existing plan-source
checks (`.omh/plans/ralplan-*.md`, `.omh/plans/ralph-plan.md`) remain intact below it.

Add to Pitfalls:
> **Spec gate fires before plan parsing.** If spec.yaml is present and load_spec()
> raises, stop. A malformed spec will corrupt every subsequent iteration.

**Acceptance criteria (grep-verifiable):**
- `grep -c 'load_spec' skills/cyclus-ralph/SKILL.md` → ≥ 1
- `grep -c 'spec.yaml' skills/cyclus-ralph/SKILL.md` → ≥ 1
- `grep -c 'ralplan-\*.md' skills/cyclus-ralph/SKILL.md` → ≥ 1 (existing logic intact)
- File is valid Markdown; YAML frontmatter unchanged

**Dependencies:** Task 1, Task 2
**Estimated budget:** < 200s

---

## Consensus record

| Round | Planner | Architect | Critic |
|-------|---------|-----------|--------|
| 1 | APPROVE | REQUEST_CHANGES (A1,A2,A3,A4,A5,A6,A7) | APPROVE (C3,C5,C8 notes) |
| Distilled | — | Applied: A1 (fields enumerated), A2+A3+A4 (Task 3 split to 3a/3b/3c), A5 (grep criteria), A6 (Task 4 deps = 1+2 only), A7 (plateau_count removed from spec) | C8: STATE.md declaration needed before dispatch |

## State.md declaration (required before dispatch — C8)

Before dispatching Task 1, update STATE.md:
```
## Current mode (declared 2026-07-07)
Mode: loop-work
Loop kind: TaskExecutionKind
Instance: spec-yaml-pydantic-gate
Issue: https://github.com/witt3rd/hermes-cyclus/issues/7
```
