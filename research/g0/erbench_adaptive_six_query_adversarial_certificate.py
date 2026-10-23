"""Universal zero-error six-query adaptive impossibility in Q-rational P4/Q2.

For ANY six distinct rational oracle query locations selected adaptively,
construct two different source functions in the same bounded grammar that
agree at all six locations and disagree at an additional rational location.

The experiment plugs in locations from already-frozen independent external
ERBench fourth32 source queries; this does NOT say the two constructed
counterexample functions are the actual author original functions.
"""
import argparse,collections,hashlib,json,pathlib
import sympy as s
x=s.Symbol("x")
SOURCE_SHA="151c9e2e2731d50fefc1e75b56c58b3971067a058cff77c04cdc67033cdb420a"
def sha(raw):return hashlib.sha256(raw).hexdigest()
def solve(points):
    points=[s.Rational(q) for q in points]
    assert len(points)==6 and len(set(points))==6
    W=s.prod(x-xj for xj in points)
    Q=1+x*x;P=x**4
    # Because x^4≡1 mod 1+x², setting V=-W modulo Q gives
    # W+P*V divisible by Q, hence U=(W+P*V)/Q degree<=4.
    V=-s.rem(W,Q,x)
    U,rem=s.div(W+P*V,Q,x)
    assert rem==0 and s.degree(V,x)<=1 and s.degree(U,x)<=4
    xstar=max(points)+1
    assert xstar not in points
    for k in range(1,12):
        eps=s.Rational(1,10**k)
        D=Q+eps*V
        if all(D.subs(x,t)!=0 for t in points+[xstar]):break
    else:raise ValueError("NO_VALID_NONZERO_ADVERSARIAL_COEFFICIENT")
    f1=s.cancel(P/Q)
    f2=s.cancel((P+eps*U)/(Q+eps*V))
    assert s.degree(s.fraction(f2)[0],x)<=4
    assert s.degree(s.fraction(f2)[1],x)<=2
    assert s.cancel(f1-f2)!=0
    assert s.cancel((f2-f1)-eps*W/(Q*(Q+eps*V)))==0
    for pt in points:
        assert s.cancel(f1.subs(x,pt)-f2.subs(x,pt))==0
    delta=s.cancel(f2.subs(x,xstar)-f1.subs(x,xstar))
    assert delta!=0
    return {"queries":[str(p) for p in points],"epsilon":str(eps),
        "adversarial_first_function":"x^4/(1+x²)",
        "adversarial_second_function":str(f2),
        "nontrivial_divergence_test_x":str(xstar),
        "exact_nonzero_divergence_SHA256":sha(str(delta).encode()),
        "all_six_observation_answers_identical":True,
        "different_on_seventh_observation":True,
        "inside_human_restricted_P4_Q2":True}
def main(src,out):
    blob=pathlib.Path(src).read_bytes()
    assert sha(blob)==SOURCE_SHA,"IMMUTABLE_SOURCE_HASH_MISMATCH"
    input=json.loads(blob)
    assert len(input["results"])==32
    rows=[];counts=collections.Counter()
    for item in input["results"]:
        counts["all_original_source_rows"]+=1
        if item["status"]!="SEVEN_EXACT_RATIONAL_REPLIES":
            rows.append({"id":item["id"],"status":"UNKNOWN_SEVEN_VALID_SOURCE_QUERY_POINTS_UNAVAILABLE"})
            counts["unavailable"]+=1
            continue
        pts=[item["replies"][i]["x"] for i in range(6)]
        cert=solve(pts)
        rows.append({"id":item["id"],"status":"ADAPTIVE_6_QUERY_NONIDENTIFICATION_CERTIFIED","certificate":cert})
        counts["certified"]+=1
    assert counts["all_original_source_rows"]==32
    result={"schema":"NEUMANN_Q34_ADAPTIVE_SIX_QUERY_UNIVERSAL_LOWER_BOUND.v1",
        "immutable_first_external_source_SHA256":SOURCE_SHA,
        "proof_generalizes_to_any_six_distinct_rational_query_points":True,
        "formal_adversarial_construction":
          "Given any six rationals x1..x6, W=Π(x−xi), Q=1+x², P=x^4, V=−(W rem Q), U=(W+P*V)/Q, choose any nonzero rational epsilon avoiding finite denominator poles. Then f1=P/Q and f2=(P+epsilon U)/(Q+epsilon V) are in grammar degP<=4 degQ<=2, agree on the six x_i, differ at every other common non-pole x where W(x) !=0.",
        "logical_conclusion":
          "No adaptive deterministic algorithm can GUARANTEE UNIQUE exact identification of arbitrary target in the full P4/Q2 class from at most six finite rational source queries. Transcript under f1 is also consistent with a different f2 constructed after the six query locations are known.",
        "tested_external_author_source_query_locations":rows,
        "counts":dict(counts),
        "original_author_formula_used":False,
        "not_a_new_literature_mathematical_theorem":True,
        "autonomous_neural_primitive":"NOT_TESTED",
        "total_system_10x":"NOT_PROVED"}
    output=pathlib.Path(out);output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
    print("Q34_ADAPTIVE_SIX_QUERY_LOWER_BOUND_EXACT_RESULT",
          json.dumps({"counts":dict(counts),"sha256":sha(output.read_bytes())},sort_keys=True),flush=True)
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--source",required=True)
    p.add_argument("--out",required=True)
    z=p.parse_args();main(z.source,z.out)
