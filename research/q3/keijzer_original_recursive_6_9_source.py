"""Isolated published Keijzer 2003 original author program source generation.

Reference:
Maarten Keijzer, "Improving Symbolic Regression with Interval Arithmetic
and Linear Scaling", EuroGP 2003, equations (7)..(10) and Table3.
https://groups.csail.mit.edu/EVO-DesignOpt/groupWebSite/uploads/Site/keijzer-improving-symbolic-regression-interval-arithmetic-linear-scaling-eurogp-2003.pdf

Keijzer6: harmonic(n) = sum_{k=1}^n 1/k, n integer >=1.
Keijzer7: log(n), Keijzer8: sqrt(n), Keijzer9: asinh(n).
These have different published author origins than train recurrence examples.
Use common 48 POSITIVE INTEGER consecutive source probes n1..48,
NOT official Keijzer 2003 train/test protocol. It grants exact rational
measurement to ALL methods when f(n) is rational; others are binary64
observations converted to exact binary64 rationals. State this explicit
oracle advantage and preserve full originals exclusively in grader job.
"""
import argparse,json
import numpy as np
import sympy as sp
from recursive_operator_source_inventor import N,save,sha

PUBLIC_AUTHOR_EQS=(
  ("Keijzer-6",sp.harmonic(N)),
  ("Keijzer-7",sp.log(N)),
  ("Keijzer-8",sp.sqrt(N)),
  ("Keijzer-9",sp.asinh(N)),
)
def prepare(sourceout,truthout):
    cases=[];truth=[]
    for name,expr in PUBLIC_AUTHOR_EQS:
        xs=list(range(1,49))
        yy_exact=[]
        for k in xs:
            if name=="Keijzer-6":
                value=sp.Rational(0)
                for j in range(1,k+1):value+=sp.Rational(1,j)
            else:
                value=sp.Rational(float(sp.N(expr.subs(N,k),16)))
            yy_exact.append(value)
        yy=[float(z) for z in yy_exact]
        uid=sha("KEIJZER_2003_EQUATION_COHORT_6_TO_9\x1f"+name)[:24]
        cases.append({
            "id":uid,"x":xs,"y":yy,"y_exact":[str(z) for z in yy_exact],
            "benchmark":"Keijzer2003",
            "task_ID":name,
            "domain":"n integers 1 to 48, noiseless, source-only 48 points",
            "conditional_exact_numeric_oracle":"exact rationals for harmonic; binary64 rational surrogate for transcendental"}
        )
        truth.append({"id":uid,"benchmark":"Keijzer2003","task_ID":name,
           "original_author_expression":str(expr),
           "original_function_for_positive_integer_domain":True,
           "author_citation":"EuroGP2003 Keijzer equation 7-10"})
    assert len(cases)==len(truth)==4
    src={"schema":"NEUMANN_Q3_KEIJZER_6_9_FIRST_SOURCE_ONLY.v1",
         "source_numeric_without_equations":cases,
         "published_originals":4,
         "original_author":"Keijzer2003 EuoGP eq7-10",
         "evaluation_not_official_benchmark_sampling":True,
         "no_original_author_expression_in_source_records":True}
    private={"schema":"NEUMANN_Q3_KEIJZER_6_9_PUBLISHED_ORIGINAL_TRUTH_SEPARATE.v1",
             "private_true_equations":truth}
    shasrc=save(sourceout,src)
    shagold=save(truthout,private)
    print("Q3_KEIJZER4_REAL_ORIGINAL_SOURCE_SEPARATED_FROM_RECURSIVE_AUTHOR_GRADER",
        json.dumps({"source_sha256":shasrc,"author_gold_sha256":shagold,
          "names":[x["task_ID"] for x in cases]},sort_keys=True),flush=True)
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--source",required=True);p.add_argument("--truth",required=True)
    a=p.parse_args()
    prepare(a.source,a.truth)
