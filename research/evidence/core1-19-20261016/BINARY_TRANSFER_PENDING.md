# Binary evidence transfer: 25-archive current ledger

GitHub PR #180 contains the complete **scientific text records and 25 original ZIP SHA-256 identities**, but **not the binary ZIP bytes or model checkpoints**.

## Complete local vault, validated 2026-10-16

- `NEUMANN_CORE1_22_COMPLETE_LOCAL_VAULT_20261016.zip`
- SHA-256 `e021c4a9495dbc74aee4df70bafb73b3f86f689537a27fa144c33ed1ed8f4ad5`
- Size: **2,417,287 bytes**.
- 25 original individual ZIPs: every file verified against its SHA-256 and ZIP CRC, both prior to creating this vault and after reading it back.
- Corrected archival manifest: `NEUMANN_CORE1_22_ARCHIVE_MANIFEST_20261016.json`, declares **25** records. An older local vault for CORE1–21 mistakenly declared 23 when it contained 24; the older original has been preserved instead of rewritten.
- Included upload helper: `NEUMANN_CORE1_22_ARCHIVE_UPLOADER_20261016.py`. Dry-run result: **LOCAL_PREFLIGHT_PASS 25 archives 2436578 bytes** and **DRY_RUN**, no GitHub mutation.

## Binary upload instruction and secure boundary

On the owner's locally GitHub-authenticated computer, download and SHA-256-check the full vault, then extract it. Run `python NEUMANN_CORE1_22_ARCHIVE_UPLOADER_20261016.py` to recheck all 25 local blobs. If ready, run the same command with `--push`. This uses only the isolated branch `research/core1-19-evidence-audit-20261016`, refuses clobbering existing source files, rejects a moved branch head, and checks remote Git blob contents byte-for-byte. Do not put GitHub tokens into chats; use local `gh auth login` or an environment variable.

**Remote archive upload is NOT complete until `ALL_25_ARCHIVES_UPLOADED_AND_REMOTE_VERIFIED` and remote SHA readback are observed.** Scientific Q1–Q7 remain OPEN; no reported frontier or neural superiority.
