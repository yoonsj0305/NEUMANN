# NEUMANN 1 | Q3 Frontier Capability and Discovery Economics
2026-11-08 | Immutable original FIRST | Global Q3/Q4/Q6/Q7 OPEN

## What was actually run

Original external dataset: official ARC-AGI-2 at upstream Git SHA f3283f727488ad98fe575ea6a5ac981e4a188e49. A source-only program policy was discovered using 256 official training tasks and a separate 128 training tasks for source validation. Source SHA-256 3120ae1192ebf896cb64646981b5c3348316597b1576e36e94cf6e76271328eb was archived BEFORE any of the 120 public evaluation originals was accessed.

**Run: https://github.com/yoonsj0305/NEUMANN/actions/runs/42440957648**

All 626 executable grid-program candidates were available to both NEUMANN and the strong same-language cold comparator. 9/256 discovery training problems had any matching program; 247/256 had none. Source validation: 79,169 checks cold versus 79,099 learned, 70 checks saved across 128 tasks, source discovery wall time 61.50174 seconds.

OFFICIAL ARC-AGI-2 PUBLIC EVAL 120, unmodified FIRST:
- NEUMANN learned order: 0/120 correct original tasks, 75,120 candidate checks, 26.34604 s target search time.
- Same-language classical: 0/120, 75,120 checks, 26.28608 s target search time.
- Zero evaluation parse or execution errors; all evaluation task gold answers used only after predictions were fixed.

Published frontier: the ARC Prize creator-administered semi-private ARC-AGI-2 board lists GPT-6 Astra Max 95.0%, GPT-6.1 Sol Max 94.2% as of November 2026. Sources:
https://arcprize.org/arc-agi/2
https://arcprize.org/results/openai-gpt-6-astra
https://arcprize.org/results/openai-gpt-6-1-sol

NEUMANN evaluated PUBLIC originals and frontier scores are from DIFFERENT SEMI-PRIVATE originals. This is a capability gap comparison, NOT a paired model or same-hardware efficiency comparison. No frontier provider full FLOPs, energy or equivalent telemetry was available.

## First-principles cost

Source-only original candidate checks: 158,635. Discovery wall time: 61.50174 s.

Estimate: source empirical mean discovery wall time per candidate (includes overhead) = 61.50174 / 158635 = 0.000387693 seconds. Source-validation savings = (79169 - 79099)/128 = 0.546875 candidates per task. Under a constant-savings assumption this represents an Estimated 0.000212020 s saved per future task, implying 290,075 future tasks before source discovery pays back. The frozen target experience saved exactly ZERO candidate checks, so observed break-even is not established.

Source discovery plus learned target candidate search time = 61.50174 + 26.34604 = 87.84778 s, compared with 26.28608 s cold target candidate search alone, about 3.34x higher on these partially accounted stages. Does not include CI setup, network, full processing overhead or complete model costs. Both score 0/120 so cost-per-solved-task is undefined, not an improvement.

## Changed NEUMANN core

The actual NEUMANN engines now support SOURCE-ONLY discovery-investment admission. In neumann1/meta_utility_policy.py, source method capability and amortized expected computation benefit are evaluated before deploying an invented method. In neumann1/structural_meta_invention.py, a negative utility decision removes learned methods from the actual family inference hot path but preserves source observations and the original-verified classical fallback for further self-improvement. Both NeumannEngine and RegistryEngine have an admission API. Source utility evidence persists in method checkpoints and decisions are recomputed at load time. Actual core production tests passed 28/28 in GitHub Actions run 42441596771.

## Verdict

- Global Q3, autonomous invention of a new problem representation and discovery metalanguage: OPEN.
- Frontier-grade ARC2 capability: FAIL, original 0/120.
- New search policy on same vocabulary improves correctness or evaluation checks: FAIL.
- Claimed 10x amortized total compute advantage: FAIL/OPEN, no valid success.
- Profit-aware method deletion and safe classical fallback integrated into the real core: scoped implementation PASS.
- The real scientific bottleneck is missing expressive object-centered compositional representations and reusable causal operator invention, not search ordering. Do NOT rescore the opened 120 originals as a fresh first evaluation following revisions.

**Original failures remain immutable. Green CI does not close Q3/Q4/Q7.**
