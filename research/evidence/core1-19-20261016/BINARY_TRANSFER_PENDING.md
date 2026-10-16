# Binary evidence transfer | CORE-1–26 · 31 original ZIP archives

**The GitHub PR presently contains scientific reports and 31 locally verified archive SHA256 identities, NOT the original ZIP binary payloads or checkpoint weights.** No remote archive completion is claimed.

## Verified latest local vault

- Bundle: `NEUMANN_CORE1_26_COMPLETE_LOCAL_VAULT_20261016.zip`
- Exact SHA256: `07e73a62c30103a47739afe76cee7482252ffcb741c8b7ae565d1321f5ad300e`
- Bundle size: **2,957,951 bytes**
- Original experiment ZIPs: **31**, combined original nested ZIP bytes 2,980,867, each SHA256-verified, each CRC-tested.
- Uploader: `NEUMANN_CORE1_26_ARCHIVE_UPLOADER_20261016.py`
- Freshly extracted local readback: `LOCAL_PREFLIGHT_PASS 31 archives 2980867 bytes`, followed by `DRY_RUN: no GitHub mutation`.

## One safe remote import path

1. Download the exact local vault from the producing ChatGPT response. Verify whole-vault SHA256.
2. Extract. Run `python NEUMANN_CORE1_26_ARCHIVE_UPLOADER_20261016.py` from inside the extracted folder. It verifies each of 31 ZIP archive byte identities *without contacting GitHub*.
3. Authenticate using `gh auth login` or set repo-scoped `GITHUB_TOKEN` locally. Do not disclose credentials in chat.
4. Run `python NEUMANN_CORE1_26_ARCHIVE_UPLOADER_20261016.py --push`. The helper is restricted to the specific research branch, rejects overwriting archive paths, does not force-push or rewrite historic evidence, and checks uploaded Git blobs after the commit.
5. Only declare remote ZIP upload complete when the tool prints `ALL_31_ARCHIVES_UPLOADED_AND_REMOTE_VERIFIED` and the remote binary SHA values match the manifest.

This document records a tested dry-run only. CORE-26 confirms the source proof (tree mirror/height) but the required equality form was visible from paired `ff` safety guards. **New learned abstraction invention is not proven; Q1–Q7 OPEN**.