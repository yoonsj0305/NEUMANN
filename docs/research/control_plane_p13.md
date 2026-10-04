# P1.3 — Contract-First Hierarchical Routing

## Problem and hypothesis

The first P1.2 fresh result remains FAIL / TYPED_ROUTE_COMPATIBILITY_FAILURE:
10/12 compatible, planning 2/4; p12v_09 and p12v_12 select ARITHMETIC stably
although their public representation is a CSP contract. Original ZIP SHA256
362b13d7d7006ea1c55ad33788acd11d1712e94c081d59d52b28581d3abe3444.
Stability gates passed on that registered set. This does not establish global
stability, semantic correctness, capability, economic routing or Q1-Q7.

Hypothesis: if one public representation satisfies exactly one supported
executor interface, derive its route without model work. The invariant is
SelectedRoute in AdmissibleRoutes(original public input). The arithmetic,
Python and CSP tools and the original verifier remain unchanged.

## Admission before selection

Only instruction/public enters admission. No task ID, family, private reference,
expected route, construction source or hidden test enters routing. Unknown
fields are rejected; optional background is text, never selector authority.
Complete groups are validated structurally, not merely by key presence:

| Interface | Required public fields | Bounded admission |
| --- | --- | --- |
| ARITHMETIC | expression, bindings | <=2000 characters, <=256 AST nodes; integer literals/bindings within 10^12; only +,-,*,/, unary +/-; every used name bound |
| CSP | domains, constraints | 1..9 variables, 1..8 distinct integer values each, product <=200000; <=128 supported complete-rule constraints |
| PYTHON | requirement, examples | nonempty <=4096-character requirement; 1..16 exact input/output public examples; bounded JSON |
| Raw text | query | semantic interpretation required; no automatic execution |

Complete public input cap: 32768 UTF-8 bytes. Missing fields, unknown operators,
wrong values, booleans masquerading as integers and oversized contracts reject
the entire input. A valid second group cannot conceal an invalid first group.
Admissibility proves the executor accepts the representation, not that an
arithmetic expression avoids division by zero, a CSP is satisfiable or a
Python implementation exists/is correct.

Exactly one valid specialist and no raw query: select it, do not construct the
scorer, no neural forwards. Multiple valid specialists: abstain if no adapter;
otherwise lazily attach the frozen P1.2 full-S4 backend. A raw query, even beside
a typed group, remains NEEDS_SEMANTIC_INTERPRETATION. No general representation
extractor is claimed here.

## Full-S4 as expensive fallback

FrozenFullS4Fallback attaches an existing frozen Gemma core and does not load
weights itself. Same original model/revision/BF16/artifact/tokenizer/codes,
all24 permutations, three execution modes and numerical/LOO gates. No token,
legend, prompt or original P1.2 source is retuned. Generation tripwire remains.
Rank only admissible routes; inadmissible scores cannot win. Masked adjusted
winner must have >0.50-nat margin and agree across all six LOO20 and three modes;
full24/LOO centered delta <=0.50 nats, batch/order delta <=0.05 nats. Any partial
failure, identity drift, accounting mismatch or ambiguity stops selection.

Cost weighting is optional S(r)-lambda*estimated_ms(r), lambda in nats/ms.
Every estimate is finite, nonnegative and has provenance. Defaults lambda=0,
no measured-cheapest claim. Full token layouts, forwards, padding, scored rows,
VRAM, loading/scoring wall and partial receipts are retained. A failed lazy
factory leaves neural forward cost UNKNOWN, not a fabricated zero. A complete
three-mode fallback costs 36 forwards per input; startup is inside routing wall.
It is not automatically economical; its complete cost must be measured in P2.

## Execution and verification boundary

execute_selected recomputes original public admissibility, checks original-view
identity and the exact projected executor fields before invoking a callback.
Only original verifier boolean establishes acceptance. No family/witness is
passed to the executor. Executors/verifier must enforce their own deadlines;
this injected wiring is not an end-to-end model runner. No retry, source
synthesis or verifier-based evidence expansion is claimed implemented yet.
Wrong candidates, executor errors and unproved projected changes cannot pass.

## New opened CPU contract diagnostic

Register 24 new authored opened interface cases before first routing outcome:
12 positive typed contracts (4 arithmetic, 4 new coding algorithms, 4 new CSP
graphs), 8 invalid contracts, 2 mixed valid contracts, 2 raw queries. Positive
cases are structurally deduplicated against 27 prior opened views (original
12, original Runtime-0 development3, failed fresh12). Alpha-AST, normalized
coding specification, CSP graph isomorphism/domain cardinalities/constant
markers are construction checks, not proof of all semantic novelty.
Original checker accepts12 construction witnesses and rejects12 deliberately
wrong controls. Finite coding vectors are not proof for all inputs. Construction
witnesses are not NEUMANN answers and never enter routing.

Fixed gate: all24 expected public-interface/stopped-state decisions; zero
neural forwards, fallback calls, generation and executor calls; <=500ms per
item, <=30000ms entire routing/input/source/receipt study. No learned scoring
or task-solving. GPU/weights are neither installed nor loaded. Energy, FLOPs,
memory and money remain UNKNOWN. Compared with the retained P1.2 432-forward
study, model routing work is deleted on these typed inputs. Different task sets,
hardware and scope prohibit a measured speedup or iso-capability total-cost
claim; there is no valid raw-material Idiot Index for this software diagnostic.

The first runner requires exact clean Git head and frozen source hashes;
exclusive directory, pre-task started receipts, every decision and complete wall
accounting, terminal file pins and raw-public replay are retained even FAIL or
INCOMPLETE. CI attempt1 only; do not rerun/replace the first result. A new source
version after seeing it requires a new registration and new opened data.
The first CPU diagnostic runs once in dedicated CI after contract tests and
construction checks. Its first ZIP and replay are logged and uploaded, never a
synthetic fixture masquerading as Gemma evidence.

PASS reason is FRESH_TYPED_CONTRACT_DIAGNOSTIC_ONLY. It admits neither P2
registration nor P2 nor Decision3, and closes no global question. It validates
public dispatch and stopped states only. P1.2's old FAIL remains unchanged;
the two prior 12-item sets are now development evidence.

## Next capability interface

Before P2, register genuinely ambiguous/generic problems and an obligation-
preserving representation path. Validate real fallback behavior on new problems;
do not count abstentions as solved capability. DIRECT, full-input TOOL and
NEUMANN must share the same deterministic type-admission layer, tools, frozen
weights and context cap. Only certified evidence elimination, computation
allocation and original verification can differentiate NEUMANN. Coding still
needs real generated source; answering still needs a strong normal DIRECT path.
Complete discovery+execution+verification+retry+routing costs decide Q5.

Each iteration retains one hypothesis, one preregistered gate and one first
result. Current work packages: contract/P0, new CPU interface diagnostic, then
new semantic representation/fallback validation, then matched capability/cost.
No date or GPU-runtime estimate is asserted for the latter two packages.
