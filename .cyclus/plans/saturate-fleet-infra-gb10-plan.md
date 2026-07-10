# PLAN — saturate-fleet-infra-gb10

Build full Saturate distributed infrastructure (Postgres queue + Nomad cluster,
single client node gb10) so Goal 1 (MiniCPM-o 4.5 finetuning autoresearch loop)
can run unattended. Designed via cyclus-loop-design, 3 rounds, DRI-approved
2026-07-10.

Repos: `~/src/witt3rd/saturate/`, `~/src/witt3rd/continuum/`, this repo.
Hosts: roger (100.65.5.5, Postgres+Nomad server), gb10 (100.71.24.76, Nomad
client, aarch64 — fetch ARM64 Nomad binary).

---

## Task 0 — Declare loop-work mode in STATE.md

Description: Establish the LDD DECLARE gate before any task dispatch —
records mode and instance identity so the loop is auditable from tick zero.

Files owned: `STATE.md`

Acceptance criteria: `grep -q "Mode: loop-work" STATE.md && grep -q "Instance: saturate-fleet-infra-gb10" STATE.md`

Dependencies: none
Estimated budget: 30s

---

## Task 1a — Postgres local bring-up + schema

Description: Bring up the local Postgres substrate for the fleet queue via
docker-compose on roger and apply the schema. Postgres-only concern; two
independently-failing checks so a failure names the specific broken step.

Write `infra/postgres/docker-compose.yaml` (postgres:16, named volume
`saturate_pg_data`, port 5432 bound to `0.0.0.0`, env `POSTGRES_USER=saturate
POSTGRES_DB=saturate`). Write `infra/postgres/schema.sql`: a `tasks` table
(task_id PK, name, kind, spec_path, state_path, output_path, status, priority,
deadline, earliest_start, spawned_by, depends_on JSONB, required_node_class,
heartbeat, submitted_at, completed_at, terminal_reason, extra JSONB), and a
`turns` table (task_id FK, turn_n, record JSONB, PRIMARY KEY(task_id, turn_n)).

Files owned: `infra/postgres/docker-compose.yaml`, `infra/postgres/schema.sql`

Acceptance criteria (2 independent assertions — failure names the broken precondition):

1. Container starts: `docker compose -f infra/postgres/docker-compose.yaml up -d && docker compose -f infra/postgres/docker-compose.yaml ps | grep -q "running\|Up"`
2. Schema present: `psql "$DATABASE_URL" -c "\dt" | grep -q tasks`

Dependencies: Task 0
Estimated budget: 250s

---

## Task 1b — Tailscale/SSH preflight to gb10

Description: Verify the network path to gb10 exists and is usable before any
downstream task assumes SSH/Tailscale reachability. Network-only concern,
isolated from the Postgres check so a failure here is unambiguous.

Files owned: none (verification only)

Acceptance criteria (2 independent assertions — failure names the broken precondition):

1. Tailscale sees gb10 online: `tailscale status --json | jq -e '.Peer[] | select(.HostName=="gb10") | .Online == true'`
2. SSH to gb10 succeeds: `ssh gb10 'echo ok'`

Dependencies: Task 0
Estimated budget: 150s

---

## Task 2a — PostgresQueue core CRUD methods + tests

Description: Implement `PostgresQueue` in `saturate/queue_postgres.py`
covering the non-concurrency-sensitive half of the interface: `post`,
`write_state`, `read_state`, `record_turn`, `counts`, `get`, `turn_history`.
Unit tests for each against a real (test-schema) Postgres instance. Does NOT
touch `claim`/`complete`/`requeue` — those are Task 2b.

Files owned: `saturate/queue_postgres.py`, `tests/test_queue_postgres.py`

Acceptance criteria: `uv run pytest tests/test_queue_postgres.py -q -k "not concurrency"` exits 0 with ≥7 passing tests

Dependencies: Task 1a
Estimated budget: 500s

---

## Task 2b — PostgresQueue concurrency semantics + deterministic concurrency test

Description: Implement `claim()` using `SELECT ... FOR UPDATE SKIP LOCKED`,
`complete()`, and `requeue()`. Deterministic pytest: seed exactly 5 pending
rows, spawn 8 concurrent workers via `concurrent.futures.ThreadPoolExecutor`
each calling `claim()` in a loop until the queue is empty, collect all
returned `task_id`s across all workers, assert the collected set has exactly
5 unique entries (no duplicates, none missed). Assumes Postgres is already
running from Task 1a — does not re-provision.

Files owned: `saturate/queue_postgres.py`, `tests/test_queue_postgres_concurrency.py`

