# NEUMANN 1 | Ownweight AST sequence generation, exact failure mechanism

**2026-10-26 · existing Discovery Policy causal gate; NO new RC or PR. NO Q1–Q7 promotion.**

## Scientific intervention, actual CPU training
Old NEUMANN proposals merely rank pre-written program kinds. Here we implemented a **real variable-length PyTorch GRU sequence generator** (128-dimensional source IO encoding, 64 hidden, 35,860 parameters, up to 5 sequential executable Atom tokens). It emits complete AST programs rather than selecting a stored *complete program*. **Important**: its executable atom token *vocabulary* still comes ONLY from 12 previously developer-verified original Microsoft PROSE tasks (19 sampled developer cases, 7 rejected). It cannot invent unseen opcode parameters and is NOT an unconstrained semantic-program generator.

Eight external Microsoft PROSE ORIGINAL task IDs were frozen BEFORE reading source under GitHub commit **81d1f768fae67a8487a0a3cf3be4c0e93744934e**: `Log.000021, UserAgent.000004, Name.000011, Email.000007, Address.000006, Phone.000003, City.000007, DateTime.000004`. Source first two original IO, next up to three original heldout outputs. `Name.000011` has only two examples: pre-registered **INELIGIBLE, not replaced**; actual evaluator denominator **7**.

Normal verified-program teacher-sequence A vs equal epochs (140) **task-to-program target permutation** B, matching four random seeds **[3,7,11,17]**, 120 generated full AST programs per task; no exact previously solved program retrieval. Sham is **supervised-target shuffle**, NOT full equivalent reward-shuffled meta-RL. Strong classic C: task-conditioned general substring/regex/split/typed-multi-input AST synthesis, up to 1,800 expansions, max 12 source-fitting programs, source consensus required. No test gold used by proposal.

**First-source prediction SHA256** `661e04887a620a2ce9d2edbb60575f97f95b29cd96411336f4fbd43dd912fc21` and GitHub seal commit **ca2768d7c75b15b29e784e217fa6b333e7868218** BEFORE reading original gold. Original PROSE source file SHA1 authenticated and gold later checked: **A 0/7** all four seeds; **B 1/7,1/7,0/7,1/7**, **C 5/7 correct, 2 HOLD, zero wrong**. Learned A never found a source-fitting program on any eligible original task; B occasionally did on Phone.000003. This is a scientific **NEGATIVE causal result**, not a discovered capability.

CPU measured process-time per original 8 task batch, A median **2,049.934 ms**, B median **2,036.735 ms**, C one batch **26.751 ms** (A/C observed CPU ratio 76.6×). A/B includes 140 epochs of training plus proposals; classical C only source search. These are NOT matched training scope for complete resource Pareto; energy, money, peak RAM and cold start UNKNOWN. Same-original-task utility C beats A regardless. Public task corpus, previously opened category families, one task ineligible; no formal generalization inference.

## The hard cause: semantic OUTPUT SUPPORT (beyond ranking)

The 12 validated old training task programs produced only **19 distinct fully parameterized AST Atom tokens**. The new decoder dynamically generates new SEQUENCES but uses a **closed 19-token action alphabet** + EOS. Training more epochs cannot produce a novel fully parameterized token omitted from that softmax.

We examined the source-consistent **and original heldout-correct** C programs. Count absent atom instances within the source-found classical program:
- Log.000021: **5 unknown atoms**, actual required program has **6 atoms**, exceeds decoder length cap 5.
- Email.000007: 1 unknown atom (unseen new literal suffix).
- Address.000006: 1 unknown atom (unseen regex extraction instance).
- Phone.000003: 0 unknown atoms; reachable inside output language, but observed learned A still 0.
- DateTime.000004: 2 unknown atoms (typed multi-input access).

Thus **4/5 of the exact classical witness programs cannot be emitted by A at all**. This is NOT proof that there are no semantically equivalent solutions expressible by the model; it is a reproducible, narrower output-support diagnosis. It establishes why simply rewarding the limited decoder cannot recover those **witness programs**.

**Minimal representation repair experimentally tested (NO neural merit)**: generate task-conditioned typed atoms using source inputs, and new constant operands by copying common substrings of source outputs. These generalized, source-only operands provide representability for **5/5 of the historical C source-exact witness programs**, without consulting gold. This is a retrospective representability PASS, not a new prospective 5/5 task success. The interpreter is classical and already does the work cheaper. Do not route it through an expensive NN until A demonstrably creates additional capability or reduces full verified cost.

## Reproducible evidence

Complete runnable conversation ZIP:
`NEUMANN1_GENERATIVE_AST_CAUSAL_FAILURE_20261026.zip`, SHA256 **04337316cbd56855638d1bd26819f8e4d43d540e7e68d7b9b80e33f5dd28bd0f**, 20 packaged entries. It includes untouched executable code, old dev observations, source-only new original task instances, pristine frozen first receipt, checkpoint, post-first original external gold/grade, AST support diagnostic, tests, SHA256 manifest, reference classical solver and source features, clean replay script and optional fresh retrain behavioral check. **Fresh extract:** manifest **18/18 PASS**, `pytest` **8/8 PASS**, exact first hash PASS, first-sha/proposal comparison PASS, **8 full fresh model training runs reproduced first source prediction behaviors** (CPU durations not compared).

Original first output, actual code and preserved receipt are the authority. The full implementation and weights remain in conversation archive, NOT falsely described as committed to GitHub.

## Next NON-negotiable admission criterion

Stop training the closed-tokens GRU. Next model MUST propose **new typed AST operator parameters in a domain-general format**, e.g. an actually trained source-conditioned copy/pointer or program text generator, rather than drawing from 19 seen operator instances. Classical solver should still construct candidate operands/verifiers; learner should receive causal revision experience and produce new parameter *and* novel composition on next independent author-domain family. Test A/B/C with original-task independent verification, weight/data split SHA, exact program memory reset, failure/success regression and all-in costs. A is retained only when it beats powerful C on capability or matched full cost. Until then **Q1–Q7 OPEN**.
