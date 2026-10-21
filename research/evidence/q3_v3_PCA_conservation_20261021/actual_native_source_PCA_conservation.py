"""NEUMANN Q3 v3 | actually FITTED PCA discovers conserved affine relations.

Posthoc development: original program bodies already opened by PR395.
No source-specific state names, no copied manual invariants, and no SAT labels
as target features. PCA is fit on ORIGINAL source Pre/Trans SAT reachable traces.
It generates integer affine equalities with evidence-only rational reconstruction;
unchanged native Pre, Trans, Post three-VC Z3+cvc5 decide actual correctness.
An EXACT rational no-learn nullspace comparator is included, preventing a
spurious 'uniquely learned' conclusion from classical linear algebra.
"""
from __future__ import annotations
import argparse,collections,hashlib,itertools,json,math,time
from fractions import Fraction
from pathlib import Path
import numpy as np
from sklearn.decomposition import PCA
from sympy import Matrix
import z3
from research.evidence.q3_trained_affine_from_native_samples_20261021.actual_selfsupervised_candidate_miner import (
    source_samples,candidate_generator,houdini,millis
)
from research.evidence.q4_prospective_six_20261021.first_six_classical_cheapest_safe_portfolio import prepare
PATHS=[
 ("lib/Inv_Track/from_2018/fib_21.sl","836f4cbecd25fbd37fddd3a2c3c936a8ac230293"),
 ("lib/Inv_Track/from_2018/jmbl_hola.41.sl","19e13372aa064e62b539bb6c8fbf13e1d45ccc3")
]
MAX_ARITY=4
MAX_DATA_MAGNITUDE=100000000
MAX_RATIONAL_DENOMINATOR=12

