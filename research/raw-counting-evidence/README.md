# Immutable counting first evidence transport

This branch stores the original opened `COUNTING_NATIVE_FIRST.zip` in twenty
ordered chunks. The original archive is 165,751,643 bytes and was INCOMPLETE:
12/17 cases certified, five certificate-generation timeouts. Partitioning is
transport only; the original archive contents and verdict are unchanged.

All paths are under `research/raw-counting-evidence/`. From that directory:

```sh
python reassemble.py
python reassemble.py --output /absolute/path/COUNTING_NATIVE_FIRST.zip
```

The first command checks each part and the SHA-256 of the joined stream without
writing an archive. The second writes a new file only if the whole joined stream
passes the same checks; it refuses to overwrite an existing output. Python's
standard library is sufficient. No archive member is executed or extracted.

This is a research-evidence storage branch, not a proposed main merge, new
experiment or scientific PASS. It shares ancestry with PR #175 only to preserve
repository history. Source parts and original hash are in `manifest.json`.
