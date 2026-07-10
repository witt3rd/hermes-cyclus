# finetuning — Autoresearch Loop Example

This directory documents the **finetuning autoresearch loop** for Cyclus:
automating the LLM finetuning research cycle that has been running manually
for 11 iterations in `~/src/witt3rd/continuum/docs/finetuning/llamafactory_recipe.md`.

---

## What this is about

**Continuum** is a continuously-running cognitive loop for MiniCPM-o 4.5.
To route work to the right system (memory recall, deep reasoning, task dispatch),
the model needs to emit structured signal tokens like `<|recall|>` at the right
moments. Teaching it to do this reliably requires finetuning.

We're using **LLaMA-Factory** on **gb10** (a Blackwell GPU machine with 128GB VRAM
on the local Tailscale network) to finetune MiniCPM-o 4.5 via LoRA. Each
finetuning run takes 20–120 minutes. We've done 11 manual iterations so far.
The full history lives in `~/src/witt3rd/continuum/docs/finetuning/llamafactory_recipe.md`.

The goal of this loop: automate that manual research cycle so it runs
unattended, documents itself, and eventually runs N hypotheses in parallel
across gb10, tensor, and omarchy simultaneously.

---

## The core insight

The `llamafactory_recipe.md` document IS this loop's `STATE.md` — written by hand.
Each of the 11 iterations is one turn of a `MetricOptimizationKind` loop.
The loop's job is to continue writing it, automatically.

---

## Nested loop structure

```
MetricOptimizationKind  ← the only loop kind needed
│  State: accumulated iteration history (currently 11 turns, manual)
│  Each turn = one finetuning hypothesis tested end-to-end
│
└── Turn N:
    │
    ├── executor: Nomad worker on gb10 (gap 3 below)
    │   Applies the hypothesis: writes LLaMA-Factory YAML config on gb10,
    │   launches training, waits for completion (blocking — the shell script
    │   owns the polling loop internally via `while ps... ; do sleep 1800; done`)
    │   Training runs 20–120 min. The executor's shell script handles it.
    │
    ├── evaluate: shell script on gb10 via Nomad
    │   Runs probe script → returns JSON with signal_score fields
    │   Fast (~minutes) once training has finished
    │
    └── level: L1 (propose only) or L2 (apply + confirm)
        At L1: loop proposes the next config, human reviews before training starts
        At L2: loop applies and trains autonomously; human gates only on cut decisions
        HUMAN_GATED ClarificationKind tasks handle ambiguous cut decisions
        via the existing queue mechanism — no new loop kind needed
```

The asyncness, polling, and cut decisions live in **shell scripts and executor behavior** — not in new loop kinds. Loop-spec stays general-purpose.

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

Current problem (v11): the model learned to suppress `[[` at non-recall
boundaries (good) but can't yet assemble the full `[[RECALL]]` token sequence
cleanly — outputs garbled like "CALLCALLCALL" or "[[[[]][[RE]]]]".
Next bet: v11 fix plan in `llamafactory_recipe.md` → increase Phase 2 LR
aggressively, add bare-forcing examples early in Phase 2.

---

## Gaps to close (the meta-loop's task list)

| # | Gap | Where | Effort |
|---|-----|--------|--------|
| 1 | **Postgres on roger** — replace SQLite as the shared durable queue | saturate | Small |
| 2 | **Nomad cluster** — roger as server, gb10/tensor as clients via Tailscale | infra | Medium |
| 3 | **Saturate→Nomad integration** — scheduler submits jobs to Nomad HTTP API | saturate | Medium |
| 4 | **Finetuning shell scripts on gb10** — launch LLaMA-Factory, poll, probe | continuum | Medium |
| 5 | **Finetuning spec.yaml** — `MetricOptimizationKind`, evaluate over Nomad dispatch | here | Small |

**The meta-loop:** a `TaskExecutionKind` loop that closes gaps 1–5 in order,
each task verified, until one real finetuning iteration (iteration 12) runs
end-to-end via the loop on gb10. The distributed swarm (gb10 + tensor in
parallel) follows naturally once Nomad is up.

**Note:** No SSHExecutor, no custom worker daemon. Nomad handles node
registration, GPU allocation, and push dispatch. This is exactly
what `~/src/witt3rd/saturate/ARCHITECTURE.md §Fleet Management / Phase 2`
already specifies.

---

## Distributed swarm (after gaps 1–5)

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
- Saturate fleet architecture: `~/src/witt3rd/saturate/ARCHITECTURE.md`
- Model on gb10: `/home/dt/minicpm-o-4_5/`
- Training data: `/mnt/nasty/training/continuum-signal-v1/dataset/`
- Issue to rewrite as clean recipe (post iteration 12):
  https://github.com/witt3rd/hermes-cyclus/issues/25

