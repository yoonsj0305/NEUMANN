# Q3M · Fail-closed assertion location in original-C proofs

**2026-10-18 | preregistered before first Q3M GitHub execution.**

## Motivating unsoundness

Current `replay_real_c_loop_invariants.py` `static_assertions` extracts exactly one `//@ assert(...);` label from anywhere in the whole source, discards all C comments, and `model_original` treats this label as the **post-loop original postcondition**. The location is never checked. A false source assertion placed BEFORE a loop whose final state satisfies that condition can be mistakenly certified as an exit assertion. This threatens historical `13/150` source-file scope claims if any accepted original annotations were not placed at the physical exit verification point.

## Fixed soundness patch and adversarial gates

- Preserve original `//@ assert(...);` source content, original C input bytes and original state transition unchanged.
- In a **separate parser-only copy** of original source, replace the exact one standalone source assertion line with a unique inert marker `__neumann_original_assert_site_marker__();`. All other C text is parsed normally by the existing pycparser frontend after exactly the same accepted include/define handling. The original C verifier never executes the marker; it is a source-location *tag only*.
- The marker must be a **top-level statement of `main()` immediately after the unique original `while` or `for` loop**, allowing only inert empty statements before the marker. Return may occur after the marker but never before. Reject annotations before the loop, inside the body, in another function, after a return, or in unmodeled nested blocks. Reject malformed/multiple annotations and any marker-name collision in original source. If parsing fails, **ABSTAIN**, not UNSAT proof.
- Adversarial controls include a **false assertion before the loop that happens to be true at exit**, a valid after-loop assertion, an inside-loop assertion, and a post-return assertion. The false-before-loop control must be rejected by this new safety guard even if the old backend's exit-only semantics could have accepted it.
- Re-run the **exact historical 13 original SHA identities** (first Q3I 9 + Q3K-2 sum04 1 + Q3L 3). Hash-match and count all 13, check location under the strengthened guard. Any historical original failing it is **NOT CERTIFIED** until independently revalidated. Never silently preserve 13/150 if the assertion-placement proof fails.
- The original Q3K2/Q3L solver obligations must be re-run under this guard where needed; a location-only success is **necessary, not sufficient** for an independent source safety theorem. At minimum preserve exact prior mathematical proof receipts and verify no semantic code regression.
- Same pre-registered fixed source group; no new learned model, no newly unopened benchmark access, no Q3F sealed original source access. All global Q1–Q7 OPEN.

**Scientific status not predetermined:** This study might invalidate a prior C proof. Preserve the exact outcome and withdraw any claim no longer supported. STOP additional source-only solver microbenchmarks until original-source proof frontend is robust enough to trust.
