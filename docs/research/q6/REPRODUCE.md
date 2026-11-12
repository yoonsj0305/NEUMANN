# Reproduce the frozen SOURCE study

The archived results are immutable. `prepare`, `run`, `grade` refuse to overwrite
their first files. Replay in a new worktree at the exact pre-evaluation producer
commit, preserved in a small Git bundle. No original benchmark examples are
republished in this repository.

## 1. Recover the precise frozen producer

From the repository containing this PR (the baseline commit must be available):

```bash
OPENBLAS_NUM_THREADS=1 python research/q6/verify_archive.py
git bundle verify docs/research/q6/results/source_v1_20261112/source_freeze.bundle
git fetch docs/research/q6/results/source_v1_20261112/source_freeze.bundle HEAD:refs/heads/q6-source-v1-frozen
git worktree add --detach --no-checkout /tmp/neumann-q6-source-replay q6-source-v1-frozen
git -C /tmp/neumann-q6-source-replay sparse-checkout set --no-cone \
  /neumann1/ /research/q6/ /research/q3/invention_first.py \
  /research/q3/sequence_specialist.py /tests/q6/ /docs/research/q6/ \
  /docs/experiments/results/spec_core_dev_source.json \
  /docs/experiments/results/spec_core_inverses.json \
  /docs/experiments/results/invention_core_frozen.json \
  /docs/experiments/second_evidence_seal.json \
  /docs/experiments/third_evidence_seal.json
```

Frozen HEAD must be `c95fd10d016650485a1a38fcf45b855674863070`.
Use a different new worktree path if the example path already exists.

## 2. Prepare an original-author metadata clone

If the pinned BIG-bench clone used for the original work is available, reuse it.
Otherwise, in a new directory:

```bash
git init /tmp/neumann-q6-bigbench
git -C /tmp/neumann-q6-bigbench remote add origin https://github.com/google/BIG-bench.git
git -C /tmp/neumann-q6-bigbench config remote.origin.promisor true
git -C /tmp/neumann-q6-bigbench config remote.origin.partialclonefilter blob:none
git -C /tmp/neumann-q6-bigbench fetch --depth=1 --filter=blob:none origin 092b196c1f8f14a54bbc62f24759d43bde46dd3b
```

No task body checkout is needed. The study fetches only its exact 125 authorized
SOURCE blobs. It has no OEIS, A001, FRESH or rule TARGET loader path.

## 3. Execute a separately labeled replay

Python 3 with the repository's existing runtime dependencies is required;
`pytest` is needed only for tests. No learned weights, accelerator or model API.

```bash
cd /tmp/neumann-q6-source-replay
OPENBLAS_NUM_THREADS=1 python -m pytest -q tests/q6
OPENBLAS_NUM_THREADS=1 python -u research/q6/source_study.py prepare --bigbench /tmp/neumann-q6-bigbench
OPENBLAS_NUM_THREADS=1 python -u research/q6/source_study.py run
OPENBLAS_NUM_THREADS=1 python -u research/q6/source_study.py grade --bigbench /tmp/neumann-q6-bigbench
```

The frozen version has the original 9 tests; the final integration facade adds
3 separately tested fail-closed cases. All 320 receiver/arm records are required
before grading. CPU cutoffs can affect marginal cases, so bit-identical runtime
or all 320 selected programs is not promised. Never replace the archived FIRST
outcomes with a favorable replay.

## 4. Additional controls and recorded witness replay

The final review branch includes the post-primary control and audit scripts.
After completing steps 1–3, copy only these new diagnostic scripts from the final
PR checkout to the separate replay worktree. Run this block from the final PR
checkout first; do not run it inside the frozen worktree:

```bash
Q6_REVIEW_ROOT="$(git rev-parse --show-toplevel)"
cp "$Q6_REVIEW_ROOT"/research/q6/{negative_controls,primitive_context_control,witness_audit,final_analysis,probe_disagreement,reproduce_witness}.py \
  /tmp/neumann-q6-source-replay/research/q6/
cd /tmp/neumann-q6-source-replay
```

Then run the diagnostics there. The separately generated primary results and
TRAIN cache from step 3 are the inputs; the published first archive stays intact:

```bash
OPENBLAS_NUM_THREADS=1 python research/q6/negative_controls.py
OPENBLAS_NUM_THREADS=1 python research/q6/primitive_context_control.py --bigbench /absolute/path/to/the/pinned/bigbench
OPENBLAS_NUM_THREADS=1 python research/q6/witness_audit.py
OPENBLAS_NUM_THREADS=1 python research/q6/final_analysis.py
OPENBLAS_NUM_THREADS=1 python research/q6/probe_disagreement.py
OPENBLAS_NUM_THREADS=1 python research/q6/reproduce_witness.py
```

These preserve first receipt files too. Use a new replay worktree for another
run; do not delete or rewrite published evidence. Timing can change the primary
solutions selected in a replay, and those are separately labeled results.
Primary and post-primary scopes remain distinct. The recorded
TRAIN-only witness replay regenerated the exact AST and again returned UNKNOWN
with mapping removed; see `witness_generation_replay.json`.

The code/knowledge/provenance hashes are in `freeze.json`; final artifact hashes
are in `seal.json`. The source task cache is reconstructed outside the repository
by `prepare`. It is not a required private input or a target answer oracle.
