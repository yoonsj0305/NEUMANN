# 2026-10-26 · Actual external counterexample assimilation (same discovery-policy study)

**RESEARCH RESULT, not new RC/PR or new trained NEUMANN neural model. All global Q1–Q7 OPEN.**

## Frozen chronology

1. **Preregistered BEFORE reading external task source**: GitHub commit `1da319b9cfd491d0fcf6bc0a7c94829eca5ada54`, exact 12 Microsoft PROSE original task IDs, first two labelled examples SOURCE, third provided as additional authentic FEEDBACK, fourth/fifth original examples FUTURE blinded until after proposals, eligibility >=5 original demonstrations. General classical source-consistent program compiler `semantic_version_space.py` SHA256 `ea6d5b3e0f54bf64728cad4ed73a6aeec6b3e82a0579f314ab282876c43eaa64`.
2. **Frozen the complete source-only FIRST** (including candidate counts, decisions, labels ONLY from third feedback, future input strings, CPU) SHA256 `9bb34e9f727f3b5dc4278a12eb809799f003ddf974520885af62d889852e5fd6`, GitHub commit **`c31b5ac3d27ffaee340dc0046ca19477b0797a06`**, BEFORE opening original future answer strings.
3. Then checked original Microsoft PROSE `spec.json` Git blob SHA1 fingerprints for every original task, compared future outputs and retained first mistakes. **12 IDs frozen, 2 ineligible**, remaining 10 eligible; ineligible `FilePath.000002` four examples and `Address.000008` three examples. No replacements.

## Actual ORIGINAL heldout fourth/fifth example scoring

| Control | Exact complete tasks / 10 | Wrong | HOLD |
|--|--:|--:|--:|
| C0 2-source finite version space, zero oracle feedback | **4** | **1** | **5** |
| C1 prune same version space with third ORIGINAL labelled feedback | **5** | **0** | **5** |
| C2 stronger classical resynthesis using all 3 source observations (1800 expansion cap) | **5** | **0** | **5** |

- **Positive causal example** `UserAgent.000006`: 5 two-source-valid programs, 2 distinct prospective output classes, authoritative third labelled example eliminated 2 programs, remaining 3 predict one output class; exact future original outputs `6.6.2,8.1.7`, scored correct. C0 withheld; C1/C2 correctly respond.
- **Negative, more important epistemic counterexample** `DateTime.000007`: 7 source-compatible programs all agree on a future output that is **WRONG** (they predicted Nov 2018/Nov 2007 vs true May 2018/Sep 2007). New third feedback refutes **all seven**. C1/C2 fail closed HOLD, eliminating a confident wrong answer. Thus *bounded version-space consensus does not prove correct semantic rule*, even though all candidate source examples are correct.
- In the remaining 8 eligible originals, feedback made no strict future correctness difference.
- The THIRD original example was **freely supplied by the test harness**, but must be treated as a nonzero potentially unavailable expensive oracle at real deployment. These were NOT active-learning-generated inputs, and no token-model learned to pick them.
- Source-only bounded 2-observation candidate search aggregate process CPU on eligible tasks **34,504,518 ns** one run, separate 3-observation Dijkstra fresh search aggregate **96,616,080 ns** one run; this excludes C1 feedback-pruning CPU and excludes oracle, energy, money, RAM, startup. The observed C1/C2 solution outcome is matched, but these are **not full all-in comparable cost**. No Q5 pass.
- **Zero** neural training or inference; a small mechanistic prerequisite for later learning from verified failures, **NOT an actual transferable neural discovery-policy learning demonstration**. Distinguish current-task evidence assimilation from next-task weight self-improvement.

## Reproducibility

Full source, bounded candidate enumerator, preserved 12 source+feedback-only records, first pre-gold predictions, external original after-first gold, referee scoring, exact source SHA and independent test suite contained in conversation ZIP:
`NEUMANN1_COUNTEREXAMPLE_ASSIMILATION_20261026.zip`
SHA256 `4fbf12f7f0a2295ed61c820ca1583dae6c9af0cde0c85effb520df67f579a9b1`.
Clean fresh unzip `bash REPRODUCE.sh`: ZIP CRC PASS, **14/14 SHA256**, **13/13 pytest PASS** (engineering tests), **10/10 real first prediction behavioral replays** (ignoring nondeterministic CPU ns), original independent gold score receipt reproduced. Does NOT require network for frozen replay. Full program is ONLY in attached ZIP; this GitHub record does not pretend to contain source/weights.

## NEUMANN architectural decision

**Keep** CEGIS/version-space disagreement + independent verification as a CHEAP classical learning/evidence-updating subsystem. **Delete** unnecessary NN approximation of that filtering. Never turn SOURCE_CONSENSUS into universal correct proof. Novel semantic generator must have a VERIFIED ability to propose a different representation when feedback rules out all candidates, ideally learn an *edit policy across tasks* in own model weights after exact solution memory is reset. Need independent source-authoring, hidden future problems and matched classical baseline before approving training. If evidence missing, HOLD. All global original questions remain OPEN.

Source: https://github.com/microsoft/prose-benchmarks and pinned original 12 Git blob SHA1 IDs in attached source-only JSON.
