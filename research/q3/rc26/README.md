# NEUMANN 1 | Q3 RC26 neural latent → formal executable grammar

2026-10-25. Research-only DRAFT. Do not merge as global Q3 PASS.

Previous RC25 plain tanh RNN achieved 0/4 exact seeds on 3-state
running-sum-mod3. RC26 uses a 12-dimensional GRU, with **only** end-to-end
prefix output labels on binary streams of length 4/8/12/24, NO state-count
labels, NO transition labels, NO completed solution-program menu. Four fresh
trained models each achieved 131,072/131,072 frozen-first bits n1024.

Harder five-state mod5 task: raw GRU n1024 first-bit correct scores
130,909; 125,219; 105,214; 108,265 / 131,072 across four seeds.
A HUMAN-written CLASSICAL counterexample-guided observation-signature
extractor, with no supplied state count or probe depth, reads ONLY the actual
OWN trained GRU behavioral responses. New observation suffixes are proposed
upon signature/transition inconsistency. The generated language syntax
`AUTOMATON NEURAL_EXTRACTED_BINARY / START / ON READ / END` has new
state-name hashes and runnable transitions from OWN weights.

Independent whole-machine product proof against the SPECIFICATION finds:
4/4 exact-minimal 3-state programs and 3/4 exact-minimal 5-state programs;
the incorrect 7-state model for seed504 is fail-closed (counterexample
1111111111). On seven accepted original 128×1024 first-frozen batches,
**917,504/917,504 discrete-program output bits correct**.
The three repaired modulo5 models removed respectively 163, 5,853 and
22,807 original GRU errors, **28,823 total repaired, zero newly introduced**.
The FOUR modulo5 continuous GRUs have errors at length1024, and no neural
all-length soundness is asserted. Only certified *discrete extracted code*
has an all-finite-length proof under these hand-authored tasks.

Strong classical modulo5 reference processes the same batch in a
7-repeat median **0.003696 CPU s**, versus exact extracted symbolic Python
0.041813s (11.3× slower) and inaccurate GRU 0.059359s; training costs
3.5–7 CPU s per seed. NO Q4 efficiency or frontier result.

**Full reproducible original 86-file research archive**
`NEUMANN1_Q3_RC26_NEURAL_SYMBOLIC_ERROR_CORRECTION_20261025.zip`
SHA256 **7a8464a76c98819e1197667c08e68120799ebd96bf4c8cac59c1f78558730fb7**,
provided in this conversation. Eight actual original Torch checkpoints,
each SHA-frozen unseen input/pred output, adaptive extractor and its new
programs, independent grader, failure witnesses, cost audit, fail-closed
interpreter and complete code. Clean extraction of ZIP:
`bash REPRODUCE.sh` EXIT0, sha256 checks and all independent receipts PASS.
An uninterrupted 8-run re-train script hit a wall cap after 7 exact models;
last seed505 was independently re-trained in another clean session and
matched exactly. Both partial 7-run and last-seed logs archived, 8/8 verified
across two executed runs; this is NOT a single uninterrupted full PASS.

GitHub intentionally hosts TWO representative frozen executable programs
and quick regressions, not all torch tensors or original run receipts.

**IMPORTANT BOUNDARIES:** Model learns real latent state representations.
A classical research-authored observation-table abstraction algorithm creates
and names the formal grammar, a human-coded interpreter executes it, and the
human-authored target oracle in the independent proof applies only to the
*compiled finite machine*. There is NO claimed self-invention of the
foundational metalanguage by NEUMANN weights, no independent externally
authored benchmark and no 10× all-in or frontier gap proof.
Global Q3/Q4/Q6/Q7 remain OPEN. North Star unchanged.
