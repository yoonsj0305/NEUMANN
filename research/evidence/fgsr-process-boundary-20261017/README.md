# NEUMANN 1 | FGSR verification-cost deletion (2026-10-17)

**Question:** Can we delete 26 redundant Python process startups while preserving the original RustHorn 13-clause proof and negative controls?

**Bounded ENGINEERING test only. No learned Q3, global Q4, Q7, or 10x model claim.**

Both implementations call the exact same `core35.native_evaluate` code, which allocates and frees a fresh Z3 context for **every individual clause**. Only process orchestration changes.

- Verified sources: pinned original safe/unsafe `chc-comp/rust-horn`, exact SHA256 and Git SHA-1 blobs.
- 27 unchanged original obligations: 13 SAFE, 13 UNSAFE and one deliberately corrupted SAFE original rule.
- Prior: `core35.one`, separate Python process and native context per clause; 4-second hard subprocess timeout per clause.
- New: ONE Python process, but **fresh native context for each clause**. Parent enforces an aggregate 112-second hard process timeout. Timeout granularity differs; do not imply identical real-time isolation.
- Proof admission: SAFE 13/13 UNSAT, UNSAFE 12/13 UNSAT + 1 SAT, poisoned SAT, and exact paired outcome equality across all 27. UNKNOWN, timeout, missing/mutated original, parse failure: ABSTAIN.
- Paired frozen order: resident then per-clause; single-run wall records include Python process startups and native proof checks but exclude source discovery, manual witness invention, training, environment installation and human labor. No claimed energy, GPU or end-to-end advantage.

Reproduce from repo root with Linux native Z3:

```bash
python research/evidence/fgsr-process-boundary-20261017/fgsr_resident_original.py --fetch-upstream --output /tmp/fgsr-receipt.json
```

This audit deliberately reuses an **already opened** human-authored witness and cannot establish a neural semantic invention or novel-family transfer. Its only potential win is removal of redundant verification-process work. ALL Q1–Q7 remain OPEN.
