# Binary evidence transfer | CORE-1–25 · 30 original ZIP archives

Scientific report text and SHA256 catalog are committed in research draft PR #180. **The original binary ZIPs, source bundles and model checkpoints are NOT remotely uploaded.** Do not claim the remote archive is complete.

## Independently verified local vault

- Filename: `NEUMANN_CORE1_25_COMPLETE_LOCAL_VAULT_20261016.zip`
- Exact SHA-256: `e5df3488e8dd7aa6dae1ceb03eaeffd99e88653461168a1fe21063c31903ad27`
- Size: **2,946,446 bytes**
- Includes **30** individually SHA-256 and CRC-verified original experiment ZIP archives (combined inner ZIP bytes: **2,969,158**), local JSON manifest and source-checking binary uploader.
- Importer file: `NEUMANN_CORE1_25_ARCHIVE_UPLOADER_20261016.py`
- Independent extraction dry-run: **`LOCAL_PREFLIGHT_PASS 30 archives 2969158 bytes`** followed by **`DRY_RUN: no GitHub mutation`**.

## Verified-upload procedure (user-side GitHub-authenticated environment required)

1. Download the latest vault from the ChatGPT conversation and verify its exact SHA-256.
2. Unzip. Authenticate GitHub in a local terminal using `gh auth login`, or use a scoped `GITHUB_TOKEN` with repo write access. Never share tokens in the chat.
3. Run `python NEUMANN_CORE1_25_ARCHIVE_UPLOADER_20261016.py` and verify all 30 original ZIP byte identities in dry-run mode.
4. Run `python NEUMANN_CORE1_25_ARCHIVE_UPLOADER_20261016.py --push` ONLY from a trusted, authenticated environment. It does not force-push or overwrite and verifies remote Git blobs after a fast-forward commit on the research branch.
5. **Only after** output `ALL_30_ARCHIVES_UPLOADED_AND_REMOTE_VERIFIED` and matching remote SHA values is GitHub byte-level archival complete.

Q1–Q7 remain OPEN. CORE25 passed a new kind of narrowly prewritten nil-shape auxiliary on development source but failed 0/4 incompatible heldout family type preflights; strong exact baseline wins. Neither research truth nor archive state may be upgraded because these instructions were written.