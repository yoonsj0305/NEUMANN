# Q3J fixed authentic sum04 quadratic experiment: first result and scoped obligation closure

**Date**: 2026-10-18 KST.
**Scientific decision**: `Q3J_ORIGINAL_SIGNED_OVERFLOW_OBLIGATION_CLOSED / ORIGINAL_EXIT_SAFETY_NOT_PROVEN / GLOBAL_Q1_Q7_OPEN`.

## Frozen experimental identities and actual results

- Source unchanged: Microsoft Loopy original `loops/loops/sum04_true-unreach-call_true-termination.i.annot.c`, SHA256 `7b1ed83d1a2e80a1e5aa97e27a23c7ac1a53bd734cc95808ecce4aa868c41a23`, corpus Git blob `17cac0f6734a39f0fe73558199cc2ad8d5c1a810`. Already opened **development** source, not blind, no published target invariant used in candidate construction.
- Before reading the source body, first-stage quadratic grammar was preregistered in commit `e063606cb9310667fbc372548bbc4530aa83255e`. Max degree 2, exact symbolic reachable C states, rational nullspace and classical Houdini fixed-point, no source-target lemma injection; Q3F competition originals stayed sealed.
- First [GitHub Actions #39086074828](https://github.com/yoonsj0305/NEUMANN/actions/runs/39086074828) ran successfully and preserved immutable artifact **12121180486**. `QUADRATIC_CLASSICAL_ORIGINAL_NOT_PROVEN` is the true whole-source outcome. Runner and workflow success means **test completed**, not whole-source PASS.
- Original source has 2 integer state variables `i` and `sn`. 9 exact reachable state samples from unmodified original loop; degree≤2 feature basis 6; sample rank 3; rational nullspace dimension 3; 3 generated polynomial candidate equations and 33 preexisting generic source-derived comparison candidates. 18 initially true candidate formulas, 8 final inductive facts (3 polynomial), five Houdini rounds, 94 exact Z3 solver queries, first first-run candidate+proof wall **517.905ms**, not end-to-end energy/cost.
- All final checks: **initial UNSAT**, **consecution UNSAT**, **signed 32-bit overflow UNSAT**, original **exit safety SAT**, wrong-goal SAT, weak-empty-invariant SAT. SAT for original exit obligation does NOT by itself prove real program UNSAFE, only shows the current invariant cannot exclude a bad exit state.

## Identical original source paired with first Q3I control

[Q3I first original C census #39084573345](https://github.com/yoonsj0305/NEUMANN/actions/runs/39084573345), first artifact **12119829506**, same original source SHA. Baseline source-only Houdini for this program reported:
- initial **UNSAT**, consecution **UNSAT**,
- **signed 32-bit overflow SAT** (not proved),
- original **exit safety SAT** (not proved).

Hence the new polynomial candidate grammar **closes precisely one previously unproven original-loop sub-obligation, no-overflow, but does not close complete safety**. This stronger algebraic invariant is a real classical structural extension. The exact three polynomial candidates may be algebraically dependent; their independence or operator novelty is NOT established.

## Evidence reproducibility and integrity

The immutable paired first GitHub JSON receipts were cross-checked with a separate local auditor: source SHA equality, `signed_overflow SAT->UNSAT`, `exit_safety SAT->SAT`, other UNSAT proofs and SAT negative controls all PASS. Complete bundle: `NEUMANN1_Q3J_SUM04_OVERFLOW_SUBPROOF_20261018.zip`, **26,849 bytes**, SHA256 `e637bf2338e2038ae2a27a2cfda1d38386d66b76fc1dd065e266ad5c307999c6`, includes two first receipts, verdict, audit script, README and manifest; fresh extraction CRC + SHA256 member audit + cross-report audit PASS. This conversation ZIP is NOT committed to the GitHub repo; this branch's executable source and CI are authoritative. Does not redistribute third-party C source.

## Stop-loss and scientific limit

**Stop adding source-specific relationships or polynomial degree for this opened program.** Do not claim NEUMANN learned new structure, neural generalization, Q4 cost superiority or Q7 frontier parity. The new candidate grammar was classical, and the original whole safety still fails; all global Q1–Q7 remain OPEN. The research consequence is that precise original sub-obligations can be improved algebraically without a neural model, and **actual remaining headroom is the exit-safety condition**, which is not magically solved by an overflow certificate. The next Q3 learner still needs variable-bound typed AST proposals that outperform the stronger equal-information classical baseline on source-disjoint real originals. The Q3F 2025/2026 competition holdout texts remain unopened.
