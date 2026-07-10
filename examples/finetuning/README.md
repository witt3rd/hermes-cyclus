# finetuning — Two Parallel Goals

---

## What this is actually testing

**The goal is one level higher than "finetune RECALL."** Continuum's harness
design (`~/src/witt3rd/continuum/docs/architecture/harness.md`) defines a
taxonomy of ~10 handoff signals the model needs to emit when it has to hand
off to something outside its own forward pass — not just memory recall, but
reasoning delegation, task dispatch, flow control, and more:

```
Memory     [RECALL:] [RETAIN:] [SEARCH:] [REFLECT:]
Reasoning  [THINK:]
Tasks      [TASK:] [SEND:] [REMIND:]
Flow       [WAIT:] [DONE:] [QUIET:]
```

**This finetuning arc is the pilot run for that whole effort — not the RECALL
signal itself.** The actual open question is: *can we finetune MiniCPM-o 4.5
to reliably emit ANY detectable handoff signal at all, in a form the harness
can parse out of the token stream without contaminating spoken output?*
RECALL was picked as the first test case because memory-recall-need is the
easiest handoff condition to generate synthetic training data for — not
because RECALL is the target. If this pilot proves feasible, the same
recipe extends to the other five-plus signals. If it doesn't, we learn that
before investing in a much larger multi-signal dataset.

Two *signal mechanisms* have been tried under this goal so far — both are
hypotheses about *how* to make the emission detectable, not the goal itself:

- **New vocabulary token** (`<|RECALL|>`) — expand the embedding space,
  teach a token that doesn't exist yet. Abandoned (embedding-init issues,
  wrong model class for the approach).
- **Existing-token sequence** (`[[RECALL]]...[[/RECALL]]`) — compose the
  signal from tokens the model already knows how to produce, no vocab
  expansion. In progress; this is what v8–v11 are testing.

If `[[RECALL]]` sequences also fail to converge, the next hypothesis is a
third signal-mechanism — not a bigger dataset for the same mechanism. The
metric (`signal_score`, below) is scoped to *whichever mechanism is under
test*, not to `[[RECALL]]` specifically — swapping mechanisms means
redefining what "clean emission" means for the new one, not restarting the
higher goal.

---

## Goal 1: Autoresearch loop (running NOW, manually)

Run finetuning research on MiniCPM-o 4.5 until the current signal-mechanism
hypothesis converges or clearly diverges. This loop is already running — 11
manual iterations yesterday. It should keep running regardless of Goal 2's
progress.

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
It runs until `signal_score ≥ 0.85` (converged — feasibility proven for this
mechanism) or the mechanism is abandoned and a fundamentally different
signal-emission strategy is chosen. New hypotheses are generated from the
full iteration history each turn.

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
│  Terminal: signal_score ≥ 0.85 OR human decides to abandon signal-mechanism
│
└── Turn N:
    ├── executor: Nomad worker on gb10
    │   Reads full iteration history → generates next hypothesis
    │   Writes LLaMA-Factory YAML config, launches training
    │   Polls until completion (shell script: `while ps...; do sleep 1800; done`)
    │
    ├── evaluate: probe script on gb10 → signal_score JSON
    │
    └── level: L2 (autonomous) with DRI gating, not human gating
        The DRI (Decision-maker Role Instance) is whoever can evaluate whether
        the plan still serves the original intent. For finetuning research, that
        is NOT necessarily the human — it can be an external ML expert LLM.

        DRI role in this loop: a ConsensusKind sub-loop that queries
        Gemini + Grok as external advisors before each new hypothesis is applied.
        (This mirrors the manual arc: 11 iterations already consulted Gemini and
        Grok to advise on next-iteration plans — the loop formalizes that pattern.)

        Human gates only on:
          1. Budget exhaustion (cost ceiling reached — surface summary, await go-ahead)
          2. Signal-mechanism pivot (abandoning [[RECALL]] token sequences for a
             fundamentally different emission mechanism — strategic call that
             transcends ML expertise, since it re-scopes what "detectable" means)
        Everything else — including hypothesis generation — runs via DRI consensus,
        not human approval. The human is not the bottleneck.
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

This metric is defined for the current signal-mechanism under test
(`[[RECALL]]` token sequences). If the mechanism changes, `signal_score`'s
components get redefined against the new mechanism's shape — the ≥ 0.85
convergence bar and the "does it fire correctly / stay clean at boundaries"
structure carry over, but what counts as "well-formed" is mechanism-specific.

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
- Signal / handoff design (the higher goal this pilot tests feasibility for): `~/src/witt3rd/continuum/docs/architecture/harness.md`
- LLaMA-Factory cookbook: `~/src/ext/MiniCPM-V-CookBook/finetune/llamafactory/finetune_llamafactory.md`
- Saturate fleet architecture: `~/src/witt3rd/saturate/ARCHITECTURE.md`
- Model on gb10: `/home/dt/minicpm-o-4_5/`
- Training data: `/mnt/nasty/training/continuum-signal-v1/dataset/`
- Issue to rewrite as clean recipe after convergence: https://github.com/witt3rd/hermes-cyclus/issues/25


This directory documents the **finetuning autoresearch loop** for Cyclus:
automating the LLM finetuning research cycle that has been running manually
