# NEUMANN 1 | Semantic-role recovery from real CHC programs

Date: 2026-11-07. Real, already-opened COPY2 and COPY3 development originals. Global Q3/Q4/Q5/Q6/Q7 OPEN.

## The falsified assumption

Our first graph/type-only invariant compiler, Draft PR #681, failed on a **real unchanged external benchmark** in [FIRST #42320555670](https://github.com/yoonsj0305/NEUMANN/actions/runs/42320555670). COPY2 was 9/9 UNSAT, while COPY3 passed only 3/11 clauses (12/20 total). The first run and its complete artifact ID 13552658124 are preserved unchanged.

The exact counterexample arose at COPY3 clause 3. Two adjacent Int parameters had identical types but distinct meanings: array base (x7) versus loop range bound (x8). The typed-only compiler selected the wrong bound. The missing information was **semantic variable role**, not program size, model weights or a higher search budget.

## Structural repair implemented

Separate post-FIRST code in [Draft PR #682](https://github.com/yoonsj0305/NEUMANN/pull/682):

1. Parse original linear Horn-clause dependency graph and strict typed stage signatures.
2. Read each original self-loop SSA guard and extract the actual bound/cursor relationship.
3. Generate quantified aligned-array prefix relations with base, cursor and bound in their semantically established roles, with no per-stage handwritten predicate interpretation.
4. Check every unchanged original Horn clause using independent Z3 negated-implication SAT testing. Any SAT/UNKNOWN is a failure.
5. Use a deliberately wrong +1 copy operator and demand a real SAT witness.

The prefix relation grammar and role recognition rule are human-authored classical algorithms. This is NOT own-weight new-operator invention.

## Measured post-FIRST results

[Executed proof run #42320886672](https://github.com/yoonsj0305/NEUMANN/actions/runs/42320886672):

- COPY2: 9/9 original Horn clauses UNSAT.
- COPY3: 11/11 original Horn clauses UNSAT.
- Wrong relation in each case: genuine original-clause SAT witness (index 4).
- Recovered COPY3 bound positions: stage 0 x8, stage 1 x8, stage 2 x7, final stage x5.
- Whole process with source retrieval and proving: **1.22 s**; observed process max RSS **39,936 kB**.
- Positive proof-only wall sums: COPY2 **152.752 ms**, COPY3 **220.097 ms**, not full Q4 costs.
- Model calls/training: **0**. New external original source access: **0**.
- Immutable postfirst report SHA256: 1708ea42cafc72f45841c4bc9ed73711931e65bbb4332bb6e1ce15b4fd787821.
- Full artifact ID 13553495288.

[Separate independent read-only audit #42321116535](https://github.com/yoonsj0305/NEUMANN/actions/runs/42321116535):

- Rechecked exact frozen report SHA and pinned Git blobs for both original source files.
- Re-executed **20/20 unchanged original negated Horn clauses, all UNSAT** using archived proof scripts, without importing/running the new invariant generator.
- Checked **7/7 generated stage predicates are SAT (nonvacuous)**. This excludes a simple contradictory predicate explanation, but is not a complete reachability certificate.
- Independently confirmed both deliberately wrong +1 copy mutants yield SAT.
- Read-only recheck measured **1.90 s**, max RSS **40,352 kB**.
- Historic FIRST 12/20 failure preserved.

## Why the abstract rule works

Suppose the completed stage k has established that original array A0 equals the current copy Ak over indices 0 to n-1. During the next copy, maintain Ak+1[j] = Ak[j] for every j smaller than the cursor i. This holds at i=0, is preserved when the source is unchanged and the correct element is written, and holds over the whole interval at i=n. By equality transitivity A0 equals Ak+1 over all n positions. This is a conditional induction over any number of idealized copy stages, not proof that any arbitrary program matches the grammar. Each real original clause remains independently checked.

## Cost, risk and decisions

The native Eldarica 2.2 baseline previously timed out at 60 seconds each on COPY2/COPY3; this is **censored unresolved** evidence, not a matched-capability speed comparison. Do NOT claim 10x from the 1.22 s process wall: grammar and human invention costs are not metered, and source family was previously inspected. A material-based Idiot Index does not apply directly to software-only proof discovery; a proper full-cost ratio must include grammar authoring, model training, failed attempts, verification and reuse on independently authored tasks.

KEEP the deterministic semantic-role extractor and proof-checked relational compiler for this narrow domain. DELETE learned lexical and absolute-size selectors where exact algebra or program semantics provides better answers. ABSTAIN on unrecognized types, ambiguous guards, unsupported graphs, SAT or UNKNOWN proof results; use a strong classical fallback.

Remaining gates: genuinely new, learned operator not present in human grammar; full independent original proof beyond already-opened development; matched strong-classical capability and amortized total cost; and formalism-independent Q6 transfer with a proven abstraction map. COPY4-COPY6 remain reserved and unopened.

Scientific decision: a concrete **manual stage-specific invariant assignment bottleneck** was removed in already-opened real COPY2/COPY3. Q3 autonomous invention, Q4 total cost advantage and Q6 cross-formalism transfer remain OPEN.
