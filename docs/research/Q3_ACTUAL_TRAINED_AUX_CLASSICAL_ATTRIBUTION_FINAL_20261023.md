# NEUMANN Q3: ACTUAL self-supervised learned auxiliary proposer, strongest classical attribution, original verification

Date 2026-10-23 KST. **FIRST dedicated science execution completed with 3/3 separate GitHub Actions jobs SUCCESS:** https://github.com/yoonsj0305/NEUMANN/actions/runs/39893205295 . [PR #533](https://github.com/yoonsj0305/NEUMANN/pull/533) based on frozen previous original 4/4 classical proof from [PR #532](https://github.com/yoonsj0305/NEUMANN/pull/532).

## Important actual new step
Previous PR532 had **no trained model**, just a human-programmed exact mathematical relation `e_i=1-denominator*inv_i`. Here an ACTUAL 12-hidden-unit tanh NumPy neural network was trained on CPU (not a mock inference) to propose the nonconstant coefficient `a` of a source-conditional auxiliary relation `e(t)=1+a*t`, where `t=denominator*inv` and the transition source is `t'=2t+b*t²`.

**No answer/teacher coefficients in learning objective**: The original source's `b` is observable from the original update syntax. The self-supervised learning signal is whether `e(t')=e(t)^2` for training transition coefficients. Nonconstant negative initial parameterization `a=-softplus(MLP(b))` and 9 synthetic training coefficients `b in {-1.9,-1.75,-1.6,-1.45,-1.3,-1.2,-0.9,-0.8,-0.7}`. The original source coefficient `b=-1` was deliberately omitted from this synthetic training set. Model architecture, train values, 3 training seeds (11,23,37), 5000 steps, learning rate .02, exact integrality/equality gates were FIXED before the GitHub run. **The model did not synthesize the outer form `1+a*t`: that hypothesis family and negative sign were HUMAN-DEFINED**, and source input task family was already opened previously. This is narrow new coefficient fitting, not unrestricted autonomous semantic invention.

## Actual first-run source-only trained results
GitHub Actions middle source-only job sealed prediction JSON SHA256 `2c8dc3dd45f83620574845253bd5d0bdc23e044a9b13121c750260c85302d65c`.

| Random seed | Learned real-valued a on withheld synthetic coefficient b=-1 | Training process CPU |
|---|---:|---:|
| 11 | -0.9913315372066331 | 0.4932181050 s |
| 23 | -0.993685614592628 | 0.4836554010 s |
| 37 | -0.9934552641912819 | 0.4830522650 s |

Total actual model training CPU **1.459925771 s**, excluding Python start and package setup, includes three seeds. The modeled floating coefficients cannot by themselves prove original safety: inference rounded the consensus proposal to **integer a=-1** only under independently specified tolerance <=.05 and a !=0. The matched same-author QF_NIA original four inputs are EXACT original `modInv8/32/64/Full`; original answer/ground truth/status metadata physically withheld from the training job, predictor consumes only sanitized recurrence coefficients and IDs.

## After-seal independent true original mathematical grading
Distinct independent third job downloaded only the frozen neural proposal and separately original-authenticated source references and calculated symbolic exact local identity `a*(b-a)==0` with a!=0. Then `a=-1` had to activate exactly the frozen previous source-derived 2-adic/Hensel proof and independently verify full original mathematical UNSAT. Four original inputs were **already opened in earlier PR531/532** so this is NOT an untouched first-blind learner study. Original negative status metadata is never used by the learner.

**FIRST genuine independent source grading** JSON SHA256 `ce69d628a30bfbccabe888a898dfba600fd8006dfa3cfc753de2b678b9c83f9a`.

| Exact input cohort | Trained a proposal | Complete equal-grammar algebraic classical a solution |
|---|---:|---:|
| Four original full SMT2 UNSAT certificates | **4/4** | **4/4** |
| Nontrivial exact functional identities | **4/4** | **4/4** |
| Neural-exclusive certified original tasks | **0/4** | n/a |

Classical complete algebraic candidate construction of the original four took **0.000003647 s process CPU** for its source-only candidate loop versus model training >=**1.459925771 s**. **Do NOT advertise a 400,000x end-to-end advantage**, since candidate loop alone and training loop have distinct overheads and original grading work is shared. Nonetheless there is no evidence of economical learned exclusivity in this registered four-case DEV cohort. G1 properly remains NOT ADMITTED.

## Mathematical exact finite-language dominance theorem and nonvacuity trap
Given a symbolic recurrence `F_{u,b}(t)=u*t + b*t²` and candidate `e_a(t)=1+a*t`, subtracting:
`e_a(F_{u,b}(t)) - e_a(t)^2 = a*(u-2)*t + a*(b-a)*t²`.
A polynomial identity for ALL integers or reals t must have both coefficient values 0. Therefore:
- `a=0` always yields the **vacuous constant function** `e(t)=1` for arbitrary u,b. It cannot establish the intended original inverse precision, regardless of training loss.
- For a NONCONSTANT `a!=0`, such a quadratic semiconjugacy exists **if and only if** `u=2` and `a=b`. If u differs (e.g. u=3), NO candidate inside this fixed grammar can possibly work. If b=0, no valid nonconstant solution.
- A classical algebraic solver given exactly the SAME permitted grammar and symbolic input `u,b` is **complete**, and outputs `a=b` or fail. A trainable score model confined to this grammar cannot yield a mathematically valid new class outside it. It can compete in bounded compute, but not in **solution expressivity**. This is elementary polynomial coefficient comparison, NOT a new academic theorem.

This theorem closes the limited **capacity** question for the present family permanently; retraining the network cannot produce a learner-exclusive original correctness certificate against this full same-grammar algebraic control, no matter how many seeds or weights are tried. Hence **STOP** expanding this architecture without a new representation-generating mechanism and strong specialist headroom.

## Scientific scoped verdict
- `Q3_ACTUAL_NEURAL_TRAINING_AND_CERTIFIED_PROPOSAL=PASS_4_OF_4_OPENED_DEV`: the parameter-fitting neural proposer really trained without teacher coefficients and produced exact proposed coefficient after rational repair.
- `Q3_NEURAL_UNIQUE_SEMANTIC_INVENTION=FAIL_FOR_THIS_FIXED_GRAMMAR`: complete classic algebra same 4/4; theory proves there is no larger solution set from fixed grammar.
- `Q3_GENERAL_OUT_OF_HUMAN_GRAMMAR_NEW_OPERATOR=OPEN`, `Q6_CROSS_AUTHOR_TRANSFER=OPEN`, `Q4_TOTAL_COST_10X=OPEN`, `Q7_FRONTIER_PARITY=BLOCKED`.
- Four original independent mathematical proofs belong to same author and SAME source update schema, previously opened; not four independent semantic discoveries.
- `G1=HOLD` under existing G0 entry gate. This was a **development-only mechanistic experiment**, not a permitted claim of G1 pass.
- Strongly recommended: do NOT spend GPU/further tuning on a fixed-choice form. Next admissible learner must construct its own typed compositional expression graph and be challenged by classical synthesizers with the SAME graph operations/whole cost, and on new original unseen families.

Source truth SHA from pinned original; CI evidence survives unchanged in the first run. Preserve negative causal attribution even when neural-original accuracy is perfect.
