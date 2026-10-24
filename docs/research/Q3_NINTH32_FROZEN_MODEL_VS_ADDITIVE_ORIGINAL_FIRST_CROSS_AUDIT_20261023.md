# NEUMANN Q3: First original proof, previous frozen model vs additive macro

2026-10-23 | [PR #547](https://github.com/yoonsj0305/NEUMANN/pull/547) previously frozen unary model | [PR #548](https://github.com/yoonsj0305/NEUMANN/pull/548) source-composed two-term macro. Independent artifact-matching [CI #39928118313](https://github.com/yoonsj0305/NEUMANN/actions/runs/39928118313) PASS, report SHA256 `e631edc04801ca8a02a04e9e3f92b5b55e7848607db2029dcf8dd51a1f9de56f`.

The two original studies refer to **exactly the same public EquationDiscovery ERBench original author equations, 32 source IDs**, SHA-ranked2256..2287. Their separate private entire true author expressions are byte-identical, original-truth SHA256 `70177035c01d16a7c0ed0da003ee3049bc3d605ea282a16bf927ba22a80206e1`. **28/32 original numeric x-y observation records also match exactly**, four do not (IDs `6523302d1a25a1f06d560d3c`, `654dca7f266f31b2133293d7`, `65bb51eee18bfd088bf4b140`, `65fb09977fe42c938f188c6e`). The original numeric arrays for ALL THREE *additional* source equations solved by the additive model are exactly identical across both experiments.

| First native original independent exact judge | Frozen unary model | New additive program constructor |
|--|--:|--:|
| Entire original author formula exact | **2/32** | **5/32** |
| Newly recovered original source equations | n/a | **3 extra** |
| Original-only solutions vs each method's classical baseline | 0 | 0 |
| Known model training + source inference process CPU | **32.141049426s** | **7.607514107s** |
| Each method's own strong classical source-test CPU | 7.325804413s | 0.904692503s |

The three new author tasks are `OEIS oeis_1468` (true cubic), `OEIS oeis_2971` (true quadratic), and `OEIS oeis_3047` (true quadratic). These source-only samples were exactly matched, so observation changes on four OTHER original tasks do not explain these gains. Model training differs: the original frozen neural MLP weights and macro-library SHA were **exactly verified against its previous eighth32 pregrade first source** by [run #39927068026](https://github.com/yoonsj0305/NEUMANN/actions/runs/39927068026). Its workflow initially contained a wrong unit test Python module import and was corrected *without changing model code*; it finished after PR548 had first graded this same original32, so no claim of chronological private-blind leaderboard validity.

Mathematical source program certification:
- [Original true cubic two-cube irreducibility #39926416895](https://github.com/yoonsj0305/NEUMANN/actions/runs/39926416895) PASS: `2x³+2x²+2x−2=(2/9)(x−1)³+(2/9)(2x+1)³−2`, no single cubic `A(Bx+C)^3+D` over ANY real parameters, since `a2²−3a3a1=4−12=−8`. First receipt SHA256 `4e56b613ec248e8997b17018b50541b543f8abd33b2cf244efdc9262296a2127`.
- [True quartic nested-square impossibility #39926872625](https://github.com/yoonsj0305/NEUMANN/actions/runs/39926872625) PASS: `(10x+5)^4` found by learned `SQUARE∘SQUARE`; single affine-shifted polynomial atom of degree≤3 cannot represent degree4. Two fixed-budget nolearning 512 controls missed it; full 3920 classical solved it. Receipt `90a757dfb21b65bdc91562fcb2e794ae8a95029f0ca2990ed9dd3b49c4d5bb02`.

**Scientific conclusion:** Human-restructured compositional source synthesis yields 3 more true original author equations and less measured CPU than old frozen learned model, but grammar, fitting and source optimizer all changed. It does **not** isolate a learned model's inventiveness. New additive MLP predicts primitive categories, while HUMAN-coded two-branch joint OMP constructs full AST. Both approaches are worse than own strong classical comparator after training cost. A all-basis OMP is not a globally exhaustive GP/PySR/Operon baseline. These are public original source tasks, not a private official blind benchmark. `STRUCTURAL_SCOPED_PASS`; `G1=HOLD`; `Q3_GLOBAL=OPEN`; `Q4_10X=OPEN`; `Q6_UNSEEN_AUTHOR_WEIGHT_TRANSFER=OPEN`; `Q7_FRONTIER=OPEN`. Classical polynomial algebra underlies certificates, not novel mathematics.
