# NEUMANN 1 Q3 · RC26 + RC27: own-weight neural → provable symbolic state, causal audit

**2026-10-25 · RESEARCH ONLY · Do not merge as global Q3 PASS.**

## Actual original GRU source + RC26 fixed neural accuracy repair
RC26 is an actual independently retrainable 12-hidden-unit GRU, trained
end-to-end from length4/8/12/24 binary input/output only, without supplied
state-count labels or transition tables. Classical researcher-written suffix
refinement extracts binary Mealy automata from each GRU's behavioral queries;
a human-authored independent product-state verifier decides all-finite-length
correctness; a researcher-authored VM executes the extracted named-state
text. Thus the neural weights supply **useful internal behavioral signal**,
but the MODEL DOES NOT WRITE THE META-LANGUAGE, ISA PARSER OR PROOF.

Of 8 pretrained frozen GRUs, 7 give independently all-length-proved minimal
symbolic programs: 4/4 modulo3 and 3/4 modulo5. Modulo5 seed504 generates a
WRONG 7-state program with explicit independent proof counterexample and is
**BLOCKED**. Original heldout n1024 GRUs have 28,823 erroneous bits across
the three certified modulo5 models, corrected to ZERO by the verified
symbolic replacements. Original full checkpoint/frozen-first prediction ZIP
SHA256 `7a8464a76c98819e1197667c08e68120799ebd96bf4c8cac59c1f78558730fb7`.
The original RC26 all-8-seed retraining was verified in two separate clean
batches, not a single fully-completed run.

## RC27.1 actual causal interventions

- 8 ACTUAL frozen trained GRU weights: 7/8 minimal correctly-certified.
- 8 NEVER trained control GRU weights: 0/8 correctly-certified.
  This supports that neural learning changes useful observable behavior,
  not that the resulting grammar is neural-exclusive or a novel metatheory.
- 4 CLASSICAL gold-behavior oracle variants passed the same extractor (4/4);
  they have privileged task-specification access, so are NOT an equal-rights
  opponent. Their extractor only queried strings up to length10 or12.
- Both gold-behavior oracle variants corrupted EVERY output for histories of
  length >=20, yet still yielded the EXACT same provable automaton. This
  establishes that extracted symbolic all-length proof DOES NOT certify
  the producing observer/GRU beyond the finite queried behavior.
- First evaluation never changes original weights, initial task grammar,
  extraction procedure or the proof oracle. Random controls are deterministic
  and seeded. No task labels were smuggled into the trained GRU inference.

## RC27.2 ACTUAL longer out-of-distribution evaluation

Four original mod3 GRUs and four mod5 GRUs independently re-evaluated on
**32 × 8192 fresh bits per model** with four adversarial patterns plus seeded
random streams. Across 7 formally *CERTIFIED* models:
- **1,835,008 / 1,835,008** extracted symbolic outputs correct,
- **125,253** raw neural wrong bits repaired to ZERO,
- Including 5,067 errors from previously n1024-perfect mod3 GRUs and
  120,186 errors from three modulo5 GRUs.
Rejected mod5 seed504 has 50,729 raw GRU errors and 50,729 extracted symbolic
errors on the same 262,144-bit fresh batch: not authorized.
Across all 8 raw GRUs: 175,982 total erroneous bits.

These are finite independent holdouts. The separate full-length guarantee
is ONLY for the admitted symbolic finite-state programs as independently
proved by a product-machine argument, NOT original real-valued GRUs.

## RC27.3 strong iso-input execution baseline

Interleaved median-of-seven Python process CPU comparisons on the SAME
32×8192 input bits. The certified symbolic VM was median **3.16× SLOWER**
than a direct exact conventional modulo counter. Training/extraction/proof,
memory and energy are EXTRA (and have not been counted here), thus no global
Q4 all-in neural advantage. Full Q3/Q6/Q7 completely OPEN.

## Original weights, real receipts, actual reproducibility

The self-contained 415K ZIP
`NEUMANN1_Q3_RC27_CAUSAL_AND_LONG_HORIZON_AUDIT_20261025.zip`
SHA-256 `68151a320fdf46ad6a850cb8208a26e4b33bb78956b9da724818ba69fb504f18`
includes the unchanged ORIGINAL RC26 ZIP, full original model weights,
first-prediction blobs, all RC27 source and independently fixed sha receipts.
Its own quick `bash REPRODUCE.sh` executed PASS *twice* and again after
clean ZIP extraction. Original RC26 independent replay and each of the three
RC27 causal, long and cost runs completed independently. The combined
two-cycle `--full` runner TIMED OUT after its stages output: **DO NOT**
claim the entire full orchestrator finished. It remains an optional slow mode.

## Mandatory scientific gate

**SCOPED PASS:** trained GRU behaves as useful stateful source; classical
abstraction + independent proof recovers correct and minimal machine in 7/8
cases; new 125,253 long-horizon GRU errors corrected with zero symbolic errors.

**GLOBAL OPEN:** neural-exclusive discovery of a non-prelisted fundamental
grammar, complete autonomous meta-ISA syntax/semantics/parser invention,
all-in compute superiority, external task author OOD transfer, real frontier
problem-solving. Classical extractor with gold access 4/4 underscores that
calling this a "self-invented foundational language" would be misleading.

Action: in production choose simple exact classical algorithm whenever
available; use neural proposal→external proof only for classes where
classical matching-resource baselines do not already dominate.