def integer_basis(raw):
    """Normalize a rational model vector to minimal nonzero integer coefficients."""
    lcm=1
    for r in raw:lcm=math.lcm(lcm,r.denominator)
    ints=[int(r*lcm) for r in raw]
    g=0
    for z in ints:g=math.gcd(g,abs(z))
    if g==0:return None
    ints=[q//g for q in ints]
    first=next(x for x in ints if x)
    if first<0:ints=[-x for x in ints]
    return ints

def propose_from_svd(coefficients,raw_states,indices):
    """Recover exact integer relation and use samples only as candidate filter."""
    if not len(coefficients):return None
    for anchor in range(len(coefficients)):
        if abs(float(coefficients[anchor]))<.12:continue
        rat=[]
        for v in coefficients:
            if abs(float(v))<1e-9:rat.append(Fraction(0))
            else:rat.append(Fraction(float(v)/float(coefficients[anchor])).limit_denominator(MAX_RATIONAL_DENOMINATOR))
        ints=integer_basis(rat)
        if ints is None or max(map(abs,ints))>100000:continue
        vals=[sum(int(c)*int(row[j]) for c,j in zip(ints,indices)) for row in raw_states]
        if len(set(vals))==1 and any(ints):
            return ints,int(vals[0])
    return None

def learned_pca_candidates(src,states):
    start=time.perf_counter_ns()
    dims=len(src["now"])
    observed=np.asarray(states,dtype=np.float64)
    outputs={};receipts=[];fitted=0
    for width in range(2,min(dims,MAX_ARITY)+1):
        for indices in itertools.combinations(range(dims),width):
            X=observed[:,indices]
            if len(X)<width+2 or np.max(np.abs(X))>MAX_DATA_MAGNITUDE:continue
            try:
                pca=PCA(n_components=width,svd_solver="full").fit(X)
                fitted+=1
                largest=max(float(pca.singular_values_[0]),1e-6)
                nearzero=[j for j,v in enumerate(pca.singular_values_)
                          if float(v)<=max(1e-7,largest*1e-8)]
                for j in nearzero:
                    rel=propose_from_svd(pca.components_[j],states,indices)
                    if rel is None:continue
                    coefs,val=rel
                    lhs=z3.Sum(*[int(c)*src["now"][i] for c,i in zip(coefs,indices)])
                    expression=lhs==val
                    key=expression.sexpr()
                    if key not in outputs:outputs[key]=(expression,{"FITTED_PCA"})
                    receipts.append({"variable_indices":indices,"PCA_train_samples":len(states),
                                     "PCA_zero_singular_value":float(pca.singular_values_[j]),
                                     "fitted_integer_coefficients":coefs,
                                     "fitted_integer_constant":val,
                                     "source_independent_candidate_SHA":hashlib.sha256(key.encode()).hexdigest()})
            except Exception as exc:
                receipts.append({"indices":indices,"exception":type(exc).__name__})
    return list(outputs.values()),{
        "real_CPU_PCA_model_fits":fitted,
        "original_reachable_observations":len(states),
        "genuinely_learned_integer_affine_candidates":len(outputs),
        "learned_components":receipts,
        "fit_and_candidate_generation_wall_ms":millis(start)}
def exact_classical_nullspace_candidates(src,states):
    """Strong equal-information NO-learned regression baseline using exact rationals."""
    t=time.perf_counter_ns()
    dims=len(src["now"])
    output={};computations=0
    # Compute the exact nullspace of observed differences. It is a classical
    # solver with full rights to the SAME initial/source transition state data.
    for width in range(2,min(dims,MAX_ARITY)+1):
        for indices in itertools.combinations(range(dims),width):
            raw=[[int(row[j]) for j in indices] for row in states]
            differences=[[q-v for q,v in zip(row,raw[0])] for row in raw[1:]]
            basis=Matrix(differences).nullspace()
            computations+=1
            for vector in basis:
                ints=integer_basis([Fraction(q) for q in vector])
                if ints is None:continue
                k=sum(v*x for v,x in zip(ints,raw[0]))
                lhs=z3.Sum(*[int(c)*src["now"][j] for c,j in zip(ints,indices)])
                expr=lhs==k
                key=expr.sexpr()
                if key not in output:output[key]=(expr,{"CLASSICAL_EXACT_NULLSPACE"})
    return list(output.values()),{
        "exact_rational_no_fit_nullspace_computations":computations,
        "candidate_integer_affine_count":len(output),
        "generation_wall_ms":millis(t)}
def one(root,item):
    start=time.perf_counter_ns()
    out={"path":item["path"],"real_source_blob":item["git_blob"],
         "status":"ABSTAIN","new_first_blind_original":False}
    try:
        raw,src,native,identity=prepare(root,item)
        out["original_full_native_PreTransPost_dual_parity"]=identity
        samples,edges,data=source_samples(src,native)
        out["actual_native_data"]=data
        if len(samples)<5 or len(edges)<2:raise RuntimeError("NOT_ENOUGH_REAL_TRANSITIONS")
        basic,basefit=candidate_generator(src,samples,edges,False)
        trained,learnrec=learned_pca_candidates(src,samples)
        classical,baseline=exact_classical_nullspace_candidates(src,samples)
        out["actual_trained_PCA_numeric_learning"]=learnrec
        out["exact_no_learning_linear_algebra_comparator"]=baseline
        out["zero_fit_small_template_original_dual"]=houdini(src,native,basic)
        out["PCA_actually_learned_full_original_dual"]=houdini(src,native,basic+trained)
        out["equal_data_exact_classical_no_learning_full_original_dual"]=houdini(src,native,basic+classical)
        out["PCA_original_solver_pass_only_when_small_templates_fail"]=bool(
            out["PCA_actually_learned_full_original_dual"]["fully_verified_complete_original_3VC"] and
            not out["zero_fit_small_template_original_dual"]["fully_verified_complete_original_3VC"])
        out["PCA_necessary_vs_exact_classical_algebra"]=bool(
            out["PCA_actually_learned_full_original_dual"]["fully_verified_complete_original_3VC"] and
            not out["equal_data_exact_classical_no_learning_full_original_dual"]["fully_verified_complete_original_3VC"])
        out["status"]="COMPLETE_ORIGINAL_3VC_PCA_VS_EXACT_NULLSPACE_AND_BASIC"
    except Exception as e:
        out["status"]="ABSTAIN_SOURCE_DATA_OR_SOLVER";out["error"]=type(e).__name__+":"+str(e)[:320]
    out["full_training_and_native_verification_wall_ms"]=millis(start)
    print("Q3_V3_ACTUALLY_FITTED_SOURCE",item["path"],out["status"],
          "PCA_MODEL_FITS",out.get("actual_trained_PCA_numeric_learning",{}).get("real_CPU_PCA_model_fits"),
          "PCA_CAND",out.get("actual_trained_PCA_numeric_learning",{}).get("genuinely_learned_integer_affine_candidates"),
          "PCA_PROOF",out.get("PCA_actually_learned_full_original_dual",{}).get("fully_verified_complete_original_3VC"),
          "EXACT_CLASSICAL",out.get("equal_data_exact_classical_no_learning_full_original_dual",{}).get("fully_verified_complete_original_3VC"),
          "BASIC",out.get("zero_fit_small_template_original_dual",{}).get("fully_verified_complete_original_3VC"),
          "ERROR",out.get("error"),flush=True)
    return out
def main():
    a=argparse.ArgumentParser()
    for k in ("root","freshfreeze","oldfreeze","out"):a.add_argument("--"+k,required=True)
    args=a.parse_args();d1=json.loads(Path(args.freshfreeze).read_text())
    d2=json.loads(Path(args.oldfreeze).read_text())
    targets={t["path"]:t for t in d1["originals"]+d2["new_originals"]}
    selected=[]
    for k,v in PATHS:
        if k not in targets or targets[k]["git_blob"]!=v:raise RuntimeError("V3_ORIGINAL_MANIFEST_SHA_MISMATCH")
        selected.append(targets[k])
    selected +=d1["originals"]
    rows=[one(Path(args.root),x) for x in selected]
    report={
        "schema":"neumann.q3.v3_posthoc_trained_PCA_affine_conserved_inductive_original_v1",
        "original_source_count":len(rows),
        "all_original_source_bodies_previously_OPENED":True,
        "actually_fitted_PCA_case_count":sum(r.get("actual_trained_PCA_numeric_learning",{}).get("real_CPU_PCA_model_fits",0)>0 for r in rows),
        "PCA_full_original_dual_3VC_pass":sum(r.get("PCA_actually_learned_full_original_dual",{}).get("fully_verified_complete_original_3VC",False) for r in rows),
        "exact_no_learn_nullspace_full_original_dual_3VC_pass":sum(r.get("equal_data_exact_classical_no_learning_full_original_dual",{}).get("fully_verified_complete_original_3VC",False) for r in rows),
        "simple_no_fit_template_full_original_dual_3VC_pass":sum(r.get("zero_fit_small_template_original_dual",{}).get("fully_verified_complete_original_3VC",False) for r in rows),
        "bounded_PCA_gain_over_basic":sum(r.get("PCA_original_solver_pass_only_when_small_templates_fail",False) for r in rows),
        "bounded_PCA_gain_over_exact_classical":sum(r.get("PCA_necessary_vs_exact_classical_algebra",False) for r in rows),
        "strong_equal_authority_ML_uniqueness_unproven":True,
        "model_is_actually_trained_on_native_trajectories_not_hand_invariant":True,
        "global_Q3":"OPEN","global_Q4":"OPEN","global_Q6":"OPEN",
        "programs":rows}
    out=Path(args.out);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    for k in ("actually_fitted_PCA_case_count","PCA_full_original_dual_3VC_pass",
              "exact_no_learn_nullspace_full_original_dual_3VC_pass",
              "simple_no_fit_template_full_original_dual_3VC_pass",
              "bounded_PCA_gain_over_basic","bounded_PCA_gain_over_exact_classical"):
        print("V3_ACTUALLY_LEARNED_CONSERVATION",k,report[k])
if __name__=="__main__":main()
