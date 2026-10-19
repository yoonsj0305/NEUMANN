# Q3 proof engine engineering closure | 2026-10-19

**Scientific status: Q3's oracle-free structural proof mechanism is validated for a bounded source language; CLI engineering PASS. Frozen global Q3 remains OPEN.**

This is the end of the *current Q3 engineering track*. It is **not** a claim of neural mathematical invention, broad Q6 generalization, lower complete cost than the strongest matched direct model, or frontier-level reasoning.

## Exact Q3 boundary

Frozen [Core Question Gates](../../docs/research/core_question_gates.md) ask: "A deployable system discovers useful hidden structure without gold/oracle input." This is a question about actually producing useful structure, **not** a contract that the proposer must be trained. The stronger claims "trained model invents new operators" (historical Q3R: NO-GO) and "persists across unseen independent task families" (Q6 / Q3 global deployability: OPEN) must not be silently bundled into one yes/no.

**Now available:** a standalone command operating on a single actual LoopInvGen-formatted SyGuS safety source, with no privileged invariant, answer key, per-file solution, or basename routing:

```bash
python -m pip install . sympy==1.13.3 z3-solver==4.13.3.0
python -m experiments.q3_source_prove --source /path/to/original.sl --out /path/to/proof_receipt.json
```

Implementation: [`experiments/q3_source_prove.py`](../../experiments/q3_source_prove.py). All source code for Post-only original 3VC, source-initial-state anchored signed-octagonal Houdini, exact per-transition-branch affine nullspace, and fallback source-only Z3 SPACER is imported **byte-identically** from Q3V4/Q3V6 historical frozen mechanisms. No training/model calls and no source-identity-specific control branch.

The actual command re-parses the original source with two independent parser paths; native/custom semantic XOR for Pre/Trans/Post must be UNSAT. It checks original Pre SAT, NotPost SAT. On success by a structural proposer it **rederives** the invariant from the original source and checks each original obligation: `Pre∧¬I`, `I∧Trans∧¬I'`, `I∧¬Post`, each UNSAT, then exports SMT-LIB scripts with content SHA256 for external replay. **If only source-only SPACER returns UNSAT**, label it separately as source-only solver decision **without** an inductive invariant or three exported bad-condition scripts. Malformed, unsupported, parity failures, wrong candidate, bad certificate, unknown solver status must fail closed. Reads at most 512KiB of regular .sl source.

## Reproducible FIRST functional regression

Pre-registered [Issue #245](https://github.com/yoonsj0305/NEUMANN/issues/245) **before creating code**. Single initial integrated CI [Actions #39188864631](https://github.com/yoonsj0305/NEUMANN/actions/runs/39188864631) **SUCCESS** on 18 previously opened original LoopInvGen files, source repo pinned `6ac90265b11431c9477dfbd33e3e3380234c0499`:
- **18/18** legitimate source safety answers.
- **16/18** exact original safety inductive invariants and three original 3VC UNSAT, SMT-LIB SHA-locked, independently Z3 query replayed: 48/48.
- **2/18** (`hola/add.sl`, `hola/countud.sl`) source-only SPACER UNSAT with NO falsely claimed inductive invariant certificate.
- Of 16 original 3VC, **8 non-Post-only**: 5 OCTAGON + 3 BRANCH_AFFINE_NULLSPACE; **8 POST_ONLY**.
- 18 unique original source SHA256s, native-vs-custom original source XOR 3/3 UNSAT all 18.
- A real `python -m experiments.q3_source_prove` invocation is included in CI and verifies a stored original source; malicious input, bad extension, replaced-SMT2 query even with recomputed hash, and deleted proof obligation were all rejected.
- **0 neural/model/GPU/API calls**, and no new source-family blind study.

First artifact [`12159450850`](https://github.com/yoonsj0305/NEUMANN/actions/runs/39188864631/artifacts/12159450850); independently downloaded ZIP SHA256 `bcf54303f561bc0ce45ed8ba244ba403e1ff53ae8a24dda1fe10151c178e4bf0`; first raw 18-case receipt JSON SHA256 `3acb60a3a3f5afa8a9573c53cfc6017b5e4b88352044c14a6706c4033976d2f5`; ZIP CRC PASS, 18 original source SHA unique, original verdict counts re-audited from downloaded JSON. The regression receipt lists exported obligation **hashes**; running the CLI directly on a source produces the full scripts. This 18 set is ALREADY OPENED and cannot be promoted to Q6.

## Final no-churn decision

**CLOSE** `Q3_BOUNDED_LIA_SOURCE_PROOF_CLI_ENGINEERING=PASS`.
**CLOSE** `Q3_ORACLE_FREE_SOURCE_DERIVED_NON_POST_3VC_EXISTENCE=PASS_IN_SUPPORTED_SOURCE_CLASS`.
**CLOSE / NO-GO** `Q3R_FIXED_GRAMMAR_NEURAL_NEW_SEMANTIC_OPERATOR` from immutable historical 0/24 unique learned proofs and fixed-Γ exact Houdini theorem.
**KEEP OPEN** `Q3_GLOBAL_DEPLOYABILITY`, genuinely diverse unseen source generalization (Q6), learned operators outside Γ, whole-cost Q4/Q5, same-core AM2 real accelerator multiplier, and frontier Q7. This explicitly matches prior [Q3 final current-architecture disposition](Q3_FINAL_CURRENT_ARCHITECTURE_DISPOSITION_20261019.md); no historical result or frozen Q3 contract was altered.

**STOP:** do not reopen FiB/Hola/Acceleration fitting, source subset selection or speculative new variants just to improve the Q3 label. The next *mainline* program is the separately frozen matched accelerated AM2 Architecture Multiplier, NOT more Q3 classical theorem polishing. Keep all historical failed cases and original scientific FAILs immutable.

The new CLI is in a **DRAFT stacked GitHub PR**, not merged into main or independently installed as a released package. It requires valid original SyGuS `.sl` input, pinned solver libraries and a trusted SMT backend. These implementation and trust limitations are material.