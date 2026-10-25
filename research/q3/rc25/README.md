# NEUMANN 1 Q3 RC25 | Gradient-learned hidden states → runnable symbolic grammar

**Research DRAFT, not merged, 2026-10-25.**

Unlike RC24's CEM sampled NAND executable programs, RC25 independently trained **16 actual 8-dimensional PyTorch tanh recurrent models with end-to-end differentiable BPTT and Adam only**. There was NO learned or human-provided carry-state/seen-state/parity-state label, matching program template menu, state-transition table, or CEM/classical program proposal in the neural fitting procedure. The neural model gets only task I/O streams, 4/8/12 steps, 650 Adam iterations and a HUMAN-PROVIDED recurrent cell architecture with 8 real hidden dimensions. Four seeds per task: carry-producing bit addition, prefix seen-one, prefix parity, and mod3 prefix counts. An exploratory pilot preceded the fixed 16 formal seeds, so task family selection is NOT external preregistration.

A human-authored extraction procedure probes each trained net on source-side short prefixes and groups recurrent vectors by 1-step *future output behavior* (NOT target/latent labels); if two contexts sharing a signature disagree on a successor, it refuses as UNKNOWN. On deterministic signature partitions it auto-names `ST_<SHA>` states and emits executable `MACHINE MEALY_BOOL_V1 / INITIAL / ON state symbol -> nextstate output / END` text, not prelisted code. A strict HUMAN-authored parser/interpreter executes it. The independent verifier uses a *separate* mathematical task specification to check the resulting finite automaton by exhaustive **product-state graph traversal**, sufficient to PROVE compiled-program correctness for **all finite input lengths**; this is NOT a universal theorem about unbounded execution of the original continuous neural net. It also verifies all symbolic states are pairwise distinguishable (minimal for the successful programs).

### Honest frozen 16-seed experiment

All 16 separate Torch tensor files and all FIRST 128 ×256 symbol inputs and 32,768 model-predicted output bytes each SHA-frozen BEFORE heldout mathematical grades. Initial 8/32 monitoring existed and is NOT strictly heldout; formal target 256 is separate. The results:

| Target | First output correct / total | Neural exact seeds | All-length proven compiled programs |
|--|--:|--:|--:|
| Addition | 131072/131072 | 4/4 | 4/4, minimal2 states |
| Seen-one | 131072/131072 | 4/4 | 4/4, minimal2 states |
| Parity | 114922/131072 | 3/4 | 3/4, minimal2 states |
| Mod3 | 85473/131072 | 0/4 | 0/4 |

Total 462539/524288 bits and **11/16** valid all-length symbolic certificates. Three synthesized wrong programs FAIL independent product witness; two alias-conflicting nets generate UNKNOWN and NO executable symbolic program. Never claim 16/16, nor a proof of the entire RNN on arbitrary length.

### Strong conventional synthesis comparator

Same problem specifications and *fewer source examples*, human limit up to3 states (neural model has8 continuous hidden dims). Classical exhaustive **Mealy automaton** synthesis from widths1..3 addition / widths1..4 others gets **4/4 exact minimal programs**, including Mod3 where own RNN fails, and independent verifier formally proves them.

- Add: 5756 candidates, CPU~0.00438s.
- Seen: 68, CPU~0.00017s.
- Parity: 65, CPU~0.00021s.
- Mod3: 11230, CPU~0.00533s.

All 16 OWN-model trains cost ~**24.67 CPU process seconds** versus classical ~0.010s for four tasks, although this is not a hardware-energy/iso-capability TCO audit. Neural is worse. Current NEUMANN admission should use classical first; compiled neural syntax is a research result, NOT currently cost-justified.

### Original first-class evidence

User downloadable `NEUMANN1_Q3_RC25_DIFFERENTIABLE_STATE_TO_GRAMMAR_20261025.zip`
SHA256 **57460133980e9f21b903c0c50c921ef1de74298c788b75ea4c4c225e278ae063**.
This **94-file ZIP** contains ALL 16 authentic .pt tensors, original source-only differentiable trainers, all FIRST input and predicted binary bytes + corresponding SHA freeze, all14 learned .nsl language definitions and original behavioral-signature JSONs, independent heldout grader, independent all-length product proofs/minimality, strong exhaustive classical synthesizer and explicit fail-closed host tests. Clean extraction `sh REPRODUCE.sh` PASSED. **All 16 freshly retrained original model weight tensors, first prediction byte hashes, and generated language JSON EXACTLY matched: `sh RETRAIN.sh` PASSED**. This PR versions only an extracted three-program readable fixture and regression guards, NOT the full raw 94-file experiment.

**Admission boundary:** own neural weights learn useful continuous internal representations; model-behavior-generated new symbolic state names/grammar and proof-gated compilation 11/16 is SCOPED_PASS. BUT the host metalanguage, objective, recurrent memory container, probe/signature algorithm, grammar parser, target specs and proof system are HUMAN designed. Autonomous invention of the foundational instruction grammar itself remains **GLOBAL Q3 OPEN**. Efficiency Q4, external-author Q6, frontier-level Q7 OPEN. Preserve frozen North Star.
