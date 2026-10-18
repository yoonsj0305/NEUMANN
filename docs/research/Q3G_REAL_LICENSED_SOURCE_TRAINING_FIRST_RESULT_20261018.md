# NEUMANN 1 · Q3G real program-supervised CPU experiment, 2026-10-18

## What is real, and what is not

**Actual** Microsoft Loopy published program/invariant data, immutable Git repo revision `91fe89245a0894ec8ad3741d85ae91ce3b552b2e`, `GeneratedInvariants.xlsx` Git blob `3e974edea4c856fee68d723cf867140d57094957`, `dataset.zip` Git blob `17cac0f6734a39f0fe73558199cc2ad8d5c1a810`. Source identity join **398/398 exact**, 398 unique source SHA256s, 23 original source subgroups. No Q3F escrow SMT2 benchmark text accessed.

**License correction preserved**: first implementation incorrectly connected an ancestor-unrelated LICENSE to every file; after exact true ancestor-only repair, only **239/398** had any on-path license. Actual LICENSE body inspection classified **99 BSD 3-Clause**, **51 Apache 2.0**, **89 unrecognized terms**, **159 missing ancestor license**. **Only 150** permissive-license examples were allowed into the experimental study; unknown/GPL excluded. License file detection alone is NOT license permission.

## Actual CPU training against a non-ML retrieval baseline

First actual training run [GitHub Actions #39082129492](https://github.com/yoonsj0305/NEUMANN/actions/runs/39082129492), **SUCCESS**, artifact ID **12119785046**, with binary weight checkpoint and immutable JSON receipt.

- After predetermined 180-char maximum target and source-contains-label exclusion, **105 actual nonheldout source/invariant pairs trained**, **32 genuinely source-group held out**, 13 length-filtered, 248 license-excluded.
- Real source text and assertions used as model input; original published textual invariant used as supervised target. No synthetic derived program substitution.
- Trained **56,164 parameters**, 512 hashed source-token context + GRU character autoregressive output (NOT typed mathematical AST). 12 epochs CPU, train step wall **2868.863ms** (not inclusive of environment setup). Training cross-entropy decreased from **3.965864** to **1.444214**.
- Held-out entire origin groups: `LinearArbitrary-SeaHorn/VeriMAP`, `sv-benchmarks/loop-lit`, 32 cases, exactly zero train-test identical source SHA overlaps.
- Held-out exact generated Loopy invariant: **0/32** neural and **0/32** same-information nearest-neighbor lexical retrieval. Mean character similarity: **neural 0.188042**, retrieval **0.545013**. Hence current neural output is much WORSE than cheap retrieval on this test; labels are not independently reverified by NEUMANN and no original Frama-C safety proof was run.
- Frozen actual checkpoint `first-frozen-real-source.pt` size 239,641 bytes, SHA256 `de16d5be8e92e82de2a08611b79d805da4280ea2b56a39e366ca4460d3ae0091`; first receipt JSON size 3,855 bytes, SHA256 `266369a19d8f7fa5f4e76a67130cef2e08f7b50dd49a239a46f0e515b9667b00`. GitHub binary artifact CRC PASS when freshly downloaded.

## Science decision

`Q3G_AUTHENTIC_LICENSED_SOURCE_SUPERVISION_COMPLETED / SOURCE_GROUP_GENERALIZATION_FAILED / CLASSICAL_RETRIEVAL_OUTPERFORMS / ALL_Q1_Q7_OPEN`.

The improvement is **real source/verified-label provenance and an actually trained CPU checkpoint**, not general mathematical relation invention or structural reasoning. In particular this is neither a typed AST generator nor a CHC model for the two still-sealed Q3F benchmark groups. Published Loopy 'successfully verified' is their research report, NOT a independently reconstructed original theorem in this project. No Q3/Q4/Q7 admission and no 10× economics.

**Stop repeating this token-level language modeling architecture:** against 32 group-disjoint real examples it has no exact predictions and considerably worse character similarity than exact lexical retrieval. Before next neural spend, acquire **independently replayable program-invariant original proof pairs** from correctly licensed disjoint groups, normalize variable binding/AST and source semantics, and establish a meaningful source-only specialized classical headroom. Train a typed, variable-depth semantic AST *only if* the mechanism/learning ablation could plausibly outperform that classical baseline. Holdout escrow Q3F still closed. No extra training or tuning on these 32 real source group tests.

## Honest run status and source hygiene

- GitHub PR #193 remains Draft. First inventory CI fail (using raw bytes as ZIP handle), another bytes-wrapper failure, and a shell-line-continuation error were all fixed without changing either third-party source file or downstream target split; execution history preserved.
- Public repository retains training code and proof-of-provenance receipts. **No third-party benchmark program or verbatim invariant is distributed**. Raw checkpoint and receipt available as immutable GitHub Actions artifact 12119785046.
