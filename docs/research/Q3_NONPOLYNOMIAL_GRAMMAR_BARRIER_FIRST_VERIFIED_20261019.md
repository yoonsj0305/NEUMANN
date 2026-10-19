# NEUMANN 1 Q3 | Polynomial grammar remainder barrier and synthetic typed escape FIRST evidence (2026-10-19)

**First-science outcome: universal expressivity theorem proven, 24 finite contradictions Z3+cvc5 PASS, four synthetic counter programs verified Z3+cvc5 PASS. Not a learned new mathematical primitive; GLOBAL Q3 OPEN.**

## 1. Actual theorem over ALL finite polynomial degrees

For every integer `k>=2` and every rational-coefficient polynomial `P(n)`, no equality `P(n)=n mod k` holds for every nonnegative integer n. Indeed `P(0)=P(k)=P(2k)=...=0` forces infinitely many zeros, hence `P≡0`, contradicting `P(1)=1`. This is a universal mathematical proof, not merely statistical. The finite proof witness for degree <=d uses zeros at n=0,k,...,dk plus 1. The `(d+1)x(d+1)` integer Vandermonde of evaluations at n=0,k,...,dk has nonzero determinant `k^[d(d+1)/2]*prod(j!,j=1..d)`. Hence zero on d+1 distinct points forces all coefficients to zero, inconsistent with value 1 at n=1. No choice of neural weights can overcome this expressive limitation if its output is restricted to a single finite rational polynomial in n.

**Scope:** This is a statement about fully representing the function `mod(n,k)` on an unbounded integer domain with a single rational polynomial. It does not say that a polynomial *invariant* can never prove a program whose original source has mod/div (indeed PR #294 and PR #297 give counterexamples using polynomial relations plus the SMT arithmetic theory). It does not show general neural impossibility or novelty of the theorem in mathematics.

## 2. Exactly frozen solver falsification of finite claim

- Prereg contract in commit `d786afa1`, [PR #298](https://github.com/yoonsj0305/NEUMANN/pull/298).
- First independent [GitHub Actions #39268632707](https://github.com/yoonsj0305/NEUMANN/actions/runs/39268632707) **SUCCESS**. First data [artifact #12194720495](https://github.com/yoonsj0305/NEUMANN/actions/runs/39268632707/artifacts/12194720495).
- All **24 cases** `k in {2,3,4,5}`, `degree in {0,1,2,3,4,5}` checked *independently*: original real unknown polynomial coefficients forced zero at n=0,k,...,dk and forced P(1)=1, **Z3 UNSAT and pinned cvc5 1.4.2 UNSAT for each of 24/24**. Exact SymPy rational Vandermonde nonzero rank & determinant identity also rechecked in all cases.
- Finite interpolation stress positive control: any 5 observed remainders for k=2 can be exactly fit by rational degree<=4 polynomial, but the same polynomial extrapolates `P(5)=-15` while `5 mod2=1`. Exact symbolic check PASS. Thus in-range exact fit and modest heldout accuracy are NOT universal expression or true new structure evidence.
- Original raw JSON SHA256 `387e5d9eb55d55a487d6465f89892c5f67d3c4ad30b952f24924d82210cff80b`; zipped original artifact SHA256 `39da6aeed076bbeb2f6e318ac0b64187ca2ebbcc4a31024da508b1008a4281d6`, ZIP CRC PASS.

## 3. CPU-trained synthetically generated typed `mod` invariant diagnostic

Author-created counter family: `Pre: i=0,r=0`, `Trans: i'=i+1, r'=if r=k-1 then0 else r+1`, `Post: r=i mod k`. This is **NOT** an external published source or unseen author-family.

Training cases k=2..6, 48 **source-generated** residue observations each. A true two-parameter trainable linear neural readout on a **classically computed** `max remainder` statistic was trained via CPU L-BFGS-B 9 gradient iterations; weights 0.9999999999999929 and 0.9999999999999899, fit ~1.333 ms (component-only, 5 training programs). On *synthetic* heldout new modulus values k=7,8,9,11, predicts all **4/4** exactly, and combines a **pre-supplied typed `mod` grammar primitive** with frozen source-range helper to emit `r=i mod k`. **Full unchanged SYNTHETIC** initialization/consecution/Post VCs independently Z3 UNSAT 3/3 and cvc5 UNSAT 3/3 **for each of 4 heldout cases**, helper-only Post SAT. Output expression is outside all polynomial-only grammars.

**Essential attribution veto:** The model only estimates k; `mod` is an explicitly supplied syntax/operator, NOT invented by learning. The source-only exact classical `max(remainders)+1` also returns the identical 4/4 k values, no weights or training. Moreover k is a visible constant in the synthetic counter's original update; an ordinary source parser can recover it without statistical learning. Therefore, although **synthetic typed operator composition is functional**, this specific neural architecture is unnecessary and cannot establish a distinct learned abstraction or efficiency advantage. STOP spending more training on this family.

## 4. The actual next structural criterion

- **REJECT** more projects asking a trained model to output scalar coefficients over a fixed monomial set, even when high-degree or an externally verified source is found: strong exact classical linear algebra interpolates at least as well on noiseless determined polynomial systems. Preserve historical Q3 first failures and original proven partial results.
- **REQUIRE** an AST-producing learner that proposes a syntactically *new reusable abstraction*, not a scalar/label of a pre-supplied `mod` or polynomial template, with frozen distinct source-family evaluation and strong source-only exact symbolic solver, DreamCoder/LILO-style library-compression baselines on identical source+goal budgets. Module may use typed recursion, conditional branching and operator composition, not merely 21 monomials.
- **ADMIT a Q3 learned invention claim only if** the actual model outputs a certified new semantic relation that (i) wasn't enumerated in given finite Γ, (ii) isn't simply a gold/Post-only restatement, (iii) depends causally on trained parameters (matched ablation fails), (iv) solves nontrivial original goal with independently verified unchanged VCs, (v) generalizes on multiple independently preregistered source groups, (vi) beats strong complete same-information classical search under meaningful equal-budget or otherwise earns documented useful comparative value, and (vii) accounts for training/verification/all-in costs. Syntactic novelty over a deliberately weak Γ is never sufficient alone.

## Source paths and status

- Executable experiment: `research/evidence/q3_polynomial_mod_barrier_20261019/unbounded_modulo_theorem.py`
- [First GitHub Actions original receipt](https://github.com/yoonsj0305/NEUMANN/actions/runs/39268632707), [draft PR #298](https://github.com/yoonsj0305/NEUMANN/pull/298).
- `Q3_POLYNOMIAL_REMAINDER_EXPRESSION_IMPOSSIBILITY=MATHEMATICAL_THEOREM_PROVEN`.
- `Q3_SYNTHETIC_TYPED_MOD_COMPOSITION=SCOPED_PASS`.
- `Q3_GENUINELY_LEARNED_NEW_OPERATOR=NOT_PROVEN`.
- `Q3_UNIQUE_NEURAL_ADVANTAGE_OVER_MATCHED_CLASSICAL=FALSE` for this study.
- `GLOBAL_Q1_Q7=OPEN`, `Q4/Q5_10X_ALL_IN=OPEN`, `Q6_INDEPENDENT_BLIND=OPEN`, `Q7_FRONTIER=BLOCKED`.

Prior art: DreamCoder 2021; LILO / Stitch ICLR 2024. Novelty must be assessed relative to these, not just against monomial-regression variants.