# Q3T-2 | Native Z3 original SMT-LIB parser differential-proof gate (pre-first-run)

2026-10-18 KST. Registered before first Q3T-2 CI. No new neural research result.

Q3T FIRST Actions #39098626092 (original artifact 12125254285) found exactly one formerly unsupported real original that passed mixed Bool/Int source translation and complete source-original proof: benchmarks/LIA/others/pldi18_seahorn_Fig3.sl, immutable upstream original Git blob 223c65d07b2cff707cfb21a078c17f6841b30cad. The other nine remain unsupported. Pin upstream SaswatPadhi/LoopInvGen git commit 6ac90265b11431c9477dfbd33e3e3380234c0499. Frozen first Q3T JSON SHA256 is checked before new rerun.

This study addresses a real source soundness risk: a handwritten source parser can mistranslate source SMT-LIB. Require TWO independent source-parsing paths, not two independent theorem provers:

1. Retain Q3T handwritten typed source-to-Z3 compiler and exact original original Synth-Inv/Pre/Trans/Post contract and all original function/parameter names, never source-editing or guessing variable sorts.
2. Read EVERY original define-fun body through Z3's NATIVE SMT-LIB parser in a separate namespace of declarations, retaining exact original bodies and formal argument positions. Exclude only nonstandard SyGuS commands synth-inv, inv-constraint, check-synth (these are read structurally by original SyGuS parser, not accepted by standard SMT-LIB).
3. Ask SMT whether XOR(native Pre, custom Pre), XOR(native Trans, custom Trans), XOR(native Post, custom Post) each UNSAT. Any SAT or UNKNOWN means source semantics mismatch or insufficient evidence and BLOCK full claim. Adversarial opposite/surrogate predicate XOR must be SAT.
4. Independently rebuild original Reach/Bad SPACER CHC FROM NATIVE PRE/TRANS/POST, fixed 3s, require bad state UNSAT, pre SAT, not post SAT. No claim of two different solver backends: both are Z3 but input source parsing is independent.
5. Reconstruct classical inductive typed AST from Q3T original specialist using original exact source and recheck all THREE original init/step/safety VCs against the **NATIVE** source predicates, each negation UNSAT, fixed 2.5s. Never read any published answer label or source-specific solution template. Only original proof-carrying typed invariant counts.
6. Preserve all error and unsupported results. Do not alter the prior first Q3T 10-case receipt, do not claim new full Q3 learned operator invention/Q4 10x/Q7 frontier. Original Fig3 already OPENED during Q3S/Q3T, so no blind holdout claim.
7. No Q3F sealed CHC original benchmark read, no commercial benchmark redistribution, no original source or invariant formula text exported, all Q1-Q7 OPEN.

Only bounded goal: establish that this ONE genuinely real mixed Bool/Int original program's safety theorem survives two semantically equivalent but independently implemented source parsing routes and an unchanged original formal proof.
