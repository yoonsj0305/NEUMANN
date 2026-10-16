# Evidence binary transfer: current status and safe import

GitHub text ledger and CORE-20 report are committed to this branch. **The following binary artifacts are NOT committed** and the draft PR must remain draft until their 23 original ZIP byte streams are verified in GitHub.

## Complete locally CRC-verified vault
- Filename: `NEUMANN_CORE1_20_COMPLETE_LOCAL_VAULT_20261016.zip`
- SHA-256: `8c22f48c079ecc591b8b3e831a4d58931fa2631018fb1c0dcfb5cf0275dd4a4c`
- Contains **23** individual experiment ZIPs (N1 G0 + CORE1–20, including proof audits), complete SHA-256 manifest and binary upload helper script.
- ZIP CRC was confirmed in the ChatGPT working container. The helper performed a preflight dry-run and verified all 23 archive hashes and sizes. No remote ZIP bytes have yet been transferred.

## One-shot, fail-closed import (requires local GitHub authentication)
1. Download the complete vault from the generating ChatGPT conversation and unzip it into a folder.
2. Install GitHub CLI and run `gh auth login`, or set `GITHUB_TOKEN` with write access to `yoonsj0305/NEUMANN`. Never paste a token into ChatGPT.
3. Run `python NEUMANN_CORE1_20_ARCHIVE_UPLOADER_20261016.py` from that folder to verify all 23 archives without writing to GitHub.
4. Run `python NEUMANN_CORE1_20_ARCHIVE_UPLOADER_20261016.py --push` to upload ZIP blobs in ONE fast-forward commit to the existing branch only.
5. The script rereads all uploaded Git blobs and asserts SHA-256 equality. The script never force-pushes, checks for existing archive paths, and aborts on altered branch head or mismatched content.

**Do not mark the binary archive complete until the script prints `ALL_23_ARCHIVES_UPLOADED_AND_REMOTE_VERIFIED` and the branch contains every ZIP path.**

Scientific verdict remains unchanged: actual learned general abstract invention and strong matched compute superiority are not established; Q1–Q7 remain OPEN.