Acceptance criteria: `uv run pytest tests/test_queue_postgres_concurrency.py -q` exits 0

Dependencies: Task 2a
Estimated budget: 500s

---

## Task 3 — Queue backend abstraction + runner_proc.py dual-backend support

Description: Create `saturate/queue_factory.py` exposing `get_queue(backend:
str) -> Queue` dispatching to `SqliteQueue` or `PostgresQueue` based on a
`SATURATE_BACKEND` env var (default `sqlite` for backward compat). Update
`saturate/runner_proc.py` and `saturate/cli.py` to use the factory instead of
hardcoding `SqliteQueue`.

Files owned: `saturate/queue_factory.py`, `saturate/runner_proc.py`, `saturate/cli.py`

Acceptance criteria: with `SATURATE_BACKEND=postgres` exported, run
`python -m saturate.runner_proc` against a task seeded via `PostgresQueue.post()`,
then `psql "$DATABASE_URL" -c "SELECT status FROM tasks WHERE task_id='<id>'"`
returns `completed`

Dependencies: Task 2b
Estimated budget: 450s

---

## Task 4 — Thread required_node_class through scheduler dispatch scoring

Description: Fix `saturate/scheduler.py`'s `_score_task()` to pass
`required_node_class=task.get("required_node_class")` when constructing the
`SaturateTask` object from the raw dict (currently silently dropped — the
field already exists on `SaturateTask`, confirmed by reading `task.py`).
Scoped to `required_node_class` only — `spawned_by`/`depends_on` are not
consumed by `dispatch_score()` and are out of scope here.

Files owned: `saturate/scheduler.py`

Acceptance criteria: `uv run pytest tests/test_scheduler.py -q -k "required_node_class"`
— new test asserting a raw task dict with `required_node_class: "gb10"`
produces a `SaturateTask` object with that field set (not None)

Dependencies: none
Estimated budget: 250s

---

## Task 5a — Nomad server bring-up on roger

Description: Download Nomad 1.11.8 binary (amd64) to `/usr/local/bin/nomad`
on roger. Write `infra/nomad/server.hcl` (`server { enabled = true,
bootstrap_expect = 1 }`, bind to Tailscale IP 100.65.5.5). Run as a systemd
unit (`infra/nomad/systemd/nomad-server.service`). Verify it comes up and
survives a manual restart.

Files owned: `infra/nomad/server.hcl`, `infra/nomad/systemd/nomad-server.service`

Acceptance criteria: `systemctl is-active nomad-server && nomad server members | grep -q alive`

Dependencies: none
Estimated budget: 350s

---

## Task 5b — Nomad client bring-up on gb10

Description: Download Nomad 1.11.8 binary (**arm64** — gb10 is aarch64) to
`/usr/local/bin/nomad` on gb10. Write `infra/nomad/client-gb10.hcl` (`client {
enabled = true, servers = ["100.65.5.5:4647"], node_class = "gb10", meta {
gpu = "true" } }`, `plugin "raw_exec" { config { enabled = true } }`). Run as
a systemd unit (`infra/nomad/systemd/nomad-client-gb10.service`), joined to
the roger server. Verify it registers. Depends on Task 5a — client join must
not race server startup.

Files owned: `infra/nomad/client-gb10.hcl`, `infra/nomad/systemd/nomad-client-gb10.service`

Acceptance criteria: `ssh gb10 'systemctl is-active nomad-client'` AND (from roger) `nomad node status | grep -q ready`

Dependencies: Task 5a
Estimated budget: 350s

---

## Task 6 — Nomad parameterized dispatch job + _launch_runner_nomad() wiring

