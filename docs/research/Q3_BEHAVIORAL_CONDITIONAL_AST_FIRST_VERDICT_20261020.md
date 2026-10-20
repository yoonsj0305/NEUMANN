# NEUMANN 1 Q3 | Teacher-free AST **label** behavioral-gradient conditional policy first genuine original synthetic dual-SMT result

**2026-10-20 KST** · `Q3_BEHAVIORAL_GRADIENT_SHAPE_CONDITIONAL_TYPED_AST=DEVELOPMENT_SCOPED_PASS`; `Q3_FIRST_NEURAL_ONLY_STRUCTURAL_INVENTION_OVER_CLASSICAL=NOT_PROVEN`; GLOBAL Q1–Q7 OPEN.

## What changed vs PR #299 (and the failure that is actually addressed)

PR #299 first found the expression AST with UNTRAINED stochastic classical grammar exploration, **then supervised the 29 trainable weights with the found correct AST tokens**. That demonstrated learned **reuse**, not initial learned proposal.

New draft [PR #300](https://github.com/yoonsj0305/NEUMANN/pull/300) eliminates ANY gold/correct AST or discovered AST token ID from the gradient objective. It trains from empirical behavioral error on real source recurrence observations. It also changes the model's architecture: 29 independent shape/child logits cannot retain correlations between tree shape and operands; a **125-parameter conditional shape→operator/leaf policy** learns these dependencies.

The critical limitation is equally important: **all 25,920 DSL candidate AST behaviors are exhaustively evaluated before training** to derive a behavioral posterior. The training algorithm's reward distribution is essentially a soft classical exhaustive search answer (first two exact programs collectively have posterior mass ~1). Thus it is *teacher-AST-label-free*, but it is NOT *classical-discovery-free*. No new mathematical operator is learned outside the predefined complete DSL closure.

## Actual GitHub independent execution

- Source target **author-synthetic** counter recurrence k=2,3,4,5,6, 48 steps each, 240 observed (a,b,r) behaviors. No synthetic training `mod` output code or correct target AST input.
- AST DSL: all 5 ordered full-binary tree shapes with exactly three operations from `+,-,*,div` and 4 leaves from `a,b,1`. `mod` NOT present; exactly **25,920** complete programs. Exactly **2** programs reproduce all training states with zero behavioral error.
- Loss `L=log1p(mean absolute program error)+0.1×(1-fraction exact)`; temperature 0.02, determined in **already observed local development**, so this study is not blind/preregistered evaluation. Target posterior q(AST)∝exp(-L/0.02), no supplied winning program identifier or AST pseudo-label. Actual **80 NumPy analytic Adam gradient updates**, learning rate 0.2, on behavioral-posterior-weighted categorical log-likelihood, no GPU or paid API.
- **First GitHub Actions #39402593905 FAILED at pip dependency setup** because torch 2.5.1 requires sympy 1.13.1 but workflow pinned sympy 1.14.0. This run never executed the scientific model; failure retained. To honor compute minimization, dropped heavy torch requirement entirely and implemented **the same weighted cross-entropy/Adam analytic gradients in NumPy**. First revised scientific verifier [Actions #39402836605](https://github.com/yoonsj0305/NEUMANN/actions/runs/39402836605) finished **SUCCESS** with all gates.
- First authoritative actual complete result source JSON SHA256 `78da62bb1cf2013d8111cbbc769da4b34f3893eb2493d89b0dd64722bfca8887`; CI artifact [#12256685896](https://github.com/yoonsj0305/NEUMANN/actions/runs/39402836605/artifacts/12256685896), downloaded GitHub ZIP CRC PASS. Frozen [branch source](https://github.com/yoonsj0305/NEUMANN/blob/research/q3-behavioral-gradient-conditional-ast-20261020/research/evidence/q3_behavioral_conditional_ast_20261020/first_cpu_original.py).

## Three causal controls and source-original synthetic proof

| Identical 25,920 ASTs and 240 training source outputs | Trained model's greedy AST | Unseen k={7,8,9,11} |
|---|---|---|
| 29 independent logits, 80 gradient updates | `(- a (* (div b a) b))` | **FAIL** |
| 125 shape-conditional logits, 80 gradient updates | `(- a (* (div a b) b))` | **PASS 4/4** |
| 125 conditional, same inputs but permuted training source outputs | `(+ 1 (div 1 (- 1 1)))` | **FAIL** |
| Exact full classical grammar behavioral enumeration/argmin | `(- a (* (div a b) b))` | **PASS 4/4** |

A separate **untrained** both-architecture zero-logit greedily decodes trivial addition and fails. Correct conditional model training loss **10.162770150→0.707932827** over 80 updates, weights SHA256 `c67457981ed9f8faea5b1b38061ceebb998340274554e003b67bf47822280f10`, training component 3.223ms. Independent 29 model fit 10.162770150→2.092314759, loss class 3.172ms, still fails. First model generated a valid newly composed macro from reward-only posterior, with no explicit correct AST pseudo-label.

Frozen heldout k 7,8,9,11 are **same-author synthetic family**, 100 source-state observations for each k, all fit by conditional AST 4/4. Each heldout unchanged synthetic Pre/Trans/Post original program was separately checked for **all 3 negated 3VCs** `initial,consecution,post`: **Z3 UNSAT 12/12; independent SHA-pinned cvc5 1.4.2 UNSAT 12/12, exit code 0**. Helpers missing the generated remainder relation fail Post (SAT counterexample). No external real new source-family G1 in this experiment.

## True economic baseline and attribution veto

Actual same GitHub CPU run classical candidate AST behavioral enumeration+score cost **667.827ms**, first argmin coefficient selection **0.014ms**. This **same 25,920 program enumeration** is also performed as a *necessary preprocessing prerequisite* for both learned neural policies. Thus incremental conditional gradient train cost **3.223ms** is strictly additional to exhaustive classical search. A strong classical baseline already knows the exact program by loss argmin without learning, and can cache that AST at negligible cost. The neural approach is **not more economical**, not a useful deployable system improvement under the NEUMANN North Star on this workload.

`Q3_NEW_AST_OPERATOR_NOT_IN_BASE_GRAMMAR=NO`: the full **composite** `a - (a div b)*b` is absent from single primitive operators but included among 25,920 pre-enumerated programs. This matters: training a policy over an exhaustive DSL does not constitute invention outside that DSL or a learned new operator in its mathematical search space. Prior art DreamCoder/LILO includes library learning and compositional synthesis.

**Truthful closed scope**: modeling **interdependent typed AST slots conditioned on tree shape** solved a zero-gold-AST-label, behavior-posterior policy fit that naive independently factorized slots did not, while four heldout author-created programs received independent actual Z3 and cvc5 safety proofs. But `Q3_UNASSISTED_NEURAL_OPERATOR_INVENTION=OPEN`, `Q3_ORIGINAL_FRESH_AUTHOR_BLIND=OPEN`, `Q4/Q5_ALL_IN_10X=OPEN`, `Q7_FRONTIER_PROVIDER=BLOCKED`; all global Q1–Q7 OPEN. Historical failures remain unchanged.

## STOP / one decisive next architecture gate

**Do not keep improving this same family** by changing temperature, token logits, or adding more AST shape slots: the complete classical enumeration already proved and solved it cheaper. Any NEXT Q3 claim must eliminate full exhaustively computed target program posterior from the training pipeline, propose first unseen useful AST from learned weights without search teacher or enumerated gold proxy, and verify across newly locked independent real-source families against strongest same-information classical original 3VC specialists. Otherwise preserve this Q3 label-free structural binding as a **mechanism milestone**, not global Q3 innovation.