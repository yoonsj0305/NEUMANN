# Minimal Q3 integration proposal

Status: proposed, pending Claude/Q3 owner acknowledgement. No Q3 source file is
changed. The historical adapter and SOURCE study are separate from this facade.

```python
from neumann1.q6.api import structural_transport

transported = structural_transport(
    source_artifacts,                 # JSON contract; no target answers
    authorized_target_observations,   # in_types, out_type, TRAIN only
    source_authority=independent_source_evidence_verifier,
    cap_s=available_cpu_seconds,
    q3_fallback=existing_q3_executor,  # optional existing core, not a Q6 model
)
```

The source authority must validate real source provenance, method digest and
original semantic evidence. A self-asserted certificate string or `lambda:True`
is not a production verifier. The experiment adapter established its authority
by executing each actual donor program on its pinned original observations.

`UNKNOWN` returns control to the SAME discovery policy. Unsupported types or
representation versions also return UNKNOWN. `TRAIN_CONSISTENT` is a candidate
method with outstanding independent original-task verification, not an accepted
answer. Do not send original hidden TEST outcomes to transport or update a frozen
study policy from them. Source-authorized counterexamples may inform a future
explicitly separated learning episode after provenance/contamination checks.

Facade coverage is currently typed-ast.v1 and ast/zmap/zfilter over I/B/L.
Other Q3 representations are not silently coerced. Add an agreed execution
adapter only when it preserves original semantics and contains no task-specific
answer procedure. No new universal IR or second language model is proposed.

The optional fallback callback takes a remaining CPU allowance and returns the
existing core's `sol=(kind,ast)` and diagnostic candidate count. If Q3's future
public API differs, change only the caller's adapter, not its learning mechanism.

Before independent-domain work: agree the artifact contract, expose the actual
Q3 learned policy's verified artifacts and preconditions, compare against a
stronger equal-rights typed composition baseline, and freeze both knowledge and
evaluation rights. New independent data opening requires the user's separate
approval. This PR does not request or assume that approval.
