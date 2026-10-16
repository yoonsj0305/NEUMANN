# Binary evidence transfer | CORE-1 through CORE-24 · 29 archives

**GitHub PR #180 currently contains research reports and SHA-256 identities, NOT original ZIP byte streams/checkpoints.** A complete locally CRC/SHA256 verified vault with the uploader is available in the producing ChatGPT conversation.

## Verified local bundle

- Name: `NEUMANN_CORE1_24_COMPLETE_LOCAL_VAULT_20261016.zip`.
- Exact SHA-256: `f5c1953cb623857e407a31f9ad9a23a9eba7e6fadbb576c9cdfaa7913d9127d5`.
- Outer vault: 2,876,651 bytes, 29 *original* individually verified experiment ZIPs (2,899,135 combined uncompressed archive bytes), plus JSON manifest and upload helper.
- Uploader: `NEUMANN_CORE1_24_ARCHIVE_UPLOADER_20261016.py`.
- On independent extracted local preflight: `LOCAL_PREFLIGHT_PASS 29 archives 2899135 bytes`, `DRY_RUN: no GitHub mutation`.
- Original ZIP CRC checks all passed. The included uploader independently validates SHA-256 and file byte size for every archive before network access.

## Authenticated one-shot binary upload

1. Obtain the ZIP using its ChatGPT conversation download link. Confirm SHA-256 equals the value above.
2. Extract the bundle locally.
3. Authenticate `gh auth login` OR provide a repo-scoped `GITHUB_TOKEN` in your terminal. Do not paste tokens into ChatGPT or commit them.
4. Run `python NEUMANN_CORE1_24_ARCHIVE_UPLOADER_20261016.py` first to verify all 29 ZIP identities **without writing**.
5. Run `python NEUMANN_CORE1_24_ARCHIVE_UPLOADER_20261016.py --push` to stage 29 Git blobs under the dedicated research branch. It rejects overwrites and concurrent branch changes, creates one fast-forward commit, and rereads remote Git blobs to verify all SHA-256s.
6. Only say binary upload is DONE if it prints `ALL_29_ARCHIVES_UPLOADED_AND_REMOTE_VERIFIED` and the remote archive path is actually present.

**No GitHub binary upload was executed by this ChatGPT session** because the active GitHub connector does not ingest the local binary byte stream. The present draft PR should remain draft until verified import. Historic results remain development-only and Q1–Q7 OPEN.