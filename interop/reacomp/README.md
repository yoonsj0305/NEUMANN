# Reused ReaComp components

Origin: https://github.com/cmu-llab/ReaComp
Pinned revision: `2b24f50b9e55cfb6bc6fd40510c35bceaf0eda06`.
Copyright (c) 2026 LLab at CMU. MIT license retained in `upstream/LICENSE`.

`upstream/` contains byte-identical published CC/Qwen PBE solvers and the
published PBEBench reward package. `manifest.json` records SHA-256 of every
imported file. The loader verifies these before each subprocess call.
No upstream implementation has been rewritten, tuned or retrained.

The NEUMANN adapter supplies only allowed IO examples and DSL limits, enforces
wall timeout, and independently checks the entire returned cascade with AST
parsing and original example execution. Published reward is also required;
its regex parser alone does not grant execution authority. Empty identity
programs are recorded but not accepted by this strict two-verifier contract,
since published reward rejects empty programs. This is an integration screen,
not a claim to reproduce the paper's evaluator or performance.

Dataset files stay in the pinned external checkout at workspace
`External/ReaComp/data`; this vendor directory does not redistribute them.
First public development screen: module `experiments.reacomp_reuse`.
The code runs from this source checkout; `interop/` is not bundled by the
current setuptools package configuration. Include the vendor explicitly when
preparing any Kaggle bundle. Original solver induction costs remain UNKNOWN.
