# Earlier opened NEUMANN evidence

This storage branch publishes fourteen previously local first ZIPs and the
initial Master v2 audit snapshot transport. `manifest.json` lists each source,
byte count, SHA-256 and ordered parts. It also preserves each phase-1 snapshot
member's identity. The source archives remain unchanged; this is not a scientific
rerun, replacement result, new capability claim or main merge candidate.

The material includes P1.12/P1.13, code/reuse controls, native continuation,
OCaml source binding, SuFu native/build/replays and Synduce records. Build caches,
installed dependencies and unrelated private workspace exports are excluded.

From `research/raw-continuation-evidence/`:

```sh
python verify_archives.py
python verify_archives.py --archive PHASE1_AUDIT_SNAPSHOT.transport.zip --output /absolute/path/snapshot.zip
```

The first command verifies all part hashes and joined archive identities without
extracting or executing archive members. The second additionally writes only
the selected archive to a new file, refusing to overwrite an existing output.
For another archive, use its exact `original_file` from the manifest.

Research entry point: [consolidated audit PR #176](https://github.com/yoonsj0305/NEUMANN/pull/176).
The research decision remains HOLD_LEARNING. Historical PASS/FAIL/INCOMPLETE
verdicts are preserved.
