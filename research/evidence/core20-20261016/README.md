# CORE-20 | Evidence that prior learned inputs discard necessary semantics

Date: 2026-10-16. **Status: FEATURE-COLLISION PROOF; LEARNED AUTONOMOUS ABSTRACTION NOT PROVEN.**

## Actual falsification
- Source: CHC-COMP 2026 `ADTRem/isaplanner/goal41_000.smt2`, pinned SHA-256 `bcf9451674dba121a13ad2ca7f09e4c3d031bfa4f2a21c6ed3e989661dab6f34`.
- Authentic program has take(0,L)=[]; counterfactual has take(0,L)=[42]. Map is f(x)=x+1.
- CORE-18/19 frozen 11D feature extractor gives `[1,1,0,0,0,0,0,0,0,0,0]` in both sources.
- The learned checkpoint consequently gives identical score (1.0 with the reported floating precision) despite distinct validity of the take/map law.
- Concrete semantic counterexample to the poisoned law: n=0, L=[1,3], left=[42], right=[43].
- For a balanced pair of valid and invalid sources with identical input features, **any deterministic model using ONLY these 11 input components has error >= 1/2**. This does not generalize to richer-input systems.

## Deterministic source representation repair
- A typed, binder-normalized AST of relevant source clauses preserves both bases and recursive steps.
- 10 cases evaluated, 9 are exact frozen-input collisions; one unsupported head mutation was rejected earlier.
- AST signatures are invariant to harmless relation renaming and separate the 7 edited base/definition forms from the valid source.
- Tests: 5/5 pass. Unchanged frozen checkpoint SHA256 `ba33350f6aea4223533bf96da8d842e227ef14f9ad5232c6a7815e7f4e7cb5f9`.
- This frontend is classical. No new learned structural invention or matched efficiency advantage.

## Evidence availability
- Raw CORE-20 ZIP `NEUMANN_CORE20_INFORMATION_OBSTRUCTION_20261016.zip` SHA-256 `7ce7d46a46ffa9d45e92e82c9b2d4a8716dfdba6dc8b31fed27e14a793a7fdcf`, CRC PASS in working container.
- As of this GitHub commit, binary ZIP and trained checkpoint are NOT uploaded to GitHub. Full binary mirror remains pending.

## Decision
Do NOT train the old classifier further. A learned generator must be conditioned on the typed base/step AST and produce a full new typed helper definition. Preregister fresh unseen external family; matched classical synthesis and original-goal verification are mandatory. Q1-Q7 stay OPEN.