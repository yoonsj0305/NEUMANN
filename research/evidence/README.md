# Published opened research evidence

The human authorized this consolidated publication on 2026-10-09. These are
copies of already opened NEUMANN research evidence. `publication-sources.json`
records original local provenance, byte counts and SHA-256 identities. Copying
or transporting an archive does not replace its first result or grant fresh
evaluation status. Missing archives remain missing in the audit registry.

- `p1-recovered/`: eight recovered first ZIPs, retained printed diagnostics and
  model-free replay receipts. The original P1.7 replay failure remains FAIL.
- `bp-certificate-2026-10-08/`: the first 16-source, 576-observation CPU
  diagnostic. Its ZIP and report have separate identities.
- `probabilistic-native-2026-10-08/`: the frozen runner, source contracts,
  preparation attempts and first 125-job CPU archive. Outcome: INCOMPLETE.
- `native-readiness-2026-10-08/`: the existing native-tool readiness archive.
- `counting-2026-10-08/transport-manifest.json`: byte-exact transport index for
  the 165,751,643-byte counting first ZIP. The 20 chunks and verifier are on
  [the separate evidence branch](https://github.com/yoonsj0305/NEUMANN/tree/research/neumann1-counting-evidence-2026-10-09/research/raw-counting-evidence).

The counting branch is storage for first evidence, not a merge candidate.
Verify each chunk and the joined SHA-256 using its `reassemble.py`; the result
must match `004d8ed4e7ced5b62af6e629686c859e398fd2a3e2962b9d5b0c33b4b0148e61`.

Run the publication's unit checks from the repository root, for example:

```sh
python -m pytest -q tests/test_historical_causal_audit.py tests/test_bp_certificate_diagnostic.py tests/test_counting_native_headroom.py tests/test_probabilistic_analytic_controls.py
```

Those checks inspect retained evidence and engineering fixtures. They do not
rerun first performance experiments or start model inference/training. The P1
reader now defaults to these repository copies. Historical analysis scripts
which name an external Continuation directory retain their original provenance;
their JSON/CSV outputs are published and missing external inputs are not inferred.

No sealed Decision 3 payloads, unrelated account exports, installed dependencies
or browser credentials are included. The research decision is HOLD_LEARNING.
