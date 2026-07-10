# finetuning — Autoresearch Loop Example

This directory documents the **finetuning autoresearch loop** for Cyclus:
automating the LLM finetuning research cycle that has been running manually
for 11 iterations in `~/src/witt3rd/continuum/docs/finetuning/llamafactory_recipe.md`.

---

## The core insight

The `llamafactory_recipe.md` document IS this loop's `STATE.md` — written by hand.
Each of the 11 iterations is one turn of a `MetricOptimizationKind` loop.
The loop's job is to continue writing it, automatically.

---

## Nested loop structure

```
MetricOptimizationKind  ← outer loop: signal_score → 0.85
│  State: accumulated iteration history (currently 11 turns, manual)
│  Each turn = one finetuning hypothesis tested end-to-end
│
└── Turn N:
    │
    ├── HypothesisKind
    │   One LLM call: read full iteration history → generate next
    │   hyperparameter bet (lora_rank, lr, epochs, curriculum, data mix)
    │   Output: LLaMA-Factory YAML config for this iteration
    │
    ├── AsyncTrainingKind          ← NEW: not yet in loop-spec
    │   Launch: ssh gb10 "llamafactory-cli train {config.yaml}"
    │   Returns immediately. Training runs for 20–120 minutes.
    │   │
    │   └── PollingKind            ← nested: wake every 30 min
    │       Check: process alive? loss curve sane? plateau?
    │       │
    │       └── ClarificationKind  ← nested: HUMAN_GATED, optional
    │           Fires when: loss clearly diverged, or plateau before
    │           expected convergence, or >N hours elapsed
    │           Question: "Cut this run and learn from it, or keep waiting?"
    │           Human or automated policy answers → loop resumes
    │
    ├── EvaluationKind
    │   Run probe script on gb10 → extract three measurements:
    │     trigger_recall   = P(model emits <|recall|> | recall context)
    │     boundary_clean   = P(no emission | non-recall context)
    │     signal_coherence = P(well-formed token pair | emission)
    │   Composite: signal_score = weighted average ∈ [0, 1]
    │   Current best: ~0.43 (iteration 11)
    │   Target: ≥ 0.85
    │
    └── DocumentKind
        Write iteration N summary to recipe.md and STATE.md:
        hypothesis, config, loss curve (final loss, epoch), eval results,
        what was learned, what to try next
```

---

## What each loop kind does

### MetricOptimizationKind (outer)
The familiar pattern — same as function_minimization, circle_packing.
Hypothesis → measure → keep/revert → next hypothesis.
What's different: the "measure" step is hours, not seconds.

### AsyncTrainingKind (new)
Launches a long-running process on a remote machine.
Does NOT block waiting for it. Returns a handle.
The handle is polled by the inner PollingKind loop.

This is the key architectural gap. Everything else follows from it.

### PollingKind (new)
Runs on a timer. Each wake: check process status, read partial logs,
decide continue/cut/done. Returns when training terminates naturally OR
a cut decision is made.

Polling interval is a design parameter — 30 min for finetuning,
5 min for faster jobs. The loop wakes on cron, checks, goes back to sleep.

### ClarificationKind (existing, nested)
HUMAN_GATED. Fires when the polling loop detects something ambiguous.
The human (or an automated policy) decides cut vs continue.
Existing `HUMAN_GATED` queue semantics handle this correctly.

### EvaluationKind (future name for inline eval)
Fast synchronous measurement after training completes.
Could be a `MetricOptimizationKind` inner spec or just a shell command.

---

## The metric

```python
signal_score = (
    0.4 * trigger_recall      # does the signal fire when it should?
  + 0.4 * boundary_clean      # does it NOT fire when it shouldn't?
  + 0.2 * signal_coherence    # are emitted tokens well-formed?
)
```

History:
```
v1–v7:   failed (wrong model class, embedding issues, overfit)  ~0.0
v8:      first signal          0.08
v9:      [[RECALL]] pivot      0.43  ← current best
v10:     curriculum Phase 1    0.45  (suppression only)
v11:     curriculum Phase 2    0.43  (regression — sequence assembly broken)
target:                        0.85
```

---

## Gaps to close (the meta-loop's task list)

These must exist before the finetuning loop can run:

| # | Gap | Where | Effort |
|---|-----|--------|--------|
| 1 | `AsyncTrainingKind` in loop-spec | loop-spec | Medium |
| 2 | `PollingKind` in loop-spec | loop-spec | Medium |
| 3 | `SSHExecutor` in Saturate | saturate | Medium |
| 4 | Cron-based poll wakeup | cyclus/hermes | Small |
| 5 | `AsyncTrainingKind` in cyclus_queue | cyclus | Small |
| 6 | Finetuning spec.yaml (this example) | here | Small |
| 7 | Multi-machine swarm (gb10 + tensor in parallel) | saturate | Large |

**The meta-loop:** a `TaskExecutionKind` loop that closes gaps 1–6 in order,
each task verified by a test, until the finetuning loop spec validates
and one real iteration runs end-to-end. Gap 7 follows naturally once 1–6 work.

---

## Distributed execution (gap 7 — future)

Once `SSHExecutor` works:

```
Turn N swarm:
  Worker A → hypothesis_seed="conservative" → gb10
  Worker B → hypothesis_seed="aggressive_lr" → tensor
  Worker C → hypothesis_seed="curriculum_v2" → omarchy
  
  All three run in parallel. Verifier picks the best signal_score.
  Winner becomes the new baseline. Loop continues.
```

This is Saturate's `BatchKind` pattern applied to GPU finetuning.
N machines × M parallel hypotheses per iteration.

---

## Reference

- Full iteration history (11 turns, manual):
  `~/src/witt3rd/continuum/docs/finetuning/llamafactory_recipe.md`
- Signal token design:
  `~/src/witt3rd/continuum/docs/continuum_architecture.md`
- MiniCPM-o cookbook:
  `~/src/ext/MiniCPM-V-CookBook/finetune/llamafactory/finetune_llamafactory.md`
- Model on gb10: `/home/dt/minicpm-o-4_5/`
- Training data: `/mnt/nasty/training/continuum-signal-v1/dataset/`