Description: Write `infra/nomad/saturate-runner-gb10.nomad.hcl` as a
parameterized job (`parameterized { payload = "forbidden", meta_required =
["TASK_ID", "DATABASE_URL"] }`, `constraint { attribute = "${node.class}",
value = "gb10" }`, single `raw_exec` task group running `python -m
saturate.runner_proc ${NOMAD_META_TASK_ID} ${NOMAD_META_DATABASE_URL}`).
Register it via `nomad job run`. Implement `_launch_runner_nomad()` in
`saturate/scheduler.py` (replacing Task 4's stub): POST to
`http://100.65.5.5:4646/v1/job/saturate-runner-gb10/dispatch` with
`{"Meta": {"TASK_ID": task_id, "DATABASE_URL": dsn}}`, honoring
`required_node_class` (only dispatch if it equals `"gb10"`).

Files owned: `infra/nomad/saturate-runner-gb10.nomad.hcl`, `saturate/scheduler.py`

Acceptance criteria: `curl -s -o /dev/null -w "%{http_code}" -X POST http://roger:4646/v1/jobs -d @infra/nomad/saturate-runner-gb10.nomad.hcl.json` returns `200`, AND `nomad job status -json saturate-runner-gb10 | jq -e '.Allocations[0].ClientStatus == "complete"'`

Dependencies: Task 4, Task 5a, Task 5b, Task 7
Estimated budget: 500s

---

## Task 7 — gb10 environment provisioning + cross-host Postgres reachability + model/dataset precondition

Description: On gb10, clone `~/src/witt3rd/saturate` and
`~/src/witt3rd/continuum` (confirmed absent as of design time), run `uv sync`
in the saturate checkout. Verify Postgres connectivity **from gb10 itself**
(distinct from Task 1a's local bring-up — this is cross-host reachability).
Verify MiniCPM-o model weights and training dataset already exist on gb10
(no prior task checks this).

Files owned: none (provisioning only)

Acceptance criteria: `ssh gb10 "cd ~/src/witt3rd/saturate && uv run python -c 'import saturate'"` succeeds AND `ssh gb10 'psql "$DATABASE_URL" -c "SELECT 1"'` returns `1` AND `ssh gb10 'test -f /home/dt/minicpm-o-4_5/config.json && test -d /mnt/nasty/training/continuum-signal-v1/dataset'`

Dependencies: Task 1a, Task 3
Estimated budget: 400s

---

## Task 8a — SATURATE_SMOKE_TEST size cap + isolated output-dir override

Description: In `continuum/scripts/train_recall_signal.py`, add a
`SATURATE_SMOKE_TEST=1` env var gate capping `num_train_epochs=1,
max_steps=2` for fast pipeline validation. **Also** add a
`SATURATE_CHECKPOINT_DIR` env var that overrides the checkpoint output path
when set — this is the actual isolation mechanism: when unset, the script
writes to the production path exactly as it does today (no behavior change
for real training); when set, all checkpoint writes redirect to the given
directory. Without this, a smoke run's checkpoint would land in — and
silently corrupt — the production checkpoint tree that Task 9's `evaluate`
step reads via most-recent-mtime.

Files owned: `continuum/scripts/train_recall_signal.py`

Acceptance criteria: `SATURATE_SMOKE_TEST=1 SATURATE_CHECKPOINT_DIR=/mnt/nasty/training/_smoke/checkpoints python3 scripts/train_recall_signal.py && test -d /mnt/nasty/training/_smoke/checkpoints && grep -q "SATURATE_CHECKPOINT_DIR" continuum/scripts/train_recall_signal.py`

Dependencies: none
Estimated budget: 400s

---

## Task 8b — JSON signal_score emission in eval_recall_signal.py

Description: Append a single final JSON line to `eval_recall_signal.py`'s
output containing `{"signal_score": <float>}`, computed from the existing
`correct_trigger/total_trigger` and `correct_boundary/total_boundary` counts
(`signal_coherence` placeholder `1.0` with `# TODO` — coherence metric is
Goal 1's own research problem, out of scope here). This is what
`evaluate_extract: json:signal_score` parses.

Files owned: `continuum/scripts/eval_recall_signal.py`

Acceptance criteria: `python3 scripts/eval_recall_signal.py --checkpoint <known-good-checkpoint> | tail -1 | python3 -c "import json,sys; d=json.loads(sys.stdin.read()); assert 'signal_score' in d and isinstance(d['signal_score'], float)"`

Dependencies: none
Estimated budget: 300s

---

## Task 9 — Author production Goal-1 MetricOptimizationKind spec

Description: Write `continuum/goals/minicpm-recall-signal.yaml` for Goal 1.
Training lives in `executor` (the hypothesis/apply step), NOT embedded in
`evaluate` (which must stay read-only measurement per the required
hypothesis→evaluate→correctness→keep-or-revert cycle). Explicit `terminal:`
block using the README's already-decided values — without this the spec
would silently inherit `loop_spec`'s library defaults
(`max_iterations: 100, plateau_count: 10`) for a real, expensive,
gb10-distributed research loop nobody reviewed. `level: L2` is retained
exactly as previously ratified (Goal 1's L2-autonomous-with-DRI-gating
governance, documented in `examples/finetuning/README.md` — not a fresh
proposal subject to the first-loop L1 rule). This file is written and
schema-validated only — NOT run/executed by this loop.

```yaml
kind: MetricOptimizationKind
name: minicpm-recall-signal
level: L2
metric: signal_score
direction: higher_is_better
baseline: 0.43
terminal:
  max_iterations: 200
  plateau_count: 15
  target_score: 0.85
executor:
  type: shell
  command: "python3 scripts/train_recall_signal.py"
evaluate: |
  python3 scripts/eval_recall_signal.py --checkpoint $(ls -td /mnt/nasty/training/continuum-signal-v1/checkpoints/*/ | head -1)
evaluate_extract: "json:signal_score"
correctness: null
target_files:
  - scripts/train_recall_signal.py
```

Files owned: `continuum/goals/minicpm-recall-signal.yaml`

Acceptance criteria: `python3 -c "from loop_spec import load_spec; s = load_spec('continuum/goals/minicpm-recall-signal.yaml'); assert s.kind == 'MetricOptimizationKind'; assert s.level == 'L2'; assert s.executor is not None; assert 'train_recall_signal.py' not in s.evaluate; assert s.terminal is not None; assert s.terminal.max_iterations == 200; assert s.terminal.plateau_count == 15; assert s.terminal.target_score == 0.85"`

Dependencies: none
Estimated budget: 300s

---

## Task 10 — Isolated smoke-test: dispatch, verify, cleanup

Description: This is the loop's actual "done when." Prove the full chain
(Postgres queue → scheduler tick → Nomad dispatch → gb10 executor → evaluate
→ keep/revert) fires end-to-end WITHOUT touching production research state.
Author a throwaway smoke variant of Task 9's spec (`name:
minicpm-recall-signal-SMOKE`), submit with `SATURATE_SMOKE_TEST=1
SATURATE_CHECKPOINT_DIR=/mnt/nasty/training/_smoke/checkpoints` exported. Run
one scheduler tick. Scoped as verify-and-report only — on failure, routes
back to the owning task (Nomad-shaped → Task 6; gb10-env-shaped → Task 7;
training/eval-shaped → Task 8a/8b; spec-shape → Task 9) rather than
attempting repair here.

Files owned: none persistent (smoke spec + smoke checkpoint dir created and
deleted within this task)

Acceptance criteria (5 checks, run in order):
1. Snapshot production checkpoint tree BEFORE dispatch:
   `find /mnt/nasty/training/continuum-signal-v1/checkpoints/ -mindepth 1 -maxdepth 1 -type d 2>/dev/null | sort > /tmp/prod_before.txt`
2. Dispatch smoke job; verify Postgres queue row completed:
   `psql "$DATABASE_URL" -c "SELECT completed_at FROM tasks WHERE task_id='<smoke-task-id>'"` returns non-null
3. Verify Nomad job completed:
   `nomad job status -json saturate-runner-gb10-smoke | jq -e '[.Allocations[] | select(.ClientStatus=="complete")] | length > 0'`
4. Verify isolation actually held — smoke checkpoint landed in the isolated
   path AND the production tree is unchanged:
   `test -d /mnt/nasty/training/_smoke/checkpoints && find /mnt/nasty/training/continuum-signal-v1/checkpoints/ -mindepth 1 -maxdepth 1 -type d 2>/dev/null | sort > /tmp/prod_after.txt && diff -q /tmp/prod_before.txt /tmp/prod_after.txt`
5. Cleanup: `rm -rf /mnt/nasty/training/_smoke && test ! -d /mnt/nasty/training/_smoke && psql "$DATABASE_URL" -c "SELECT count(*) FROM tasks WHERE task_id='<smoke-task-id>'"` returns `0`

Dependencies: Task 6, Task 7, Task 8a, Task 8b, Task 9
Estimated budget: 650s

---

## Design provenance

Designed via `cyclus-loop-design` (Planner/Architect/Critic consensus),
3 rounds, 2026-07-10:
- Round 1: 10 tasks → REQUEST_CHANGES (both reviewers) — undersized max_iterations,
  category-error plateau_count, 5 overloaded tasks, 2 hidden dependencies, a
  read-only-eval contract violation, missing STATE.md declaration, a
  production-data-pollution risk in the smoke test.
- Round 2: 14 tasks, all Round 1 findings addressed → REQUEST_CHANGES again
  (both reviewers) — smoke isolation was *described* but not actually
  *engineered* (no real output-dir mechanism), Task 9's deliverable spec had
  no `terminal:` block (silent library defaults), a new 5a/5b dependency
  ordering bug, Task 1's compound acceptance clause never actually fixed,
  max_iterations never actually changed.
- Round 3 (final, 3-round max): 15 tasks, all 5 DRI-ratified findings closed
  with real mechanisms (not just descriptions) → DRI-approved for dispatch.
