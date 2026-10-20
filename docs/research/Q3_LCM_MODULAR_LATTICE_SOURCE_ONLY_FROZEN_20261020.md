Q3 real LCM modular congruence original proof protocol | 2026-10-20

SCIENTIFIC SCOPE: ALREADY-OPENED SOURCE, POSTHOC DEVELOPMENT. THIS IS CLASSICAL ONLY AND NOT NEURAL INVENTION.

Public upstream pin: SaswatPadhi/LoopInvGen@6ac90265b11431c9477dfbd33e3e3380234c0499 ; benchmarks/NIA/other/lcm.sl ; git blob 6c0cbaafc0c8b960d6047014dc5670554aacbc85 ; raw SHA256 c488e8b87d96e48916ffd95c656c3ef712f3d8f327128a461814f3d424936667.

ALGORITHM FROZEN BEFORE FIRST CI:
1. Check actual original Pre, Trans, Post typed custom/native parser XOR equivalence and Pre SAT, Not-Post SAT; no vacuity.
2. From ORIGINAL PRE and TRANS ONLY identify unchanged positive state variables as candidate moduli; identify changing state variables as potential linear-form terms.
3. For each positive immutable modulus m enumerate all unit modular atoms:
   (wi % m == 0); ((wi+wj)%m ==0); ((wi-wj)%m==0) for i<j across all mutable state vars. No gold invariant or manually supplied four relational formulas allowed. Also enumerate every original Pre-proved-positive state var as positivity atom. No Post used in selection.
4. Initial Pre⇒atom Z3 UNSAT filter; iterative full-conjunction source-only Houdini I∧Trans⇒atom-next with Z3 SAT/UNKNOWN removal until fixed point. Include all surviving modular candidates. Enforce Pre∧I SAT.
5. Verify ORIGINAL unchanged Pre⇒I, I∧Trans⇒I', I⇒Post (Z3 3/3 UNSAT AND independent pinned cvc5 v1.4.2 original 3/3 UNSAT). Repeat external cvc5 with explicit internal-decision 15s budget on first external UNKNOWN, preserving first outcome.
6. Strong negative controls: original Post-only and source-positive-only must fail induction or Post; source-only classical baseline counted. Never claim neural advantage. Original benchmark was already opened, so no fresh-blind G1.

SOURCE MATHEMATICAL EXPECTATION DISCLOSED AS HUMAN ANALYSIS NOT TRAINING DATA: modulo a the pairs u-y, v+x; modulo b the pairs v-x, u+y form a closed lattice under source branches, and at exit x=y imply u+v divisible by a,b. Candidate miner is NOT ALLOWED to hardcode these four formulas; generate all signed pair candidate atoms and retain solely through original Pre/Trans.

PASS is ONLY Q3_REAL_LCM_MODULAR_LATTICE_SOURCE_ONLY=POSTHOC_CLASSICAL_SCOPED_PASS upon full double original proof. If no proof, record OPEN/UNKNOWN truthfully. Learned mathematical invention global Q3 stays OPEN and Q1-Q7 remain OPEN, no paid AI/GPU.
