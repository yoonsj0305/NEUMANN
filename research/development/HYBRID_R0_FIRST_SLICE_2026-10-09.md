# NEUMANN 1: Hybrid R0 First Vertical Slice (2026-10-09)

**Verdict: \`HYBRID_R0_FIRST_SLICE_ENGINEERING_PASS\`**.  
**NOT verdicts:** \`HYBRID_R0_COMPLETE\`, learned structural discovery, R1, G1/G2, strong-native frontier performance, new Q1–Q7 closures, Edge energy saving.

**Base:** draft research PR #176 commit \`c182fd3f8d8b5c711415a214e899bfefe7511a0a\`; this is a dedicated research integration branch and **has not merged to main**. See [P0 asset manifesto](HYBRID_R0_P0_ASSET_MANIFEST_2026-10-09.md).

## Scope of implementation

- \`neumann1/hybrid_runtime_r0.py\`: single JSON stdin and persistent \`--jsonl\` CLI, structured domain validation, typed status, SHA-256 task identity, original-certification gate, timeout/dependency/invalid input fail closed, actual stage wall-clock and Linux RSS, fallback receipt, resource fields explicitly UNKNOWN when unmeasured.
- \`neumann1/hybrid_sygus_r0.py\`: classic cvc5 SyGuS original goal solved; independent Z3 checks *three* original init / inductiveness / safety obligations. Legacy SyGuS declaration is translated with no altered target.
- \`lp.standard_form\`: Highs strong native + existing original independent LP primal/dual certificate, deterministic paid residual rank fixed4m with charged restricted and native fallback, externally provided rank explicitly uncharged/UNKNOWN, optional actual **original frozen v102** seeds 100001/100002 with immutable checkpoint restore, Q34 2m→4m original verifier and investment-amortization receipt.
- \`exact.linear\`: original numeric attempt checked with exact integers, exact Fraction fallback, independent check of **original** equation system.
- Denial and negative controls are first-class: malformed task, forged ranking, false certificate, singular matrix, SyGuS unsafe invariant, unsupported syntax, no cvc5 and unknown domain.

## First successful evidence

### CPU three-domain original-certificate acceptance

[GitHub Actions 37934146693](https://github.com/yoonsj0305/NEUMANN/actions/runs/37934146693), first green complete run with two jobs at code SHA \`05cfa0be3288ab6593be9fbde3fb6e9434f65647\`.

- \`cpu-classical-r0\`: **32 tests PASS, 0 FAIL** in 2.85s. \`tests/test_hybrid_runtime_r0.py\`, \`tests/test_hybrid_sygus_r0.py\`, and a separately executed exact rational JSON CLI request (verified).
- \`frozen-q34-reuse\`: six separately original LP certified *opened-development* observations, m64 and m128 original base views, each (native, paid deterministic fixed4m, actual frozen seed100001).
- Crucial actual immutable checkpoint ranking comparison: new recovered ranking exactly matches original historical v102 first timed ranking for each sampled view.
- All six preserved as \`VERIFIED\` full original LP primal and dual, **not just restricted solution**; no new model trained.
- Measured *single execution* wall times (ms): m64 Native **105.466**, Residual4m **62.708**, Frozen1 **1257.816** including cold checkpoint restore. m128 Native **501.306**, Residual4m **306.889**, Frozen1 **215.114** with checkpoint already cached.
- **Do not compute a performance speedup or draw deployment economics from these six untimed repeats**. First cold learned run is slower than strong native, and model restore, training investment, CPU memory, measured energy and future request volumes need their own cost policy.
- Frozen smoke JSON SHA256: \`b625467127a37f1543659d894b6503f5a820c4b77f95dd0524786ade1c25b9f7\`, first retained GitHub Artifact ID \`11617084817\`. CPU basic artifact ID \`11616869442\` (GitHub expiry applies). Native execution and source case provenance are retained separately from original v102 historic trial.

**Test distinction:** 32 green tests do not mean 32 unrelated scientific problems. 6 Q34 observations are 2 independent historic originals by three policies, not six fresh tasks.

## Minimal usage

Install optional native LP, z3 and a cvc5 CLI; the torch frozen path needs pinned original v102 CPU dependency environment and archived original v100/v101 source. In the configured CI environments:

\`\`\`bash
printf '%s\n' '{"domain":"exact.linear","A":[[2,0],[0,3]],"b":[1,1]}' \
  | python -m neumann1.hybrid_runtime_r0

printf '%s\n%s\n' \
 '{"domain":"exact.linear","A":[[2]],"b":[4]}' \
 '{"domain":"exact.linear","A":[[3]],"b":[6]}' \
  | python -m neumann1.hybrid_runtime_r0 --jsonl

python -m pytest -q tests/test_hybrid_runtime_r0.py tests/test_hybrid_sygus_r0.py

# Additional original v102 archive/frozen checkpoint smoke, NOT fresh:
python -m experiments.hybrid_r0_frozen_smoke_20261009
\`\`\`

All accepted answers include independently checked original proof; all other statuses must be treated as nonanswers.

## Why this is only a first slice

Remaining R0 completion requirements from [Notion Fast Finish Plan](https://app.notion.com/p/3f47830ff334812f9759c929af41d47c):
1. Audit clean integration and merge ancestry for #174/#175/#176; avoid auto merging drafts or overwriting original receipts.
2. Full opened BP/M106 negative-transfer runtime fixture and unchanged native fallback behavior; no learned economic transfer claims.
3. Complete compare/capability/receipt schema across all domains, including cold/warm and resource usage; current process startup, actual energy and dollars unknown.
4. Controlled documentation and installation on intended lower-memory Edge CPU vs Cloud policy. Device-specific power/energy still requires physical measurement.
5. Unseen family-disjoint new G0 headroom only after separate locked preregistration. New learned structural *generation* E3 remains blocked until positive G0.

**Decision:** KEEP working hybrid first slice; HOLD training; proceed only with necessary R0 engineering regressions, then ONE prospective high-value classical headroom G0. Old global Q1–Q7 remain OPEN; Decision3 remains sealed.
