# NEUMANN P1.7 | Same-operation multiple good views, contrastive learning study (PREREG)
Date 2026-11-05 KST. Frozen before implementation/training/first scoring.

### Governing goal
**Frontier-level problem solving with minimum necessary computation.** All global Q1–Q7 OPEN. P1.5's 32-task evolutionary search FAIL and P1.6's exact semantic quotient results stay unchanged. The paper by Balestriero and LeCun, arXiv:2610.39302, proves a **conditional same-scene good-view** JEPA representation result and reports 42× sample efficiency in an alignment metric. Independent executions of the **same operator** are *not* views of the same scene in the paper's mathematical meaning; this is an explicit **new hypothesis**, not an application of their theorem or a reproduction of JEPA.

### Hypothesis
A small encoder trained to match independent examples of the **same transformation** across differing scenes (“operator-good views”) will represent operator identity more robustly than an identical encoder trained to match two minor perturbations of the **same input/output example** (“bad views”), with the same training steps, model, data distribution and optimizer.

### Frozen generative world and split
- Eight predefined deterministic binary-grid operators acting on a 12×12 array: zero-padded one-pixel shifts up/down/left/right, horizontal and vertical reflection, clockwise and counterclockwise 90-degree rotation. All semantics are human-coded.
- Input cells independent Bernoulli(p=0.18); no nonzero collision rescue or class-specific image generator.
- Source RNG seeds: 20261117 for training, 20261118 for support, 20261119 for never-seen query. Torch model initialization and minibatch RNG fixed at 20261120 and 20261121.
- **Seen training operators: six** (four shifts, two reflections); **unseen semantics: rotations** (two). A “novel operator” query is **new to encoder training**, but its executable source is made available when constructing support prototypes, so this is *NOT* autonomous operator invention and is weaker than Q3.
- Support reference: 24 independent observations per operator; final query: 48 independent inputs per operator; no query output used to train encoders or choose seeds.
- For the good arm, one positive pair is two **independent** scene executions of the same operation.
- For the bad arm, a positive pair is two independent Bernoulli(0.025) corruptions of **one and the same** input/output observation; no within-positive cross-scene invariance.
- Contrastive objective: symmetric in-batch InfoNCE across six distinct operator types; other labels are in-batch negatives. Same 2-channel 12×12 convolutional embedding encoder, 48-dimensional unit-normalized output, AdamW learning rate 0.002, temperature 0.12, 400 fixed minibatches. One batch contains six classes, each contributing two views. No pretrained encoder weights.
- A fixed-random initialization encoder and **exact deterministic candidate matching** on input/output original data provide controls. The exact symbolic comparator is expected to achieve 100% of cases distinguishable by observed examples and may outperform every neural arm.

### Frozen metrics and decision
- Primary metric: prototype retrieval top-1 accuracy over all **384** query pairs (8 operators×48 queries), with 24 independent support examples/class, cosine prototype comparison.
- Secondary: seen 288 queries; unseen rotation 96; mean positive cosine similarity and cross-operator similarities. Report training wall time, model parameter count, inference microseconds/sample, Python process peak RSS where measurable, any other resources as UNKNOWN.
- Local P1.7 view-pair hypothesis PASS only if good-view top-1 >=0.80 AND exceeds bad-view top-1 by >=0.15 absolute, with unseen rotations >=0.50 top-1. No threshold changes after results.
- Even if local PASS, **do not adopt neural encoder** until it beats a strong optimized symbolic/exact quotient search on original fresh tasks at equal original-task accuracy including amortized training, NN scoring, execution, verifier and fallback. Classification of human-coded eight operators is not open-world Q3, Q6 or Q7.
- Degraded mode: if classifier confidence fails separately frozen acceptance threshold (not tested here), ABSTAIN and defer to original-task strong Direct; no silent wrong programs.

### Required scientific cautions
The “good” versus “bad” experiment compares *different positive pairing objectives*; Bernoulli augmentation creates corrupted observations that may not correspond to a valid execution, a deliberately weak view control. Do not extrapolate to 42× fewer samples or 10× complete inference. Reporting multiple seeds would require a new pre-registered study; this first exploratory seed is retained PASS/FAIL exactly once. Any increase in alignment without original executable capability is representation-only and does not move global Q3/Q4.
