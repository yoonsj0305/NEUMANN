# NEUMANN 1 | G0-SGI native cvc5 SOURCE-ONLY FIRST candidates FROZEN BEFORE heldout grading

**2026-10-27 KST**. This report is written **BEFORE the heldout original constraint is graded**. No future output constraint was used in candidate synthesis. **Q1-Q7 GLOBAL OPEN / G1 HOLD**.

## Original integrity and chronology
- 12 original SyGuS tasks selected by SHA256 filename-only ranking from Barnard-PL-Labs/sygus-sgi-1 upstream commit **e7ae840e5546e9243ff94afb1a29064fc050011c**, no explicit task content preselection. Public, not LLM-data-sealed.
- Original prereg commit **4a5ae8b89e46b5b5a618043c9e2ea4f1de770788** wanted 6 easy+6 hard. **First run [#40451521100](https://github.com/yoonsj0305/NEUMANN/actions/runs/40451521100) failed BEFORE task contents**: only 3 easy files existed at declared pathname depth. Preserved original first failure. Filename-only **post-first, pre-content amendment 3 easy+9 hard** commit **a49478b83570447bdc186c0ec849d4253acec956**, revised runner code commit **68d871227255b0844236280ae984e8428c0c1120**. This is a visibly amended cohort, not the originally declared 6/6 one. No cherry-picked problem bodies.
- Actual GitHub Actions [#40451797444](https://github.com/yoonsj0305/NEUMANN/actions/runs/40451797444), success, commit **89a03b8a8e4273c37143b772dcefcce3e57f16ed**. Runner checked out original pinned repo and a native system cvc5 package, separately stored its reported version.
- For each source file, a balanced top-level parser removed the entire final original constraint from a source-only copy. Original synth-fun grammar and earlier constraints left unchanged. Candidate solver saw **no last original constraint**. All original file blob hashes, source-only hashes, future constraint SHA256, file identities, timing and raw stdout hashes recorded in machine FIRST JSON.

## FIRST candidates, not correctness claims
Exactly **12/12** original selected tasks received at least one cvc5 define-fun candidate with exit code 0, no error, under 15-second per-task wall budget. **0/12 graded** at time of this freeze; candidate receipt does NOT authorize a success rate.

The deterministic source selection (exact order):
1. easy/easy_3/easy_3.sl
2. easy/easy_1/easy_1.sl
3. easy/easy_2/easy_2.sl
4. hard/PRE_51_10/PRE_51_10.sl
5. hard/PRE_icfp_gen_6.12/PRE_icfp_gen_6.12.sl
6. hard/PRE_76_10/PRE_76_10.sl
7. hard/PRE_105_100/PRE_105_100.sl
8. hard/PRE_100_1000/PRE_100_1000.sl
9. hard/PRE_126_100/PRE_126_100.sl
10. hard/PRE_55_1000/PRE_55_1000.sl
11. hard/PRE_104_1000/PRE_104_1000.sl
12. hard/PRE_icfp_gen_11.20/PRE_icfp_gen_11.20.sl

- Frozen FIRST_CVC5_SOURCE_ONLY.json **SHA256 44047cd18e17e517cf0029329589411b997f53427d8fa3e152b044183d8524f0**.
- Public raw 12 stdout+stderr, original/source-only SHA and solver version artifact **[GitHub Actions artifact #12710573047](https://github.com/yoonsj0305/NEUMANN/actions/runs/40451797444/artifacts/12710573047)**; artifact ZIP SHA256 **1075da4e7f379adad13477aa92077b7247ac4eeb01bd26db36ed3955416e6ef1**.
- Measured per-process wall from first, rounded, 0.016–0.199 seconds, but do NOT equate process wall with model/system cost. More precise CPU/RSS in machine receipt. Comparisons with NEUMANN learned model NOT RUN.
- Independently verifying the omitted original gold condition remains **NOT RUN AT SEAL**. Only after GitHub freeze can a separate verifier access withheld tasks and grade, retaining exact first stdout/hash and original task count.

**Scientific stop criterion:** If 12 existing strong classical outputs all independently meet removed constraints, this corpus supplies no demonstrated new ownweight discovery headroom. In all cases, A/B learning admission stays blocked unless separately proven.
