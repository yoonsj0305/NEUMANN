# Historical first original-source exposure, do not retcon

- **Initial Action run:** `39615423133`
- **Status:** FAILED before complete 8-source evidence JSON could be persisted.
- **Actual pre-body metadata SHA registration:** `e00e96733735e9d2ff5198359e3d76801b1eed1b` (kept unchanged).
- **Observed failure:** exact classical rational solve received SymPy Float from numeric matrix (`AttributeError: 'Float' object has no attribute 'q'`), and a NumPy boolean was not JSON serializable.
- **Repair scope:** cast matrices to exact integer values (source sampled SMT integers; polynomial deltas are integer-valued), serialize NumPy scalar objects. No training/grammar/search/threshold change and no inspection-based source-specific algorithm tuning.
- **Scientific boundary:** subsequent runs are a **technical repair rerun on already opened originals**, not a second independent first-blind evaluation. The original exposure was registered prospectively; execution outcome remains an infrastructure failure.
- **Global Q3/Q4/Q6:** OPEN.
