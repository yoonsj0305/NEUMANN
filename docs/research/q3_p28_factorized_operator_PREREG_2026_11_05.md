# NEUMANN 1 / P2.8: factorized executable semantics feasibility contract

Date: 2026-11-05. Parent: research/q3-p27-compositional-schema-learning-20261105 (P2.7 is FAIL, 0/32 additional public evaluation correct). North Star: frontier-level problem solving with minimum necessary computation.

## Scientific target and hard limits
- **Only** Q3 new executable meaning, Q4 transfer, Q2 independent replay, and all-in cost.
- NOT an autonomous invention of an arbitrary opcode. The *human specifies the generic factorization representation*, and the engine learns an instance-specific executable selector from examples. A discovered selector is a typed program, not a new universal primitive.
- The original ARC-AGI training task `007bbfb7.json` was intentionally picked **after seeing its TRAIN examples and TEST input dimensions** as a mechanism feasibility diagnostic, not a statistically representative or fresh problem. Its TEST target output has not been inspected when this contract/source was committed. No private ARC-AGI data or model teacher calls.
- Upstream immutable public source `fchollet/ARC-AGI@399030444e0ab0cc8b4e199870fb20b863846f34`; path `data/training/007bbfb7.json`.
- Source frozen by GitHub blobs `experiments/q3_p28_factorized_operator.mjs` and `tests/test_q3_p28_factorized_operator.mjs` before reading original TEST gold; evaluated score can be appended later. Do not change these files to repair first-score failures.

## Falsifiable claims
1. Source shape 3x3 -> target 9x9 is not reachable by the 12 frozen P2.7 atom set at composition depth <=2. Proof uses shape transitions of rotations/flips, crop, scale2, tileH2, tileV2. Area-only check is INSUFFICIENT, because two scale2 steps do yield area >= 81 but shape 12x12, not 9x9.
2. New program family generates `y[i*h+r][j*w+c]=select(x[i][j],x[r][c])` with a learned 4-entry truth table indexed by zero/nonzero of its two inputs. Only `0`, `outer`, `inner` source values can be emitted. Deterministic exhaustive 3^4=81 candidates. The task name is not an input.
3. Exact TRAIN replay of all pairs is mandatory. On multiple training-consistent programs that disagree on TEST inputs, abstain. TEST labels are forbidden to proposals.
4. Independent source interpreter must exactly reproduce selected program and original TEST output if submitted. Misleading fixed grammar/learning claims fail validation.
5. For original diagnostic, **expected criterion**: exact 1/1 public TRAINING test with 0 false accepts, or explicit first FAIL/ABSTAIN without changes. This is not an untouched or cross-domain benchmark.
6. Novelty limited to a new executable representation **relative to P2.7 grammar**. The matched classical enumerator has the same 81 candidates; any learned-vs-classical superiority claim is **unsupported**. All Q1–Q7 remain OPEN.

## Cost and exclusion
- Local Node.js tests via `node --test tests/test_q3_p28_factorized_operator.mjs`.
- Report enumerated candidates, exact TRAIN programs, TEST prediction uniqueness, elapsed ms and code/labels hash. No GPU, JEPA, opaque model weights, or GitHub Actions dispatch necessary.
- Do not claim frontier, autonomous opcode discovery, ARC-AGI-2 transfer, 10x all-in compute, or statistically meaningful accuracy from this selected case.
- A real Q3/Q4 PASS requires a source-frozen newly selected, unseen original cohort and independent different semantic-family tasks with matched classical control.
