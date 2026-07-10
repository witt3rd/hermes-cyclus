# finetuning — AutoresearchKind Loop Example

This directory documents the **finetuning example** for Cyclus:
running an automated LLM finetuning research loop that iterates hypotheses
until a signal token finetuning task converges.

## The problem this loop solves

LLM finetuning research has a brutal time structure:
- Each run takes 20–120 minutes of GPU time
- You can't know if a hypothesis was wrong until the run finishes
- Between runs you must: examine loss curves, evaluate outputs, form a
  new hypothesis, adjust config, kick off the next run
- 10+ iterations are typical before convergence
- Human attention is the bottleneck — not GPU compute

This is exactly what `MetricOptimizationKind` loops were designed for.

## The specific task

Finetune **MiniCPM-o 4.5** via **LLaMA-Factory** to emit structured
signal tokens (`<|recall|>`, `<|think|>`, etc.) at the right moments
in conversation — enabling Continuum's harness to detect and route
them to the appropriate action (memory recall, deep reasoning, etc.).

Progress is tracked in:
`~/src/witt3rd/continuum/docs/finetuning/llamafactory_recipe.md`
(10–11 iterations documented, still converging as of 2026-07-10)

## What a single loop iteration looks like

```
1. PROPOSE:    Select hyperparameter configuration (lora_rank, lr, epochs,
               data mix, curriculum strategy, etc.)
2. SETUP:      Write LLaMA-Factory YAML config, register dataset
3. KICK OFF:   Launch training on GPU host (gb10, omarchy, or tensor)
               via SSH — this returns immediately, training runs async
4. MONITOR:    Poll training process periodically (every 10–30 min)
               Check: still running? loss curve sane? early stop triggered?
5. DECIDE:     When training ends (or plateau detected):
               - Evaluate: run probe script, check trigger/boundary metrics
               - KEEP: update baseline, record learning, propose next hypothesis
               - CUT:  loss diverged or clearly overfit — stop early, record why
6. DOCUMENT:   Write iteration summary to docs/finetuning/
7. REPEAT
```

## Why this requires new loop machinery

Standard `MetricOptimizationKind` assumes:
- Each iteration is a fast subprocess call (seconds to minutes)
- The eval command runs synchronously after the hypothesis

Finetuning requires:
- **Async execution**: training is a long-running process launched via SSH,
  NOT a blocking subprocess. The loop must launch and return, then poll.
- **Time-gated polling**: check every N minutes, not after each step
- **Human-in-loop gates**: some decisions (cut vs wait) benefit from human
  judgment, especially early in the research arc
- **Multi-machine dispatch**: N GPU machines running N hypotheses in parallel
  is the natural swarm mode — different hyperparameter seeds, different
  curriculum strategies, race to the best metric
- **Rich state**: iteration history, loss curves, eval probe results, and
  the accumulated research notes must persist and be readable by each new
  iteration's reasoning

## What we need to build (the meta-loop)

This example is both:
1. The **end goal** — a working finetuning autoresearch loop
2. The **design surface** — revealing what Cyclus needs to support it

Gaps to close before this loop can run:

### Gap 1: AsyncExecutionKind (new loop kind)
The training job is launched async and polled. This isn't
`MetricOptimizationKind` (synchronous eval) or `TaskExecutionKind` (linear
plan). We need:
```yaml
kind: AsyncExecutionKind
launch_command: |
  ssh gb10 "cd ~/src/ext/LLaMA-Factory && llamafactory-cli train configs/{config}.yaml"
poll_command: |
  ssh gb10 "ps aux | grep llamafactory | grep -v grep"
poll_interval_seconds: 1800   # check every 30 minutes
terminal_conditions:
  process_dead: true           # training finished
  loss_plateau: 5              # N consecutive checks with <1% loss change
eval_command: |
  ssh gb10 "python3 ~/src/witt3rd/continuum/scripts/probe_signal_tokens.py"
```

### Gap 2: SSHExecutor (new executor type)
The hypothesis runs on a REMOTE machine, not locally.
`HermesExecutor` and `ShellExecutor` both run locally. We need:
```yaml
executor:
  type: ssh
  host: gb10
  setup_command: "source ~/llamafactory-venv/bin/activate"
```

### Gap 3: Durable long-running state
Each iteration can span hours. State must survive:
- Network interruptions
- Manual inspection
- Multiple poll wakeups

The `STATE.md` + SQLite pattern already handles this, but the poll
wakeup mechanism needs explicit support.

### Gap 4: Human-gated cut decisions
Sometimes you want the loop to surface the current loss curve and ask
before cutting. This is `ClarificationKind` nested inside the iteration.
`HUMAN_GATED` tasks in the queue handle this — but the integration
needs to be documented and tested.

### Gap 5: Multi-machine swarm
Running hypothesis A on gb10 and hypothesis B on tensor simultaneously.
Saturate's distributed mode handles this once SSH dispatch works.

## Metric

The finetuning metric is a composite of three probe measurements:

```
trigger_recall   = fraction of recall contexts where model emits <|recall|>
boundary_clean   = fraction of non-recall contexts where model does NOT emit
signal_coherence = fraction of emitted signals with well-formed token pairs
```

Combined into a single `signal_score ∈ [0, 1]`. Target: ≥ 0.85.
Current best: ~0.43 (iteration 11, v9 MiniCPM curriculum training).

## Files

| File | Purpose |
|------|---------|
| `spec.yaml` | Loop spec (to be written once AsyncExecutionKind exists) |
| `state/` | Per-iteration state (loss curves, eval results, notes) |
| `configs/` | LLaMA-Factory YAML configs per iteration |
| `docs/` | Human-readable iteration log |

## Reference

- Full iteration history: `~/src/witt3rd/continuum/docs/finetuning/llamafactory_recipe.md`
- Signal token design: `~/src/witt3rd/continuum/docs/continuum_architecture.md`
- MiniCPM-o cookbook: `~/src/ext/MiniCPM-V-CookBook/finetune/llamafactory/finetune_llamafactory.md`
