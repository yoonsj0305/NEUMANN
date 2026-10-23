"""P2 real public OEIS *new author* partial-sum ORIGINAL source generator.

Four EXTERNAL original rational function sequences with published OEIS
provenance; all use exact source n1..48. These are a hand-picked
positive-family verification sample, NOT representative random OEIS,
NOT a secret leaderboard. They remain completely separate from the
pretrained fixed model's ORIGINAL source data and generic training.
All source formulas physically excluded from SOURCE-only artifact.
"""
import argparse,json
import sympy as sp
from recursive_operator_source_inventor import N,sha,save

K=sp.Symbol("k",integer=True,positive=True)
# Exact published OEIS rational FUNCTION ratios. Author truth is finite
# sums, not merely the integer numerator sequence.
GOLD=(
 ("OEIS:A007406/A007407","1/k**2","https://oeis.org/A007406"),
 ("OEIS:A007408/A007409","1/k**3","https://oeis.org/A007408"),
 ("OEIS:A075135/denominator(H(n,3,1))","1/(3*k-2)","https://oeis.org/A075135"),
 ("OEIS:A025550/A025547","1/(2*k-1)","https://oeis.org/A025550"),
)
def prepare(sourcefile,truthfile):
    source=[];truth=[]
    for j,(name,summand,url) in enumerate(GOLD):
        expr=sp.sympify(summand,locals={"k":K})
        assert not expr.has(sp.Function)
        x=list(range(1,49))
        values=[]
        v=sp.S.Zero
        for i in x:
            v+=expr.subs(K,i)
            assert v.is_Rational
            values.append(v)
        uid=sha("OEIS_NEW_AUTHOR_RECURSIVE_TEST_20261023|"+name)[:24]
        # Model sees neither published OEIS name nor formula in numeric.
        source.append({"id":uid,"x":x,"y":[float(y) for y in values],
           "y_exact":[str(y) for y in values],
           "source_task":"OEIS_PUBLISHED_RATIONAL_SEQUENCE_"+str(j),
           "author_formula_WITHHELD":True,
           "sample_protocol":"noiseless exact rational 48 consecutive positive n"})
        truth.append({"id":uid,"published_source":name,"url":url,
           "finite_sum_start":1,"finite_sum_end":"n",
           "finite_sum_symbol":"k","summand_expression":summand})
    src=save(sourcefile,{"schema":"NEUMANN_P2_OEIS4_UNSEEN_PUBLIC_SERIES_SOURCE_ONLY.v1",
         "source_numeric_without_equations":source,
         "truth_expression_is_in_different_CI_artifact":True,
         "preselected_recurrence_family_positive_examples_not_random_population":True})
    gold=save(truthfile,{"schema":"NEUMANN_P2_OEIS4_PUBLIC_AUTHORED_FINITE_SUM_GOLD_PRIVATE_TO_GRADER.v1",
        "private_true_equations":truth})
    print("NEUMANN_P2_OEIS4_FIRST_NEW_AUTHOR_SERIES_SOURCE_GOLD_SHA",json.dumps({
       "source_sha256":src,"gold_sha256":gold,
       "family_size":4,"publisher":"OEIS original public series"},sort_keys=True),flush=True)
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--source",required=True);p.add_argument("--truth",required=True)
    a=p.parse_args();prepare(a.source,a.truth)
