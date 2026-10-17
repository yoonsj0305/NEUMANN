# NEUMANN 1 | Q3 structural intelligence: exact information lower bound and proof-triggered active observation

**17 October 2026.** Scientific result: **`FROZEN_17_PROBE_INPUT_INFORMATION_INSUFFICIENCY_FORMALLY_PROVEN / ACTIVE_SOURCE_QUERY_CLASSICAL_RECOVERY_WORKS / AUTONOMOUS_NEURAL_NEW_OPERATOR_INVENTION_NOT_PROVEN / ALL_Q1_Q7_OPEN`.**

## Why this is a higher-value test than another synthetic 100%

Our most recent genuine gradient-trained label-free operator selector has **126 frozen weights** and only receives **17 transition delta values** at indices 0 through 16. It passed **29/29** new synthetic operator compositions after full-source recheck, but has **0/2 authentic external family transfer**, and equally informed exact classical QR was cheaper. The important scientific question is whether the current *input representation itself* contains enough information, independent of model capacity. We test a **mathematical impossibility**, not a new training-score variant.

[GitHub preregistration **before generating either adversarial source**](https://github.com/yoonsj0305/NEUMANN/commit/6989ef56445d86aed8ec2b437d195d3688f83531). Sources are two **researcher-designed synthetic adversarial original programs**, NOT independently sourced external heldout problems. No retuning or retraining. Prior frozen 126-weight checkpoint SHA256 **`e43208341dba128ba4c853ab42abe7ad8bd12ffdc292b1649ca0eb0eb74465ff`** checked unchanged.

## Exact two-source construction and mathematical theorem

Each source has a distinct named, 2-Int `R(n,s)` and **3 original universally quantified Horn clauses**: `R(0,0)` initialization, a guarded recursive transition `n'=n+1`, and an unreachable-state false rule.

| Original source | State transition delta | Its actual reachable state at step n=18 | Forbidden state at n=18 | Sound source-specific invariant |
|---|---|---|---|---|
| P0 | `s'=s+1` | `(18,18)` | `(18,19)` | `n>=0 AND s=n` |
| P1 | `s'=s+1+ite(n>=17,1,0)` | `(18,19)` | `(18,18)` | `n>=0 AND s=n+max(0,n-17)` |

For both source ASTs, the input to the previously trained model `source_probe(source,nmax=17)` is **identical: 17 ones**. For both sources the frozen learned output is identically `["N"]`, i.e. `s=n`. **P0: all 3 original clauses UNSAT under negation = complete valid invariant. P1: first clause UNSAT, transition SAT and false-goal SAT = invalid invariant.** Correct explicit proof controls **3/3 for each own source**, and the crossed source-specific candidate fails.

**Stronger model-independent theorem:** There is **no common inductive interpretation of R** that proves BOTH full originals. Original P0 reachability forces `R(18,18)`, its error clause forbids `R(18,19)`; P1 reachability forces `R(18,19)`, its error clause forbids `R(18,18)`. Contradiction. We verified this in **two independent ways**:
1. Native Linux Z3 **4.13.3.0** on a single system comprising both complete untouched sets of **3+3 actual quantified Horn clauses**, with the two predicate names normalized to one shared predicate: **`UNSAT`**. Note these are *researcher-created* originals; the source text changes only by alpha-renaming predicate names in the joint logical experiment, not by rewriting arithmetic.
2. [GitHub Actions **#38997942152**](https://github.com/yoonsj0305/NEUMANN/actions/runs/38997942152) runs a **separately authored Z3 4.13.3 exact six-Horn theorem kernel** and returns **`UNSAT`**, archival independent CI artifact ID **12088221409**. Formatting of this independent re-generated source differs from the local source strings but original logic is mathematically equivalent. [GitHub theorem script](https://github.com/yoonsj0305/NEUMANN/blob/research/core35-rusthorn-real-source-gate-20261016/research/evidence/fgsr-q3-active-information-20261017/original_six_horn_theorem.py).

Hence **ANY deterministic proposer restricted to only this 17-number source representation must fail on at least one of these two sources**, irrespective of neural parameters, optimizer or classical reasoning budget. For a uniformly random unknown member of the pair, even a randomized proposer with only that identical input has expected complete-proof success at most 1/2. This result does **NOT** constrain an architecture that can inspect original Horn AST or its safety-goal content, or request additional source observations.

## What breaks the information bottleneck

The first additional source delta query, at n=17, returns **1 on P0** but **2 on P1**. A research-predeclared **classical** piecewise candidate-grammar `n+max(0,n-k)` together with full-original Z3 verification recovers both source-specific certificates **2/2, 6/6 original Horn clauses UNSAT**. This does **NOT** mean the model invented the `max` operator family; it was provided by the researcher and selected by deterministic arithmetic.

We also implemented and tested a **proof-triggered** end-to-end decision loop on these already opened sources:
1. Frozen trained proposer reads 17 deltas, emits a typed AST.
2. Independently verify **every original clause**.
3. If certified, stop and request **zero** extra observations (P0).
4. On proof failure only (P1), request **one** additional source delta, update with predeclared classical macro, and verify all original clauses again.

| Frozen implementation | Original case P0 | Original case P1 | Additional source observations in total |
|---|---|---|---:|
| Frozen trained 126-weight head alone | **3/3 certified** | FAIL, 1/3 only | 0 |
| Head → proof → one extra probe if needed → classical macro | **3/3** | **3/3** | **1** |
| **Stronger CLASSICAL-FIRST control**, with no model call | **3/3** | **3/3** | **1** |

**The classical-first controller uses zero neural inference and matches capability and active-query count.** No NEUMANN learned problem-solving or efficiency advantage is established. The current one-extra-probe choice is hand-chosen for this pair, **not automatically derived from arbitrary solver counterexamples**. That general counterexample→query policy is still unimplemented/unproven.

## Falsification, reproducibility and status

**14/14 fail-closed regression tests PASS** on original source variants: exact 17-probe identity, 18th-probe separation, frozen checkpoint SHA, independent original union Horn UNSAT, hand-certificate pair validity and cross rejection, actual frozen model identical AST and failure, shifted bump threshold, deliberately reachable false-goal mutation, unsupported adaptive query, proof-triggered stop/no extra query, classical zero-neural control. There was one syntactically malformed, unused Python function in the initial draft before original programs were first generated/tested, corrected before evaluation. Later revised the controller from eager extra probing to actual **proof-triggered** probing; initial eager receipts are a development intermediate, not a clean heldout performance claim.

Reproducible downloadable ZIP **`NEUMANN1_INFORMATION_LIMIT_ACTIVE_PROBING_20261017.zip`**, **24,338 bytes**, SHA256 **`266d01381d279e4023724208f071b09b2fedffea3c361687660596e5b58df364`**. **12 members**, ZIP CRC PASS, **11/11 tracked SHA256 manifest entries PASS**. Includes original two complete symbolic Horn SMT2 texts and hashes, source parser and previous trained frozen 126-weight `.npz` checkpoint, two execution scripts, proof-triggered decision controller, local original 6-Horn information theorem, first actual raw evidence and controller receipts, 14 original-mutation tests, read-only audit and README. Fresh entirely separate directory audit reproduces two original sources, all six original classical controls, and 14/14 negative controls, without GPU, retraining, network or paid models. Native Z3 **4.13.3.0**.

**NEUMANN 1 architecture decision:** `SOURCE_OBSERVATION_BUDGET_IS_PART_OF_REASONING`. Adopt **`typed source graph → hypothesis → independent proof → failure diagnosis → adaptive source query or richer IR → re-hypothesize → independent proof`**. Stop using a fixed 17-delta vector as an allegedly universal source representation. Restrict extra querying to high expected information value and keep fail-closed on unsupported math. Under the actual tested pairs, **classical-first is strictly better when computation cost matters**; no justification to train/execute another fixed-basis model here.

**Remaining strictly unproven:** autonomous learning of *new* operator/relational structure, semantic learning transfer to a truly different externally sourced problem family, and frontier-level accuracy at minimum real compute on robust equal-information benchmarks. **Q1–Q7 all OPEN**. This experiment closes only one bounded, but general mathematical **negative** question: the fixed-size probe interface's identifiability failure.
