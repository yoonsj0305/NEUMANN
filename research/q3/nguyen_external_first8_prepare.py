"""FIRST independent author-family transfer source: Nguyen-1..8 (univariate).

Eight standard public benchmark functions from NeurIPS 2021 supplemental
Table 9, not from EquationDiscovery ERBench (different research authors).

https://proceedings.neurips.cc/paper/2021/file/d073bb8d0c47f317dd39de9c9f004e9d-Supplemental.pdf
Does not claim official 20-point competition protocol: here 48 independent
numeric probes per source function, split fit32/validate16 as NEUMANN uses.

This file is run ONLY in an isolated original-generation CI job; the
source-only learner never imports or receives this original author registry.
"""
import argparse,hashlib,json,pathlib
import numpy as np
import sympy as sp
from erbench_original_eleventh import sha,save,allowed_formula,calc,FUN,SYM
# Exactly the one-variable Nguyen-1..8 public benchmark formulas.
# Never pass these formulas to model or same-source baseline.
GOLD=(
 ("Nguyen-1","x**3 + x**2 + x",-1.,1.),
 ("Nguyen-2","x**4 + x**3 + x**2 + x",-1.,1.),
 ("Nguyen-3","x**5 + x**4 + x**3 + x**2 + x",-1.,1.),
 ("Nguyen-4","x**6 + x**5 + x**4 + x**3 + x**2 + x",-1.,1.),
 ("Nguyen-5","sin(x**2)*cos(x)-1",-1.,1.),
 ("Nguyen-6","sin(x)+sin(x+x**2)",-1.,1.),
 ("Nguyen-7","log(x+1)+log(x**2+1)",0.,2.),
 ("Nguyen-8","sqrt(x)",0.,4.),
)
assert len(GOLD)==8
def prepare(sourceout,truthout):
    numeric=[];truth=[]
    for name,formula,low,hi in GOLD:
        tree,var=allowed_formula(formula)
        assert var=="x"
        uid=sha(("NGUYEN2021_STANDARD_1D\x1f"+name).encode())[:24]
        rng=np.random.default_rng(int(uid[:12],16))
        xx=rng.uniform(low,hi,size=48)
        with np.errstate(all="ignore"):
            yy=[float(calc(tree,{var:float(x)},FUN)) for x in xx]
        assert np.all(np.isfinite(yy)) and len(yy)==48
        numeric.append({"id":uid,"x":xx.tolist(),"y":yy,
                        "collection":"Nguyen2021Benchmark",
                        "task_ID":name,"domain_status":"PUBLISHED_TABLE9_WITH_FRESH48_SAMPLES"})
        truth.append({"id":uid,"collection":"Nguyen2021Benchmark",
                      "task_ID":name,"original_expression":formula,"source_var":var,
                      "original_support":[low,hi]})
    out={"schema":"NEUMANN_Q3_FROZEN_NEURAL_INDEPENDENT_NGUYEN8_SOURCE_NUMERIC_ONLY.v1",
         "original_total":8,"all_selected":8,
         "pub_source":"2021 NeurIPS supplemental Table9 benchmark Nguyen-1..8",
         "external_source_author_family":"NGUYEN_2011_SYMBOLIC_REGRESSION_NOT_ERBENCH",
         "source_numeric_without_equations":numeric,
         "sampling":"48 deterministic independent uniform points each; no noise; NOT official 20-point protocol"}
    src=save(sourceout,out)
    original=save(truthout,{"schema":"NEUMANN_Q3_PRIVATE_NGUYEN8_PUBLISHED_AUTHORED_FUNCTIONS.v1",
         "private_true_equations":truth})
    print("Q3_NGUYEN8_INDEPENDENT_AUTHOR_FAMILY_SOURCE_TRUTH_ISOLATION",json.dumps({
        "task_names":[x["task_ID"] for x in numeric],
        "source_SHA256":src,"truth_SHA256":original,
        "independent_originals":8},sort_keys=True),flush=True)
if __name__=="__main__":
    a=argparse.ArgumentParser()
    a.add_argument("--source",required=True);a.add_argument("--truth",required=True)
    b=a.parse_args();prepare(b.source,b.truth)
