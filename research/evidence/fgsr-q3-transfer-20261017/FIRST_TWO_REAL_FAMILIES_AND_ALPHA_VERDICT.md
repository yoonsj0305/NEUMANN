# NEUMANN 1 | Q3 cross-source learning transfer first actual frozen gate: 0/2; source alpha-IR regression 2/2

**2026-10-17 KST. Current scientific verdict: `CROSS_SOURCE_TRANSFER_NOT_ESTABLISHED / SOURCE_NAME_IR_INVARIANT_CONFIRMED / ALL_Q1–Q7_OPEN`.**

## 1. Two real sources selected and frozen BEFORE reading actual source bodies

[PRE-SOURCE preregistration](https://github.com/yoonsj0305/NEUMANN/blob/research/core35-rusthorn-real-source-gate-20261016/research/evidence/fgsr-q3-transfer-20261017/PREREG_NEW_SOURCE_FAMILIES.md) committed **`bdf8b4704ea3b3394c3148cf9e84fab139f1bf3e`**, before fetching the full original SMT2 bodies. Data are externally published CHC-COMP 2026 at upstream commit `b4fa7a708e5863bbcdb5de50d692ead3a67cbedc`. The pretrained **15 actual trained coefficient weights** and human-designed source-only multi-relation operator grammar were frozen. Explicit goal: automatic whole-original proof on new external source group, no adapted templates, no manual certificates, no retries.

[Actual GitHub Actions #38988255737](https://github.com/yoonsj0305/NEUMANN/actions/runs/38988255737), raw evidence artifact ID **12083662834**, code [frozen_transfer_gate.py](https://github.com/yoonsj0305/NEUMANN/blob/research/core35-rusthorn-real-source-gate-20261016/research/evidence/fgsr-q3-transfer-20261017/frozen_transfer_gate.py), exact Z3 4.13.3:

| Preregistered authentic source | Original source SHA256 | Actual first result |
|---|---|---|
| `hopv/lia/mochi/sum_000.smt2` | `2b6a2e854b12c222def1ceacacba3b93d9b739f4474ad2afba1c0d66d695a827` | **`ABSTAIN_UNSUPPORTED_SOURCE`**. Current old parser falsely depends on relation names beginning `inv_`, so did NOT attempt expensive SMT or model inference |
| `eldarica-misc/LIA/llreve/fib_safe.c-1_000.smt2` | `0563111c711d49ccc642e07e835ad1f981abe4e914b8703aad262081ebd6033f` | **`BLOCKED_OR_ERROR`** logged with explicit `ValueError:NO_SOURCE_RECURSIVE_LOOP_DETECTED`. Actual program uses a recurrence outside the frozen model's `t'=t-1; acc'=acc+k*a+m*t+n` extraction contract. This is a **model-domain transfer failure** but does not prove the program's mathematical impossibility |

Correct denominator **0 certified / 2 preregistered**; no last-minute source replacement, no retries, no template tuning on opened targets. Total source retrieval+domain checks 116.929ms and 127.707ms respectively, excluding GHA setup; no neural coefficient proposals or source solver calls were justified. First status is clean abstention; second is recorded **engineering status BLOCKED_OR_ERROR** and research classification unsupported operator, not silently relabeled as a solver or proof failure. An 8-second raw classical baseline was to be executed *only if* domain supported, so none can be claimed. Pretraining contamination unknown. Q1–Q7 OPEN, **no actual new source-family transfer**.

## 2. Address only *surface* dependence on an ALREADY OPENED development source

Without regrading the two heldouts, implemented [predicate_alpha_normalizer.py](https://github.com/yoonsj0305/NEUMANN/blob/research/core35-rusthorn-real-source-gate-20261016/research/evidence/fgsr-q3-transfer-20261017/predicate_alpha_normalizer.py). It parses positive-arity `Int... -> Bool` declarations and maps every symbol name to a canonical `inv_rN`, preserving a reversible map and rejecting unsupported sorts/shadowing. No semantic operator is invented or learned. Tested using ONLY the already-opened genuine external `square_twice_safe.c-1_000.smt2` source and one systematically alpha-renamed equivalent version with five entirely different predicate names, without modifying frozen learned weights or 229-class operator grammar.

[Actual GitHub Actions #38988519493](https://github.com/yoonsj0305/NEUMANN/actions/runs/38988519493), immutable raw evidence artifact ID **12084395538**, [metamorphic executable](https://github.com/yoonsj0305/NEUMANN/blob/research/core35-rusthorn-real-source-gate-20261016/research/evidence/fgsr-q3-transfer-20261017/alpha_metamorphic_regression.py):
- Original genuine source SHA256 `f62d0fb72140e6bd7e953dcebd131a4e9498cc9c0c150588ca79944962e9e748`: **5 auto-generated relation definitions, all ORIGINAL 9/9 verified by source-scoped independent SMT checker**, 41 Houdini solver queries, 52 surviving clauses, numerical learned relation coefficients `(1,-1,0,0,0)` for all three source-recursive relations, check wall **352.625ms**.
- Alpha-renamed semantically equivalent source SHA256 `1e81b4ed5f1985e3fcca185f29dc74b4da3cbcfcac065b02d6aa0cb43c42e28f`: **five renamed original relations, all 9/9 SMT certified**, 42 Houdini solver calls, 52 surviving clauses, same frozen learned numeric relation, check wall **358.817ms**.
- **Both canonical source strings exactly identical** (normalized source SHA256 `134d30b790dcc74f4a60fbbf80a8c64149dfb9a3ceb6c2815020423b903268cf`). Different solver query counts reflect solver/iteration specifics, not different semantics. No retraining. This is a **metamorphic equivalence regression, NOT different semantic source-family learning transfer**.

## Cost and next genuine scientific gate

A mathematical theorem prover with name-sensitive relation handling is artificially narrow; alpha canonicalization is now implemented and demonstrated. It does **not** handle higher-order Fibonacci-style recurrences. The current learned coefficient head still has a human-supplied polynomial family and a teacher using exact classical algebra. Such an operation, even when learned, is not evidence of autonomous novel operator discovery; strong classical exact arithmetic remains the equal or better source-dependent option.

Next true question: freeze **before new source access** a learner that emits *compositional operator ASTs* / relationship structure rather than only numbers in a given expression, without source-specific rules; train on multiple upstream semantic families, evaluate on a distinct source-family holdout with all original Horn clauses independently certified; compare classical constraint synthesis and neural-ablation plus total computation (including training), do not conflate compilation robustness with learned semantic transfer. **No reliable time-to-success can be inferred** from current 0/2 results; gate admission depends on new verified competence, not more similar opened-source tweaks.

**STOP further science claims on the two now-opened original holdouts. Preserve their first 0/2 as historical results.**
