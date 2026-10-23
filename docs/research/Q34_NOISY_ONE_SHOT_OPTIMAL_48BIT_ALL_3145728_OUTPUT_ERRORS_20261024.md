# NEUMANN 1 Q34 | Optimal one-round discovery of unknown Boolean operator under adversarial observation noise

**Research status 2026-10-24.** Inherits [PR #562](https://github.com/yoonsj0305/NEUMANN/pull/562)'s verified complete 65,536/65,536 truth-table inference and ANF/BDD compiler using a single 4×4 toroidal controlled source. This extension is **not** a neural-model breakthrough, novel mathematical theorem, physical silicon result, or frontier parity claim. It gives tight, independent error-correction proof and actual machine execution for a sharply bounded unknown-local-operator identification task.

## Problem and semantic observation rights

A black-box synchronous uniform deterministic cellular automaton evolves a controllable binary torus. Each next-state output bit equals the SAME unknown Boolean function `f:{0,1}^4 -> {0,1}` of its known southeastern 2×2 neighborhood. There are `2^16 = 65,536` distinct possible unknown full rules. Learner sees the complete next-state grid, but at most `t` adversarial next-state output observations are flipped, and `e` observations are explicitly erased (known positions). Input state, orientation, locality, stationarity, and toroidal wrap are assumed reliable and known. No actuator noise, unknown neighbor geometry, stochastic state transition, asynchronous updates, or adversarial input corruption. A 'query' is one full-grid transition. Output bit cost counts all simultaneous observed binary next-state cells, not processor instructions or joules.

Previously, the 4×4 grid encoded by `0x12b7` has the 16 possible 4-bit 2×2 neighborhood signatures each EXACTLY once. We tile it horizontally `r` times onto a controlled 4×(4r) torus. Every local signature then occurs EXACTLY `r` times (verified by two independent grid construction algorithms), giving a repetition code for each of the 16 *independent unknown truth bits*.

## General tight information/coding lower bound

For any two possible unknown rules that differ at exactly ONE truth-table input word `u`, their observed uncorrupted full-grid outputs differ at exactly those cells whose local 2×2 context is `u`. Let its frequency be `m(u)`. A binary output code can reliably disambiguate all such rule pairs under up to `t` adversarial bit flips and `e` declared erasures only when its minimum pairwise Hamming distance `d_min >= 2t+e+1`. Thus EVERY of the 16 possible contexts must appear at least `2t+e+1` times, and any fixed controlled one-query observation design needs at least

```
B_min(t,e) = 16*(2*t + e + 1)
```

observed binary output cells. Our horizontally tiled universal 4×4 torus has exactly the required frequency for every context and therefore attains the lower bound with **one** simultaneous observation query. The majority decoder recovers all 16 truth bits and then GF(2) Möbius transformation synthesizes an actual executable AND/XOR algebraic-normal-form program; no full-target function table is supplied as a candidate list.

The lower bound is **for single synchronous observed state under given binary local-output mechanism**; it is not a global information theoretical bound for arbitrary multi-query adaptive observation, side-information, structured rule subclasses, soft-output analog observables, or other physical sensors. Mathematics are known elementary minimum-distance/repetition-code facts and de Bruijn-type covering torus, no new theorem priority.

| Guarantee | Exact minimal output observations | One torus geometry | Evidence |
| --- | ---: | --- | --- |
| No errors | 16 | 4×4 | Inherited exhaustive [PR #562](https://github.com/yoonsj0305/NEUMANN/pull/562) |
| 1 declared erased next-state bit | 32 | 4×8 | independent coding + random erasure tests |
| 1 arbitrary flipped next-state bit | **48** | **4×12** | full 65536×48 exhaustive source experiments |
| 1 arbitrary flipped + 1 declared erased bit | 64 | 4×16 | independent 20,000 sampled joint corruption tests |
| 2 arbitrary flipped next-state bits | 80 | 4×20 | 10,000 sampled primary + 20,000 independent random two-flip tests |

## Actual executed computation and scope of exhaustion

The primary no-dependency executable `research/q34/optimal_noisy_boolean_operator.py` does:
- Reconstruct every one of 65,536 possible unrestricted 4-input Boolean operator truth tables from the toroidal source.
- For **each** operator, apply all 48 possible distinct single next-state bit flips of the observed one-step 4×12 output; do a true majority decode and compare against complete original source semantics.
- Total **3,145,728 corrupted whole-state replays; 3,145,728 restored correctly, zero incorrect**.
- Independently compile EVERY operator into ANF and prove its outputs at all 16 possible inputs, giving 1,048,576 exact program semantic executions for this extra end-to-end check.
- Test strict 2-replica negative control where two full-rule codewords with just one different truth-table bit differ in two output positions. The adversary can flip ONE bit from either and produce the SAME ambiguous observation. Thus 4×8 cannot guarantee correct one-bit flip recovery.
- On a 4×20 tiled torus, run additional 10,000 deterministic sampled unknown operators × two arbitrary output-bit flips. Correct exact 65,536-operator family inference under the sampled conditions.

The independent second implementation `research/q34/independent_noise_distance_audit.py` shares **NO decoder/geometry routines** with the first. It constructs direct local input-signature observation groups, rather than grouping repeated rows, and decodes from per-context grouped majority. Independently confirms all 65,536 unknown rules uncorrupted, 49,152 one-bit-error cases (every 48 location for 1,024 uniformly spaced rules), 60,000 additional sampled erasure / flip+erasure / two-flip tests, and the 2-replica impossibility witness.

Initial local execution on 2026-10-24 completed:
- Primary Python exact proof: ~7.34 process CPU seconds; independently run 65,536 rules ×48 flips and 65,536 compiled ANF×16 full-domain checks, zero false.
- Independent complete source-group audit: ~2.26 process CPU seconds; true 49,152 single flips and 60,000 extra randomness controls, zero false.
- All programs Python standard library; no GPU, paid API, training datasets or model weights. Measured CPU is for these proofs, **not** frontier total inference/economic cost vs other AI models.
- Standalone source files executable: `python research/q34/optimal_noisy_boolean_operator.py` and `python research/q34/independent_noise_distance_audit.py`. CI uses separate assertions, preserves SHA of first outputs.

## Why this matters and why Q3 cannot be falsely closed

The new theorem is not mathematically original; its practical contribution to this specific NEUMANN bounded mechanism is that **source control + information-optimal observation + correctable coding + fully verified executable new unknown semantics** are composable at absolute known minimal output measurement budget. This *removes a fragile measurement assumption* from the real unknown Boolean operator induction test. It does not teach a neural network to **invent new parser syntax**, discover neighborhood semantics without assumptions, generalize to nonlinear continuous domains or outperform a strong symbolic classical solver. In fact our fastest solver IS a human-programmed classical coding/ANF process.

Scientific admission:
- `Q34_BOUNDED_NOISE_OPTIMAL_1_BIT_FLIP=PASS`.
- `Q34_65536_RULES_ALL_48_FLIP_CORRUPTIONS=PASS`.
- `Q34_BOUNDED_UNKNOWN_OPERATOR_EXECUTABLE_ANF_COMPILATION_ALL=PASS`.
- `Q34_OBSERVATION_INFO_LOWER_BOUND_TIGHT=PASS`.
- `Q34_TWO_FLIPS_SAMPLED_PLUS_THEOREM=SCOPED_PASS`; not an exhaustive all C(80,2) errors ×all rules empirical experiment.
- `G1_MODEL_AUTONOMOUSLY_NEW_ATOMIC_SEMANTICS=HOLD`; `Q3_GLOBAL=OPEN`; `Q4_FRONTIER_ALL_IN_10X=OPEN`; `Q6/Q7=OPEN`.

Next genuine Q3 gate is independently authored original task families with a learned **variable-length DEFINE/REUSE/REWRITE program** showing *new learned useful structures, equal-rights/compute stronger classical comparisons*; this bounded CA coding finding is a supporting verification substrate only.
