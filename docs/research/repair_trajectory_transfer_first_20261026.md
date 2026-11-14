# G0 Original Repair-Experience Transfer: immutable source-only first result
**2026-10-26 · before reading original 4th/5th answer strings.**
Previous prereg commit: `f23e20f7415a64308a28f0a39afcf80f5507f130`, task IDs `DateTime.000008,ShippingCode.000003,City.000010,Column.000002,Phone.000006,Email.000010,FilePath.000003,Number.000007,Currency.000005,UserAgent.000007`.

Exact complete source-only artifact sha256 **`4a158ee6cbf5b3d92d6fde90a2996422e29605e60107c442a097481cdb07304b`**; Python source sha256 **`c5f3cd231cb219cd141ea88415bdb7cfe9ba46d4ddffd7353ef833e72c419ecd`**, original source and unlabelled future inputs JSON sha256 **`3cf7228311175584de76fee26716da4050f4a213d97792c277105862f6b3b900`**. Original Microsoft PROSE spec Git blob SHA1 for all 10 included in full JSON. Complete runnable source and machine JSON accompany final conversation ZIP, not wholly on GitHub.

### Training evidence (only genuinely independent old developer tasks)
Original DEV 19 tasks grouped by original task identity:
- 11: first fit succeeds on example3; not informative new failure repair.
- 4: first fit fails true feedback.
- 2: no initial candidate.
- 2: insufficient original future or invalid y.
- 2 of 4 actual initial-program failures yield independently verified 1-atom C2 fixes on future examples: from `DateTime.000003` modify split ':'0 id→int; from `ShippingCode.000001` token uppercase-first→split space1. **Just TWO training episodes, not thousands of independent edits**.
- Two remaining failures cannot be repaired by within-grammar C2; not counted as positive training episodes.

### Original first source-only results, 9 eligible, 1 ineligible
- Trained historical 2-edit symbolic library adds **0 actual new verified edits**, across all 9 eligible. Not ownweight neural, zero causal discovery-policy claim.
- `DateTime.000008`, `Number.000007`, `UserAgent.000007`: no complete source program in bounded grammar.
- `ShippingCode.000003`: original 2-demo source-only predicts `['53','6']` but feedback contradicts; learned edit cannot act, outputs HOLD. Strong classical 3-demo separately predicts `['53','90']`.
- `City.000010`: original predicts `['9','20']` but 3rd feedback contradicts; learned edit produces HOLD. Strong C2 HOLD.
- `Column.000002`: all methods source+feedback predict `['column2','column6']`.
- `Phone.000006`: `['066','993']`.
- `Email.000010`: `['lamnahealtcare.com','woodgrovebank.com']`.
- `Currency.000005`: `['1438.10','966966.37']`.
- `FilePath.000003`: only 4 original demos, prereg **INELIGIBLE**, no replacement.
- All predictions computed before original future answer labels were checked. Candidate status only SOURCE_CONSENSUS and not proof of correctness. Total measured CPU and training costs in full first JSON.

This is an actual independent new-task evaluation of **transfer of a learned-in-symbolic-memory 2-edit *REPAIR LIBRARY***, NOT a trained NEUMANN neural policy: cannot claim global B/C. HOLD/OPEN for Q1–Q7. Strong classical C2 is the key equal-data comparator, includes third oracle. The 3rd original example is a provided labelled oracle, nonzero deployment cost.
