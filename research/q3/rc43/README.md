# NEUMANN 1 RC43 | external-author generalization gap without wasted neural calls
2026-10-26. RESEARCH-ONLY DRAFT. Do not merge as Q3/4/6/7 PASS.

This evaluates 24 actual **ARC-AGI-2 external-author PUBLIC TRAINING** tasks:
the lexicographically first 24 `data/training/*.json` entries of upstream
Git commit `f3283f727488ad98fe575ea6a5ac981e4a188e49` whose original
file size is <=2500 bytes. The **first12** were opened to develop/extend
a generic *classical* grid transformation program compiler. The **next12**
were selected before their contents were inspected and evaluated without
altering the frozen Python code.

Results observed from an independent same-rule **JavaScript execution** over
24 exact raw GitHub JSON files, with ground-truth test outputs only read AFTER
source-only program selection:
- simple classical program grammar on opened group: **1/12**,
- expanded classical algebra (rotation, crop, scale, tile, Kronecker,
  periodicity, mask composition, checkerboard tile, double mirrors,
  vertical bar ranking, global source-fitted recolor): **8/12** opened,
- **2/12** on next previously uninspected ARC training tasks, identical
  expanded algorithm without refit/edits,
- neural trainings/forwards **0/0**,
- no official ARC-AGI-2 public evaluation files opened by this project.

CRITICAL provenance: The expanded classical operators were added AFTER
opening the first12. This is a *development example*, not blind 8/12.
The 2/12 group is independently opened from ARC public training, NOT
the official ARC-AGI-2 public evaluation, and the subset is **size-biased**.
No claim of test generalization to all ARC, frontier parity, or classical
impossibility. The sampled classic portfolio is deliberately incomplete,
so the remaining ten tasks are NOT admitted to neural training merely
because this one portfolio failed.

The AUTHORITATIVE original Python solver was SHA-256 frozen BEFORE opening
the second12:
`872bc99c57f61729801f6a2207033a751dd6e6376d889c7d14872a391c8c23cc`.
Its complete executable source, pinned official Git object SHA1 manifest
for every task, exact dual-stage per-ID receipts, SHA verification, and
`REPRODUCE.sh` are archived in conversation:
`NEUMANN1_RC43_ARC2_REAL_EXTERNAL_CLASSICAL_GAP_20261026.zip`.
ZIP SHA256 `27e08026b442a43278d92e30f641735c5b591b53bb3ded8b4afcda44940a0432`.
Seven archived files; clean extract SHA manifest pass and pytest **5/5**.
FULL 24-task original-Python replay is **PENDING** because this container's
outbound network is disabled; do NOT call the JS run a Python replay PASS.
The ZIP offers commit-and-Git-blob-pinned ARC public train download for
internet-enabled reproduction and fails on scoring disagreement.

Source: https://github.com/arcprize/ARC-AGI-2
Original task data copyright ARC Prize and Apache-2.0; dataset raw
bytes are NOT redistributed on this branch or in the ZIP.
Source official benchmark README recommends preserving public evaluation
sets from repeated development/peeking; no evaluation tasks were accessed.

RC40/41/42 hard rule: trivial official AM1 opened tasks were classically
solved12/12, and past actual frozen core produced no executable final action
(72/72 thought-only token-capped). Use a truly strong classical portfolio,
prospective independent tasks, and a low-entropy model control interface
before spending new neural inference.

Global Q3/Q4/Q6/Q7 = **OPEN**.
