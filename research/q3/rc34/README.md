# NEUMANN 1 Q3 RC33–RC34 | The decisive META-GRAMMAR gap

2026-10-25 · Research only, DRAFT, NOT global Q3 PASS.

**Original OWN PyTorch meta-policy:** RC33 one model fitted to 1800 source grammars
under HUMAN-provided ABC alphabet, nonerasing RHS length1..3, fixed parallel
rewrite interpreter, and a 27-way latent length segmentation. Original OWN
checkpoint exactly reproduced from source-only data. With 250 new tasks of
SAME class and NO further training, 240/250 emitted entire correct hidden
grammars (241/250 fit observed IO; one happens to be ambiguous).

**The real generalization test:** RC34 ran the ORIGINAL checkpoint, unchanged,
on 3 truly NEW representational classes, 96 cases each: nonzero number of
epsilon/erasing RHSs, at least one RHS of length4, and fourth alphabet symbol
D. Two-source-shift heldouts each contain explicitly impossible clauses
under original metalanguage. In 288 frozen first actor predictions, ONLY 7
accidental correct RHS tuples arose from a permissive Python slice that
silently emitted empty suffixes, a previously UNSUPPORTED/UNVERIFIED rule.
These 7 are **not** valid authored new grammar inventions, nor admitted.
Model accepted new foundational grammar definitions: **0/288**.
Two source-consistent candidates still lack universal proof, also UNKNOWN.
This is an ACTUAL self-invention test **FAIL**, not rewritten as PASS.

**GENERAL CLASSICAL compiler as rescue** uses same original observed IO,
no fixed alphabet size and no prelisted RHS maximum, expands alphabet,
length and adds EPS syntax. Within the *HUMAN-SUPPLIED* assumption of
deterministic per-symbol parallel rewriting, from observed IO alone it
uniquely finds 262/288 grammars; 26 residual ambiguous cases require **46
separately counted membership queries** to recover all288. After model and
compiler codes were frozen, a FIFTH-letter ABCDE + EPS + RHS width5 family
of12 tasks also fully passed with no code change, 12/12 unique, zero extra
queries. 300/300 proof-gated program text grammars parse/execute. This is
CLASSICAL system-level grammar extension, NOT NEURAL own-weight base grammar
invention. The small classical cost dwarfs model training. An adversarial
non-morphism matches all given source examples and deviates on new AA, showing
all-length proof is CONDITIONAL on the target rewrite-class contract.

**A high-value stop decision:** stop iterative toy grammar width extensions,
reject any fabricated Q3 PASS, route restricted source-identifiable work
to classical code, reserve learned-model experiments for genuinely new
meta-interpreters/control-flow/memory and external-author evaluation.

Full original **actual Torch checkpoint**, full source, first SHA-frozen
RC34 OOD outputs, independent hidden grader, class shift input samples,
300 executed new grammars, alternative classical control, 7 regression
tests and physically isolated OWN-weight retrain are in current conversation
ZIP:
`NEUMANN1_Q3_RC33_RC34_META_LANGUAGE_BOUNDARY_20261025.zip`,
SHA256 `0caf71011567c3fbcd2c26cbb05be5ddd1a3c5ac82a6ff6fca3895d9ac93218f`.
CLEAN zip extract `bash REPRODUCE.sh`: 7/7 tests, source-only freeze byte
identical, 288+12 classical program receipts exactly graded, PASS.
`bash RETRAIN.sh`: PyTorch entire checkpoint tensor-by-tensor reproduced
from RC33 1800 task source IO with NO gold files in learner sandbox, PASS.
THIS repo branch stores only executable generic compiler, hostile-case tests
and factual evidence pointers, NOT the raw checkpoint.

**Q3/Q4/Q6/Q7 GLOBAL OPEN.** No claim of model-invented meta-language.
