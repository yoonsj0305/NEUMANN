# NEUMANN 1 | G2 first native-expert screen and alternate CHC cross-solver proof

2026-11-06. Real external source benchmark owner: **SyGuS-Org/benchmarks** at pinned original commit `13c8deb68a873635879c9a69bc78caebd340f646`.

## Executive research decision

**No NEUMANN learned-model call was made.** Two *mathematically distinct* published source groups were selected from upstream filenames and Git blob hashes before original source contents were opened, with deterministic source identities frozen in `docs/experiments/G2_NATIVE_RESIDUAL_24_SOURCE_METADATA_FIRST_PREREG_2026_11_06.json`. They are not Q6 learned cross-formalism transfer.

**Twenty-four previously unread originals**: 12 finite 64-bit bit-vector program synthesis problems, 12 integer transition-system safety-invariant problems.

**Confirmed final classical source baseline:**

| Source cohort | Original source certified by cvc5 | Additional post-first independent source theorem | Stronger independent Z3 Spacer |
| --- | --- | --- | --- |
| BV PBE 12 originals | **12/12** programs independently verified on 99 original TRAIN and 1 withheld LAST examples per source | Not needed | Not run |
| Integer safety INV 12 originals | Original first **7/12** with all three universal induction checks; after old negative numeral SMT parser correction **9/12** | Two additional human-derived invariants verified 3/3 UNSAT, and one **unreachable-to-safety counterexample SAT** (unsafe one-step, not solvable) | **11/11 safe**, **1/1 unsafe**, all twelve determined with zero unknown and zero student training |
| Total registered originals | 24; at least 21 with cvc5 independent original source proofs after correction | Remaining original three classified by independent proof | 24/24 original cohort mathematically classified by appropriate existing native specialized classical tool |

## Data provenance and original unmodified first receipts

- Initial selected-source [original first #42167219443](https://github.com/yoonsj0305/NEUMANN/actions/runs/42167219443). Native 64-bit PBE first: **12/12** independently original-ground verified, SHA256 `45bb7b75af101a334f1eff393483f03a3bfc017e0077405599c21cf1041c3d7b`. Native INV first: **7/12** independently proven, **2** 12-second timeouts, **1** `infeasible` return, **2** checker parser failures on legacy negative numeral, SHA256 `df7486f738cc47aa59b3fc91569ca73ccebb53da0b06ad4892c8f74e16d96229`.
- The FIRST GitHub Actions jobs both had red conclusions solely due to a final bash log **`$COHORT_FIRST...` unbound variable**; the original finished source scoring JSONs and SHA256 were generated and preserved. The evidence has not been regenerated, replaced or masked as success.
- [Immutable first read-only audit #42167502277](https://github.com/yoonsj0305/NEUMANN/actions/runs/42167502277) **PASS**. Matched all 24 original source Git blobs, original per-source order and supported/timeout statuses without rerunning original synthesis.
- [Negative numerals source-independent SMT audit #42167853857](https://github.com/yoonsj0305/NEUMANN/actions/runs/42167853857) **PASS**. Both original candidates `minor1.sl` and `minor2.sl` byte-locked, old `-N` independently normalized into SMT `(- N)` in the checker only. Each candidate passes universal init/induction/safety, mutant false invariants fail. This upgrades the **separate audit** count to **9/12**, while the original first stays 7/12.
- [Analyst mathematical post-first proof #42168295110](https://github.com/yoonsj0305/NEUMANN/actions/runs/42168295110) **PASS**. Exact source:
  - `fib_19.sl`: analyst constructed invariant for piecewise `y = max(x,m)` with (0\le x\le n\), verified all universal obligations by UNSAT.
  - `gcnr_tacas08.sl`: analyst constructed linear cone and conserved state `w=x`, `z=10w`, `x<=y<=100x`, verified all universal obligations by UNSAT.
  - `jmbl_matrix2.sl`: **UNSAFE**, concrete original initial state `m=a=j=k=0`, one legal transition to `m'=a'=k'=1, j'=0`, and `not Post` is SAT. Mutant transition is UNSAT. No universally safe inductive invariant can exist for this original source.
- [Stronger real Z3 Spacer independent native classical #42169011956](https://github.com/yoonsj0305/NEUMANN/actions/runs/42169011956): exact original source Pre/Trans/Post compiled to Horn clauses, two source-free safe+unsafe controls before originals, correctly proved **11 UNSAT** and **1 SAT** across all 12 originally registered integer problems. Z3 program receipt SHA256 `b1a22013aae9e2effc04dff9581de7c3200e8829a09b3adcbfd9ff76e1180414`. Source runs notably include `fib_19.sl` **39.887 ms** and `gcnr_tacas08.sl` **984.888 ms** on this Actions runner, compared against cvc5's **12-second cap** on each. These are per-process runtime, **not** comparable end-to-end training/energy and no 10× model claim.

## The actual abstraction and anti-cycle result

The first native cvc5 failure was *not* proof of intrinsically hard learned frontier tasks. It was **algorithm mismatch** and a **distinct safety satisfiability question**, plus old SMT syntax.

- String PBE G1: cvc5 8/8 real original, so no learned-exclusive capability headroom.
- BV program PBE G2: cvc5 12/12, same conclusion.
- Integer safety induction G2: specialized CHC engine Z3 Spacer 12/12 classified, so no learned-exclusive capability headroom under the registered original safety property.

In contrast, the analyst supplied two post-first invariants after reading source. They were valid mathematical witnesses but **not** autonomous algorithmic learning, proof of new structure invention, genuine unseen transfer or reduced total compute. They must never be promoted to Q3 PASS.

**Hard STOP**: Don't train neural invariant proposers on these 12 already-opened originals to claim new frontier ability; keep them as compiler/proof regression only. Don't re-run the 12 with many cvc5 flags or call that learned novelty.

## What to build next (one decisive hypothesis)

Use the **2025 CHC-COMP** externally published corpus (different benchmark ownership and original CHC-first format) and **first freeze filename/Git blob sample**, **then** execute strong native Z3 and ideally independent peer engine against exact same sources, with audited dialect/syntax. Pick a genuine **budget-unresolved source with proof acceptance**, not unsat mistaken as no program and not source parser errors.

Only after a genuine classical residual exists should one own-weight program proposal generator be trained on disjoint CHC-family training sources to **invent a typed reusable invariant/lemma**. Validate it independently on a different author's new CHC first set. Compare to equally-rights classical GP/CEGIS and native solver, including amortized training + inference + proof and fallback. The system should default to proven native classical route if it solves the task.

### Research status

`G2_ORIGINAL_SOURCE_NATIVE_PROOF_DISCHARGE = PASS, 24/24`

`G2_NEUMANN_GENERATIVE_LEARNING = NOT RUN`

`G2_GLOBAL_INDEPENDENT_FORMALISM_TRANSFER = NOT PROVEN`

`G2_FIRST_EXPERIMENT_SOURCE_INTEGRITY = PASS` (despite first CI shell red; SHA-bound audit)

`Q3/Q4/Q6/Q7 = OPEN`.

**Scientific guardrail:** 24/24 native = a stop on **capability-only novelty** within these originals; it does not preclude a matched cost improvement with same original rights, but G2 did not meter any model training and cannot claim cost superiority.
