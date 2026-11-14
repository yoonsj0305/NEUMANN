# NEUMANN 1 | Postfirst legacy SMT 2.5 string operator alias normalization for Euphony four | 2026-10-29

Prior original 16 FIRST SHA 7acee7938ea2b8d18db2dd38058de36f7abdcf5116fbd703f6fce048b3a4418c preserved. Four original Euphony SLIA parser HOLD. First postfirst grammar-only normalization attempt completed with four operator parser errors Symbol int.to.str not declared, original first attempt JSON SHA 8ed941302ae0a55b1c9ec40f5f6ae18fab45c34251e56f2a7bdc6b11b7a2637a. All prior results retained unchanged. This is SECOND separately declared postfirst compatibility attempt and NOT a new blind test.

Official original SyGuS-Org/benchmarks commit 13c8deb68a873635879c9a69bc78caebd340f646, exact first cohort indexes12-15. The ONLY new allowed legacy SMT-LIB 2.5→2.6 transformations after earlier grammar form conversion:
- operator int.to.str becomes str.from_int (integer to string), only in application head positions.
- operator str.to.int becomes str.to_int (string to integer), only in application head positions.
These are standardized naming equivalents, not program-computation changes. Preserve every original authored PBE example and all other grammar productions and source inputs/outputs exactly, and verify source SHA before use.

Run official CVC5 1.4.2 with original verified binary release asset SHA 0af677313c8277dc558d3049b192389db4d975d31c968fbd6f31cf0849ee411d, one attempt per normalized original under CPU12s/wall15s and RSS800MiB sampled. No additional operator replacements, solver flag tuning or retries based on outcome. Any returned source candidate UNVERIFIED until all original PBE constraints independently checked using original authored example values. All four remain opened dev. DO NOT relabel original first parser failures as solver successes. No neural learning or Q/G1 promotion; Q1-Q7 OPEN, G1 HOLD, G2 NOT RUN, PR616 DRAFT.
