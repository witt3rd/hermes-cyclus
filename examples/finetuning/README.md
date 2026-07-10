# finetuning — Two Parallel Goals

---

## Goal 1: Autoresearch loop (running NOW, manually)

Run finetuning research on MiniCPM-o 4.5 until the signal token task
converges or clearly diverges. This loop is already running — 11 manual
iterations yesterday. It should keep running regardless of Goal 2's progress.

**State document:** `~/src/witt3rd/continuum/docs/finetuning/llamafactory_recipe.md`
This is the loop's `STATE.md`, written by hand across 11 turns. Each iteration
appends: hypothesis, config, training results, eval scores, what was learned.

**The research arc so far:**
- v1–v7: custom token approach `<|RECALL|>` — abandoned (embedding issues, wrong model class)
- v8–v11: token sequence approach `[[RECALL]]...[[/RECALL]]` — in progress
  - v9: first real signal, 0.43 (trigger fires but boundaries not clean)
  - v10: curriculum Phase 1, 0.45 (suppression working)
  - v11: curriculum Phase 2, 0.43 (regression — sequence assembly broken)

**This is an open-ended research loop.** It is not "try the v11 fix then stop."
It runs until `signal_score ≥ 0.85` (converged) or the approach is abandoned
and a fundamentally different strategy is chosen. New hypotheses are generated
from the full iteration history each turn.

**Right now:** run iterations manually on gb10. Document each in `llamafactory_recipe.md`.
When Goal 2 is complete, the loop runs itself.

---

## Goal 2: Meta-loop (infrastructure to automate Goal 1)

Build the Cyclus+Saturate infrastructure that lets Goal 1 run unattended and
eventually distributed across gb10, tensor, and omarchy in parallel.

**This is a `TaskExecutionKind` loop** — a finite plan with verifiable tasks,
not an open-ended research loop.

**Gaps to close:**

| # | Gap | Where | Effort |
|---|-----|--------|--------|
| 1 | **Postgres on roger** — shared durable queue over Tailscale | saturate | Small |
| 2 | **Nomad cluster** — roger as server, gb10/tensor as clients | infra | Medium |
| 3 | **Saturate→Nomad integration** — scheduler pushes to Nomad HTTP API | saturate | Medium |
| 4 | **Finetuning shell scripts on gb10** — launch LLaMA-Factory, poll, probe | continuum | Medium |
| 5 | **Finetuning spec.yaml** — `MetricOptimizationKind` loop spec for Goal 1 | here | Small |

**Done when:** one real iteration of Goal 1 (iteration N) runs end-to-end
without human involvement: loop proposes hypothesis → Nomad dispatches to gb10 →
training runs → probe evaluates → result appended to `llamafactory_recipe.md`.

**Note:** No SSHExecutor, no custom worker daemon. Nomad handles node
registration, GPU allocation, and push dispatch. See
`~/src/witt3rd/saturate/ARCHITECTURE.md §Fleet Management / Phase 2`.

---

## The autoresearch loop structure (Goal 1, once Goal 2 exists)

```
MetricOptimizationKind  ← open-ended, runs until convergence
│  STATE: llamafactory_recipe.md (11 turns written by hand, loop continues it)
│  Terminal: signal_score ≥ 0.85 OR human decides to abandon approach
│
└── Turn N:
    ├── executor: Nomad worker on gb10
    │   Reads full iteration history → generates next hypothesis
    │   Writes LLaMA-Factory YAML config, launches training
    │   Polls until completion (shell script: `while ps...; do sleep 1800; done`)
    │
    ├── evaluate: probe script on gb10 → signal_score JSON
    │
    └── level: L1 initially (human reviews each hypothesis)
        level: L2 once trust established (loop applies autonomously)
        HUMAN_GATED cut decisions via ClarificationKind when plateau detected
```

---

## The metric

```python
signal_score = (
    0.4 * trigger_recall      # fires when it should?
  + 0.4 * boundary_clean      # doesn't fire when it shouldn't?
  + 0.2 * signal_coherence    # emitted tokens are well-formed?
)
# Target: ≥ 0.85. Current best: 0.45 (v10)
```

---

## Distributed swarm (after Goal 2 + Nomad)

```
Turn N swarm (BatchKind):
  Worker A → hypothesis_seed="conservative_lr" → gb10
  Worker B → hypothesis_seed="aggressive_lr"   → tensor
  Worker C → hypothesis_seed="curriculum_v3"   → omarchy

  All three train in parallel. Verifier picks best signal_score.
  Winner → new baseline. Loop continues.
```

---

## Reference

- Iteration history + state: `~/src/witt3rd/continuum/docs/finetuning/llamafactory_recipe.md`
- Signal token design: `~/src/witt3rd/continuum/docs/continuum_architecture.md`
- LLaMA-Factory cookbook: `~/src/ext/MiniCPM-V-CookBook/finetune/llamafactory/finetune_llamafactory.md`
- Saturate fleet architecture: `~/src/witt3rd/saturate/ARCHITECTURE.md`
- Model on gb10: `/home/dt/minicpm-o-4_5/`
- Training data: `/mnt/nasty/training/continuum-signal-v1/dataset/`
- Issue to rewrite as clean recipe after convergence: https://github.com/witt3rd/hermes-cyclus/issues/25


This directory documents the **finetuning autoresearch loop** for Cyclus:
automating the LLM finetuning research cycle that has been running manually
