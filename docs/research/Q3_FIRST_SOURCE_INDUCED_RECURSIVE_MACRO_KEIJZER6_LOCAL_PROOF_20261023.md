# NEUMANN 1 Q3 | NEW source-induced recursive function representation on original Keijzer-6, first LOCAL research evidence

2026-10-23 KST | **Local CPU first evidence, NOT YET independent GitHub Actions or official benchmark certification.** Supporting complete runnable Python source, trusted model checkpoint, first source-only prediction, original gold truth, exact all-domain mathematical verifier, controls and SHA256 manifest are packaged as \`NEUMANN_Q3_Keijzer6_Recursive_Macro_First_Evidence_20261023.zip\` in the current ChatGPT conversation. GitHub cannot itself fetch a chat-local sandbox ZIP; reproduce by copying the source files from the archive to a local workspace. Archive bytes **69,751**, SHA256 **b2315dd226d50391612650a5a6129521bca723562924a05a60fa48e70cb975e2**, 13 members, CRC PASS.

## Externally authored original: a structurally different problem family

Maarten Keijzer, *Improving Symbolic Regression with Interval Arithmetic and Linear Scaling*, EuroGP 2003, **problem 6 (Keijzer-6)**: \`H_n=sum_{k=1}^n 1/k\` over positive integers; source domain \`n=1..50\`, conventional evaluation \`n=1..120\`. Paper PDF: https://groups.csail.mit.edu/EVO-DesignOpt/groupWebSite/uploads/Site/keijzer-improving-symbolic-regression-interval-arithmetic-linear-scaling-eurogp-2003.pdf . **Different original research-author family** from previous ERBench and Nguyen, and **discrete recurrence** not standard continuous x-y elementary-expression recovery. This is a *published public* benchmark (not a private competition) with a custom first-source-only experiment reusing its original standard n-grid. Source-only original Keijzer-6 50 numeric observations delivered to neural inference with analytic truth and n51..120 held-out 70 exact-rational values in a separate file, opened ONLY AFTER model predictions saved and SHA-locked. Source id from digest of published task name.

## Mechanism actually trained and executed

Model training uses **112 different synthetic, NUMERIC-SOURCE-ONLY tasks**: 56 direct polynomial sequences and 56 cumulative shifted reciprocal sequences with \`b=1..6\` offsets, *excludes the Keijzer harmonic \`b=0\` training case*. On each, human-coded direct degree0..6 polynomial and first-difference-to-rational-term recurrent macro constructors independently check source numeric fitness. Labels are derived from **its numeric-only verification outcomes**, not complete author gold formulas. Train a real small sklearn MLP on task source shape to choose **DIRECT_POLYNOMIAL** versus **DEFINE_FOLD_SUM**. Actual 112 valid self-reward training observations, label distribution 56+56, source verifier calls 2620. Serialized trusted \`TR​AINED_FOLD_POLICY.pkl\` first checkpoint SHA \`5f5f54e7d74cebb4951b33d97d769b589e95db7a393e6b7aea91fcb8f98d2c53\`, checkpoint pickle round-trip prediction replay PASS. (Do NOT load the pickle from untrusted sources.) The model did not receive original Keijzer truth or hidden n51..120 values.

At first actual original source-only inference, the trained MLP chose \`DEFINE_FOLD_SUM\` as its sole allowed action, then a first-difference numeric verifier inferred \`a=1,b=0,p=1, f(1)=1\` and **dynamically created a previously unnamed typed executable AST**:

\`\`\`json
{"node":"DEFINE_MACRO","name":"M_1aa374ffcd","params":["n"],
 "body":{"node":"FOLD_SUM","combine":"PLUS","initial":"1","start":2,"stop":"n",
         "term":{"node":"RECIPROCAL_SHIFT_POWER","a":"1","b":0,"p":1}}}
\`\`\`

This means \`M_1aa374ffcd(n)=1+sum_{k=2}^n 1/k\`. First 50 source relative error approx **2.09e-16**, fitted difference equation error approx **7.78e-16**. The newly inferred \`b=0\` source parameter was **never in synthetic cumulative TRAIN b1..6**. This is concrete model-chosen recursive *program representation*, NOT novel elementary mathematical primitive semantics: the \`FOLD_SUM\` combinator, delta operator, family of rational terms and coefficient inference search were all supplied by HUMAN engineering.

## Independent first-source postgrade whole-domain author proof

First prediction saved under source-only SHA \`2c21233f81e4359e7c9989e6db736bce639366cf8351dfb7f0aa6484f7c58762\`, first original analytic author gold SHA \`6099f085f2f72772428eb3973081a06974614c18c6e6b0f0f6b92dec3b608e65\`. Separate post-source grader checks:
1. Exact base condition at n=1, \`M(1)=1=H_1\`.
2. Exact for **every positive integer n>=2**: \`M(n)-M(n-1)=1/n=H_n-H_{n-1}\`. By elementary induction, **M(n)=H_n for ALL positive integers**, not just 50 fitted source samples.
3. **70/70** exact rational held-out comparisons at n=51..120, each using Fraction exact rational, not rounded floats. First grader SHA \`988754d5924ce95d215cab84232a917dbd967d40471b37ed1db5b5adcb0b7704\`.

The source points alone do NOT logically force the true law among all unrestricted sequences; infinitely many alternative sequences agree for n<=50. **The infinite-domain proof depends crucially on an independent published mathematical recurrence verified after source prediction**. Claiming this is deducible from a finite x-y sample without assumptions would violate identifiability; this is an authentic original-author verifier-based program proof, not model omniscience.

| First external original Keijzer-6, same n1..50 and typed operator authority | whole positive-integer original analytic solution | source-verifier candidate calls |
| -- | -- | --: |
| **Trained neural TOP1 selects newly induced FOLD_SUM macro** | **PASS** | **1** |
| No-learning direct polynomial degree0..6 | **UNKNOWN** | 7 |
| No-learning FOLD_SUM first-difference solver, same language rights | **PASS** | **1** |
| Strong same-rights FULL both direct+fold | **PASS** | 8 |

**Model-exclusive improvements over strong classical source fitting = 0.** Training source verifier 2620 calls excludes a 10x overall work claim. Same-rights FOLD-only comparator immediately solves Keijzer original more cheaply than trained MLP full lifecycle. The experiment is one external original, not statistical generalization across many new recurrence authors. Original official GP systems may approximate the harmonic function well; these local comparisons do not imply best-in-industry performance or official Keijzer competition parity.

## Structural impossibility proof relative to rational-function symbolic grammar

Integral comparisons for harmonic numbers establish \`log(n+1) <= H_n <= 1+log n\`. Consequently \`H_n -> infinity\` AND \`H_n/n -> 0\`. Any rational \`R(n)=P(n)/Q(n)\` either remains bounded for n→∞ if degP<=degQ, or diverges as \`c n^d\` with POSITIVE INTEGER d when degP>degQ, yielding \`R(n)/n\` not→0. Hence **no rational function over real polynomial numerator and denominator can equal H_n for all positive integers**. Exact \`DEFINE_FOLD_SUM\` representation is strictly more expressive than unrestricted rational closed-form grammar on the discrete domain. This is elementary classical math and not a novel mathematical theorem.

## Robust rejection and first evidence SHA

Tampering with observed source value #36 by +0.05: first-difference fitted fold returns UNKNOWN, not false PASS. Pure polynomial \`2n³−3n+7\` direct solver PASS while fold solver abstains. No false source numeric acceptance in those designed controls.

SHA256:
- Original source numeric (first 50): \`83ea4379cd5906e84e05fd2692e4daaa398e80cf32f5a0abcefeaca343d45d16\`
- Independent numeric training source: \`ba54089cc1c8ca83d17c1eaf74775844c5e8d2a5f70ded53d8adced97b2a4377\`
- Source-trained sklearn checkpoint: \`5f5f54e7d74cebb4951b33d97d769b589e95db7a393e6b7aea91fcb8f98d2c53\`
- Frozen first predictions before opening analytic author: \`2c21233f81e4359e7c9989e6db736bce639366cf8351dfb7f0aa6484f7c58762\`
- Original Keijzer author truth + heldouts: \`6099f085f2f72772428eb3973081a06974614c18c6e6b0f0f6b92dec3b608e65\`
- First mathematical whole-domain proof: \`988754d5924ce95d215cab84232a917dbd967d40471b37ed1db5b5adcb0b7704\`
- Archive ZIP: \`b2315dd226d50391612650a5a6129521bca723562924a05a60fa48e70cb975e2\`.

## Current gates

\`Q3_SOURCE_ONLY_NEW_RECURSIVE_PROGRAM_AST_CONSTRUCTED=SCOPED_PASS\`; \`NEW_PUBLISHED_AUTHOR_KEIJZER6_FIRST_ALL_POSITIVE_INTEGER_MATH_PROOF=SCOPED_PASS\`; \`70_EXACT_HELDOUT_RATIONAL_COMPARISONS=PASS\`; \`NO_NOVEL_MACRO_TRAIN_INSTANCE_B0_EXCLUDED=PASS\`; \`CORRUPTED_SOURCE_ABSTAINS=PASS\`; \`GENERAL_RATIONAL_CLOSED_FORM_IMPOSSIBILITY=MATHEMATICAL_PROOF\`. But \`NEURAL_ONLY_V_SAME_RIGHTS_CLASSICAL=0\`, \`SELF_INVENTED_ATOMIC_SEMANTIC=UNPROVED\`, \`ALL_IN_10X=UNPROVED\`, \`FRONTIER_PARITY=UNPROVED\`. **Global Q3 OPEN, G1 HOLD, Q4 OPEN, Q6 general robust advantage OPEN, Q7 OPEN.** This first result was executed in ChatGPT's local CPU container and archived reproducibly, not independently verified in GitHub Actions yet. Next immediate step is independent Actions validation of the source archive/code in the repo, and a truly new recurrence family with variable-length operator invention and matched strong classical cost, not another 32 original ERBench equation sample.


## ADDENDUM 2026-10-23 · FULL INDEPENDENT GITHUB ACTIONS REPLICATION: ALL SIX JOBS SUCCESS

**This addendum supersedes the earlier "LOCAL ONLY / NOT YET CI CERTIFIED" limitation ABOVE.** The first local archive is preserved unmodified with original hashes; the independent CI used separate refreshed source/prediction/truth output schemas and therefore different SHA files, rather than pretending the two archives have identical bytes.

[**Fully complete real GitHub Actions #39945622502**](https://github.com/yoonsj0305/NEUMANN/actions/runs/39945622502): six jobs succeeded (three original Nguyen transfer replay jobs + **three NEW distinct Keijzer6** jobs). New runnable repository file \`research/q3/keijzer6_induced_fold_source_model.py\`, new independent three-stage job sequence in existing registered \`.github/workflows/q3_nguyen_frozen_derived_power_cross_author.yml\`. Separate standalone new Keijzer workflow YAML also checked in; its first automatic activation was not observed, so **cite executed six-job existing workflow #39945622502**, not the unexecuted standalone YAML.

**Actual Keijzer original truth isolation job:** only 50 original n1..50 numeric observations exported to model source, true full published author recurrence + exact-rational n51..120 in distinct original-GOLD artifact. First new source-only CI SHA256 \`0ffcdc5fcdb5d14e428450eb2300e9587b0a072367590a7455c14920d5e481b2\`; separately held author original/gold SHA256 \`0c3ba820abb00410c692a99b8ceb89ad906e6cbe52b89ed73bbd7be79b004dd0\`. Preparation job SUCCESS.

**Actual source-only MLP training and AST-generation job:** all three original-TRUTH-FREE model positive/negative controls PASS (shifted reciprocal source, pure direct polynomial source, one-corrupted-point abstain). Real MLP trained on **112 non-Keijzer numeric self-reward source tasks, balanced 56+56, 2620 source verifier calls** and selected solely \`DEFINE_FOLD_SUM\` for held-out Keijzer6. It recovered b0 (not in b1..6 training examples), numerator1 and exponent1, f1=1 and compiled \`M_1aa374ffcd(n) = 1+Σ_{k=2}^n 1/k\`. First source-only CI candidate SHA256 \`6d9992bbf70c4615508368d5596615123a3b413149b7159df6aa1d43667aaf7a\`; independent CI trusted MLP pickle SHA256 \`3d1f923b004d812fb13c9c17b4a2f2f964c30ba065e3d3481c2c2334d76e860c\`. Different from local proof's sklearn/BLAS checkpoint, but same source-chosen concrete macro and labels; **do not claim byte-identical learned model between different Python/sklearn settings**. Source-only job SUCCESS; source maximum relative error 2.089e-16, difference check maximum 7.780e-16.

**Actual separate original entire mathematical proof job:** only AFTER source predictions saved, downloaded author gold and original held-out 70 exact rational values. Proved \`M(1)=H1=1\`, \`M(n)-M(n-1)=1/n=Hn-H(n−1)\` exactly for ALL integer n≥2; induction certifies equality on **every positive integer n**. All 70 exact Fraction held-out n51..120 PASS. Independent new CI final mathematical certificate SHA256 \`70e6a7914836bcf75a0ea2ee7a200cd54bcd83e3a959e678a10767344447c2d9\`. Truth grade: D actual learned TOP1 **PASS**, C direct polynomial-only **UNKNOWN**, C FOLD-only SAME-RIGHTS **PASS**, A full two-action classical **PASS**. Last independent author grader job SUCCESS.

**Scope:** \`INDEPENDENT_GITHUB_ACTIONS_REAL_SOURCE_TRAINED_RECURSIVE_AST_INFERENCE_AND_AUTHOR_FULL_DOMAIN_MATH_PROOF=PASS\`; \`NO_GOLD_LEAKAGE_ACROSS_SEPARATE_JOBS=ARCHITECTURALLY_VERIFIED\`; \`70/70_EXACT_HOLDOUT=PASS\`; \`NEURAL_ONLY_V_STRONG_CLASSICAL=ZERO\`; \`GLOBAL_Q3=OPEN\`, \`G1=HOLD\`, \`Q4_SYSTEM10X=OPEN\`, \`Q6_ROBUST_SUPERIORITY=OPEN\`, \`Q7_FRONTIER=OPEN\`. Hardcoded recurrence grammar remains HUMAN supplied. This is an algorithmic scoped proof, not a frontier intelligence claim.
