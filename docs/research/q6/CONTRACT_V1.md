# Q3 ↔ Q6 proposed contract v1

2026-11-12. Baseline `0d1baec723f249a62a901d100af6e941234a43ac`.
Status: proposed integration contract; no claim that Claude has acknowledged it.
The historical-source adapter lets Q6 develop independently while that review is
pending. Q3 files, learning policy, schemas internal to Q3 and sealed evidence
are unchanged. Q6 adds no second learned intelligence core.

## Q3 → Q6: Structural Discovery Artifact

Required JSON fields: `artifact_id`, `producer_commit`, `source_task_digest`,
`observation_schema`, `discovered_representation`, `executable_method`,
`source_verification`, `provenance`, `resource_cost`.

`artifact_id` hashes the entire payload excluding itself. `source_verification`
binds the executable digest, observed-source digest, actual checker and finite
scope. A nonempty string or asserted PASS is not sufficient admission. The
caller supplies independently verified source data/evidence; Q6 checks binding,
type correctness and source execution before caching admission. Unsupported
representation versions fail UNKNOWN. Missing evidence is not invented.

Optional: `invariants`, `preconditions`, `counterexamples`,
`causal_dependencies`, `equivalent_representations`. Unknown fields are absent,
not guessed. Runtime-definedness is a precondition, not a theorem of correctness.

Initial adapter accepts the current I/B/L typed AST and method kinds ast, zmap,
zfilter. An original task's input types and a step body's state types are stored
separately. No forced common graph language. A SOURCE-verified typed subtree
is a dependency-preserving fragment of a certified procedure, not a separately
proved universal algorithm. Final original-task verification remains mandatory.

## Q6 → Q3/executor: Transport Result

Required JSON fields: `source_artifact_id`, `target_observation_digest`,
`candidate_correspondence`, `transported_representation`,
`transformed_executable_method`, `verification_obligations`,
`verification_status`, `counterexamples`, `measured_cost`, `failure_reason`.

`verification_status` before external grading is UNKNOWN or TRAIN_CONSISTENT.
Never upgrade it to independent exactness based on TRAIN. Every correspondence
records which source state roles become which target expressions. Mere variable
renaming, identical-program replay and type-only applications are distinguished
from a compound correspondence. Binder substitution is capture-avoiding.

Target observations contain only authorized TRAIN; hidden TEST is not accepted
by the inference API. A verified failure can request further Q3 discovery via
UNKNOWN and `failure_reason`; Q6 must not invent an unrelated target solver.

## Costs and integration

Extraction and source certification are charged once per immutable artifact;
source discovery investment is retained once per donor task. Matching,
reconstruction, TRAIN verification, failed candidates and memory are timed.
Final execution/checking costs are recorded separately by the grader. Cold N=1
and declared reuse horizons use the same complete accounting scope. Unmeasured
energy/monetary cost is UNKNOWN. CPU, RSS and serialized bytes are separate units.

Minimal integration: Q3 emits the JSON artifact and an independent source
verification receipt; caller invokes `q6.transport(...)`; caller independently
checks original task results or returns UNKNOWN to the SAME discovery core.
No change to Q3's invention implementation is required for this prototype.
