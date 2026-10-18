# Q3Z | FIRST ORIGINAL NIA polynomial structural discovery FINAL verdict (2026-10-18 KST)

**Scientific decision:** `Q3Z_BOUNDED_POLYNOMIAL_STRUCTURAL_MECHANISM_PASS`; `Q3Z_PROSPECTIVE_TWO_NEW_ORIGIN_GROUPS_FAIL`; `GLOBAL_Q3_OPEN`; `GLOBAL_Q1_Q7_OPEN`.

## Frozen provenance

- First mathematical preregistration **BEFORE algorithm code or first new source-group content**: commit `267d8dd0d98e2d52193730ad65d4528269f27d2e`, `docs/research/Q3Z_FIRST_POLYNOMIAL_CLOSURE_PREREG_20261018.md`.
- Exact original external LoopInvGen revision `6ac90265b11431c9477dfbd33e3e3380234c0499`.
- Original first Github Actions #39104698609 FAIL on synthetic quadratic **before original cohort**. Additional diagnostic #39104783570 and #39104872189 preserved. The bug was an exact SMT sort mismatch in polynomial encoder (Z3 power promoted Int exponentiation to Real; original math kernel was correct). Exact Int repeated multiplication fix preregistered as erratum `docs/research/Q3Z_FIRST_INTEGER_POWER_SORT_ERRATUM_20261018.md`; no source, success gate, benchmark or coefficient change.
- [Successful scientifically complete replay #39104950835](https://github.com/yoonsj0305/NEUMANN/actions/runs/39104950835), immutable Actions artifact **12128410793**, ZIP SHA256 `7f9c2331163a81555248a312ff4171e2e57d0b23378737e67ff954ac9e4f4d43`, source implementation commit `4af6dab86a45c183e549d3113c59fad1911cad7e`.
- Frozen controls all PASS: cubic forward goal delta-closure, quadratic finite-sum conservation, wrong mutated cubic source transition rejected, unsafe program not falsely proved. No original source formula bodies, gold invariant, SPACER cover or other privileged proof hints ever supplied to generator; 0 neural forwards.

## Three exact original formal theorem gains

All these have originally Pre SAT, originally Not-Post SAT, original native SMT-LIB versus custom source parser Pre/Trans/Post XOR UNSAT in ALL 3 cases; original Post-alone 3VC step SAT (not sufficient); discovered polynomial coupled with original Post original three VC refutations each **UNSAT**. Source transition extracted from original only after explicit `Trans => exact graph` proof, original guards preserved. Exact original 3VC includes I(x)&Trans=>I(x') independent from discovered algebraic generation.

| Exact original source | Formerly opened? | Method | Exact original source theorem | Original method+proof wall (ms)* | Original direct SPACER |
|---|---|---|---|---:|---|
| `benchmarks/NIA/2018.CHI_InvGame/cube2.desugared.sl` | YES Q3Y first | Original Post polynomial -> repeated exact affine pullback differences (degree3/2/1), joint inductive goal | all 3 VCs UNSAT | 491.084 | error, ~3000.444ms |
| `benchmarks/NIA/2018.CHI_InvGame/gauss_sum-more-rows.auto.sl` | YES Q3Y first | Original source transition monomial degree2 exact conservation nullspace, verify uniquely forced Pre value | all 3 VCs UNSAT | 85.215 | error, ~3000.382ms |
| `benchmarks/NIA/other/issue_8.sl` | **NO**, FIRST filename-only newly chosen test cohort | Original Post source polynomial goal invariant equation (division-remainder conservation), exact source-induced closure | all 3 VCs UNSAT | 156.229 | error, ~3000.402ms |

`issue_8` first original source relation is `x=r+q*y`, and original step subtracts y from r while incrementing q. It was not hardcoded into generator, which takes polynomial target equality from ORIGINAL Post and source transition. For `cube2`, the original next-state finite differences of goal `x-n^3` yield `y-3n^2-3n-1` then `z-6n-6` then zero. For `gauss_sum`, the exact degree2 conservation polynomial is `2*sum = i*(i-1)`; all are independently certified against ORIGINAL source, not pasted into generator.

*Wall time shown is generator algebra + internal exact original VC proof checks, NOT complete system wall or matched capability solver efficiency. Full case wall (including other controls and slow specialist) respectively 3533.861ms, 3113.314ms, 3187.444ms. Full frozen 12-case study wall 24451.278ms on one GitHub Linux runner. Direct SPACER returned `error` under fixed 3000ms, not a successful/failed competing proof in a matched budget. DO NOT infer 10x/iso-capability/Q4 from wall times.

## All FIRST frozen original results, no successes promoted or failures dropped

Development, SIX previously opened NIA:
- `poly3.pos_z.sl`: abstain state/arity cap
- `poly7.sl`: abstain no fully explicit affine next-state graph
- `cube2.desugared.sl`: genuine newly original-proven via GOAL
- `gauss_sum-more-rows.auto.sl`: genuine newly original-proven via CONSERVATION
- `non-lin-ineq-1.desugared.sl`, `non-lin-ineq-2.desugared.sl`: no newly certified polynomial theorem
Development **2/6** newly certified original theorems beyond Post, both prior Q3Y NIA originals were 0/6.

First path-selected prospective, SIX original sources across 2 NEW source groups:
- `benchmarks/NIA/2018.SV-Comp`: **0/2**, both transition forms lack fully explicit deterministic affine update graph under the current strictly checked frontend; cannot claim these originals unsafe or intrinsically unsolvable.
- `benchmarks/NIA/other`: **1/4** new genuine proof `issue_8.sl`. The other three: `div.sl` unsupported update graph, `lcm.sl` outside state cap, `mul.sl` no newly certified goal theorem.
**First prospective TWO-source-group preregistered admission: FAIL (1/2 distinct groups)**, not a global Q3 generalization PASS.

## Research conclusion and STOP

The earlier exact *affine equality-only* representation prevented discovery of needed cubic and quadratic relations. The new polynomial representation **constructs and original-VC certifies** genuine bounded new hidden structural invariants without gold/oracle input. One new original previously untouched by this research was solved, and no false proofs on negative controls. This is a defensible LIMITED Q3 mechanism success. It is a classical source-constrained symbolic algorithm, **not model-trained invented operators nor new scientific polynomial algorithm**. Broad open-set, branch/nondeterministic/original nonlinear update generalization and deployability not proven.

The failed prospective SV-Comp group is a clearly identified frontend representation gate, not evidence for opening/reselecting a different group. STOP rerunning this group with posthoc source-specific patches while describing it as blind. Any future independent experiment on branching/multi-branch source transitions needs a separate preregistration and truly untouched external corpus. Q4 complete 10x matched-cost, Q5 end-to-end advantage, Q6 general unseen domains, Q7 frontier parity remain OPEN. No inflated results, no replacement of first failures.

Original full first JSON is in the immutable GitHub Actions artifact; source/input/trans program text not redistributed by our repository receipts.
