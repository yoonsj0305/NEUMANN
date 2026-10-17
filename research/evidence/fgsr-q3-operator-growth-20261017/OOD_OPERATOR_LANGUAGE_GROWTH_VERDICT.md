# NEUMANN 1 · P2 OOV abstraction-language boundary and source-driven grammar growth

**2026-10-17 KST | Executed locally, CPU | ALL Q1–Q7 OPEN.**

## Key difference from previous 70/70 composition test
The previous frozen 126-weight neural AST selector solved 70/70 new combinations of **seven researcher-given source operators**, but it cannot propose any operator outside them. Instead of enlarging the same toy test or retuning the learner, this test checks **exactly where the seven-operator language becomes inadequate**, and whether a fail-closed hybrid system can construct a new useful abstraction macro from the *actual original source transition*.

### Method frozen BEFORE new source generation
[GitHub pre-OOD preregistration](https://github.com/yoonsj0305/NEUMANN/commit/62465089b12206fb9622b430d0d149f4321e646d) fixed:
- **Unchanged pretrained head**, actual learned checkpoint SHA256 `990c7ba0b96e017180c35388da622ab292cb9d270d0e8a5fc43b0d65d72d21a3`, 126 scalar parameters, seven previous AST leaves `n,n²,n³,n mod 2,n mod 3,ramp(n-3),ramp(n-6)`. No new gradient updates.
- Exactly TWO controlled researcher-authored **synthetic** three-clause Horn programs, with actual hidden mathematical invariants `s=floor(n/5)` and `s=floor(n/7)`, original transition `s'=s+ite((n mod k)==k-1,1,0)`, n→n+1, initial n/s=0 and a concrete forbidden state at n=35. **The target formula is not displayed in the safety goal**, but the transition AST does contain the known period, and the **researcher knew the target formulas when designing the problems**. This is NOT a blinded external real-source holdout, nor unseen operator-family discovery.
- OOV test: exact 17×7 primitive-delta integer matrix; append source's exact 17-delta signature and compute exact **rational matrix rank** via SymPy, not a soft neural classifier. Full rank jump proves impossibility for ALL linear combinations of those seven known leaves over the 17 observations.
- Bounded **RESEARCHER-SUPPLIED classical** grammar-expansion family `FLOOR_DIV(n,k)`, k from 4 through 11. Pick source-signature-matching candidates and then independently refute negations of **all three original universally quantified SMT-LIB Horn assertions** using native Z3 4.13.3. No candidate may pass on sample fit alone.
- Compare frozen model alone, exact old seven-leaf classical span, new macro synthesis; verify zero, wrong neighboring divisor and artificially reachable safety goal all cause rejected proof.

## Actual first result

The first implementation hit **one Python syntax error before any source programs were executed or receipts created**; corrected an unmatched bracket, no experiment logic or sample tuning. Then exactly the registered two new source cases were executed once.

| OOD original | Frozen 7-leaf trained model | Old 7-primitive exact linear span rank | Automatic NEW bounded macro | Unchanged original proof |
|---|---|---|---|---|
| `s=floor(n/5)` | **0/3**, transition rule SAT | 7→8, cannot represent | generated `(div n 5)` | **3/3 UNSAT** |
| `s=floor(n/7)` | **0/3**, transition rule SAT | 7→8, cannot represent | generated `(div n 7)` | **3/3 UNSAT** |

Note: frozen model initial and safety conditions were UNSAT and transition condition SAT for both, so `0/3` here describes **zero complete three-clause proofs**, NOT zero individual obligations. The first frozen model guessed empty leaf set, second guessed `RAMP_6`.

Exact rank `rank(B)=7`, `rank([B|y])=8` for both original 17-point transition signatures. This is a **mathematical impossibility certificate for the fixed seven-leaf vector span**, not proof that no more expressive operator AST or arbitrary neural architecture could represent either function.

- Classical macro enumeration successfully selected k=5 and k=7, and a second independent source-reparse SMT verifier certified **2 original × 3 clauses = 6/6 original negative checks UNSAT**.
- Tamper/falsification: fixed `s=0`, wrong adjacent divisor and changing goal to an actually reachable state were all detected by a SAT counterexample, **6/6 rejected**.
- **Safe compute-first router**: exact OOV span test before invoking neural head. Both sources fully proven with **0 neural forwards**; bounded unsupported source and an unknown period outside k=4..11 yield explicit ABSTAIN. Six scoped regression checks **6/6 PASS**. New grammar search **classical**, not learned.
- Actual first two-source experiment wall **101.987ms** on local CPU, includes frozen-model baseline, rank, macro search, native-Z3 source checking and negative controls, excludes past model training/dependency installation. Do not compare this wall with full frontier inference, energy or external source solver.
- Equal-information classical solver **can** and did generate these same macros from the same source, so no proof of learned necessity, learned cost superiority or 10× NEUMANN advantage.

## Replay and immutable evidence

**Reproducible downloadable artifact:** `NEUMANN1_OOD_ABSTRACTION_GRAMMAR_GROWTH_20261017.zip`, **22,787 bytes**, SHA256 **`12c106f7fb3e1f43853bdfbe4dfd15b6bf1295e57cc36df5896ec932927d326a`**. ZIP CRC PASS. Includes unchanged 126-weight `.npz` checkpoint, previous engine, full experiment implementation, original source files 2, first frozen-run JSON, independent audit, source-only safe hybrid router, six fail-closed tests, exact SHA256 manifest **13/13** tracked payloads, original safe router receipt and analysis README.

Audited in a **fresh independently extracted directory** (not code state from development):
- `python audit.py` **PASS**, original Horn obligations **6/6**, exact rank **2/2**, source/macro integrity and falsification **6/6**.
- `python -m unittest -v test_fail_closed`: **6/6 PASS**, including mutated actual reachable goal, unsupported source, out-of-enumeration operator and known-operator no false novelty.
- SHA256 manifest **13/13 PASS** before AND after audit.

The complete source code and numerical model are in the reproducible ZIP; repo retains immutable science provenance and decision boundary.

## Scientific decision

**`SYNTHETIC_SOURCE_DRIVEN_GRAMMAR_EXPANSION_CLASSICAL_PASS / OLD_VOCABULARY_PROVABLY_INSUFFICIENT / LEARNED_NEW_OPERATOR_INVENTION_OPEN / AUTHENTIC_SOURCE_FAMILY_TRANSFER_OPEN / GLOBAL_Q1–Q7_OPEN`.**

This is an important *engineering* step: the system can detect that a trained proposal language is mathematically inadequate, **abstain rather than silently repair a neural output**, generate an entirely new **macro instance** from a predeclared operator family, and accept it only if it proves the original source. It has not learned to invent its **operator family**. Q3 closure requires a trained, frozen generator of new operator/schema types verified on genuinely different real source families and a gap against strong classical. Do not scale more synthetic period k examples; classical exact grammar expansion already dominates.
