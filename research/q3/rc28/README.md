# NEUMANN 1 | RC28 | Own-weight cross-family latent state -> executable grammar

**Research-only DRAFT, 2026-10-25. Do not merge or label global Q3 PASS.**

The existing OWN-TRAINED GRU12, same 750-step end-to-end source I/O-only gradient trainer (no hidden-state/automaton labels) and SAME RC27 human-authored automatic state extractor were independently tested on TWO NEW formal task families unlike earlier RC26 modulo-3/5:
1. `suffix101`: whether the observed prefix ends in pattern 101; minimum binary *Mealy* machine has **3 states**.
2. `seen101`: whether the prefix has EVER contained pattern 101; minimum binary Mealy machine **4 states**.
These state numbers/transition labels were unknown to the trainer/extractor. The model only received binary input stream and binary end-to-end outputs at source lengths4,8,12,24.

**Blind freeze:** eight fresh own PyTorch weights (4 fixed seeds702..705 ×2 tasks) and 8 first 128×256 output files were frozen before independent gold was implemented. Sealed `SOURCE_ONLY_FROZEN.json` SHA256 **6c47e25c92edf9f1274e43293fac49828a454b83c49e7a7fdcfd4a58f7335d09**; raw signed tensor SHA and first prediction SHA supplied within manifest of the exact full archive.

**Results actually run:**
- Neural on unseen first 256-step sequences: **262,119/262,144** output bits; 25 errors concentrated in one seen101 model.
- Neural on independent 1,024-step streams: **131,070/131,072** output bits, 2 errors in the same one.
- Classical abstraction of actual weights' behavior with unchanged pre-existing RC27 `adaptive_extract.induce` produces 8/8 new runnable DFAs, 4/4 3-state (suffix), 4/4 4-state (seen). Human authored the output syntax/compiler and independent formal verifier.
- Independent finite product automaton compares every state pair and transition against fresh KMP/seen reference: **8/8 EXACT for ALL finite binary stream lengths** for the **extracted SYMBOLIC programs only**, and separate reachability/distinguishability check proves 8/8 **MINIMAL**. Frozen first inputs evaluated by symbolic programs **262,144/262,144** outputs, eliminating 25 GRU errors.
- All **56/56** single-transition-output mutants rejected by separate proof.
- Same extractor run on eight NEVER-trained GRUs with the same seeds: **0/8** exact. Learned weights causally contribute useful behavior in this fixed empirical controlled intervention (not a proof of neural-exclusive invention).
- Strong separate CLASSICAL Mealy observation-table learner has **exact same type of target I/O membership access**, no target transition labels, discovers exact minimal suffix/seen machines with **23 membership queries per task (46 total)**. Local process CPU approx 0.00016 and 0.00035 seconds; eight neural trainings around29 seconds process CPU. Classical has adaptive query rights, not identical sampling schedule. Q4 all-in10x neural advantage demonstrably NOT established.
- Two-type Dyck nesting at depth7 requires at least 2**7 = **128 distinguishable pending histories**, with **8,128 pairwise distinguishes** independently checked. Any fixed 3/4-state extracted grammar fundamentally cannot solve unbounded typed nesting. Dynamically growing memory still remains required.
- A delayed adversarial oracle matches all observations up to 256 bits but differs at257; finite neural observation does NOT prove the underlying continuous GRU all-length correct. The ALL-LENGTH theorem attaches only to the **independently verified finite extracted program**.

**Full original source-only trainers, all 8 actual Torch weight files, all first frozen bytes, independent grader/product/minimal proofs, 56 mutants, 8 untrained controls, strong classical synthesis, growth bound, SHA manifest and independent seed retrain** are in the user-provided conversation artifact:
`NEUMANN1_Q3_RC28_PATTERN_FAMILY_NEURAL_SYMBOLIC_GENERALIZATION_20261025.zip`
SHA-256 **bf0836daa2416effa6299fe6f3412920d9d98f517a42aadff53e75f7a0f5257e** (56 files).
On a CLEAN ZIP extraction `bash REPRODUCE.sh` PASS, all SHA hashes verified.
On a SEPARATE fresh temporary directory `bash RETRAIN.sh` PASS, **8/8 exactly identical Torch tensors and FIRST predictions**, elapsed CPU time excluded from bit-identity comparison. GitHub contains lean illustrative compiled machines and formal regression, not the original Torch tensors.

**PASS (limited):** own-weight cross-family continuous behavioral learning is extractable into fully certified minimal runnable grammar via a classical compiler, good causal learned-vs-untrained control, mutation/fallback guard.
**OPEN:** the trained neural network itself inventing a foundational execution ISA, autonomous creation of its own metalanguage/parser, unbounded memory innovation, truly external independent-author tasks, full Q3, Q4/Q5 cost/energy, Q6 Q7 frontier. Frozen North Star unchanged: *frontier-level problem solving with minimum necessary computation*. Next effort should be on unlisted grammar/memory generation, not repeating finite-state demonstrations.
