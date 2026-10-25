# Q3 · Fixed-state online multiplication is impossible for arbitrary bit width

**2026-10-25 · bounded research result; NOT a new NEUMANN neural discovery.**

For a deterministic Mealy transducer reading `(a_i,b_i)` LSB first and emitting product bit i immediately, take any k-bit low prefix u of a while all first k b bits are zero. All 2^k histories output only zeros so far. Append the SAME future input to each: all remaining a bits zero, `b_k=1`, all remaining b bits zero. Each future output suffix k..2k-1 then reveals u exactly. The 2^k prefix histories are pairwise distinguishable. Therefore any exact bit-serial multiplier for n >= 2k+1 must have at least 2^k internal states. Since k arbitrary, no fixed finite state count can do general multiplication for all n. This assumes ONLINE simultaneous per-bit output, and does NOT apply to arbitrary-access RAM, unbounded tapes or arbitrary-precision memory.

Human-authored `GrowingMemoryMultiply` expands its operand history and computes the diagonal convolution coefficient and carry for each new bit. Local independent full n1..8 grading **87,380 input pairs** exact, plus 18 n16..512. Math invariant: `sum_{i<=m} output_i 2^i + carry_{m+1}2^{m+1}=sum_{i<=m} (sum_{j<=i} a_j b_{i-j})2^i`. This implies all finite-width correctness.

The user conversation's full **17-file** SHA-audited artifact: `NEUMANN1_Q3_EXPONENTIAL_STATE_LOWER_BOUND_AND_DYNAMIC_MEMORY_20261025.zip`; archive SHA256 **ddad1176cc564f14d03c138cc3e8dba89aeb10d79c301856750bc88009856b36**; manifest SHA256 **369167dd452f4d26e7b8c7e0944472b7b41b9e0dccb08384088b5f60a0327a37**. Clean extraction `bash REPRODUCE.sh` EXIT0, all code SHA and actual prior own PyTorch checkpoint SHA verified. Full archive includes own-weight learned adder binary table `.pt` checkpoint sha `4cc8498de9ebecc2f5e629027686524e143ee31149496978a643fb1ea02bd935` and a HUMAN-authored shift-and-add multiplier composed from that prior own-weight adder. It passes 21,844 exhaustive n1..7 input pairs, but **the multiplication orchestration was NOT proposed by model weights**.

Measured same set of 100 n64..512 random products: built-in Python `a*b` process CPU0.000024 seconds, online convolution ~0.895 seconds, human shift-add using own-weight learned adder ~1.586 seconds. Native Python optimized implementation and process timing on specific CPU are not an algorithmic benchmark across identical hardware languages, but no claim of Q4 all-in savings is remotely supported. Past six neural training attempts total CPU15.53 seconds, none trained in this study.

**PASS**: fixed-state universal streaming multiplier **mathematically refuted**; memory-growing human authored operator **independently complete-tested and inductively verified**; original learned adder reused by a HUMAN classical planner, scoped pass. **OPEN**: own-weight model autonomously invents memory/interface/synthesis logic, outperforms strongest same-rights classical on independent multi-author tasks, Q3/Q4/Q6/Q7 global. Avoid inflating Q3 from impossibility theorem or code authored by the assistant. Draft PR not merged.

## RC6.1 independent extension · same date · stronger theorem

For a width-n ONLINE LSB multiplier producing only its low n product bits, choose
k=floor(n/2). The same 2^k indistinguishable prefixes and one common continuation
work whenever **n>=2k**, not merely the earlier sufficient condition n>=2k+1.
The suffix reveals all k bits of u by output positions k..2k-1, which fit
within the first n outputs. Any exact deterministic transducer thus needs at
least **2^floor(n/2) states**, or **floor(n/2) state bits** at that point.

The human-coded streaming binary-convolution upper-bound witness uses 2n
historical input bits and O(log n) bits for carry/index, with O(n^2) elementary
bit work. Its arithmetic recurrence is
d_i=sum_(j=0..i) a_j b_(i-j),
y_i=(d_i+c_i) mod 2, c_(i+1)=floor((d_i+c_i)/2).
The invariant for output prefix length t,
sum_(i<t) y_i 2^i + c_t 2^t = sum_(i<t) d_i 2^i,
implies exact low product modulo 2^n for all n. This establishes the
**tight asymptotic space complexity Theta(n) bits** in this streaming model;
it does NOT establish time optimality or neural self-invention.

The new `streaming_space_contract.py` includes an intentionally conservative
memory gate: capacity below floor(n/2) => IMPOSSIBLE_UNDER_CONTRACT;
otherwise => UNKNOWN_NOT_CERTIFIED, never unsupported PASS.
The independent new pytest contract enumerates witnesses n=2..20,
all **87,380** input pairs for n=1..8 low products, 300 width16..512
random cases, and capacity boundary checks n=2..100.

Full same-day local 5/5 PASS reproducible evidence:
`NEUMANN1_Q3_STREAMING_SPACE_TIGHT_BOUND_20261025.zip`
SHA256 `c300ea41344ea1d2654917115cadd46b195b848724a3b8039a7bed6b355dc901`.
Previous own-weight learned adder (PR #573) is 2-state with exact 8-rule
induction, whereas exact streamed multiplication requires linearly growing
state bits. This is a **human-proven representation-class separation**,
not a model-weight-generated architecture choice.

New scoped gate PASS: exact-n online memory lower bound and matching
asymptotic upper bound. Global G1/Q3 own-weight new primitive OPEN;
Q4 all-in 10x OPEN; Q6/Q7 OPEN. Research-only draft; do not merge on this result.
