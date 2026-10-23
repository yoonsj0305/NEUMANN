# NEUMANN Q3: hidden local geometry and law, independently sealed evidence

Date: 2026-10-23 KST. Source PR: https://github.com/yoonsj0305/NEUMANN/pull/528. Authenticated CI: https://github.com/yoonsj0305/NEUMANN/actions/runs/39885239826. Status: **ALL THREE DEDICATED JOBS SUCCESS**.

## Test contract
- Input: four controlled complete 8x8 one-step before/after transition pairs per task; no rule family name, permutation, block shape, block partition offset, true initial answer or metadata.
- A **human-authored 9-template finite local program grammar** stays present in solver code: (1x1 offset0), (1x2 offsets0/1), (2x1 offsets0/1), (2x2 4 offsets).
- Inference: enforce a globally deterministic injective/surjective local mapping for every candidate geometry and every calibration pair, require observed coverage of all patterns, choose unique candidate with smallest block area; otherwise UNKNOWN.
- For external 4x4 original initial-state inversion, reuse frozen `hidden_rule_inference.py` blob `9c74ec9761bd983de62f70669155d20a05cc02e6` after structure learned; no modifications to that solver.
- Provenance: third-party `neelsomani/automata-bench` pinned `7d86373fdb63fe1bd3592ddf71d923ceebc5acd9`, previously published public_dev300 and public_eval300, both **already seen by earlier research**. Added hidden-family supervised controlled interventions are NOT native benchmark tasks.
- Extra 360 tasks: four *internally generated* geometric families (90 each); not from an independent external dataset. Deterministic new source seed `202610231431`.
- Three separate GitHub job boundaries: source + withheld truths, source-only inference + SHA-sealed predictions, original-author independent grader + separate 12x12 heldout states. No truth accessible to inference job.

## SHA identities
- Author original public_dev SHA256 `ae709b00492d1cd6e539d140997f47049efd0cc24f587ffef9cac3d091ec0cbb`
- Author original public_eval SHA256 `9cf0cf5219876e14beb7ad3898403020727165b82b9c26aa35a518146a5cf795`
- New public_dev source-only SHA256 `a1629833aa547df58de0f34802ca9bb8de95d6a0d2a29702c178b02d1fa7abbc`
- New public_eval source-only SHA256 `8235bf0f00c439e6b1b0ef13b628c9419f4889a21c25bc5242339c94dca91fed`
- New internally generated source-only SHA256 `d204c74f1a56a9d2cb5f41bcc979959e15cb4f643716e7b45b33af31c6bcc9a4`
- Sealed pre-grade predictions public_dev SHA256 `3d97016409efd9b625caff30378f478cbd17f09983ec50783647f0438cc1388f`
- Sealed pre-grade predictions public_eval SHA256 `71f2aaac4e62d629a84a63b4d398ad100b52f55d6d21b15b3a72fd42633f4144`
- Sealed pre-grade predictions generated SHA256 `f5c608f26143f3e64d07d0cf69d6ec3715536a4d6c70fe3641beb257d625cf28`
- Independent original-author official verifier SHA256 `200f09b844e410671220cc6913aaa66aaa74ba7878e82b7cb787220d5437dd38`

## Source-only blinded results vs post-seal independent grade
| Cohort | Total tasks | Exact original latent geometry + local rule | 12x12 heldout full transition exact | Original real initial grid exact | UNKNOWN | Wrong submitted |
|---|---:|---:|---:|---:|---:|---:|
| External author's public_dev | 300 | 300 | 300 | 300 | 0 | 0 |
| External author's public_eval | 300 | 300 | 300 | 300 | 0 | 0 |
| Internally generated 1x1 / 1x2 / 2x1 / 2x2 | 360 | 335 | 348 | N/A | 12 | 0 |
| **All** | **960** | **935** | **948** | **600 authentic original** | **12** | **0** |

The 13 generated cases with incorrect *latent representation identity* nevertheless predicted the withheld 12x12 transition correctly. That does **NOT** prove the two candidate mechanisms are universally functionally equivalent: this test's holdout may fail to separate them. No post-grade retuning was conducted. The 12 UNKNOWN cases correctly abstain by ambiguity policy, not certified impossible in principle.

Separate source-only measured process CPU:
- public_dev300: **0.476484781 s**
- public_eval300: **0.441662244 s**
- generated360: **0.204533300 s**
These figures exclude separate physical oracle creation, full CI runner/container overhead, energy, network, and prior planning. They are not comparable to other experiments without a controlled matched CPU baseline.

A distinct 1,000 synthetic selftest (250 each grammar family, fixed generator seed) obtained **965/1,000 valid heldout 12x12 exact / 35 UNKNOWN / 0 wrong**. The additional original 960-case independent grader result is stronger evidence for the declared study.

## Constructive size-generalization theorem for EXACTLY reconstructed programs (935 cases)
Suppose the true one-step update partitions any rectangular toroidal grid (height divisible by `bh`, width divisible by `bw`) into disjoint identical `bh × bw` blocks at a fixed `dy,dx` phase, and applies an identical local lookup permutation `p` independently to each block. Suppose source inference has recovered **exactly** `(bh,bw,dy,dx,p)`. Then the learned one-step global update equals the true global update **for every possible binary source grid** at **every such rectangular dimension**, not merely on the withheld 12x12 examples. Proof: the two programs induce precisely the same partition of all cells by their equal block dimensions and offsets. Every input block is therefore converted by the same permutation `p` in both programs; the output at every cell coincides. Equality of the entire next-state grid follows by disjoint union. By composition the result extends to repeated steps **only if both programs use the same specified phase schedule at every step**. No arbitrary CA or unknown physics outside this grammar is covered.

Therefore this theorem applies to **600 external original programs + 335 additional generated programs = 935 proven-exact program identities**, subject to this declared model, and does not require sampling all larger grid sizes.

## Admission and limits
- **SCOPED PASS**: finite-grammar latent local block geometry + unknown permutation discovery, 600/600 external source tasks, 335/360 additional generated exactly identified.
- **SCOPED PASS**: original-author initial states 600/600 and disjoint withheld 12x12 transfer 948/960 with 0 wrong submissions and 12 abstentions.
- **SCOPED THEOREM PASS**: for all 935 exact programs, one-step size-independent equivalence under block tiling assumptions.
- **OPEN**: spontaneous novel program primitives not in the declared nine-template grammar, neural-exclusive learned structure discovery, true unseen external-author neural transfer, real physical sensor intervention costs, whole NEUMANN training+inference+verification >=10x, frontier-level problem-solving parity.
- **Degraded mode**: when pattern coverage or minimum model uniqueness fails, output UNKNOWN without guessing.
- **Critical experimental caveat**: controlled four 8x8 oracle interventions are extra supervision; they consume more source-observation work than previous one 8x8 known-family benchmark. This experiment tests *structural uncertainty*, not efficiency dominance.

