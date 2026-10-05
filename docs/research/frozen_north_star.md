# NEUMANN 1 — Frozen North Star

Status: USER-FROZEN, 2026-10-02. This document is the highest-priority research
objective. It supersedes narrower architecture/task priorities, not retained
experiment facts. Q1–Q7 are fixed; implementations are not.

## 1. North Star

**Frontier-level problem solving with minimum necessary computation.**

The goal is NOT a small model. Solve difficult problems that a frontier system
actually solves, while minimizing necessary compute, memory, energy, latency
and monetary cost. A cheaper system that cannot solve the original problem
does not meet the objective.

## 1.1 Overwhelming Advantage and Category Change

The project does **not** define success as a small benchmark win, a modest cost
reduction, or a slightly smaller model. Local gains are mechanism evidence only.

The final ambition has two coupled requirements:

1. **Overwhelming advantage.** At the same useful capability, NEUMANN must
   repeatedly produce a clear Pareto gap in complete compute, memory, energy,
   latency and/or monetary cost across unseen problem families and real Frontier
   Gap tasks. Numeric multipliers and thresholds must be preregistered before
   each evaluation; they are never chosen after observing results.
2. **Category change.** NEUMANN is intended to establish a different operating
   regime for intelligence-per-compute: change the representation, eliminate
   work that need not be done, and buy learned intelligence only for the
   irreducible uncertainty that remains. The target is not merely a better small
   LLM, router, solver wrapper or tool-use system.

A desirable scaling signature is that structural elimination, reuse and
specialization preserve or increase NEUMANN's relative advantage as task
complexity grows. Gains confined to toy or narrowly constructed regimes do not
satisfy the final project objective.

**One-line criterion:** Do not stop at a small win. Create an overwhelming
resource gap at iso-capability and change the computational category in which
useful intelligence is produced.

P1.x PASS/FAIL results remain local research evidence under this North Star.
They do not by themselves constitute NEUMANN success. Q1-Q7, complete
iso-capability accounting, independent verification and fresh/open-set evidence
remain mandatory.

## 2. Core hypothesis

An important part of intelligence may come from changing a problem into a
better representation, eliminating unnecessary work and selecting only the
necessary computation—not merely performing more computation.

Problem → Structure → Minimal Sufficient Representation → Eliminate →
Cheapest Sufficient Compute → Verify.

This is a governing principle, not a sacred sequence of software modules.
Minimality is a target; sufficiency must be established on the original task.

## 3. Learned intelligence

The Learned Core can perform semantic understanding, abstraction, hidden
structure discovery, representation change, hypothesis generation, decomposition,
strategy selection, uncertainty judgment and restructuring after failure.

**Do not learn what can be derived more cheaply.** AI is not removed; it is used
where it earns capability or lower complete resource cost. Deterministic work
that is cheaper at the same useful capability belongs outside learned inference.

## 4. Computational principle

**Do not compute what can be eliminated.**

**Never spend compute unless it buys capability.**

Escalate C1<C2<C3<…<CF only when evidence demands additional work to meet the
capability/verification target. Edge local computation, deterministic algorithms,
specialized solvers, larger neural models and cloud frontier models form one
heterogeneous compute pool. Routing, uncertainty checks, retries and escalation
are not free. Buying the same capability with less total work is also valuable.

## 5. Architecture is not sacred

Q1–Q7 are fixed. Transformer, SSM, graph, symbolic, solver, retrieval, verifier
and accelerator components are means, not ends. At fixed capability, component X
earns its place only if C_without_X > C_with_X. If deleting X does not worsen the
system, delete it. **No component earns permanence.**

The missing comparison symbol in the supplied formula is rendered as `>` in
accordance with the user's accompanying deletion rule. For multiple resources,
use the declared Pareto objective or an explicitly preregistered cost model;
do not silently sum unlike units. Verification authority remains a correctness
obligation even when its implementation changes.

## 6. Edge and cloud

Same principle, different executor/budget constraints:

- Edge: RAM, energy, latency and thermal load.
- Cloud: GPU time, VRAM, energy/query and cost/query.

Every offload must charge both local and remote work. A small local frontend
using uncounted frontier calls is not a low-resource NEUMANN system. Heat and
energy require measurements or explicitly labeled estimates, not parameter counts.

## 7. Frontier capability requirement

The primary task set is G={T: small baseline fails AND frontier succeeds}.
Membership requires actual frozen baseline/frontier observations and independent
verification of the original task—not perceived difficulty or aggregate benchmark
reputation. Model identities, eligible tools, budgets and success conventions
must be fixed before opening data.

Target: Q_NEUMANN(G)≈Q_Frontier(G), while CN≪CF, MN≪MF and EN≪EF.
Define “approximately” and “far less” numerically in a future preregistration,
not after seeing results. Capability/cost frontiers include all failed attempts.
Never infer reasoning recovery from a supplied solution, hidden label or free oracle.

## 8. Fixed core questions

| ID | Question |
|---|---|
| Q1 | Does exploiting structure actually reduce computation? |
| Q2 | Is original correctness/capability preserved despite that reduction? |
| Q3 | Can useful hidden structure be discovered without an oracle? |
| Q4 | Is discovery sufficiently cheap? |
| Q5 | Is the COMPLETE end-to-end system cheaper than strong Direct? |
| Q6 | Do gains persist on unseen problems, new families, open-set conditions and scaling? |
| Q7 | Does a small NEUMANN system recover the real frontier capability gap? |

Q5 charges discovery+execution+verification+retry+routing, with parsing,
reconstruction, transport, storage/caching, cold start and relevant investment
also assigned to complete costs under the frozen accounting convention.

Historical Q numbers are namespaced, NOT retrospectively overwritten. See
`core_question_gates.md` for the mapping and current evidence limits.

## 9. Primary evaluation surface

Capability × Compute × Memory × Latency × Energy × Cost.

Minimize R_total subject to Q>=Q_target at **iso-capability**. Units and scope
remain explicit. Tokens/latency are not FLOPs; RAM/VRAM are not energy; API prices
are not hardware memory measurements. Missing telemetry is UNKNOWN, not zero.
Do not claim a full resource Pareto improvement from one measured axis.

## 10. What NEUMANN 1 is not

It is not merely model compression, a small LLM, a solver router, an LP optimizer,
a tool-use wrapper, a benchmark shortcut or frontier-looking UX.

The target is a **general intelligence architecture minimizing the computation
required for useful problem solving**. These components may be useful internally,
but component success is not proof of the whole-system goal.

## 11. Final test

Take difficult original problems actually solved by frontier systems. NEUMANN
also solves them. At the same useful capability, independently measure much less
compute, memory, energy and monetary cost. Repeat across multiple problem families
and unseen conditions. Only then is the central hypothesis supported at that scope.

Current boundary: none of the retained LP/graph/toy-model experiments establishes
this final test. They remain useful bounded mechanism evidence. The next primary
line builds toward actual Frontier Gap admission/evaluation. The user's subsequent
execution decision is Runtime-0 → Fresh General Holdout → Frontier Gap → Edge
Reality; see [the v106 roadmap](general_runtime_v106.md).
