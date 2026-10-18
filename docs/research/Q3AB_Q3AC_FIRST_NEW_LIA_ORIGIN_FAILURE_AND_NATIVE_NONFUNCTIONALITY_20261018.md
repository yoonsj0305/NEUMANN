# NEUMANN 1 · Q3AB / Q3AC | Two fresh LIA origin groups 0/2 FAIL and proof of nonfunctional native transitions in 2 original sources

**2026-10-18 KST | Final falsifiable evidence.** This is a domain-representation **failure** that narrows Q3 next design, NOT learned discovery or certified new source safety theorems. Prior Q3Z classical 2/6 developer +1/6 prospective origin math successes remain unchanged; global Q3 and global Q1–Q7 OPEN.

## Q3AB original source-family experiment: frozen classical source polynomial generator fails

Registered **BEFORE** reading six selected original source bodies: [GitHub Issue #235](https://github.com/yoonsj0305/NEUMANN/issues/235). Genuine LoopInvGen upstream Git commit `6ac90265b11431c9477dfbd33e3e3380234c0499`, exactly two chosen groups from LIA not used in Q3Z original NIA groups and not Q3R's first three LIA origins: `benchmarks/LIA/Lustre` alphabetically first three .sl and `benchmarks/LIA/others` alphabetically first three .sl. No filtering by source/formula/gold result, no substitutions after seeing original results.

Algorithm was **exact same unchanged Q3Z source-conditioned polynomial semantic generator** from frozen Git commit `4df97c0f9f51b0a88e413b1c617b0466a1611fed`, exact git blob `869271c35fad857ebd7889291bfe1c74e0ca59fc` verified BEFORE any selected source interpretation, and its original source-reader versus native-SMT equivalence checks; exact source-domain initial/pre SAT, negated post SAT, and new invariants only if all ORIGINAL Pre=>I, I&Trans=>I', I=>Post VCs independently UNSAT and Post alone insufficient. No changing arithmetic, no learned weights, no source-specific theorem, no retraining, no GPU/API.

**[GitHub Actions FIRST SUCCESS (execution) #39135955333](https://github.com/yoonsj0305/NEUMANN/actions/runs/39135955333)**, [immutable six-file evidence artifact #12139582397](https://github.com/yoonsj0305/NEUMANN/actions/runs/39135955333/artifacts/12139582397), ZIP SHA256 **`bb757e9f6b958ffc6f8f56aedeb12b0856f8273197ce3ad1f24ac838366f73d3`**, independently downloaded/unzipped and all six original Git blobs/statuses/negative results re-audited.

| Original filename and pinned Git source | Original Q3Z result | Reason | Strong specialist original-native SPACER |
|---|---|---|---|
| `LIA/Lustre/DRAGON_1.sl` | ABSTAIN, no new theorem | `UNBOUND_ORIGINAL_SYMBOL` (large Boolean/helper-function source outside current safe reader) | Not evaluated because source not extracted |
| `LIA/Lustre/DRAGON_10.sl` | ABSTAIN | same parser limitation | Not evaluated |
| `LIA/Lustre/DRAGON_10_e1_3587_e3_2749.sl` | ABSTAIN | same parser limitation | Not evaluated |
| `LIA/others/brett.sl` | Q3Z case completed, ZERO new certified invariant beyond Post | Polynomial goal not newly original 3VC verified; Post-only 3VC `[unsat,sat,unsat]` | **`unsat`** (source-native safety) |
| `LIA/others/gcnr_tacas08.sl` | ABSTAIN | original transition not a single fully explicit affine update | **`unsat`** (source-native safety) |
| `LIA/others/inria-00615623_4.sl` | ABSTAIN | original transition not a single fully explicit affine update | **`unsat`** (source-native safety); **Post-only three original VCs already `[unsat,unsat,unsat]`** |

**Preregistered cross-two-origin structure-generation outcome `0/2 = FAIL / CLOSE`, novel original-proven relation `0/6`, ZERO trained neural.** Original strong classical source-native SPACER returns safety for all three `LIA/others` originals where a native parser exists; the one already Post-inductive source cannot demonstrate any relation novelty beyond Post. Hence no demonstrated new classical specialist gap for the examined cases, even if an alternative generator were built.

## Q3AC separate source-OPENED semantic blocker proof, WITHOUT modifying Q3AB original score

A new **posthoc original-source semantic diagnostic** was preregistered only AFTER Q3AB first failure in Issue #235 [comment #6251090226](https://github.com/yoonsj0305/NEUMANN/issues/235#issuecomment-6251090226). It NEVER re-ran Q3Z on different targets or revised Q3AB's 0/2 score. On the two already-exposed original `LIA/others` formulas that did not fit a deterministic affine graph, original Pre/Trans/Post native SMT semantics were checked against the parser's re-expression, with three independent XOR refutation queries each equal to `unsat`.

Test the actual native original transition `T` for **two distinct permitted next-state successors from the same old state**:

[
T(s,s_1)\land T(s,s_2)\land(s_1\ne s_2)
]

No original formula modification: the second transition has ONLY its next variables alpha-renamed; old state variables shared; additionally enforce pairwise distinct next tuples. **SAT with a concrete same-old two-different-next model mathematically proves the entire source transition is NON-FUNCTIONAL and cannot be exactly represented as a SINGLE deterministic update `s'=As+b` on all original allowed transitions.** It does NOT prove program unsafe and does not rule out relational/guarded invariant proofs.

- `gcnr_tacas08.sl`: original native Pre/Trans/Post XOR **3/3 UNSAT**, above two-successor original semantic query **SAT**, original old state [`-1,4,0,400`], successor1 [`0,4,0,410`], successor2 [`0,5,1,410`].
- `inria-00615623_4.sl`: native XOR **3/3 UNSAT**, two-successor query **SAT**, old state [`-1,0,0`], successor1 [`-1,0,0`], successor2 [`0,1,0`].
- Both original source full transition-relations are truly nonfunctional, confirmed original model witnesses, not just syntactic "OR" appearances. These counterexamples use arbitrary source-permitted old states, not necessarily reachable ones; they invalidate global `Trans ⇒ exact single deterministic graph` precondition required by Q3Z, not all possible invariant reasoning.

**[Actual first native-source functional diagnosis GitHub Actions #39136333150 SUCCESS](https://github.com/yoonsj0305/NEUMANN/actions/runs/39136333150)**, [immutable original semantic witness artifact #12139649086](https://github.com/yoonsj0305/NEUMANN/actions/runs/39136333150/artifacts/12139649086), ZIP SHA256 **`38377db9154a34da54d06d0a3613bfab42bafa8bcbbc3b434715e35ab36b64b1`**, independently downloaded and re-read source-hash/3-parity/two-successor concrete witnesses. No new original safety theorem, no training.

## Fastest sound Q3 architectural conclusion

The failure is a **TYPE/RELATION REPRESENTATION CAP**, not proof the model needs larger weights or more epochs:
- **Lustre** original selected tasks genuinely include large Boolean states and nested define-fun node helpers, while old source reader assumes bounded small scalar polynomial variables and fails symbol binding. Do NOT “fix” by ignoring Boolean state or constraints: any such transformation must independently prove Pre/Trans/Post XOR equivalence against the source first.
- **LIA/others** two actual original transitions are mathematically nondeterministic. Thus a single global deterministic affine transfer function is NOT an equivalent model of the source: must preserve guarded/non-deterministic relational `Trans` as an exact typed semantic relation. Any specialized case splitting must preserve disjunction and guards, prove source equivalence, and check every branch's inductiveness under the ORIGINAL `Trans`.
- **Strong classical source-SPACER already proves 3/3 LIA/others** where readable. Q3 learning novelty cannot be claimed on these as classical-gap wins, nor on original `inria` where `Post` alone is inductive.
- One sound next representation contract: source-original mixed-sort `TypedRelationalIR` with explicit helper binder substitution, guarded branches, nonfunctional transitions, optional nondeterminism, bounded semantics and **native original XOR UNSAT check**. A future model must emit **new** original-source-grounded predicates `ΔΓ\Γ`, not just TOP12 from fixed Γ, and certify full original Pre/Trans/Post 3VC. Compare against Post-only, untrained, full classical grammar and source SPACER. Train+inference+verification and fallback compute charged. Until this real new capability runs on source-unopened two genuine independent origin families, GLOBAL Q3 OPEN.

**Final**: `Q3AB_FROZEN_SOURCE_GROUP_TRANSFER=FAIL/CLOSE`; `Q3AC_OPENED_SOURCE_NATIVE_RELATION_NONFUNCTIONALITY=PASS/SCOPED_EXACT_TWO_ORIGINALS`; `G1_NEURAL_NOVEL_RELATION=NOT_TESTED`; `GLOBAL_Q3=OPEN`; `GLOBAL_Q1_Q7=OPEN`. Stop further source retuning of either opened group or old Q3Z frontend under the name of blind validation.

Code: [Q3AB fixed new-origin proof trial](https://github.com/yoonsj0305/NEUMANN/blob/research/q3ab-frozen-polynomial-two-LIA-origins-20261018/research/evidence/q3ab-first-two-LIA-origins-20261018/first_six_original_polynomial_generator.py) · [Q3AC exact source transition two-successor proofs](https://github.com/yoonsj0305/NEUMANN/blob/research/q3ab-frozen-polynomial-two-LIA-origins-20261018/research/evidence/q3ac-original-transition-two-successors-20261018/first_opened_source_nonfunctional.py).
