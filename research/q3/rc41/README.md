# RC41 · Actual original Architecture Multiplier opened-task classical ceiling

**26 October 2026 · RESEARCH-ONLY Draft. Do not merge as global Q3/4.**

## Key result, not another neural toy

We implemented a NEW model-free, public-input-only deterministic route for the
EXACT 12 author-constructed opened Architecture Multiplier source tasks.
Raw task SHA256 `ad32fd947e4c63fc1b67f849254bb16bd62fad6067bd719d5ad3da6c1f11e99f`
and model-visible SHA256
`c883a44136817bf2501549a42c268b29577b8f153b3ca95b807e7ab245fdd2f0`
match the official frozen original first-run manifest. These identities are
checked by the GitHub CI directly against the original
`experiments/general_multiplier_tasks.py`.

Four EXACT arithmetic tasks are solved with Fraction+AST, four coding tasks
with a hand-authored **small compositional English specification parser**
emitting a safe solve(items) program, and four finite CSP tasks with exact
classical backtracking. All candidates use only the exact model-visible
`instruction,public` record, not task ID/family/private gold.

**12/12 of the original opened problems pass** semantic independent checks:
math Fraction against original private gold; CSP ORIGINAL complete constraints;
coding ORIGINAL `general_python_worker_v106.execute` allowable AST semantics
and original retained hidden finite test cases. CI calls original worker's
`execute` directly without simulating original process kernel caps. Separate
full ZIP has a subprocess semantic mirror and 2s wall limit; original
RLIMIT_AS=256MiB/CPU=1s could not be reproduced in this restricted
container. The four generated Python programs are thus VERIFIED against the
frozen code semantics and tests but NOT a real original accelerator worker run.

**0 neural forwards / 0 neural training / 0 GPU.** Tiny deterministic solver
CPU excludes the original checker; full local package wall clock including
checker processes is recorded separately, and no cross-hardware speed ratio is
claimed. The developer-written grammar was built POST-HOC on OPENED tasks,
so NOT a prospective unseen neural-vs-classical comparison.

## Critical authority boundary

The IMMUTABLE official October 3 first accelerator Decision2 **FAIL** stays
unchanged: DIRECT 0/12, TOOL 0/12, NEUMANN 0/12, model 72/72 calls at
256-token caps, 0 final-channel action, 0 tool calls. This additional
deterministic executor is NOT one of the registered three arms; it DOES NOT
retrospectively modify their 36 terminal observations or compute a valid
Architecture Multiplier value.

**Actual engineering decision:** the 12 opened tasks are sufficiently
classically tractable that further small-network tuning on these author
examples should be STOPPED as NEUMANN's mainline. Next neural spending
needs an independently authored unseen problem family, matched strongest
classic algorithms, independent original verification, and all-in cost
accounting. Only after a new separately frozen *opened control-plane*
architecture passes Decision2 should a sealed frontier/general test be
opened. Failing one small grammar is never global classical impossibility.
Global Q1-Q7, notably Q3/Q4/Q6/Q7, all remain OPEN.

## Complete clean reproducible package

`NEUMANN1_RC41_OFFICIAL_AM1_CLASSICAL_SATURATION_20261026.zip`
SHA256 `4b8b6c3adbe7ebcf15e8ad65bca3a750dd2678212fe2e92c9e76ee2860dcc6a9`.
**11 actual files**, direct mirror of official task public/private corpus and
identity check, model-free solver, source-private separate semantic verifier,
first frozen 12 task candidate receipts, manifest SHA, six regression tests.
CLEAN extract `bash REPRODUCE.sh` PASS; exact first candidates and hashes
match; 6/6 pytest PASS. User-download file in original conversation.
GitHub branch holds slim executable classical route and test against
OFFICIAL imported source, not duplicate private fixtures.

RC41's "PASS" is **only**: frozen source identity + 12/12 original
opened development tasks passed under a model-free additional route.
