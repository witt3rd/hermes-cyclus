# Resources

Reference articles and transcripts that inform Cyclus's design. Kept here
for offline reading and searchability alongside the code.

---

## Loop Engineering — Cobus Greyling

**Source:** Greyling's Substack  
**File:** [`Loop_Engineering.md`](Loop_Engineering.md)

Overview of loop engineering as the next evolution after context engineering
and harness engineering. Introduces the three-layer model and the core patterns
that Cyclus's L1/L2/L3 maturity model and loop budget convention draw from.

---

## The Art of Loop Engineering — LangChain

**Source:** LangChain blog  
**File:** [`The_Art_of_Loop_Engineering.md`](The_Art_of_Loop_Engineering.md)

Frames agent loops as stackable levels (agent loop, eval loop, optimization
loop) and explains how to instrument each with LangChain primitives. The
multi-level loop taxonomy here maps directly onto Cyclus's typed loop kinds.

---

## What Is Loop Engineering? AI Feedback Loops — Kilo

**Source:** Kilo  
**File:** [`What_Is_Loop_Engineering_AI_Feedback_Loops_Kilo.md`](What_Is_Loop_Engineering_AI_Feedback_Loops_Kilo.md)

Defines loop engineering as the discipline of structuring AI-assisted software
development around repeated cycles of intent → context → action → observation →
adjustment. Clear treatment of how loop engineering differs from prompt
engineering.

---

## What Is Loop Engineering? The New Meta for AI Coding Agents — MindStudio

**Source:** MindStudio  
**File:** [`What_Is_Loop_Engineering_The_New_Meta_for_AI_Coding_Agents_MindStudio.md`](What_Is_Loop_Engineering_The_New_Meta_for_AI_Coding_Agents_MindStudio.md)

Practical introduction to loop engineering from a product/practitioner
perspective. Covers the ReAct pattern, stopping criteria, and how loop
infrastructure relates to tools like Claude Code.

---

## Loop Engineering (essay) — Addy Osmani

**Source:** <https://addyosmani.com/blog/loop-engineering/>  
**Author:** Addy Osmani, Director of Engineering, Google DeepMind  
**File:** [`AddyOsmani_com_-_Loop_Engineering.md`](AddyOsmani_com_-_Loop_Engineering.md)

Independent convergence on the same five-primitive architecture Cyclus
implements.

> *"Build it like someone who intends to stay the engineer, not just the person
> who presses go."*

---

## Skill Issue: Andrej Karpathy on Code Agents, AutoResearch, and the Loopy Era of AI

**Source:** <https://youtu.be/kwSVtQ7dziU>  
**File:** [`karpathy-skill-issue-transcript.md`](karpathy-skill-issue-transcript.md)

The most complete public articulation of the autoresearch thesis — agents, loop
orchestration, and the "loopy era" of AI development. The
`MetricOptimizationKind` loop kind traces directly to Karpathy's formulation:
run until a metric improves, not until a workflow completes.
