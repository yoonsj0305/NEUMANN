# NEUMANN Q3 first outside-SMT ERBench sixth32: no-teacher own-reward graph-edit training. NEGATIVE global research verdict.

2026-10-23 KST. **Original evaluation** [PR #544](https://github.com/yoonsj0305/NEUMANN/pull/544), [first three-stage GitHub Actions #39913799990](https://github.com/yoonsj0305/NEUMANN/actions/runs/39913799990) **3/3 SUCCESS**; **unchanged-first-receipt independent postgrade audit** [GitHub Actions #39914399141](https://github.com/yoonsj0305/NEUMANN/actions/runs/39914399141) SUCCESS.

## Research question actually tested

Can a learning agent **construct a named executable mathematical AST from its own reward feedback, without a teacher target expression**, and have this demonstrate NEW exact original mathematical problem solving outside the already opened Jochen Hoenicke SMT `modInv` recurrence?

**Training and native original source truth boundary:** Independent public EquationDiscovery ERBench 10,000 original program-formulas, upstream Git SHA `95bf15c27de68c3f170ca6140d2e4a811c60344f`, original CSV SHA256 `03c0ceb53ed0348650c0a94ed5cd1e452325d2b7c7d3be68f9a458316eda33b1`. Metadata SHA-ranked 1-D eligible 5,717. For this run **128 different author source train tasks** ranks96..223, 123 provided enough original numeric observations, all true author expressions removed before training. **First previously unused test originals ranks2160..2191** (32), no identity overlap with training, earlier benchmark source evaluations or author-original label inspections. Train numeric-only SHA256 `c773efe1e31bee25fae5587f86c2d447b96888e3daf36ff73f071116ee4d5fd2`, test source numeric SHA256 `06177e1df48a8d74e46dbc6f443302198c457f293acc0b80a4822144660cd743`, physically separate original true formula SHA256 `5acfdeb8d2c75194635331640c896c5b6c6d853c189e32444c6a3811631cb6fd`. Source numbers are 48 binary64 observations per valid task and **do not themselves prove the true law**. Public original set, not secret official ERBench evaluation.

## Learned program mechanism, not vague code-generated AST

Researcher supplied a fixed 6-edit typed AST: binary root operator `ADD/SUB/MUL/DIV`; left/right nested subtree; nested operator; three typed leaves from `X,1,2,-1`. Exactly **2048 graph action sequences**. Each emitted intermediate AST `tree(x)` can become a distinct whole candidate named lambda `f(x)=a*tree(x)+c` by numerical fitting and exact rationalization `a,c∈Q`. Graph edits are sampled without knowing the benchmark author formula. For 123 valid train source tasks, **256 uniform graph programs per task** and numerical source feedback; 544 positive graph proposals from exactly **6** author training tasks. The neural MLP is trained only on the model's own positive action sequences and receives no teacher gold formula target.

**Critical architecture precision:** Despite filename and name containing “online”, these first-run model weights are trained **after** a uniform random source-reward collection pass. The sampling policy **does not adapt online during this training collection**. It is **self-rewarded off-policy behavior cloning / reward-filtered imitation**, followed by autoregressive program action sampling. It is NOT an on-policy reinforcement learner and NOT a source-specific CEGIS counterexample-to-rewrite system. The prior SMT #543 DID use online prefix action-count adaptation; this external new-family experiment did not carry learned weights over, only method/grammar. This distinction is essential for honest claims about learning of *expressions* vs syntactic offline imitation.

First training source reward + program verifier candidate construction CPU **3.547079646s** and actual small MLP fit **0.517253968s**. These CPU numbers exclude preparing 128 original numeric-source tasks, system startup, package installs and official formula grading.

## Actual first exact external original32 verification

Three independent GitHub Actions jobs kept original true author function completely out of the source-only proposal/training job. Predictions sealed SHA256 `0c547b2de0b9a3e453e8942dd8ee7c72b6709ec05b826d52010ad1a364f53db9` before final third job read original and checked **whole analytic author-formula symbolic equivalence**, with all unproven originals not admitted. First exact full original source grader JSON SHA256 `e96c50ee751eec11735b382e210a6077efb6afd405198e04f3472734f535e33c`.

| Original same 32 source tasks and primitive authority | EXACT source-author equations | Not proven | actual test candidate work | source-test CPU |
| --- | ---: | ---: | ---: | ---: |
| D: actual neural autoregressive graph-edit policy (up to 256 generated, duplicates removed) | **1/32** | 31 | **4212** unique candidate graph evaluations | **8.761246435 s** |
| C: same number of nominal draws from nolearn uniform random, 256 unique per task | **1/32** | 31 | **8192** graph evals | **0.874363148 s** |
| A: all 2048 same-typed-program grammar, complete source graph enumeration | **1/32** | 31 | **65536** graph evals | **6.404986759 s** |

**Neural-only genuine original wins vs A or C = ZERO.** No unproved macro was certified equal to original full source function. Learned test CPU 8.761s PLUS known train reward 3.547s + learned fit 0.517s = **12.825580049 seconds known first-run process CPU**, without corpus prep, package installs, independent proof. Complete classical A on these exact same 32 originals costs **6.404986759 seconds source search process CPU**, approx **half** the known learned cost even before preparation. C is still cheaper. **Do NOT advertise 10x efficiency** or claims that 256 vs 256 had precisely equal ACTUAL program evaluations; D had duplicated neural draws (4212 unique) whereas C had 8192 unique, so they had same *nominal 256 sampling slots* but NOT equal distinct search budgets.

**Important mathematical experimental design no-go:** For a fixed finite 2048-program graph grammar and identical native numeric and exact-author verifier, exhaustive A is a semantic superset of every valid D sequence. Thus a score of D-only correct original **beyond complete A is structurally impossible** unless A's candidate reporting truncation/timeout/implementation drops a validated result. In this first run each source method emitted only one source candidate in aggregate, so the SHA-pinned postgrade audit explicitly confirmed every D emitted named lambda occurs in the complete A source-proposal set. Hence merely training the D prior more cannot make it discover **a genuinely new EXPRESSIBLE whole function not available to A**, although learning COULD legitimately be faster under an equal-compute budget in a larger shared grammar. This particular run also fails any such cost claim.

## First immutable truth-assisted AFTER-GRADE grammar audit

[Separate audit CI #39914399141](https://github.com/yoonsj0305/NEUMANN/actions/runs/39914399141) SHA-asserted all FIVE original first-run artifacts before reading original true formulas. First audit JSON SHA256 `54872e3cefe681c7b8083c079df07dd832b96e2ffbaad2671e97d8681de956fa`.

Original 32 author expressions: **22/32 NOT RATIONAL FUNCTIONS** under exact SymPy normal form, thus outside the provided *arithmetic-only rational function* AST in its current whole-function symbolic sense. The remaining **10/32 were rational-function-shaped** in SymPy; 1/10 exactly source-authenticated by all D,C,A. The 22 figure is a symbolic-normal-form classification, not a formal impossibility proof for each special support-restricted piecewise equivalence; do not overstate.

The 1/32 exact ORIGINAL is from **a previously unused genuine external author equation**, rather than another opened Jochen Hoenicke modular inverse source. But learner and nolearning same candidates, **not independently learned net benefit**; the MLP weights were trained anew on different examples *in the same ERBench corpus*, not transferred verbatim from SMT to this family.

## Scientific decision / stop

- `Q3_SELF_REWARDED_GRAPH_EDIT_POLICY_CAN_CREATE_VALID_NAMED_AST_ON_DISTINCT_EXTERNAL_SOURCE_FAMILY=SCOPED_PASS_1/32`, with mandatory caveat nolearner baseline **also 1/32**.
- `Q3_LEARNED_EXCLUSIVE_NEW_ORIGINALS=FAIL_ON_THIS_FROZEN_ARCHITECTURE`.
- `Q3_GENERATED_NEW_SEMANTIC_ATOMIC_OPERATOR_OUTSIDE_HUMAN_GRAMMAR=NOT_PROVED`.
- `Q6_REUSE_SAME_LEARNED_ABSTRACTION_IN_DIFFERENT_EXTERNAL_FAMILY=NOT_PROVED` (new weights trained on new-domain examples).
- `Q4_MATCHED_WHOLE_TASK_TOTAL_COMPUTE_10X=FAIL_THIS_CAMPAIGN` on measured known CPU, and unmeasured packaging costs cannot rescue a claimed established PASS.
- `Q7_FRONTIER_PARITY=BLOCKED`; `G1=HOLD`. No academic novelty over existing genetic programming/program synthesis; no fake breakthrough.
- **STOP this exact 2048 fixed-program grammar family**. More seeds or more ERBench original32 rows cannot show learner-only *expressivity* beyond a complete same-grammar enumerator. The meaningful next mechanism must **induce a reusable typed lambda/macro and optionally synthesize new graph rewrite operators not enumerated as complete fixed programs**, then *prove out-of-distribution utility under equal compute and grammar authority, including training and verifier query cost*, on a truly independent original author family. Strong specialist GP/CEGIS/PySR comparison required. Source condition failures and negative receipts remain immutable.

Original source code `research/q3/online_self_reward_original_equation_ast.py`, cohort `research/g0/erbench_original_sixth.py`; first and aftergrade CI workflows in `.github/workflows`. GitHub Issue [#530](https://github.com/yoonsj0305/NEUMANN/issues/530) owns global G0/G1/Q1-Q7 decision. No paid GPU/model APIs.
