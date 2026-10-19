# NEUMANN 1 Q3 | Source-derived relational Houdini recovers two previously unproved official originals

**Date: 2026-10-19. Exact outcome: 2/2 PREVIOUSLY ABSTAIN official originals now have explicit native original inductive invariant with independent cvc5 backend after documented input-serialization repair. Scope is one near-duplicate source family, DEV-only.**

## Research importance

Original official SyGuS source study first [Actions #39210016907](https://github.com/yoonsj0305/NEUMANN/actions/runs/39210016907) recorded `anfp.sl` and `anfp-new.sl` both **ABSTAIN**, no original 3VC, despite 3/3 native-vs-custom original source parser parity. The latter has a larger `y < 100000` loop guard rather than `y < 1000`; they represent related versions of the same algorithm, **not independent source origins**. Those historical receipts and their exact raw SHA were frozen and NOT replaced.

Full preregistration: [Issue #277](https://github.com/yoonsj0305/NEUMANN/issues/277), created before writing the new mechanism and its first proof result. Public source upstream `SyGuS-Org/benchmarks` exact commit `13c8deb68a873635879c9a69bc78caebd340f646`, original raw SHA256:

| Original | Source byte SHA256 | Old status | New final status |
|---|---|---|---|
| `comp/2017/Inv_Track/anfp.sl` | `1caa46662e6093fa0d95f48349558abda0ffa2974bc23db025b78d3d5a1a63cb` | ABSTAIN | **3VC native Z3 + cvc5 3/3 UNSAT** |
| `comp/2017/Inv_Track/anfp-new.sl` | `97d4acb56916aca25cc4136cee9da4760baa3b15eb9a2e2feff1bca62da86769` | ABSTAIN | **3VC native Z3 + cvc5 3/3 UNSAT** |

## What new mechanism actually did

The new source-driven classical **relational Houdini** proposer takes only original SyGuS **public Pre and Trans**, not the Post condition or any privileged gold invariant, generates a uniform finite set of sparse signed integer inequalities over one or two original state variables with cutpoints `-1,0,1` plus the public Pre witness, filters atoms independently implied by Pre, then repeatedly asks Z3 for a concrete counterexample to inductiveness of the entire candidate conjunction. Every atom falsified in the next-state witness is deleted. Terminate only when induction counterexample is UNSAT. The full candidate is then checked against actual original Post **separately** by the existing immutable source-bound original Z3/independent cvc5 3VC verifier. No filename-specific winning solution is inserted.

Both originals: **16** initially Pre-entailed candidate atoms, **6** removed after actual counterexamples, **10** survived. The survivor conjunction entails the simple useful relation:

\[\boxed{y\ge0\quad\land\quad x\ge1\quad\land\quad x\ge y}\]

More redundant admissible inequalities remain in the exported certificate. This conjunction is **inductive** under original `x'=x+y, y'=y+1` with loop guard `y<T` for `T=1000` or `100000`, and implies original safety at loop exit `y≥T⇒x≥y`. Native Z3 checked original `Pre ⇒ I`, `I∧Trans ⇒ I'`, and `I ⇒ Post` bad conditions all UNSAT on both originals. Independent standalone cvc5 independently replayed those six exact exported source-bound SMT-LIB obligations, all UNSAT exitcode 0. `Post` alone is NOT inductive; nontrivial relational strengthening is actually needed.

True, false, an illegal SMT command, and wrong original source SHA negative controls were all rejected on both originals (8/8 negatives). Original native/custom Pre/Trans/Post parser parity 3/3 UNSAT on each. The Z3 proof, exact source bytes, output candidate, source-only heuristic trace and independent verifier results are archived.

## First external proof backend FAIL preserved, and the narrow repair

FIRST Actions [#39227159056](https://github.com/yoonsj0305/NEUMANN/actions/runs/39227159056): **SCIENTIFIC GATE FAIL**. Both source-invariants had genuine native original Z3 3VC UNSAT; cvc5 rejected every original obligation at **SMT-LIB parsing** because `z3.Sum(singleton)` printed an invalid unary `(+ (* 1 x))` for strict cvc5, exitcode 1. This was **not** recorded as external UNSAT. First failure artifact `12174247890`, ZIP SHA256 `1f17c7f2bfe5efa48a51c576fb03318d7ff815079bd35e39a9d33bc65668b791`, original raw JSON SHA256 `58936e0fe89401ab0e5c7afb4dae5cc16542b6ebe73ac45bcc6f6e41584986b8`. These first verdicts and texts remain intact.

Precisely one source-independent **protocol interoperability repair**: simplify the complete original native invariant via `z3.simplify`, **independently require `XOR(first_native_invariant, simplified_invariant) = UNSAT`** under Z3, and pass only the equivalent canonical SMT-LIB Boolean expression to the **UNCHANGED original verifier**. Do not change source selection, Houdini atom grammar, offsets, parameters, loop condition, reasoning algorithm, or 8 prenominated scientific criteria. Repair is named and auditable; revised success is a SECOND run, not a fictitious clean first success.

SECOND exact [GitHub Actions #39227531556](https://github.com/yoonsj0305/NEUMANN/actions/runs/39227531556): **SUCCESS / all 8/8 preregistered conditions true**.

- Evidence artifact `12175560722`, ZIP exact SHA256 **`2e1831dbc5d6a4268e06ca950538b922b9048d508f8043d104f2ce9b164c2bf5`**, ZIP CRC PASS.
- First valid cross-backend JSON exact SHA256 **`324ebcb7dbb09447aca4d5fe205764b28c05ae42e0d567aabc0108e87c5c0809`**. Independently downloaded and inspected original assertions, 2 x 3 native and 2 x 3 independent cvc5 statuses and all 8 negative tests.
- Final recorded total original wall approximately `129.140 ms` and `125.905 ms` in the hosted environment. Historical 3,075ms prior abstention includes different failed solver fallbacks, so **do NOT claim matched iso-capability 20× or 10× speedup**.

## Scientific adjudication and STOP

```text
Q3_ORIGINAL_ANFP_PREVIOUS_ABSTAIN_TO_ACTUAL_3VC = PASS_SCOPED (two related published source variants)
Q3_RELATIONAL_PRE_POST_SOURCE_ONLY_USEFUL_INVARIANT_DISCOVERY = PASS_SCOPED (one algorithmic source family)
Q2_REAL_SOURCE_PROOF_Z3_PLUS_CVC5 = PASS_SCOPED (6/6 original obligations, 8/8 negative inputs)
FIRST_CVC5_PARSER_PROOF_GATE = FAIL_PRESERVED
POST_SERIALIZATION_INTEROP_RECHECK = PASS_SCOPED
Q3_NEURAL_LEARNED_UNIQUE_STRUCTURE_OVER_STRONG_CLASSICAL = NOT PROVEN; this is a classical method
Q3_INDEPENDENT_UNSEEN_AUTHORED_SOURCE_ORIGIN = NOT PROVEN; near-duplicates
Q4_Q5_COMPLETE_10X_RESOURCE_ECONOMICS = NOT EVALUATED
Q7_REAL_FRONTIER_CAPABILITY_RECOVERY = NOT EVALUATED
SEALED_DECISION3 = BLOCKED
HISTORICAL_AM1_E2B_FIRST = FAIL_UNCHANGED
GLOBAL_Q1_Q7 = OPEN
```

**Action:** The new SOURCE-ONLY relational guard-derived Houdini operator is a genuinely useful classical Q3 capability and can be kept in a source-proof portfolio, but must not be promoted as neural transfer or full Q3 closure. Further probes on the two threshold variants are STOPPED. The next meaningful test requires source-authorship-independent hard families where strongest classical grammar cannot provide the structure cheaply, plus complete resource accounting. On this narrow original family, deterministic symbolic inference deserves precedence over unnecessary neural work.

Code and archived first/second evidence: [Draft PR #278](https://github.com/yoonsj0305/NEUMANN/pull/278).