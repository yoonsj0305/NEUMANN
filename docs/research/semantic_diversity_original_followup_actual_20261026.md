# NEUMANN 1 | Semantic diversity, source-equivalence loss, and selective oracle outcome (2026-10-26)

**Research-only. NO new RC/PR; Q1–Q7 globally OPEN. No NEUMANN neural model trained or called in this study.**

## Chronology and pinned evidence

- **NEW 12 exact Microsoft PROSE original public tasks** preregistered before reading any selected `spec.json`, GitHub commit `9cc6dc31596f47e976f7052446e0ea956d6f14c1`. The tasks and unaltered code SHA256 are in `semantic_diversity_active_oracle_prereg_20261026.md`.
- **Stage1 source-only receipt FIRST** SHA256 `d7c9dd22cda91b7cb6ac83f2f2d32f7bca11529862ffc54b8134ff21c969a390`, GitHub freeze `9e7fb80ecf82a2b7581bce964bc42e4f494c9507`; froze requests BEFORE receiving any third-example target labels.
- Selective classical policy requested **only 2 third-example labels**, for `ShippingCode.000004` and `.000005`, because among all 1,632 generic one-atom source candidates, there were 2 distinct predictions of the third output. In every other eligible case it requests none.
- **Stage2 source+conditional-oracle FIRST** SHA256 `c2f713f27cffbdf51ce58bdf356aafd33ce63bcaed3ac37985f39bc60efc55bc`, GitHub freeze `ce619b73b2bd035008a9b63d5edca2fc16791232`. Only THEN read fourth and fifth original future labels.
- **Provenance error admitted and excluded:** human transcription changed the second future **input** of `Phone.000008` in the locally frozen fixture. Upstream author original file Git SHA-1 authentic, but initial FIRST was computed for a non-original input. Preserve first receipt and DO NOT promote the corrected result. Of 12 prereg tasks: **3 objectively ineligible** due to <5 demonstrations; **1 invalid fixture**; **8 strictly scorable**. All 11 other original task source+probe+future inputs verified via two independent GitHub-content and local serialized UTF-16 checksum implementations, plus original SHA1.

## Scored prospective ORIGINAL outcomes: 8 valid tasks

| Arm | Third original output labels requested | Exact | Wrong | HOLD |
|--|--:|--:|--:|--:|
| Classical rich source-equivalent atomic 2-demo, no feedback | 0 | **4** | 0 | 4 |
| Classical diverse *conditional* third output query | **2** | **6** | 0 | 2 |
| Classical diverse atomic, ALL third output labels | **8** | **6** | 0 | 2 |
| Classical stronger 3-demo composite Dijkstra search | **8** | **7** | 0 | 1 |
| **Old strong 2-demo Dijkstra classical baseline** (source-equivalent dedup) | **0** | **7** | 0 | 1 |

Actual selective queries correctly resolved source hypothesis ambiguity for the two ShippingCode tasks and reduced oracle requests from 8 to 2 for the **same 6/8 score as all-oracle atomic**. **BUT IT DID NOT BEAT the strong original cheap no-oracle classical solver**, which happened to give 7/8 correct first predictions. Causal discovery-policy transfer, 10x overall, ownweight semantic invention and frontier parity **ALL NOT DEMONSTRATED**. Source-only consistency is not independent proof even when lucky heldout exact is measured.

## Root cause and cost, honest scope

The original `create_atoms` kept only the cheapest atom per vector of 2 source outputs. Across **41 separate already opened original tasks** (retrospective, not new blinds), 37 were eligible, 28 had first programs; 8 authentic third outputs FALSIFIED all source-surviving programs, yet 0/8 triggers would have been recognized by disagreement over the *collapsed* hypothesis space. Thus apparent program agreement can be an artifact of premature source-behavior dedup.

Enumerating all 1,632 atomic alternatives found source-consistent third-input disagreements in six historical atomic tasks, three of which were independently future-verified repair cases, showing the structural evidence previously lost. It remains purely classical.

Measured **15 complete 8-task batch repeats, process CPU median, post-gold timing only**:
- Old classic 2-source Dijkstra **31.52ms**
- Rich atomic no-oracle **12.54ms**
- Selective version 1 **25.23ms** (accidentally enumerated all source atoms twice)
- All-oracle rich atomic **12.54ms**
- Strong C2 3-demo Dijkstra **43.14ms**
- **Behavior-preserving post-gold cache repair** to selective **12.36ms**, same ALL frozen first decisions across 12 original tasks and 41 historical tasks, tested 12/12. This is a local CPU refactor, NOT a new blind model capability or matched whole-system advantage.

Exact oracle acquisition latency, money and energy UNKNOWN; peak RAM and USD NOT MEASURED. The 2 vs 8 query counts do not translate to 4x whole-system win, and 6/8 vs strong 7/8 prevents same-capability Pareto comparison. No neural meta-training merit.

## Reproduction and files

**Full executable conversation artifact:** `NEUMANN1_SEMANTIC_DIVERSITY_CAUSAL_AUDIT_20261026.zip`, SHA256 **`9f86f39ac7f626d566be7989fcfb1d36fe1c9427f47f123de6bfd61498920425`**. Portable 27 members, zipped source-first JSON, individual original SHAs, separate third auth output, separate later fourth/fifth output, original frozen first SHA, prospective grader with invalid-source exclusion, a 41-task retrospective census, tests, batch CPU results, cached refactor and replay script. Fresh extraction checks: SHA256 26/26, pytest 12/12, 12/12 first prediction behavior replay PASS. Full scripts in conversation ZIP; this GitHub document doesn't pretend all source files or weights were committed here.

**Architectural decision:** Keep semantic diversity where extra oracle information is available and cheap, but run the stronger classical generator as a mandatory comparator. This only fixes an information-loss bug in the CEGIS/verifier prerequisite. *How to learn new semantic representations after all current hypotheses are falsified* remains the core OPEN learned discovery-policy problem. No more expensive neural candidate ranking of identical finite source-equivalent atoms unless prospective A/B/C equal-rights gains justify it.
