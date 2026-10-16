# FGSR Q3 authentic source-family transfer: FULL ORIGINAL PROOF, **classical-only** (2026-10-17 KST)

**Scientific verdict: `EXTERNAL_ORIGINAL_9_OF_9_CERTIFIED_CLASSICAL_WITNESS / FROZEN_18_WEIGHT_HEAD_ABSTAIN / LEARNED_Q3_UNPROVEN / ALL_Q1_Q7_OPEN`.**

## Genuine public original, selected before opening

We **pre-registered** actual external CHC-COMP 2026 `eldarica-misc/LIA/llreve/square_twice_safe.c-1_000.smt2` at fixed upstream commit `b4fa7a708e5863bbcdb5de50d692ead3a67cbedc` in [commit 5472869](https://github.com/yoonsj0305/NEUMANN/commit/5472869a7caa446772f8afffbb78b9d3145bffa1). Upstream original is **2,057 bytes**, **9 original quantified Horn assertions**, five source-declared relations of different arities, SHA256 **`f62d0fb72140e6bd7e953dcebd131a4e9498cc9c0c150588ca79944962e9e748`**, source Git blob `4ee7f95005f78a4ac25b482324a03ae69edec5c6`. External benchmark metadata `expected_verdict: true` is not a proof.

[First actual CPU direct original Z3 4.13.3 run #38981187214](https://github.com/yoonsj0305/NEUMANN/actions/runs/38981187214): **15-second TIMEOUT**, 15,022.472ms native original-query wall, exact source untouched. Artifact `NEUMANN_REAL_SQUARE_CLASSICAL_FIRST_20261017.zip` SHA256 `9ed84b72e499a616623873f6c909646ff20db1701ab3d0673f11b2c785aee33c`. Direct solver timeout is NOT classical impossibility.

### Concrete human-authored original invariant certificate

AFTER inspecting the original, a researcher supplied the following source-specific full interpretations, not pretrained/NEUMANN learned output. Let
`R(a,t) = ((a<=0 AND t=a) OR (a>0 AND 0<=t<=a))`,
`Sum(a,t) = a*(a-t)`, `Total(a)=ITE(a<=0,0,a*a)`.

- `inv_main3(n) := true`.
- `inv_main8(a,b,s,t) := (a=b) AND s=Sum(b,t) AND R(a,t)`.
- `inv_main13(a,b,s,t) := (a=b) AND s=Sum(b,t) AND R(a,t)`.
- `inv_main22(a,b,c,s,t) := (a=c) AND (b=Total(a)) AND s=Sum(c,t) AND R(a,t)`.
- `inv_main26(a,b,c) := (b=c)`.

The source's loop steps decrement `t` and increment `s` by `a`, so `s=a*(a-t)` is inductive. The stopping guard `t<=0` plus `R` entails `s=Total(a)`, including **negative and zero starting values**. The final original error rule can hold only if the two computed totals differ, contradicted by `inv_main26`.

[Runnable independent verifier and exact SMT definitions](https://github.com/yoonsj0305/NEUMANN/blob/research/core35-rusthorn-real-source-gate-20261016/research/evidence/fgsr-real-square-20261017/original_9_clause_certificate.py) fetches the externally pinned exact source, checks its SHA, and **independently refutes the negation of each ALL NINE untouched original quantified clauses** after substitution of interpretations.

- Initial [GitHub Actions #38981479182](https://github.com/yoonsj0305/NEUMANN/actions/runs/38981479182) **BLOCKED before any SMT proof**: our strict source-declaration checker wrongly expected `CHC_COMP_FALSE` despite the original having a **direct `false` goal**, not a sixth relation. Original receipt archived and NOT counted as failure of mathematical witness. Fixed only declared-relation validation, no mathematical formula or source changes.
- Actual corrected [GitHub Actions #38981620887](https://github.com/yoonsj0305/NEUMANN/actions/runs/38981620887): **9/9 original negated assertions UNSAT** with original-source SHA verified and Z3 4.13.3. Nine obligation solve walls: `[0.899,1.558,1.156,1.539,1.152,1.188,1.154,1.239,0.434]` milliseconds, sum **10.319ms** (excludes setup/source retrieval). Entire runner-side proof script **52.118ms** after remote original received, including negative control.
- **Negative control**: replace original terminal relation's equality `inv_main26(a,b,c) := (b=c)` with `true` and rerun original safety clause. The ninth original proof obligation now **SAT**, meaning this checker rejects a false proof instead of declaring everything UNSAT.
- Actual first corrected proof ZIP artifact ID **12080634095** / `NEUMANN_REAL_SQUARE_CORRECTED_PROOF_20261017.zip`, includes one original-proof JSON receipt. GitHub Actions green CI here means successful verified original proof by classical *human-authored* certificate, not model gain.
- All steps CPU only, zero neural forwards, original never modified, license of external source not assumed (file fetched from pinned GitHub, not distributed in user ZIP).

### Research boundary / stop

The frozen former `torch.nn.Linear(6,3)` 18-weight head only accepts one synthetic 3-Int relation and two unit-step transitions. This external source has **five predicates of arities 1,4,4,5,3**, and the frozen model's valid input representation **cannot parse it**. **ABSTAIN without model call** is mandatory. Extending the extractor AFTER seeing this source and claiming a clean heldout win would invalidate the experiment.

This **closes the external original's mathematical safety proof**, NOT NEUMANN's autonomous relation invention, cross-family neural transfer, end-to-end computation advantage, or frontier-level Q1–Q7. The apparent difference between 15s direct solver and 10.319ms checked certificate is **not an algorithmic speedup ratio**: the human effort to discover/write the certificate was not charged. The conceptual result supports **structure-first proof compression**, but does NOT demonstrate the learning head found that structure. Stronger classical provers may synthesize it automatically.

**STOP** on more opened-source special-case classical proofs. To promote Q3, freeze a learned source-conditioned grammar/relationship constructor BEFORE any *different* independent external family, then prove its neural output by all-original independent checker, compare source-aware strong classical synthesizers and matched full costs.
