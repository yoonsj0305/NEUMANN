# NEUMANN discovery policy gate — prospective counterexample assimilation, 2026-10-26

Existing research branch and draft PR #616, **NO new RC/PR**. GLOBAL Q1–Q7 all OPEN.

## Scientific purpose
Before spending additional NN training on another ranker, isolate the **information bottleneck**: do independently verified additional experiences eliminate source-consistent but misleading original hypotheses? Unlike memorizing answers, counterexample assimilation may identify when further observation, or a genuinely novel semantic rewrite, is necessary. This is a **purely CLASSICAL necessary precursor** to a learned revision policy, NOT proof of neural continual learning.

## Frozen external corpus selection BEFORE any spec content
Original Microsoft `microsoft/prose-benchmarks/Transformation.Text/<task>/spec.json` with exact names, in this ordered list:
1. FilePath.000002
2. Phone.000005
3. Number.000006
4. Currency.000004
5. DateTime.000006
6. City.000009
7. UserAgent.000006
8. Name.000013
9. Email.000009
10. Address.000008
11. ShippingCode.000002
12. DateTime.000007

- Eligibility: **at least 5 original examples** per exact task; no replacement and no filtering by observed outcome. Original examples 1–2 are initial SOURCE, 3 is **explicit authoritative feedback** / oracle purchase, 4–5 independent FUTURE evaluation and never used in any proposal or candidate pruning. Hence task scoring denominator is the preregistered list minus genuinely ineligible tasks, not cherry-picked examples.
- No-feedback C0: generate multiple bounded source-consistent typed AST programs, compare **only prospective examples 4–5 inputs**, HOLD if no candidate or if predicted answers disagree, no source-only consensus permitted as a universal proof.
- Feedback C1: same exact candidate pool frozen from examples 1–2, selectively DELETE candidates that disagree with authoritative original example3. Does not learn new programs, cannot promote if set becomes empty; same source-search cost plus one oracle fee. Compare original exact correctness, wrong, HOLD on examples 4–5.
- Strong classical C2: **re-synthesize from all three** observed demonstrations within separate unchanged Dijkstra search cap=1800, 12 programs, with independent original examples4–5 labels only for scoring. Must be compared alongside C1 because filtering a fixed pool may miss newly necessary representation.
- This feedback is the third original example, not an active query selected or purchased by an autonomous deployed model. Treat its cost/availability as nonzero and hypothetical if no live oracle exists.
- Source-only code already written and **pre-frozen** SHA256: `semantic_version_space.py = ea6d5b3e0f54bf64728cad4ed73a6aeec6b3e82a0579f314ab282876c43eaa64`; focused tests SHA256 `test_version_space.py = f565165495ec3530e977c44d3e99132cd21e82c66399fbca45aaf4ec0c79eee0`; 4/4 tests PASS.
- Fixed exact code parameters: max_expansions=3000, cap=100, max_nodes=6, n_per_state=14; same source + feedback for all. No changes after source or test gold. Freeze **C0/C1/C2 first predictions** before viewing example4/5 output labels. Record original upstream blob SHA1 for each.
- Report original task exact / wrong / HOLD / INELIGIBLE for all, program counts, contradictions, oracle information gain and source-search CPU. No model trained / no neural inference; full resource and oracle cost unknown. NO Q3/Q4/Q5/Q7 general PASS possible in this study. If C2 dominates C1: delete redundant neural program repair and use classic resynthesis unless a truly learned semantic-invention action demonstrably helps.

## Commitment
Prior preregs and external failures persist unchanged. Any future post-gold repair remains DEVELOPMENT ONLY, requires completely NEW task IDs for prospective verification.
