# First authentic-external transfer audit of frozen Q3B model: preregistered BEFORE target source fetch

2026-10-17 (KST). **Do not view target source bodies, their exact relation signature, or their goal before committing this protocol.** Target names selected only from a repository file-name listing.

## Model freeze
- Frozen source: `research/evidence/q3b-trained-two-relations-20261017/frozen_checkpoint.json`
- Checkpoint exact SHA256: `2d557d5d92f4627749ded23c762ec0faf343ee20db679cee0b3222f15bf1b360`
- 40 real learned weights. Already trained on 1024 researcher-authored synthetic affine two-predicate programs with 8-D handcrafted bilinear source features: `[a,b,p,q,a*p,a*q,b*p,b*q]`.
- **No further fit, decoder/feature changes, retries, choice of benchmark based on score, manual hints or candidate proof corrections**. Frozen semantics are two 2-Int predicates A and B, linear invariants plus cross-predicate offset.

## Two first authentic external targets (same RustHorn corpus, distinct subgroups)
Immutable upstream `chc-comp/rust-horn` commit `e5a86a1ad252fe1df75e06814769ec1d14540032`.
1. `inc-max-2-base3-safe.smt2`: integer-control subgroup, first.
2. `lists-3-inc-some-safe.smt2`: recursive ADT subgroup, second.

This is **out-of-generator-distribution** from synthetic training, but both external targets share a single external repository, so **not two independent source families for research-generalization counting**. The word `safe` in filenames may disclose intended verdict; NO filenames, known labels, summaries, external answers or metadata may be model inputs. Entire original bytes allowed to source parser.

## First-only fixed execution
- Do one source download per case from commit-pinned raw URL. Verify SHA256, Git blob SHA1, byte counts; no other source fetch or replacement.
- Parse complete original SMT2 via Z3 4.13.3.0. Record all original clauses, relations (name/arity/sorts), ADT declarations, and goal structure. No editing, renaming, or pretending source is equivalent to a synthetic instance.
- Strictly recognize the **previously trained two binary integer predicates / exactly 5 original rules / two affine self-loops + A-to-B affine shift + original goal** pattern. If any relation count, sorts, clause count, transition semantics, or parsing differs, return `ABSTAIN_UNSUPPORTED_SOURCE_GRAPH` with original source identity and exact reason **BEFORE neural inference**. No automatic hand-seeding of a new predicate grammar.
- If the exact predeclared pattern is supported, extract only `(a,b,p,q)` from source (no label/goal-to-gold leak), load frozen weights and emit original predicate interpretations. Independently check **all original quantified clauses** on unchanged bytes. Require every negated clause UNSAT, fail closed on SAT/UNKNOWN/timeout.
- Baseline: same-information exact classical coefficients `[-b,a,-b,a,-b*p+a*q]`, plus zero-head ablation; all cases include parser+inference+verification timing and number of solver calls, even rejections.
- Hard deadline: 6 seconds source parsing, 5 seconds per original obligation, 90 seconds per case max. Unknown/missing native C interface = ERROR, not safety proof.
- If unsupported, no positive/negative model proof can be claimed; we learn exactly what interface/representation expansion is necessary. The **response must not claim Q3 external failure for a model that was never run**.
- No paid provider, GPU, frontier comparison, training, sealed holdout or 10× claim.

## Admission boundary
Primary verdict: `MODEL_EXACT_GRAMMAR_COVERAGE: 0..2` with strict source identities; scoped conditional proof if any model actually runs. New independent source-family generalization and global Q1–Q7 all remain OPEN unless separately met by much more demanding prospectively frozen admission contracts.

**This is the last test of Q3B's current two-relation affine grammar. If external coverage is zero, stop further Q3B tuning and pivot to a typed source-conditioned relation-graph proposer.**
