# NEUMANN Q3: automatic source-based 2-adic error-squaring proofs for 4 opened SMT-LIB originals

2026-10-23 KST. **Dedicated CI full success** [GitHub Actions #39891323395](https://github.com/yoonsj0305/NEUMANN/actions/runs/39891323395). GitHub [PR #532](https://github.com/yoonsj0305/NEUMANN/pull/532). Previous independent original G0 control: [PR #531](https://github.com/yoonsj0305/NEUMANN/pull/531) first source trial #39889561531. Original external Jochen Hoenicke SMT-LIB repository `SMT-LIB/benchmark-submission-2023` frozen `7f993a017850ba547c6ea19a1bf3b54adf54a449`, source family `QF_NIA/20230328-sqrtmodinv-hoenicke`.

## Genuine new verified result, not just test count
All **four** official previously opened source originals `modInv8.smt2, modInv32.smt2, modInv64.smt2, modInvFull.smt2` had direct Z3 UNKNOWN and pinned cvc5 UNKNOWN under 5s caps in first #531. On the SAME original, before editing, this new source-template conditional classical proof synthesized the auxiliary quantity `e_i=1-denominator*inv_i`. Exact Z3 original assertion AST required positive original clause `denominator mod2=1`; `inv0=3d`; `inv1=4*div(inv0,4)+(inv0+2)mod4`; all genuine Newton update clause AST `inv_j=inv_(j-1)*(2-d*inv_(j-1))`; final genuine original required `NOT(d*last mod M=1)`. Every original source blob was checksum-pinned. If any clause mismatched, return UNKNOWN and DO NOT assert a proof.

Universal base theorem: every integer d is d=16q+r; for odd d, odd residue r∈{1,3,5,7,9,11,13,15}. `inv1(d)=48q + 4*floor(3r/4)+((3r+2)mod4)` so d*inv1(d) mod16 equals r*inv1(r) mod16, which equals 1 in all eight exhaustive cases. Independent separate Z3 QF_BV 4-bit finite-state UNSAT counterexample check. Hence for ALL odd integers d, `16|(1-d*inv1)`.

Exact ring identity `1 - d*[x(2-dx)] = (1-dx)^2`, checked by Z3 polynomial simplifier and an intentional altered-constant negative control. Therefore for k further source-matched Newton steps `2^(4*2^k)|(1-d*last)`, for all integer d, including negatives. All four original required final moduli are powers of two no greater than that proven modulus, covering **8, 32, 64, 256 bits** respectively. Add ONLY the independently mathematically proven final congruence as a lemma to the unchanged full original source: Z3 returns UNSAT, and checksum-pinned independent cvc5 1.4.2 independently confirms UNSAT of original plus lemma for all four.

## First-run identity
- First executable proof receipts JSON SHA256 `7843b04070da29ce836ebcd0560127fe1e3469e6e4940ee7092a5d25adc9a372`.
- Uploaded GitHub Actions artifact ZIP SHA256 `425952da40224c5b4b99d0feeda087731cd3a86e0a2a0ccf9329f175e6ee618b`.
- All four cases `ORIGINAL_UNSAT_CERTIFIED_BY_2ADIC_SOURCE_INVARIANT`; 0 wrongly accepted by the actual code path. Dedicated source-to-lemma verifier success; general mainline CI merge not asserted.

## Scientific boundaries
**This is one algebraic mechanism successfully applied to four program instances of the same previously opened author/family**, NOT four independent learned abstractions. The simple Newton-Hensel error-squaring theorem is established classical mathematics, not our novel mathematical discovery. New source-to-lemma algorithm was human-authored AFTER these originals were opened and G0 baseline failure observed; development-only, no fresh first-blind neural transfer. The proof has unbounded-integer mathematical validity; measured first-run Z3/cvc5 UNKNOWN does not prove universal commercial solver incapability or an overall 10x lifecycle CPU speedup. Independent cvc5's check of *source plus valid lemma* does not constitute an independent discovery of the lemma.

Retain this as useful evidence of **new state variable being decisive for automated proof**, not evidence of learned unique primitive. Future learned NEUMANN must propose such a variable from source without human-made conditional template; frozen same-rights expert classical with access to 2-adic techniques remains strongest comparator.

**Verdict:** `Q3_CLASSICAL_SOURCE_DERIVED_AUX_RELATION=SCOPED_PASS_4_OF_4_POSTHOC`; `Q3_NEURAL_NEW_OPERATOR=OPEN`; `Q6_UNSEEN_AUTHOR_TRANSFER=OPEN`; `Q4_TOTAL_LIFECYCLE_10X=OPEN`; `Q7_FRONTIER_PARITY=BLOCKED`.
