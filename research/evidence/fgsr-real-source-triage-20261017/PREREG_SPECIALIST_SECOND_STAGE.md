# FGSR exact-source specialist second-stage classical screen

2026-10-17. Registered **after first Z3 screen** and **before any Eldarica attempt** on this source pair. The two targets are now opened development cases, not frozen blind future neural holdout. The first raw Z3 outcomes must remain preserved: each `TIMEOUT_OR_ERROR` under 10 seconds.

- Sources and revision: same two Git SHA1/SHA256 identities first recorded at GitHub Actions 39033821826. Never change bytes or swap originals.
- Specialist: **Eldarica v2.3**, official `uuverifiers/eldarica` release; reuse existing `research/evidence/fgsr-q3-single-independent-family/eldarica_once.py` release asset selection and safe unpacker, not a new algorithm.
- Exact solver invocation: release command + unmodified original SMT2 file. No manual lemma, no source rewriting, no trained model.
- Budget: one actual attempt per case, 30 seconds hard subprocess cap each; pinned order lists then prusti. Source download/install time recorded separately. One shared pinned solver asset, SHA256 recorded.
- Parse only exact `sat`, `unsat` or `unknown` whole-line response with process return code 0. Errors, downloads, UNKNOWN and timeout must remain separate statuses.
- If specialist decides, classify as solver-reported `CLASSICAL_SOLVES_WITHIN_BUDGET`; this is not an independent generated certificate but blocks cheap neural claims. If both time out, classify as `HEADROOM_CANDIDATE_ONLY` still NOT a demonstrated classical-to-learned gap: other stronger solvers and a frozen learned model remain absent.
- Preserve negative historical outcomes, no recomputation of the Z3 first result.
- Global Q1-Q7 stay OPEN. This is an evidence-triage prerequisite, not FGSR final test.

No paid budget. CPU-only GitHub Actions.
