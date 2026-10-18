# NEUMANN 1 · R9 classical-specialist headroom test: 10.762× LOWER measured work than R8 generic, SAME 16 original theorems
**2026-10-18 KST. Historical first same-runner one-campaign result.**

## Decision: R9 bounded classical control PASS; R8 minimum-compute superiority FAIL / NOT ADMITTED

The new low-level result is NOT the NEUMANN architecture becoming 10.76× more efficient. It is precisely the opposite external-validity control: **an appropriate traditional specialist that already knows the problem family can prove all 16 original UNSAT claims using 90.7085% less full measured Python subprocess work than R8's general parser + exact modular search + SymPy verifier**. That means R8's important **16/16 mathematically valid originals and 8/8 source-body-unseen (within-generator) result remains correct**, while **any claim of minimum necessary computation or dominance against a relevant classical specialist on this family is disproven**.

The well-known modular-9 theorem underlying BOTH implementations is not NEUMANN's neural learned semantic discovery, and the dedicated three-cubes baseline was written AFTER all 16 R8 source bodies became opened. These are **already opened same-generator ORIGINALS**, not new generalization.

## Method frozen before R9 data collection
[Issue #232 preregistration](https://github.com/yoonsj0305/NEUMANN/issues/232) before new performance data. Both algorithms solved EXACT SAME immutable 16 original SMT2 source files from `SMT-LIB/benchmark-submission-2022@81a39628827f61fbd74c6f3e67feb5c1b740d2f0` in `non-incremental/QF_NIA/20220315-MathProblems`, using the **per-file original SHA256 checks** from the earlier independent first R8 original evidence [#39130417694, artifact #12137797624](https://github.com/yoonsj0305/NEUMANN/actions/runs/39130417694/artifacts/12137797624). All 16 original hashes matched, all uniquely identified.

**Unchanged R8 generic arm**: original source Git commit `17c127dde4b477edf0a93ca041ae53150dc97e93`, Git blob SHA1 `e6e8682bbc87def7921d13954331e1ab66ac9267`, exact formal Z3 AST and SymPy independent polynomial residue verifier, m=2..12, 3 variables, 729 checked for proof at mod9, one newly cold Python subprocess per case (imports Z3 and SymPy for EVERY source). Input and math neither tuned nor modified.

**Strong specialized classical control**: original-code Git commit `e53b00c110b7528050de42c9f0b7facdb595e9b6`, Git blob SHA1 `fd2fdbda8637b3ba0150cc22257d73c9dfcc22cb`, zero-dependency Python stdlib-only SMT-LIB S-expression parser. It handles quoted symbols, strings, SMT2 ; comments, balanced parens, and accepts ONLY a real **top-level original required asserted** equality of exact `(+ (* x x x) (* y y y) (* z z z)) = n` with three distinctly declared nullary Int vars (operand order reversible). It computes reachable mod9 sum residues from three cube residues, and **separately rechecks all 9³=729 exact integer triples modulo9**; if `n mod9` is absent, the original required equality has NO integer assignment, hence the whole original source UNSAT. No reference status, filename, n-specific answer or weakened original expression is supplied. On 0..8 synthetic integer controls it certifies exactly 4 and 5, and a disjunctive `(assert (or (impossible cube sum) true))` **does not** falsely prove UNSAT. Artificial controls are only negative correctness tests, never counted as original benchmark successes. Independent generic R8 source verifier also rechecked mathematical same-original UNSAT for all 16 in the trial.

**Cost**: three independent repetitions, all 16 original cases each (48 per arm, **96 separate cold original-source processes**). Fixed alternating per-file/per-trial execution order on ONE free GitHub Actions Ubuntu CPU runner. `/usr/bin/time` wall and peak RSS for each trial, independent mathematical certificates and original SHA recorded. The pinned source code for EACH arm was fetched once and its fetch wall charged to that same arm. The raw original 16 file downloads and shared CI environment provisioning/install are excluded symmetrically. No fake zero-cost runtime for either arm. All 48+48 proof runs correct, no failure, no timeout.

## Immutable first artifact and independent recount

- [GitHub Actions FIRST SUCCESS #39131850618](https://github.com/yoonsj0305/NEUMANN/actions/runs/39131850618), [complete first 96-execution 16-source ZIP #12138227855](https://github.com/yoonsj0305/NEUMANN/actions/runs/39131850618/artifacts/12138227855); independently downloaded and verified ZIP SHA256 `04f596f08c9d6512b66ee12d6bdaf18bb351a0000e667243322f4e17104b98e2`, JSON `neumann_r9_specialist_first_repeated.json` read in an independent Python auditor. All 16 unique original source SHA and 48 trial rows validated, source SHA per proof matches its original, exactly **48/48** math original certificates in EACH arm.
- Correctness guards: specialist independently exhaustively enumerates 729 original modulo9 assignments, source top-level AST assertion verified; independent mathematical source checker R8 accepted the exact same original. Source-SAT remainder 0,1,2,3,6,7,8 test cases correctly refused by specialty; valid source with OR disjunction correctly NOT falsely rejected.
- No learned model, GPU, paid API, PR, training or model architecture changes.

| Original exact-source proof | R8 generic classical math | R9 specialized classical math |
|---|---:|---:|
| Verified original source UNSAT | **48/48** | **48/48** |
| Cold subprocess wall sum, 16×3 | **12.134738s** | **0.967816s** |
| Program source fetch once, charged to arm | 0.169224s | 0.175412s |
| Conservative matched arm total | **12.303962s** | **1.143228s** |
| Median original cold-process wall | 0.2399255s | 0.0198105s |
| Peak observed process RSS | 88,312 KiB | 15,256 KiB |
| Per 16-case cold-round wall | 4.283740s, 4.170976s, 3.680022s | 0.331164s, 0.326099s, 0.310553s |

The specialized arm used **1.143228 / 12.303962 = 9.2915%** of R8's measured algorithm cost. Saving **11.160734s / 90.7085%**, elapsed-work ratio **R8/R9 = 10.762474327×** under this narrow three-repeat original SMT2 proof comparison. These are *positive* time-to-correct-proof ratios because BOTH methods generate accepted original mathematical certificates. This is deliberately NOT a claim of global mathematical superiority of all special-purpose algorithms over all generic methods, nor a frontier 10× NEUMANN milestone.

## First-principles architectural implication, not demonstrated learned capability

R8's old general mod2..12 enumerator performs unnecessary work for an original known to have the three-cubes `m=9` obstruction: broad input interpretation, many irrelevant moduli, exhaustive 729-variable residue tuples, and heavy dependencies (Z3 AST + SymPy polynomial engine) per original. The dedicated original-checking specialty has minimum search complexity over a finite cube residue set plus O(original input bytes) parsing and explicit proof replay. A viable NEW inference architecture must cheaply determine **which sound specialized proof plan applies**, then dispatch to that plan rather than spending large cost on indiscriminate generic search.

Under additive accounting, if source structure is eligible with probability p, expensive general proof cost is G, applicable cheap proof cost is S and dispatch selection overhead is R, a hybrid selector has expected cost `R+p*S+(1-p)*G` and beats plain generic ONLY IF **`p*(G-S)>R`**, provided it never sacrifices correctness and all fallback/verification costs are also included. This necessary break-even inequality is mathematically derived, NOT a performance guarantee that a neural selector exists. A learned low-cost semantic structure detector requires frozen prospective original-source holdout, strong classical basis (including this specialist), discovered proof plan + whole-original witness certification + all-in dispatch/learning amortization. Nothing of that kind was trained/tested in R9.

## FAST-CLOSE status

- **`R9_RELEVANT_SPECIALIST_BEATS_R8_GENERIC_OPENED_STC16=PASS/CLOSE`** (appropriate cheaper classical baseline, exact original math 48/48 each over 3 repeat runs).
- **`R8_THIS_STC_FAMILY_MINIMUM_NECESSARY_COMPUTATION_ADVANTAGE_OVER_SPECIALIST=FAIL`**. This does NOT negate R8's mathematical theorem proof PASS 8/8 DEV and 8/8 source-body-unseen same-generator.
- Prior R7 `frozen Hoenicke-mod1 theorem new-source transfer=FAIL` unchanged.
- **`G0_FULL_STRONGEST_SPECIALIST_ACROSS_GENERATORS=OPEN/NOT_ADMITTED`**, **`G1_AUTONOMOUS_LEARNED_DISCOVERY=HOLD/NOT_TESTED`**, `G2_FRONTIER=BLOCKED`; **GLOBAL Q1–Q7 ALL OPEN**. R9 just set an actual relevant efficient classical performance floor. No new discovery architecture has been validated.
- **STOP this STC16 family now**. No further extra modules/microbenchmarks to find a favorable run. Any genuinely new investment needs a source-independent learned or algorithmically generic *low-cost semantic proposal/selection mechanism* compared against its specialized baselines with an independent verifier and bounded all-in costs. Otherwise the honest scientific result for the same family is CLOSED.

Code: [specialist source](https://github.com/yoonsj0305/NEUMANN/blob/research/r9-specialist-cube-mod9-control-20261018/research/evidence/r9-specialist-cube9/specialist_original_smt_cube9.py) · [same-host 16×3 original replay](https://github.com/yoonsj0305/NEUMANN/blob/research/r9-specialist-cube-mod9-control-20261018/research/evidence/r9-specialist-cube9/one_shot_16_original_3repeat_headroom.py) · [Issue #232](https://github.com/yoonsj0305/NEUMANN/issues/232).
