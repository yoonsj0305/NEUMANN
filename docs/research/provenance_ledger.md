# Research provenance ledger

| Component or data | Primary source | Use | Material incorporated | Status |
| --- | --- | --- | --- | --- |
| BCSSTRUC1 `bcsstk05/06/09/10` | NIST Matrix Market, Harwell–Boeing BCSSTRUC1, `https://math.nist.gov/MatrixMarket/data/Harwell-Boeing/bcsstruc1/` | External test data | None in repository; original compressed files fetched for local audit; hashes and URLs pinned in v0.0.52 | Attribute source in results; consult source terms before redistribution |
| SuperLU ordering policies | SciPy `splu` documentation, `https://docs.scipy.org/doc/scipy/reference/generated/scipy.sparse.linalg.splu.html` | Installed library baseline | SciPy dependency, no copied source | Library's distribution license governs installation |
| Reverse Cuthill–McKee | SciPy `reverse_cuthill_mckee` documentation | Installed library candidate | SciPy dependency, no copied source | Not a NEUMANN algorithm claim |
| IR2Solve, COVER and symbolic pipelines | Original publications, to be checked before publication | Comparative ideas only | No code, data or model weights imported | Exact mechanisms and dates need verification |
| Gurobi presolve, L2P-MIP, equality saturation | Primary documentation/publications, to be checked before publication | Baseline and positioning ideas | No code, data or model weights imported | Strong existing alternatives |
