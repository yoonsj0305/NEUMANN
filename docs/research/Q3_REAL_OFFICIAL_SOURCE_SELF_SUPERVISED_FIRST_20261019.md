# Q3: Authentic official-source self-supervised learned conserved relation (first result)

**2026-10-19 KST. First prospective execution: 8/8 preregistered checks PASS, restricted scientific scope.**

Pre-registered [Issue #273](https://github.com/yoonsj0305/NEUMANN/issues/273) before source-local training, original proof, or outcome inspection. Two previously OPENED authentic public official SyGuS 2018 originals were fixed in advance at SyGuS-Org/benchmarks git SHA 13c8deb68a873635879c9a69bc78caebd340f646. No sealed task, Gemma inference, GPU or paid API.

## Real learned source-only invariants

| Published SyGuS original | Learned linear conserved relation | Earlier immutable result | New verified result |
|---|---|---|---|
| cggmp2005_variant_true-unreach-call_true-termination.sl | **lo + 2mid - hi = 0**, equivalently hi = lo + 2mid | **SOURCE_ONLY_SPACER_UNSAT**, no explicit original inductive invariant | **Native original 3VC UNSAT x3 + independent cvc5 UNSAT x3** |
| cggmp2005_true-unreach-call_true-termination.sl | **i + 2j = 21** | BRANCH_AFFINE_NULLSPACE original 3VC | Native original 3VC UNSAT x3 + independent cvc5 UNSAT x3 |

The source-local trained learner was a **single linear neuron with 3 or 2 learnable numerical weights**, optimized with deterministic projected gradient descent over pairs of states satisfying only PUBLIC Pre and Trans. Initial-state differences and state-transition deltas constrain the one-neuron conserved output. Training uses **zero supervised structure labels, zero gold solutions, and no Post values**. Frozen 2500 learning steps, fixed seed and rational coefficient extraction construct an exact integer relation from weights. The original **published Post** was added only after training to strengthen the final inductive candidate; source-only inductive nonnegativity constraints were also derived from Pre+Trans. This is a *per-source self-supervised linear invariant learner*, NOT pretrained transferable language reasoning, and NOT a new mathematical grammar.

The verifier is existing frozen PR #268 source-bound original SyGuS checker: actual original Pre/Trans/Post semantic parity, nonvacuity, all three native Z3 bad conditions UNSAT, and independent cvc5 also UNSAT for the exact SMT queries. Post-only is non-inductive for BOTH original cases. Prior first official archive #39210016907's source-only-SPACER result for the variant is untouched.

## First evidence and controls

- First valid [GitHub Actions #39218217283](https://github.com/yoonsj0305/NEUMANN/actions/runs/39218217283) SUCCESS, artifact #12170402701 archived before final verdict.
- Independently downloaded ZIP 3311 bytes, SHA-256 **a7d20d6af324e1c48b076521a70b5518f17c7f8cb7ce531ca58a49f8d44a089e**, ZIP CRC PASS.
- Exact first JSON SHA-256 **0c5fa54f59718a2c11a3cea37419bcc6e0e8467c9868f49c0683b6436fd48b25**, 12314 bytes, all source SHA, sample stats, learned vectors, original proofs, independent checker outcomes and timings independently inspected.
- Variant original: 12 source Pre samples, 20 Trans pairs, 31 nonzero linear constraints; neural drift loss **0.8552356447 to 1.320166811e-31**, learned coefficients **[1, 2, -1]**, train wall **10.618 ms**. Same-data exact full classical sympy nullspace: **[-1, -2, 1]** (sign-equivalent), wall **0.728 ms**. Seeded untrained weights FAIL original 3VC.
- Previous-positive original: 1 Pre sample, 20 Trans pairs, 20 constraints; drift loss **0.5345608246 to 8.568632992e-33**, learned coefficients **[1, 2]**, train wall **10.114 ms**. Same-data exact classical nullspace: **[1, 2]**, wall **0.417 ms**. Seeded untrained weights FAIL original 3VC.
- BOTH learned proposed relations combined with Post pass exact original 3VC and cvc5 x3 each; all 8 predefined gates PASS, false original certificates zero.

## Strong comparator null result: no resource or distinct-capability advantage

An independently solved **strong exact deterministic full-classical nullspace** baseline produced the SAME mathematical conserved relations and passed BOTH original tasks. On the isolated coefficient computation, classical **0.417 to 0.728 ms** is substantially faster than neural gradient learning **10.114 to 10.618 ms**. These numbers exclude common source sampling, proof, original checker, process cold start, money, energy, and investment, so **no complete-cost 10x finding** is possible. The experiment did not find any unique neural correctness advantage over strongest classical; under NEUMANN's deletion rule, this linear self-supervised neuron should NOT remain as a permanent component for this simple class.

## Exact bounded scientific verdict

- **Q3_SOURCE_LOCAL_LABEL_FREE_GRADIENT_DISCOVERY_ON_AUTHENTIC_ORIGINAL = SCOPED PASS 2/2**.
- **Q3_PRIOR_SPACER_ONLY_SOURCE_TO_EXPLICIT_INDUCTIVE_INVARIANT = SCOPED PASS 1 original**, without overwriting historical status.
- **Q2_ORIGINAL_Z3_AND_INDEPENDENT_CVC5_CERTIFIED = SCOPED PASS 6/6 original bad conditions**.
- **LEARNED_GAIN_OVER_UNTRAINED_SAME_VECTOR = SCOPED PASS 2 vs 0**.
- **LEARNED_UNIQUE_CAPABILITY_OVER_FULL_CLASSICAL = ZERO (both 2/2)**; **local gradient runtime worse**.
- **TRANSFERRED_PRETRAINED_WEIGHTS_TO_UNSEEN_EXTERNAL_TASKS = NOT TESTED**, since weights were fitted separately per known published source; Q6 OPEN.
- **MODEL_GENERATED_NEW_NONLINEAR_GRAMMAR = NOT PROVEN**; weights encode linear invariants only, no new operator type.
- **Q4/Q5_COMPLETE_ECONOMICS, Q7_FRONTIER_CAPABILITY = NOT EVALUATED; GLOBAL Q1–Q7 OPEN**.
- Frozen historical E2B AM1 FAIL, neural fixed-Γ Q3R NO-GO and sealed D3 BLOCKED unchanged.

**STOP** repeating these two opened sources or expanding easy constructed families. The next genuinely discriminative learned-science gate is a frozen cross-source learned parameter transfer or novel source representation on **new independently authored originals**, retaining full classical expert and all-in cost accounting, after an eligible GPU is legitimately available where required.

Implementation [Draft PR #274](https://github.com/yoonsj0305/NEUMANN/pull/274).