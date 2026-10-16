# Binary archive handoff | CORE-1–28, 33 ZIP archives

**GitHub research draft PR #180 contains the scientific text results and SHA-256 identities only. The original ZIP files and neural checkpoints are NOT on GitHub.**

## Exact complete local vault
- `NEUMANN_CORE1_28_COMPLETE_LOCAL_VAULT_20261016.zip`
- SHA-256: `9e46040023238e99477824cf63e2c82b6bc2df9530e98350a0f06188343d9344`
- 3,012,355 bytes in outer ZIP; 33 original experiment ZIP archives, combined compressed archive payload 3,036,902 bytes
- All 33 archives passed nested ZIP CRC and independent SHA-256 equality to the exact per-file manifest.
- Uploader: `NEUMANN_CORE1_28_ARCHIVE_UPLOADER_20261016.py`, included in complete local vault.
- Independently extracted local readback reports: `LOCAL_PREFLIGHT_PASS 33 archives 3036902 bytes`, `DRY_RUN: no GitHub mutation. Add --push for the isolated branch.`

## Safely transferring exact bytes (in user-authenticated local terminal)
1. Download the complete local vault from the generating ChatGPT turn; verify its exact outer SHA-256.
2. Extract and inspect uploader code. Authenticate via `gh auth login` or a narrowly scoped local GitHub token. Never share credentials in the chat.
3. First run `python NEUMANN_CORE1_28_ARCHIVE_UPLOADER_20261016.py` with no flags. The dry-run checks all archive bytes and does not modify GitHub.
4. Then run `python NEUMANN_CORE1_28_ARCHIVE_UPLOADER_20261016.py --push`. Importer is restricted to the audit branch, refuses overwriting existing evidence paths, uses a fast-forward commit, and checks all remote Git blob hashes after upload.
5. Only report complete binary preservation after `ALL_33_ARCHIVES_UPLOADED_AND_REMOTE_VERIFIED` and all 33 remote identities match.

**Scientific caution:** CORE-28 demonstrates a goal-hidden CLASSICAL typed theorem generator that produced an off-goal lemma and original 11/11 certificate, but it still depends on HUMAN-CODED functional meaning. It contains NO learned abstraction invention, and official global Q1–Q7 remain OPEN.