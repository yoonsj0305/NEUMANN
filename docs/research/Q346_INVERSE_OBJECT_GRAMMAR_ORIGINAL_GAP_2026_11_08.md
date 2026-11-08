# NEUMANN 1 | Q3 Inverse Object Grammar, Q4 Real Cost, Q6 Transfer Limits
2026-11-08 | PR #732 | original author source-first study | Global Q3/Q4/Q6 OPEN

## Primary failure and architectural fix

The first new object learner attempted to enumerate object selection × rendering × geometry and asked whether each generated program matched original inputs/outputs. On 115 external original source instances the object branch cost **49.42847 seconds** and solved 3 problems missed by the previous composed-grammar solver. The second 107 original source instances yielded **zero new original wins**, while object search consumed 32.07597 seconds. Changing simple enumeration order was not sufficient.

The new engine performs **inverse witness generation**. For each original source example (x,y) and each candidate object partition, compute:

W(x,y) = { (object, render_type, D4, scale) : execute(object, render_type, D4, scale) = y }.

The only possible generalizing render structures are in the INTERSECTION of the projections of each W over (render_type, D4, scale). Infer a consistent source-relative selector for that intersection, then verify the resulting full AST against independent additional SOURCE input/output examples.

No original target outputs are used to create a method. This eliminates combinatorially many syntactically valid but output-impossible proposed programs instead of merely ranking them later. Classical graph traversal handles component extraction; NEUMANN only constructs the source-supported selection and output program. On a known/classically source-verified problem, the live \`ObjectGapRouter\` skips object invention entirely.

## Mathematical properties

**Soundness of inverse pruning relative to the supplied finite DSL**: If a program p from this DSL exactly explains each source pair, p must choose some component o_i and a common render/transform/scale tuple m such that execute(o_i,m)=y_i for every i. Therefore m appears in every inverse witness projection, so pruning programs whose m is absent from any projection cannot delete any source-fitting program. If search is exhaustive (no time, candidate or two-prediction cap), the inverse-space enumerator can enumerate every source-consistent program from the fixed DSL. This theorem does **not** say the true unknown law belongs to the DSL, nor that source-fitting programs predict unobserved tasks correctly.

**Complexity note**: Forward search considers |segmentation|×|selection|×|render|×|symmetry|×|scale| candidate compositions, evaluating many programs. Inverse witness search considers source objects and only dimension/structure-compatible render instances, intersects the source witness projections, then learns a selector. Runtime savings depend on input/output shape selectivity, object count and implementation; no universal 10× cost statement follows from the asymptotic expression alone.

## Pinned external ARC-AGI-2 TRAINING-original outcomes

Original author \`arcprize/ARC-AGI-2\` pinned revision \`f3283f727488ad98fe575ea6a5ac981e4a188e49\`. In all studies, **source task IDs were frozen before original task-test outputs were scored**, test outputs were removed from the proposal process, a prediction SHA-256 was frozen, and a separate scoring process opened outputs after freezing. These are original author **TRAINING tasks**, *not official ARC evaluation*, not frontier independent-author untouched-original proof in the broader historical sense.

| Cohort/version | Selected / scorable | 626 classic | previous composer | object branch alone | integrated two attempts | new vs previous | Previous composer source time | Object source time | Integrated source time |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| FIRST, forward enumeration | 128 / 115 | 0 | 1 | 3 | 4 | +3 | 13.18509 s | 49.42847 s | 62.61355 s |
| SECOND, forward with shape pruning | 128 / 107 | 4 | 4 | 2 | 4 | +0 | 10.3574 s | 32.07597 s | 42.43337 s |
| THIRD, inverse witness grammar | 128 / 105 | 5 | 5 | 4 | 7 | **+2** | **5.70686 s** | **0.59385 s** | **6.30071 s** |

Cohorts are strictly disjoint from each other by code-frozen ID exclusions: FIRST excluded a prior 96 source training task IDs; SECOND excluded the prior 96+128; THIRD excluded all prior 352. The first/second/third algorithms differ and must **not** be aggregated as one immutable policy's generalization statistic. They also occupy different source task distributions, so FIRST 49.4s vs THIRD 0.594s is **not** a controlled 83× speed claim. Only a same-original paired old/new run would provide that measurement.

THIRD SHA-256 frozen proposal: \`5c518035d458d830595fb5ec011be493010f858de11177bf2d7cd54\`.

THIRD object-only residual wins (previous composer wrong): \`b9b7f026\`, \`a87f7484\`. THIRD previously-solved examples were preserved (no integrated loss against the matched two-attempt prior). **New exact tasks relative to prior: 2/105, integrated 7/105 (6.67%) vs 5/105 (4.76%).**

## Q3/Q4/Q6 evidence decision

- **Q3:** New executable, source-discovered object-selection/render ASTs solve two additional *external-author TRAINING-original test* tasks in the third frozen cohort. The semantic feature basis and object segmentation remain programmer-defined, so **arbitrary new primitive or invented grammar OPEN**.
- **Q4:** On THIRD cohort, prior composed-grammar source search 5.70686s; add inverse object search .59385s (+10.4% source search cost) to achieve +2 correctly solved original tasks. Accuracy-increasing, bounded overhead, but **NOT 10× vs strongest classical/total discovery and execution**. Paired SAME original old vs inverse enumeration result belongs in \`research/q3/q3_object_inverse_paired_cost.py\` workflow, not an unverified cross-cohort ratio.
- **Q6:** The same inverse algorithm learned object programs with different colors, object sizes and layouts in synthetic controlled cases, with real ARC originals not seen in earlier 352 tasks. This is transfer to different spatial tasks **within one semantic superfamily**; cross-formalism autonomous generalization remains OPEN. The separate exact polynomial/graph grammar components do not magically prove that this learned object grammar transfers to unrelated mathematics.
- **Fail-closed and Degraded Mode:** Strong previous classic/source-certified program executes first; no need to run invented object method on that task. If learned object AST cannot explain source and independent source verification, no target answer is fabricated.

## Code and reproducibility

- \`neumann1/scene_graph_inventor.py\` (inverse causal-object witness synthesis)
- \`neumann1/object_gap_router.py\` (classical-first economic runtime)
- both \`NeumannEngine\` and \`RegistryEngine\` production methods \`invent_arc_object_only_on_classical_gap\`
- \`tests/test_scene_graph_inventor.py\`, \`tests/test_object_gap_router.py\`
- \`research/q3/q3_arc2_object_blind_first.py\` and three retained exclusion manifests
- \`.github/workflows/q3_object_external_first.yml\`
- \`research/q3/q3_object_inverse_paired_cost.py\`, \`.github/workflows/q4_object_paired_cost.yml\`

Target next original mathematical capability gate must be new primitives for multi-object **relations and correspondence**, not yet another hard-coded color operator or search order.
