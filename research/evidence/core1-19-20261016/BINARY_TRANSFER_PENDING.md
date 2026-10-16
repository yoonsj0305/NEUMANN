# Binary evidence transfer | 24-archive current ledger

GitHub PR #180 currently contains **scientific records and 24 SHA256 archive identities, but NOT the original ZIP byte streams or checkpoints**. Do not mark this archive remote complete until all byte streams are uploaded and verified.

## Local complete bundle, independently verified

- `NEUMANN_CORE1_21_COMPLETE_LOCAL_VAULT_20261016.zip`
- Complete bundle SHA256: `09dcfbb5443dd8dfdfa71a573294cba5c1dcaf9bee33a95545fa2a21a6ff9254`.
- Contains **24** original individually SHA256-checked, CRC-valid ZIPs, an exact JSON manifest and the upload utility.
- Import utility: `NEUMANN_CORE1_21_ARCHIVE_UPLOADER_20261016.py`.
- Tested after separate ZIP extraction: `LOCAL_PREFLIGHT_PASS 24 archives 2315875 bytes` and dry run performed **NO GitHub mutation**.

## Complete remote import procedure (must run in locally GitHub-authenticated session)

1. Obtain the bundle download from the producing ChatGPT conversation and verify the SHA256.
2. Unzip it into one local directory.
3. Use `gh auth login` or provide `GITHUB_TOKEN` with repository write permission on your own machine. Never share your token.
4. Execute `python NEUMANN_CORE1_21_ARCHIVE_UPLOADER_20261016.py`; expect `LOCAL_PREFLIGHT_PASS 24 archives`.
5. Execute `python NEUMANN_CORE1_21_ARCHIVE_UPLOADER_20261016.py --push` to create 24 Git binary blobs, one fast-forward commit in the research branch, and perform byte-for-byte remote readback.
6. Only treat upload as complete after **`ALL_24_ARCHIVES_UPLOADED_AND_REMOTE_VERIFIED`** appears and each recorded SHA256 matches the GitHub file bytes.

Additional caveat: the uploader intentionally refuses overwriting existing evidence archive paths and rejects branch-head changes rather than force pushing. All results and past Q1–Q7 verdicts are frozen and unaffected.