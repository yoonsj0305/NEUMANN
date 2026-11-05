# NEUMANN P1.5 Bitter Lesson: immutable first complete FAIL (2026-11-05)

North Star: **Frontier-level problem solving with minimum necessary computation**. Global Q1–Q7 OPEN.

Source: official public ARC-AGI-1 training at `fchollet/ARC-AGI@399030444e0ab0cc8b4e199870fb20b863846f34`. Selected 32 files by filename hash, excluding exactly 112 prior public ARC study filenames. Registered hypotheses, exact harness, budget, seeds and selected cohort before task-body fetch. First result remains immutable in `docs/experiments/results/q3_bitter_lesson_p15_FIRST_COMPLETE.json`, four eight-task first shards retained.

| Arm | Entire original tasks solved | Attempts | Coarse in-isolate CPU wall region |
|---|---:|---:|---:|
| U: uniform shortest-first program enumeration | 1/32 | 32,768 | 8,897 ms |
| E: train-feedback evolutionary search | 1/32 | 32,768 | 11,718 ms |
| S: frozen broader P1.1 B prior-strong classical | 1/32 | different program set / budget | ancillary, not iso-capability |

- E made **41,613 duplicate generation attempts** and recovered no extra original task.
- U and E both solved `9172f3a0`; S separately solved `a740d043`. This shows search-space differences, not overall ranking of AI intelligence.
- Test-target leakage blocked in code by constructing both proposals from `train` plus `test.input` before fetching original test outputs for final scoring. No test labels, target grids or task IDs enter program generation.
- U/E exact program consensus can ABSTAIN rather than force a guess. No false accepted output observed on 32 problems.
- Source was human-authored P1.1 grid operations, including rotations, scaling, cropping; no newly generated novel opcode. E adapted candidate scores **within tasks**, not persistent learned search policy across tasks. It ran no JEPA, did not train a neural net and did not invoke GPT-6 as a teacher.
- First local claim **FAIL_NO_FEEDBACK_SEARCH_HEADROOM**. This is negative evidence for this finite search method, not a disproof of general search or Sutton's Bitter Lesson.
- Full-system model training/inference, energy, peak memory, monetary cost and GPU resources NOT MEASURED; 8.9/11.7 second summed JS study regions cannot be cast as 10×/iso-capability complete compute.
- Original Q3/Q4/Q5/Q6/Q7 and Q1/Q2 global gates remain OPEN. P1.12, P2 and sealed Decision3 untouched.

## Research pivot: Good Views must be about executable semantics

The arXiv preprint `Proving and Improving the Platonic Representation Hypothesis with JEPAs` (Balestriero & LeCun, arXiv:2610.39302, October 29 2026) proves an alignment result under paired 'good views' of a shared scene, up to a rotation in representation space. The cited 42× metric refers to **samples to matched representation alignment**, not reasoning capability, end-to-end cost, or 42× program-discovery efficiency.

Hypothesis to test **separately**: positive views should be *independent input/output executions of the same semantic operator*, not incidental crops of a single example. A learned encoder must predict unseen executable operator structure and accelerate a real original-task solver over strong exact classical matching, while charging all training, index, search, execution and verification costs. Control bad views, wrong pairs, direct symbolic features, and leave-operator-family-out. If the learned system cannot improve independent original-task correctness or full cost, delete it.

Do not further tune this first scored 32-problem cohort. Future study must preregister a new one.
