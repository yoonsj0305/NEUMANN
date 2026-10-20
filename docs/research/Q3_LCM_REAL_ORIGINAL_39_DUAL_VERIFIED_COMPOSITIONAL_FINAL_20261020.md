# Q3 authentic LCM original: 39 independent Z3+cvc5 compositional subproofs
Date 2026-10-20 KST. Status: AUTHENTIC_ORIGINAL_LCM_COMPOSITIONAL_SAFETY=POSTHOC_CLASSICAL_SCOPED_PASS; monolithic original 3VC remains UNSAT/UNKNOWN/UNKNOWN; neural structural invention and global Q3 OPEN.

## Provenance and first execution
Original: SaswatPadhi/LoopInvGen@6ac90265b11431c9477dfbd33e3e3380234c0499, benchmarks/NIA/other/lcm.sl; Git blob SHA1 6c0cbaafc0c8b960d6047014dc5670554aacbc85; raw SHA256 c488e8b87d96e48916ffd95c656c3ef712f3d8f327128a461814f3d424936667.
Frozen protocol committed BEFORE CI in docs/research/Q3_LCM_GHOST_QUOTIENT_COMPOSITIONAL_FROZEN_20261020.md.
First successful independent official GitHub Actions https://github.com/yoonsj0305/NEUMANN/actions/runs/39414437806 : 39/39 negated sublemmas UNSAT in native Z3 and independent official cvc5 1.4.2; subprocess returns 0 on every cvc5 lemma. Unchanged original native/custom Pre/Trans/Post semantic XOR parity 3/3 UNSAT.
Original GitHub artifact https://github.com/yoonsj0305/NEUMANN/actions/runs/39414437806/artifacts/12260926214 ; raw original JSON SHA256 1aa793b3fec3b9833f10f91b69e73e4a76d72fed64103fb78b02120cf795f20b ; original ZIP SHA256 5104e735796e40b3989205fdb1779293c4bac7441f7de2cd2b24b503b368152d CRC PASS.

## Source-only generated arithmetic invariants
Four mined original state relations: (x+v) mod a=0, (y-u) mod a=0, (x-v) mod b=0, (y+u) mod b=0; original positive state variables a,b,x,y,u,v.
Introduce integer proof-only ghost witnesses q1,q2,q3,q4, with x+v=a*q1; y-u=a*q2; x-v=b*q3; y+u=b*q4. No physical source variable changed, no goal weakened.
Actual original Pre provides q=(2,0,0,2) verified under original native Pre with both solvers.
Source-extracted branch x>y, physical original update x'=x-y,y'=y,u'=u,v'=v+u; ghost update q1'=q1-q2,q2'=q2,q3'=q3-q4,q4'=q4.
Source-extracted branch x<y, physical original update x'=x,y'=y-x,u'=u+v,v'=v; ghost update q1'=q1,q2'=q2-q1,q3'=q3,q4'=q4-q3.
These ghost updates were derived from EXACT integer column-module coordinates of real source branch affine matrices, not hardcoded into learned data.
At original exit x=y, u+v=a*(q1-q2)=b*(q4-q3); by the independently double-proved universal integer property (m>0 implies (m*q) mod m=0) and original positivity, published original Post holds.

## Original soundness proof rule and all 39 checks
1 original transition branch coverage: source native Trans logically equivalent to union of source AST branches.
12 source branch physical variable next-state checks: source branch implies source-derived affine update for all 6 original variables per 2 branches.
8 quotient relations induction checks: original branch plus current ghost invariant implies updated source expression equals actual preserved positive modulus times the automatically derived successor ghost.
12 positivity preservation checks (6 physical vars ×2 branches).
1 original Pre has explicit initial integer witness verification.
1 original Post AST parity / equivalence to the exact required original LCM goal.
2 original exit quotient witness checks.
2 universal Euclidean mod-multiple lemma checks.
Count 1+12+8+12+1+1+2+2=39, each Z3 UNSAT and independent cvc5 UNSAT, no unknown promoted to pass.
Reason this proves ORIGINAL physical program safety: every true original physical execution has a lifted ghost execution by initial witness existence and branch-total deterministic successor witness updates; induction preserves the witnessed invariant. The proof-only ghost variables do not restrict the physical original program, and invariant plus original exit implies published Post. This is a sound compositional/simulation proof of all reachable original runs.

## Explicit boundary
Historical raw direct monolithic original solver results in PR #303 initial=UNSAT, consecution=UNKNOWN, Post=UNKNOWN remain unchanged. Independent monolithic original cvc5 3VC success is NOT asserted. What is certified is a separate full original compositional safety argument made of independently verified source-bound sublemmas.
This is a classical integer-HNF-plus-SMT achievement and posthoc opened original, not a neural model discovering a new primitive, not new-source G1, not 10× full-cost or frontier parity. GLOBAL Q3 OPEN and all Q1-Q7 OPEN.
Dev wall for source-specific study reported ~1493.223 ms only, NOT all-in discovery or trained neural comparison.

Source code: https://github.com/yoonsj0305/NEUMANN/blob/research/q3-lcm-ghost-quotient-compositional-certificate-20261020/research/evidence/q3_lcm_ghost_quotient_20261020/compositional_source_original_proof.py
Draft PR https://github.com/yoonsj0305/NEUMANN/pull/304
Next: retain this reusable cheap exact certificate backend, evaluate genuinely fresh independent-source-family learned module proposal versus the same-information exact classical integer HNF solver, under frozen scoring and all-in cost.