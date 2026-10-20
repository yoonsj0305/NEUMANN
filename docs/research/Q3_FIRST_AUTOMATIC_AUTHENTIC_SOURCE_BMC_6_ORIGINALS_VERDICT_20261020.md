# NEUMANN 1 | Q3 first automatic original-source pre-learning BMC, real six-source verdict

Date 2026-10-20 KST. Scientific result: SCOPED_PASS for a generic CLASSICAL source-only UNSAFE triage. Global Q3 and Q1-Q7 remain OPEN. This does not demonstrate neural-first mathematical invention or frontier cost advantage.

## Frozen source cohort and tests
Upstream SaswatPadhi/LoopInvGen commit 6ac90265b11431c9477dfbd33e3e3380234c0499. Preregistered body-uninspected sources in SHA freeze commit 66daabbcac884f5d8d2be879c41bd92dff008512:
- pottsumm3.sl: Git blob e0734e4358956b3ca66d280c9d4f8282b18d29b4
- s9.desugared.sl: Git blob 36234fd712b21a9111f834058e8371b10e3de191
- non-lin-ineq-3.desugared.sl: Git blob 728ee7e03686db111e47b429e3d584ad3ed668db
Already opened positive unsafe control prod4br.sl, and safely proven negative controls mul.sl and sorin04.desugared.sl. Three new source files belong to two subdirectories of ONE upstream author repository and are NOT three independent author-origin families.

## Generic unchanged-source algorithm
For each original native Pre, Trans, Post, validate pinned SHA and native-versus-custom parser semantic XOR parity 3/3 UNSAT. Original Pre SAT. Instantiate bounded chain Pre(s0) AND all actual Trans transitions AND NOT Post(sd) for d=0,1,2,3 with new physical state copies; 3-second Z3 budget per depth. Never manually provide candidate counterexample state. A SAT model is converted to an exact grounded ORIGINAL physical source execution. It is accepted only if the entire grounded chain and separately actual original Pre, every original Trans step, and actual original NOT Post all independently return SAT with Z3 and SHA-pinned official cvc5 1.4.2, exit 0. UNKNOWN fails closed. Bounded UNSAT NEVER means unbounded SAFE.

## Actual first official execution
Draft PR #308 https://github.com/yoonsj0305/NEUMANN/pull/308
First fully executed science workflow GitHub Actions #39420403593:
https://github.com/yoonsj0305/NEUMANN/actions/runs/39420403593
Official artifact #12262924019:
https://github.com/yoonsj0305/NEUMANN/actions/runs/39420403593/artifacts/12262924019
Unchanged GitHub JSON SHA256 64a697b5a09b46fa7f4638cc36b544311b6fcdac88a6aebd0c945883e1b2c1a9
Original artifact ZIP SHA256 88fe8abfdbe8770d9575fabcc9d882753c6ba20b685b409ee8401eba0a95ee9f; CRC PASS.
Earlier GitHub first attempt #39420104078 failed workflow YAML parse before execution; second #39420272877 failed transitive sympy import before science. Both historical failures retained and no first scientific result overwritten.

Six source SHA, parsers and nonvacuity checked. Automatic true UNSAFE detection on previously known positive control prod4br at exactly depth 1, NO hardcoded witness. The new Z3 model differs from previous PR #307 hand-constructed example:
CURRENT (x,y,a,b,p,q)=(1,5,1,5,1,0)
AFTER actual source transition (1,5,0,4,1,3)
Original Post false because original loop exits when a=0 and q=3 differs from x*y=5. Entire exact original ground chain and each phase separately SAT in Z3 and independent cvc5 1.4.2. This is a second source-authentic reachable violation, found completely automatically.
Two prior SAFE controls mul and sorin04 had 0 false UNSAFE claims. The three NEW source bodies all had original depth 0,1,2,3 BAD formula Z3 UNSAT (4 per original). That is **only no short witness**, NOT a claim of safety. Total CPU source analysis and SMT timing from original runner 152.224ms, excludes dependency installation and previously performed research, not a neural 10x speed claim.

## Scientific decision
Q3_AUTOMATED_PRETRAINING_UNSAFE_FILTER=SCOPED_CLASSICAL_PASS.
Q3_NEW_ORIGINAL_THREE_SAFE=OPEN (bounded depth only).
Q3_UNASSISTED_LEARNED_MATH_STRUCTURE=OPEN.
Q3_UNIQUE_ADVANTAGE_VS_EXACT_CLASSICAL=NOT_PROVEN.
GLOBAL_Q3=OPEN and GLOBAL_Q1_Q7=OPEN.

Before any GPU training, preflight all original source families for reachable counterexample and strong exact polynomial, integer HNF and ghost-quotient symbolic solvers. Only then consider a frozen learned proposal on independently authored safe and truly hard original source families, with equal-information exact classical, model ablation and all-in compute controls.

Reusable source code: research/evidence/q3_generic_source_original_bmc_20261020/first_six_real_sources.py
Frozen pre-source protocol: docs/research/Q3_GENERIC_BOUNDED_BAD_PATH_6_REAL_ORIGINALS_FROZEN_20261020.md