# Binary research archive transfer | CORE-1–27

GitHub draft PR #180 currently contains scientific reports, frozen verdicts and **32 original ZIP artifact SHA-256 identities**, NOT the ZIP binaries or neural weights.

## Locally verified latest complete vault
- Filename: `NEUMANN_CORE1_27_COMPLETE_LOCAL_VAULT_20261016.zip`.
- SHA-256: `d64a1213d216691353a99ec8d51e95dd4be2c9f720b9d943b5084eda90b43828`.
- Total size: **2,992,388 bytes**.
- Nested original ZIPs: **32**, aggregate 3,016,081 original compressed bytes, each CRC- and SHA-256-verified.
- Local uploader: `NEUMANN_CORE1_27_ARCHIVE_UPLOADER_20261016.py`.
- Independent extraction + dry run: `LOCAL_PREFLIGHT_PASS 32 archives 3016081 bytes`; `DRY_RUN: no GitHub mutation`.

## Required verified binary handoff
1. Download the above archive from the producing ChatGPT response. Independently check its SHA-256.
2. Extract on your own GitHub-authenticated computer. Verify the uploader source first. Use `gh auth login` or a minimally scoped GitHub token in your terminal; do not paste credentials into ChatGPT.
3. Run `python NEUMANN_CORE1_27_ARCHIVE_UPLOADER_20261016.py` first. It only validates local SHA-256/CRC.
4. Run `python NEUMANN_CORE1_27_ARCHIVE_UPLOADER_20261016.py --push` on the research branch. It is intended to fail closed on overwrites/concurrent changes, create one fast-forward commit, then reread remote bytes.
5. **Declare remote binary archival complete only after** `ALL_32_ARCHIVES_UPLOADED_AND_REMOTE_VERIFIED` and matching remote ZIP checksums.

No authenticated binary transfer has been performed from this conversation. Q1–Q7 are unchanged (all OPEN); CORE-27 exhibits a human-framed off-goal intermediate with learned operator token, NOT independent neural abstraction-language invention.
