# Tutorial: Running Your First Cyclus Loop

hermes-cyclus turns long-running, iterative work into *loops* — systems that
prompt the agent on a schedule so you don't have to. This tutorial walks you
through the key concept and your first real loop in about 15 minutes.

---

## The core idea: stop prompting, design the loop

Without loop engineering, you prompt the agent, get a result, and come back
tomorrow to prompt it again. The work only advances when you remember to push.

With loop engineering, you design the system that does the prompting. The agent
runs on a schedule, accumulates progress in `STATE.md`, and you check in on your
own terms.

> *"You shouldn't be prompting coding agents anymore. You should be designing
> loops that prompt your agents."*
> — Peter Steinberger

**That's what `hermes cron` is for.** It is the heartbeat that makes a
single-session task into a recurring loop. Without it you have a one-off.
With it you have a system.

---

## The two modes

**In-session work** (immediate, you're watching):

```bash
# You are at the keyboard. You want results back in this conversation NOW.
# Use delegate_task or just talk to the agent directly.
```

**Loop work** (autonomous, scheduled, you're not watching):

```bash
# You want this to run every day at 9am whether or not you're around.
# Use hermes cron.
hermes cron create "0 9 * * 1-5" \
  --name "my-loop" \
  --skill cyclus-ralph \
  --workdir "$PWD" \
  --deliver local \
  "Run one turn. Update STATE.md. Do not commit."
```

The difference: `deliver local` means the output is saved to
`~/.hermes/profiles/forge/cron/` — you read it at your convenience, not in
real-time. The loop runs whether you're asleep or not.

---

## L1 first — always

Every loop starts at **L1 (report-only)**. The loop proposes; you decide.

| Level | What the agent does | What you do |
|-------|---------------------|-------------|
| L1 | Proposes a diff in `STATE.md`. Nothing committed. | Read the proposal. Apply it yourself if you like it. |
| L2 | Applies the diff in an isolated worktree. Opens a draft PR. | Review the PR. Merge when ready. |
| L3 | Commits and pushes automatically. | Review after the fact. |

**Never start at L3.** Greyling's anti-pattern #4: *"L3 before L1 quality."*
You do not know whether your eval command is correct, whether the baseline is
right, or whether the loop is actually improving anything — until L1 shows you.

The `level: L1` field in every `spec.md` is the machine-readable enforcement of
this. L1 workers never touch the repo; they only write to `STATE.md`.

---

## How one loop iteration works

```
┌─────────────────────────────────────────────────────────┐
│  hermes cron fires (e.g. 9:00 AM Monday)                │
│                                                         │
│  1. Fresh agent session starts                          │
│  2. Reads spec.md (goal, metric, terminal conditions)   │
│  3. Reads STATE.md (what was tried, lessons learned)    │
│  4. Proposes one improvement                            │
│  5. Runs the eval command, records the score            │
│  6. Writes proposal + score to STATE.md                 │
│  7. Session ends — output saved to cron output dir      │
└─────────────────────────────────────────────────────────┘

You check STATE.md when you want. Apply the proposal if it looks good.

┌─────────────────────────────────────────────────────────┐
│  hermes cron fires again (9:00 AM Tuesday)              │
│  ... same cycle, one more iteration                     │
└─────────────────────────────────────────────────────────┘
```

The agent is **stateless between sessions** — it forgets everything. `STATE.md`
is what gives the loop memory. The agent reads it at the start of every tick to
know what has already been tried, what was discarded, and what the current best
score is. Without `STATE.md`, every tick would start from scratch.

---

## Your first loop: test coverage

This loop improves Cyclus's own test coverage. It's the meta-example — Cyclus
eating its own dogfood.

**Step 1: Check the baseline**

```bash
cd ~/src/witt3rd/cyclus
PYTHONPATH=. uv run pytest tests/ --cov=. --cov-report=json -q 2>/dev/null
python3 -c "import json; d=json.load(open('coverage.json')); print(d['totals']['percent_covered'])"
# → 77.93
```

This is the number the loop will try to improve. It's already recorded in
`examples/test_coverage/spec.md` as `baseline: 77.93`.

**Step 2: Initialize STATE.md**

```bash
# STATE.md is already at the repo root — check it
cat STATE.md
```

The `STATE.md` template is pre-populated with the active loops. The agent reads
and writes this file on every tick.

**Step 3: Start the loop**

```bash
hermes cron create "0 9 * * 1-5" \
  --name "cyclus-test-coverage" \
  --skill cyclus-ralph \
  --workdir "$(pwd)" \
  --deliver local \
  "Read examples/test_coverage/spec.md. Read STATE.md.
Run one MetricOptimizationKind turn at level L1:
1. Run: PYTHONPATH=. uv run pytest tests/ --cov=. --cov-report=json -q 2>/dev/null
2. Read coverage.json and extract coverage_percent.
3. Identify the least-covered file or function.
4. Propose ONE new test or test extension as a fenced patch block in STATE.md.
5. Do NOT apply the patch (level: L1).
6. Update STATE.md: add the proposal under 'Loop Run Log', update Last run timestamp.
Report the current coverage_percent and what you proposed."
```

**Step 4: Verify the loop is scheduled**

```bash
hermes cron list
```

**Step 5: Check the output after it runs**

```bash
# Output goes here (not to your chat session)
ls ~/.hermes/profiles/forge/cron/output/

# Read STATE.md for the proposal
cat STATE.md
```

**Step 6: Apply a proposal you like**

When you see a proposal you want to keep:

```bash
# Apply the fenced patch from STATE.md manually
patch -p1 < <(grep -A100 '```python' STATE.md | head -100)

# Or just copy-paste the test into the right file and run tests
PYTHONPATH=. uv run pytest tests/ -q
git add tests/
git commit -m "test: add coverage for <what the loop proposed>"
```

---

## The `--context-from` chain: L2 maker/checker

When you're ready to graduate a loop to L2, wire two cron jobs together.
The proposer runs first; the verifier receives its output and applies the patch
in an isolated worktree:

```bash
# Proposer — same as L1 above
PROPOSER_ID=$(hermes cron create "0 9 * * 1-5" \
  --name "coverage-proposer" \
  --skill cyclus-ralph \
  --workdir "$(pwd)" \
  --deliver local \
  "Propose one test improvement as a fenced patch. Update STATE.md. Do not apply." \
  | tail -1)

# Verifier — receives proposer stdout as injected context
hermes cron create "5 9 * * 1-5" \
  --name "coverage-verifier" \
  --skill cyclus-ralph-driver \
  --workdir "$(pwd)" \
  --deliver local \
  "Read the injected proposer output. Apply the fenced patch in an isolated
git worktree. Run tests. If all pass and coverage improves, open a draft PR.
Update STATE.md with the outcome."

hermes cron edit <verifier-job-id> --context-from "$PROPOSER_ID"
```

The verifier's prompt is automatically prefixed with the proposer's most recent
output on every tick. No extra infrastructure — `--context-from` is native
Hermes.

---

## Kill switch

If a loop goes wrong or you want to pause everything:

```bash
# Pause a specific loop
hermes cron pause <job-id>

# Kill switch in STATE.md (the skill checks this and short-circuits)
# Add to STATE.md: loop-pause-all: true

# Resume
hermes cron resume <job-id>
```

---

## FAQ

**Why does the loop run at 9am and not immediately?**

`hermes cron create "0 9 * * 1-5"` is a cron expression: "minute 0, hour 9,
every weekday." Change it to `"*/30 * * * *"` for every 30 minutes, or use
`hermes cron run <job-id>` to fire once immediately.

**Where does the output go?**

`--deliver local` sends output to `~/.hermes/profiles/forge/cron/output/`.
Change to `--deliver telegram` (or `slack`, `discord`) to have it delivered
to a connected channel instead.

**Can I run multiple loops at once?**

Yes — each loop gets its own cron job and its own `STATE.md` section or file.
See `LOOP.md` for the coordination conventions (one owner per file per hour,
separate state files per loop).

**What if the eval command is wrong?**

This is exactly why L1 exists. Run the eval manually first:

```bash
PYTHONPATH=. uv run pytest tests/ --cov=. --cov-report=json -q 2>/dev/null
python3 -c "import json; print(json.load(open('coverage.json'))['totals']['percent_covered'])"
```

If it produces the right output locally, it will work inside the loop. Fix the
eval command before starting any loop.

**Why `--deliver local` and not `--deliver origin`?**

`origin` delivers into your current chat session — fine for one-off tests, noisy
for recurring loops that fire every day. `local` keeps loop output out of your
chat history until you're ready to review it. Graduate to channel delivery
(Telegram, Slack) once the loop output is clean enough to be worth seeing.

---

## Summary

| Concept | What it is |
|---------|------------|
| Loop | A recurring cron job that prompts the agent on a schedule |
| `STATE.md` | The loop's memory between stateless sessions |
| L1 | Propose only — nothing committed, human reviews |
| L2 | Apply + verify in a worktree, open draft PR |
| L3 | Fully autonomous — only after trust is earned |
| `--context-from` | Chains two cron jobs: upstream stdout injected into downstream prompt |
| Kill switch | `loop-pause-all: true` in `STATE.md` |

The loop runs. You stay the engineer.
