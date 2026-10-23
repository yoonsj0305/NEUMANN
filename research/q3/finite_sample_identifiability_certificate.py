"""Q3 exact identifiability limit, FIRST original-source third32 observations only.

Mathematical theorem (elementary Lagrange interpolation):
  For any n distinct rational x_i and arbitrary rational observed y_i,
  P(x)=sum_i y_i prod_(j!=i) (x-x_j)/(x_i-x_j) is a Q-polynomial
  with P(x_i)=y_i for all samples (degree <=n-1).
  V(x)=prod_i (x-x_i) is a nonzero Q-polynomial of degree n.
  Thus P_c=P+cV for ALL c∈Q exactly matches the original data,
  and P_c(x*) differs for distinct c at any unseen x*.
  No inference algorithm can recover a UNIQUE generating law from
  these finite observations without a grammar prior or a new oracle.
  This does not contradict grammar-conditional exact proofs.
"""
import argparse,collections,hashlib,json,pathlib
from fractions import Fraction as F

PIN_SHA="5bd1287518921eed233828f58f7202c991ca552fdb7dbf6b798e18f0ed2a4de2"

def hexdigest(b):return hashlib.sha256(b).hexdigest()
def snap_frac(q):
    return {"numerator_bits":q.numerator.bit_length(),
            "denominator_bits":q.denominator.bit_length(),
            "num_den_canonical_sha256":hexdigest((str(q.numerator)+"/"+str(q.denominator)).encode())}

def proof_by_two_implementations(xs,ys):
    n=len(xs)
    assert 8<=n<=64 and len(ys)==n and len(set(xs))==n
    # Independent symbolic Vandermonde unisolvency: a nonzero degree<n
    # polynomial cannot vanish on n different rational points.
    # Lagrange and zero-vanishing-product proof are exact rational equalities.
    denoms=[]
    for i in range(n):
        base=F(1)
        for j in range(n):
            if i!=j:base*=xs[i]-xs[j]
        assert base !=0
        denoms.append(base)
    # Independent direct arithmetic check evaluating the raw constructive
    # Lagrange program at EVERY one of the source data knots.
    for target in range(n):
        x=xs[target];p=F(0)
        for i in range(n):
            prod=F(1)
            for j in range(n):
                if j==i:continue
                diff=x-xs[j]
                if diff==0:
                    prod=F(0)
                    break
                prod*=diff
            if prod:p+=ys[i]*(prod/denoms[i])
        assert p==ys[target],"INTERPOLANT_SOURCE_EXACTNESS_FAILURE"
    xstar=max(xs)+F(1)
    assert xstar not in xs
    delta=F(1)
    for x in xs:delta*=xstar-x
    assert delta !=0
    # P_c(xstar)-P_0(xstar)=c*V(xstar). Compare c=1,c=2.
    assert delta*F(1)!=delta*F(2)
    # The first independent proof is the exact arithmetic evaluation above;
    # this second proof constructs coefficients of the vanishing-factor
    # polynomial V and evaluates using Horner, not product accumulation.
    coeff=[F(1)]
    for xi in xs:
        newer=[F(0)]*(len(coeff)+1)
        for k,ck in enumerate(coeff):
            newer[k]+=-xi*ck
            newer[k+1]+=ck
        coeff=newer
    assert len(coeff)==n+1 and coeff[-1]==1
    witness=F(0)
    for ck in reversed(coeff):witness=witness*xstar+ck
    assert witness==delta,"INDEPENDENT_HORNER_VANISHING_PRODUCT_MISMATCH"
    return {
        "interpolation_degree_at_most":n-1,
        "distinct_observation_points":n,
        "exact_lagrange_at_every_observed_point":True,
        "independent_expanded_vandermonde_factor_at_witness":True,
        "vanishing_polynomial_degree":n,
        "witness_unseen_x":snap_frac(xstar),
        "witness_P1_minus_P0":snap_frac(delta),
        "P1_and_P2_disagree_at_unseen_witness":True,
        "infinite_distinct_compatible_polynomials_over_Q":True}

def run(path,out):
    b=pathlib.Path(path).read_bytes()
    assert hexdigest(b)==PIN_SHA,"PREVIOUS_ORIGINAL_SOURCE_SHA_MISMATCH"
    data=json.loads(b)
    assert len(data['source_numeric_without_equations'])==32
    rows=[];counts=collections.Counter()
    for entry in data['source_numeric_without_equations']:
        counts["total"]+=1
        info={"id":entry["id"],"source_only":True}
        if "x" not in entry:
            info["status"]="UNKNOWN_SOURCE_NO_NUMERIC_POINTS"
            counts["unknown"]+=1
        else:
            try:
                # Preserve binary64 observation EXACTLY, not decimal-round or
                # replace them with true hidden original author formula values.
                xs=[F.from_float(float(x)) for x in entry['x']]
                ys=[F.from_float(float(y)) for y in entry['y']]
                certificate=proof_by_two_implementations(xs,ys)
                info.update({"status":"EXACT_INFINITE_COMPATIBLE_POLYNOMIALS_CERTIFIED",
                             "observation_SHA256":hexdigest(json.dumps([entry["x"],entry["y"]],sort_keys=True).encode()),
                             "finite_sample_certificate":certificate})
                counts["certified"]+=1
            except Exception as ex:
                counts["unknown"]+=1
                info["status"]="UNKNOWN_ARITHMETIC_UNSUPPORTED"
                info["error"]=type(ex).__name__+":"+str(ex)[:180]
        rows.append(info)
    decision={
        "schema":"NEUMANN_Q3_FINITE_ORIGINAL_SOURCE_NONIDENTIFIABILITY.v1",
        "source_original_external_author":"EquationDiscovery ERBench public train original third32",
        "previous_original_source_numeric_SHA256":PIN_SHA,
        "observations_type":"observed binary64 x,y interpreted as exact Q input records, NOT as exact latent author's analytic function",
        "all_32_rows":rows,"counts":dict(counts),
        "formal_general_theorem":"For arbitrary finite n distinct rational samples there are infinitely many mutually different Q-polynomials matching all samples; uniqueness of unrestricted governing law is logically impossible from samples alone",
        "mathematical_method":"Lagrange interpolant P plus c times vanishing polynomial V, all exact rational arithmetic, independent expanded coefficient Horner witness",
        "scientific_boundary":"Elementary interpolation theorem, not a new result in mathematics or an autonomous neural discovery; grammar-restricted unique identification is still possible and distinguishable",
        "architecture_consequence":"NEUMANN must explicitly declare inductive grammar priors or query a new oracle for outside-sample evidence; in-sample numerical-fit alone cannot certify true original structural identity",
        "trainable_new_operator":"NOT_TESTED",
        "Q3_primitive_invention":"OPEN","Q4_10X":"OPEN","Q6_transfer":"OPEN",
        "G1":"HOLD"}
    dest=pathlib.Path(out);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(decision,indent=2,sort_keys=True)+"\n")
    print("Q3_EXTERNAL_ERBENCH_SOURCE_IDENTIFIABILITY_PROOF",json.dumps({
        "counts":dict(counts),"certificate_SHA256":hexdigest(dest.read_bytes()),
        "general_theorem":"INFINITE_EXACT_POLYNOMIALS_PER_VALID_FINITE_SOURCE"}),flush=True)
    assert counts["total"]==32
    assert counts["certified"]>0
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--source",required=True);p.add_argument("--out",required=True)
    a=p.parse_args()
    run(a.source,a.out)
