# NEUMANN 1 Q3 | Official source-bound certificate authenticity audit

**Date:** 2026-10-19 KST. **Scope:** source identity and proof authenticity of the already completed first official 2017/18 original SyGuS trial. This is NOT a new generalization experiment or a new learned model result.

## First immutable original evidence (unchanged)

- Original external source: SyGuS-Org/benchmarks exact commit `13c8deb68a873635879c9a69bc78caebd340f646`, first six lexicographic *.sl from official `comp/2017/Inv_Track` and six from `comp/2018/Inv_Track`, pinned before source-body access.

- First science run [Actions #39210016907](https://github.com/yoonsj0305/NEUMANN/actions/runs/39210016907), artifact `12167690489`: 8/12 exact original 3VC Z3 inductive certificates, including **7 POST_ONLY and 1 BRANCH_AFFINE_NULLSPACE non-Post-only**; 2 source-only SPACER unsat *without exported inductive certificate*; 2 true abstentions. All 8/8 explicit certificates independent CVC5 UNSAT on all three original bad-condition SMT2 queries. Original 12 source SHA all unique and no byte-level overlap with previous 18 opened LoopInvGen files. This DOES NOT prove independent source authorship.

- First archived JSON SHA256 `090e63f7839df2cd43e7db4132928dc00c098987b71904f052b3366b84cc3fbd`; ZIP SHA256 `498b72869f17d1f3026112255812d49f74369df4d8fdc815dc61a0100a52f085`.

## Previously unproven and now fixed verification distinction

Previous `replay_exported_queries(receipt)` validates that the receipt contains three SHA-matching SMT queries and each returns `UNSAT`. It is **not an original-source proof checker**: replacing every obligation with `(assert false)` and recomputing the corresponding hashes passes this old checker while proving NOTHING about the original source. This was actually demonstrated in all 8 successful originals. Such a receipt must never be called original-bound authenticated simply because it carries three UNSAT results.

The existing stricter `replay_original_source_bound(path, receipt)` in separate frozen newer PR #246 at commit `7b111a5ef8d2bc71d7bc8c03a8056c771da8848b` reopens the **actual byte-SHA-identified original**. It reconstructs the original native Pre/Trans/Post relation, recomputes source-conditioned proposed invariant and all three original bad-condition queries, checks their exact assertion AST structure, and rejects any changed receipt/source linkage. It is a Z3-based reference re-computation using the *same* source-prover algorithm; it is NOT a different proof assistant. Independence of SMT satisfiability checking is from the prior recorded CVC5 replays.

## Newly executed source-bound audit

- Preregistered before audit execution: [Issue #263](https://github.com/yoonsj0305/NEUMANN/issues/263). It specifies **post hoc verification** of first data, NOT source selection or model fitting.

- New read-only executable: `research/evidence/q3source-bound-authenticity-20261019/audit_first_official_proofs.py`; frozen exact first JSON download via immutable Actions run, exact first JSON SHA, exact upstream commit, strict-prover file blob `a74b62cc97958e06f70116f3c8cec2f6db3d3b75`.

- **First valid [GitHub Actions #39210994622](https://github.com/yoonsj0305/NEUMANN/actions/runs/39210994622): SUCCESS.** Artifact ID `12167069986`. ZIP SHA256 `a862011b7e0f16f066fc3e2e20fddb3dc7001eaff29fbc822423a98c85cb3860`, raw audit JSON SHA256 `b1213e1e3a07077788a219e8086517f6f67dbed66197b4779e6a97e3ca4509ad`. ZIP independently downloaded, CRC PASS, first report status/check summaries independently inspected.

### Exact first audit results

| Fixed check | Outcome |

|---|---:|

| Archived official 12 original SHA, chosen paths, route and status replay unchanged | 12/12 PASS |

| All explicit original 3VC reconstructed from source, SHA/AST-bound | 8/8 PASS |

| Same 8 original 3VC first independent CVC5 verification retained | 8/8 PASS |

| Malicious `(assert false)` triple with recomputed SHA fools old replay (vulnerability confirmation) | 8/8 correctly demonstrated |

| Strict original-source binding REJECTS malicious triple | 8/8 PASS |

| Strict binding REJECTS mutated source SHA identity | 8/8 PASS |

| Strict binding REJECTS modified invariant textual form | 8/8 PASS |

| Genuine non-Post-only structure stays exactly one | 1/1 PASS |

| 2 SPACER-only not misidentified as inductive 3VC, 2 abstentions kept | 4/4 PASS |

### Research verdict

- `Q2_OFFICIAL_SOURCE_PROOF_ORIGINAL_BYTE_BOUND_VALIDATION = PASS_SCOPED` for **these eight** original induction certificates.

- `Q3_ORACLE_FREE_CLASSICAL_NONPOST_USEFUL_STRUCTURE_EXISTENCE = PASS_SCOPED` for **one of 12** previously uninspected official originals. This is an existing-source result authenticated more strongly, not an additional new task success.

- `ORIGINAL_EXTERNAL_PROOF_FORGERY_RESISTANCE = PASS_SCOPED` against three specified falsification classes. Does not imply mathematical completeness, absence of all possible attack vectors, or security guarantees on third-party solvers.

- `LEARNED_DELTA_GAMMA_OPERATOR_INVENTION = NOT_PROVEN`, prior Q3R trained fixed-Γ result NO-GO unchanged.

- `Q3_GENERAL_UNSEEN_FAMILY_SUCCESS = OPEN`, because official annual folders alone do not prove distinct independently authored family/source origin.

- `EX1_ACTUAL_MODEL_MULTIPLIER = NOT_EVALUATED`, `Q4_Q5_COMPLETE_10X_COST = NOT_PROVEN`, `Q7_FRONTIER_GAP_RECOVERY = NOT_EVALUATED`, `GLOBAL_Q1_Q7 = OPEN`.

**STOP:** The value of this particular evidence is the exact original-proof authenticity, not new iterative Q3 tests. No GPU, neural training, model generation, frontier API, billing, benchmark selection or contract revision. Keep historical AM1 initial FAIL unchanged. The next indispensable science evidence for Q1-Q7 is still a properly preregistered genuine matched model run on independently original-checked hard opened tasks with a strong eligible TOOL+ and source-relevant structure, once compliant actual GPU hardware is available.