# NEUMANN 1 · CORE-35 | Original RustHorn Horn certificate (2026-10-16)

**Scientific verdict: EXTERNAL_SAFE_WITNESS_CERTIFIED (post-hoc / researcher-supplied); LEARNED_STRUCTURAL_DISCOVERY_UNPROVEN. Global Q1–Q7 OPEN.**

## Source identity and preregistration
The [protocol was frozen in commit `1d1ae37`](https://github.com/yoonsj0305/NEUMANN/blob/research/core35-rusthorn-real-source-gate-20261016/research/evidence/core35-20261016/PREREGISTERED_PROTOCOL.md) *before reading* either source. External repository [chc-comp/rust-horn](https://github.com/chc-comp/rust-horn), pinned commit `e5a86a1ad252fe1df75e06814769ec1d14540032`.
Two real, byte-identical-to-upstream files were checked via both SHA-256 and Git blob SHA-1:

- `trees-2-inc-all-safe.smt2`: Git blob `75f06780eaa4d48f48c56228e007a9dbe87a9df6`; SHA-256 `713e61bb9abe535491e93a36581d1d16f2ba617e454366a1b589d692b0453456`; 2,788 bytes.
- `trees-2-inc-all-unsafe.smt2`: Git blob `e3029c62337109beace3c9c318ac4c316a848c20`; SHA-256 `df1b8a1d09829f72ba886ad5ae1f0460ae315a946fd55acdd70e6620419eb8bb`; 2,788 bytes.

Different benchmark family to CORE-31/32's `ADTRem/isaplanner/goal52_000.smt2`. Filename hints the labels, so this is **not label-blind**. No third-party source bytes are committed here.

## Frozen protocol: actual result
Unmodified real Horn source, fresh Z3 context/process, native `libz3.so.4`, OS-enforced 10-second cap per file:

| Actual source | Z3 original check-sat | Parent wall |
|---|---|---:|
| Safe | TIMEOUT (no result, not a proof failure) | 10.014 s |
| Unsafe | UNSAT (no model for the Horn relations) | 0.737 s |

The preregistered strict decision is **ABSTAIN**, because the safe file was not decided under the 10-second budget. The original protocol also disallowed supplying a theorem after examining the target.

## Explicitly marked exploratory protocol deviation
After seeing the actual source, **a human wrote an explicit proof witness** for all ten Horn relations based on two total recursive tree functions `SUM` and `SIZE` and the invariant

`SUM(output_tree) = SUM(input_tree) + SIZE(input_tree)`.

This witness was **not emitted by a frozen learner**, and its creation after target opening is a **protocol deviation**. It may prove a mathematical fact about this already-opened target but cannot earn preregistered learned Q3/Q6 admission. Do not count human design time as zero.

For each of the **13 original asserted Horn clauses**, the program retains the exact original source clause and tests the negation under the explicit witness in an independent Z3 check. Correctness of a proposed interpretation requires all 13 results UNSAT. No clauses were dropped, skipped, or replaced.

Actual local evaluation:

- Original **SAFE**: **13/13 negated clauses UNSAT**, including the real query safety clause.
- Original **UNSAFE** under the same witness: **12 UNSAT, 1 SAT** (clause #4, the main implication).
- **Poisoned witness** omitting the tree size delta: SAT on the actual safe source recursive increment clause (#2), so invalid certificate rejected.
- All 26 original clauses verified or rejected as above; a separate malformed-input/source-hash check fails closed.
- **Neural calls: 0.** Learned complete-source new auxiliary invention: **NOT PROVEN**.
- Certifying 13 clauses uses 13 separate Python/native-Z3 process starts and is not a matched end-to-end performance comparison to the 10s direct timeout. Real researcher time is not included.

This is strong *formal proof construction feasibility* evidence: adding a correct external relation closes a problem that raw bounded Z3 did not close, **but it does not demonstrate NEUMANN can discover that relation autonomously**.

## Reproduce
On Linux with Python 3.10+ and native Z3 shared library (`libz3.so`), run from this directory:

```sh
python core35.py --fetch-upstream --output receipt_core35.json
```

This downloads the two upstream original files at the pinned commit, checks both cryptographic hashes *before evaluation*, and writes a JSON receipt. An offline cache of the exact same files may be supplied with `--source-dir /path/to/files`. Exit/result codes of `UNKNOWN`, timeout, parse error, mismatched hash or missing negative-control check are **not proof of success**. The prototype was executed on Linux Python 3.13.5 with libz3.so.4; portable Windows loading is **not tested**.

## Next only admissible research gate
Freeze an **actual** whole-source + task-goal learned decoder and unchanged model weights *before opening a new external family*. Emit a genuinely unprovided predicate signature + all base/recursive Horn clauses, independently certify all original source clauses, and compare against the best source-derived classical synthesis with matched input information and full training/inference/proof/human/fallback costs. The RustHorn family is now contaminated for future blind validation; do **not** reuse it as fresh.

**All historic failures and Q1–Q7 remain OPEN.**
