# NEUMANN 1 · Source-neutral Horn Semantic IR, actual external 17/17 equivalence gate
**2026-10-17 KST. Scientific verdict: `GENERIC_CHC_SOURCE_IR_SEMANTICS_17_OF_17 / ONE_LEARNED_LOCAL_LEMMA_CERTIFIED / NO_GLOBAL_LEARNED_PROOF / Q1–Q7_OPEN`.**

## Why this is needed
Earlier automatic proof generation for the opened `square_twice_safe` benchmark implicitly assumed **exactly nine Horn clauses and five relations**; a rename-only regression did not establish applicability to structurally different programs. Before reading two new external files, preregistered source choices in [commit 5951717](https://github.com/yoonsj0305/NEUMANN/commit/5951717cedec9e92fc2a3ddb922254d691e26f11).

Pinned real public CHC-COMP 2026 upstream `chc-comp/chc-comp26-benchmarks` at `b4fa7a708e5863bbcdb5de50d692ead3a67cbedc`:

| Genuine original | Original SHA256 | Number original Horn clauses | Original predicates | Formal semantics-preserving IR check |
|---|---|---:|---:|---|
| `hopv/lia/mochi/sigma_sum_000.smt2` | `1166d27fee68ff467c3afd012b4a2012d9cbfe115bc94f7bbf4b1710c4e12304` | 7 | 3 | **7/7 UNSAT** on rule XOR |
| `eldarica-misc/LIA/llreve/square_twice_merged_safe.c-1_000.smt2` | `a1013134a1c0e465e0905eddfc55e2651f03190d37e322f992c1ce82080b8d35` | 10 | 4 | **10/10 UNSAT** on rule XOR |

Exact original Git blob IDs `5e9f4d9f82a7db6e5bc0f0ab1e2351d2016aa9b4` and `d6dda2f244abf438f6f11e4d923a6687aeed07d6` independently verified **byte-for-byte** using Git blob SHA1. Unchanged 2,355-byte and 1,668-byte original texts were parsed with Z3 native 4.13.3.0.

## What was implemented, tested, and NOT claimed
- Source-neutral SMT-LIB quoted/unquoted relation symbol normalization, arbitrary clause/predicate counts, Int-arity handling, generic Horn relation dependency graph and guard preservation, per-clause alpha-renaming of quantified variables.
- Reconstructed source meaning independently refuted as `XOR(ORIGINAL QUANTIFIER BODY, RECONSTRUCTED)` with a new solver under **fresh unconstrained variables and uninterpreted predicate meanings**. All **17/17 UNSAT**, proving semantics of transformations, **not safety of the CHC source**. HOPV's two-premise rule retained.
- **Independent false-source reconstruction detected as SAT**, and source Git blob mutation rejected.
- Existing frozen **15 genuinely learned weights**, SHA256 `cc2b34773dd095b7980fa6365518714d896e69a64dd38a37e34cf522a64cc3e6`, were *not* retrained. The original source's arity-three recurrence `inv_main5` in **merged square original rule 8** yielded source vector `(k,m,n)=(1,0,0)` and learned coefficient vector `(1,-1,0,0,0)` for **only** `s=a²-at`. Independent local transition inductiveness **UNSAT**, same-info exact classical **UNSAT with identical formula**, zero coefficient ablation **SAT**. This is **one locally preserved relation only**: no complete five- or four-predicate invariant certificate and **0 new original full proofs attributed to the model**. The HOPV source falls outside the frozen recurrence grammar, so model **ABSTAIN**.
- Independent cold source Z3 4.13.3.0 (3-second subprocess cap) answered **SAT** for both complete real originals in about **1.2s each including subprocess start**. A solver's SAT result is not a separately replayed emitted certificate. **No potential neural speed or problem-coverage edge** on these two sources.
- These new targets were selected before their bodies were viewed; however **the semantic IR implementation was refined after looking at them** (including quoted/unquoted source-name handling). Hence this is **developer-exposed engineering validation**, NOT pristine end-to-end blind cross-family learned transfer, even though frozen model numerical weights did not change.

## Independent audit and reproducibility
**Full executable ZIP** `NEUMANN1_GENERAL_HORN_IR_FIRST_TRANSFER_20261017.zip` **22,534 bytes**, SHA256 **`d236d908cfe92fd865619234d900a44b485f66115c514517c1b5ba0951a7f741`**, 11 members with signed-format SHA256 manifest **10/10 PASS** and ZIP CRC PASS. Includes source-neutral IR code, real-source original checker, frozen checkpoint, trained local lemma proof, receipt, independent audit, 10 unit tests and README. External original source bytes **not redistributed**; reproducer fetches pinned revision and verifies exact Git blob before proving. Tested in a **fresh extracted separate directory** with temporarily supplied exact upstream originals: **17/17 semantic SMT XOR UNSAT**, 1/1 trained local lemma independent UNSAT and 1/1 ablation SAT, audit PASS, **10/10 regression PASS**, source/receipt mutation controls PASS.

**Major missing competence:** the neural model still cannot **invent operator/relational abstract syntax families**, and the new IR is handwritten deterministic infrastructure. Even positive component transfer is to a closely related square-loop family. No actual cross-family neural full proof, strong-classical superiority or total-cost advantage. **Q1–Q7 all OPEN.**

## Highest-value next gate
Freeze the **grammar-emitting trained operator AST model and its source-neutral IR** *before* sampling/reading any further unseen actual external sources. Test original quantified clauses with an independent verifier and equally informed best classical CEGIS or domain specialist, with training/decoding/verification time included. Terminate with ABSTAIN when model output is insufficient. The existing 15-weight polynomial coefficient learner and known sum-of-seven-leaves teacher are not credible methods of autonomously discovering new operator kinds. Stop them rather than scale another toy success.
