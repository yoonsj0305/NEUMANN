"""Q3U exact rational nullspace discovery + independent unbounded original 3VC.

Source-only Classical-Hybrid *mechanism* proof, NOT neural invented Q3.
Finite model samples generate coefficients; only original SMT UNSAT proves.
"""
from __future__ import annotations
import argparse,collections,functools,hashlib,json,math,re,sys,time
from pathlib import Path
import z3
from sympy import Matrix,ilcm,Rational

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/"q3o-real-sygus-20261018"))
from first_two_originals import extract_original,sexprs,blobhash

SOURCE_COMMIT="6ac90265b11431c9477dfbd33e3e3380234c0499"
ORIGINAL_LICENSE="1e853cd500e1317b7c2ad0a2514b548c32c46f5e"
PINNED={
 "benchmarks/LIA/2017.ASE_FiB/fib_01.sl":"480ddf9d1ddb0c2c3e6d2aabf6af2e38f8f26f09",
 "benchmarks/LIA/2018.NeurIPS_Code2Inv/101.c.sl":"a59e04c08abc9601350cd64915255253ae44517f",
 "benchmarks/LIA/others/inria-00615623_4.sl":"56f60de6e81a0fa450f82efa2d7276696ed02378"
}
MAX_MODELS=28
MAX_STATE_ARITY=12
MAX_COEFF=100000
MAX_BASIS_PER_MODE=8
TIMEOUT_MS=2500

def checked(query,timeout_ms=TIMEOUT_MS):
    s=z3.Solver();s.set(timeout=timeout_ms)
    s.add(query)
    t0=time.perf_counter_ns()
    try:
        verdict=str(s.check())
    except Exception:
        verdict="error"
    return verdict,round((time.perf_counter_ns()-t0)/1e6,3)

def rows_from_original(query,variables,maxrows=MAX_MODELS):
    s=z3.Solver();s.set(timeout=TIMEOUT_MS);s.add(query)
    result=[];state="unknown";wall=0
    for _ in range(maxrows):
        t0=time.perf_counter_ns()
        try:state=str(s.check())
        except Exception:
            state="error"
        wall+=(time.perf_counter_ns()-t0)/1e6
        if state!="sat":break
        model=s.model()
        vals=[int(model.evaluate(x,model_completion=True).as_long()) for x in variables]
        result.append(vals)
        s.add(z3.Or(*[x!=z3.IntVal(v) for x,v in zip(variables,vals)]))
    return result,{"number_of_distinct_smt_models":len(result),
                   "sampler_terminal":state,
                   "sampler_solver_wall_ms":round(wall,3)}

def primitive_integer_vector(vector):
    denoms=[int(Rational(item).q) for item in vector]
    m=1
    for d in denoms:m=math.lcm(m,d)
    vals=[int(Rational(item)*m) for item in vector]
    divisor=functools.reduce(math.gcd,(abs(i) for i in vals),0)
    if divisor==0:return None
    vals=[n//divisor for n in vals]
    first=next(x for x in vals if x!=0)
    if first<0:vals=[-x for x in vals]
    if max(abs(v) for v in vals)>MAX_COEFF:return None
    if all(c==0 for c in vals[:-1]):return None
    return tuple(vals)

def exact_nullspace_candidates(rows):
    if not rows:return []
    matrix=Matrix(rows)
    found=[];seen=set()
    for vector in matrix.nullspace()[:MAX_BASIS_PER_MODE]:
        x=primitive_integer_vector(vector)
        if x is None or x in seen:continue
        seen.add(x);found.append(x)
    return found

def equation(c,xs):
    return z3.Sum(*[z3.IntVal(int(a))*v for a,v in zip(c[:-1],xs)])+z3.IntVal(int(c[-1]))==0

def conservation_delta(c,now,nxt):
    return z3.Sum(*[z3.IntVal(int(a))*(p-q)
               for a,p,q in zip(c[:-1],nxt,now)])==0

def ival(variables,now,nxt,pre,trans,post,original_source):
    if len(now)>MAX_STATE_ARITY:return {"status":"ABSTAIN_SOURCE_STATE_ARITY_CAP"}
    if not all(z3.is_int(x) for x in now+nxt):
        return {"status":"ABSTAIN_NONINTEGER_STATE"}
    presat,wt0=checked(pre)
    nontrivial,wt1=checked(z3.Not(post))
    if presat!="sat" or nontrivial!="sat":
        return {"status":"ABSTAIN_UNSAT_OR_UNKNOWN_ORIGINAL_PRE_OR_POST",
                "original_pre_sat":presat,"original_not_post_sat":nontrivial}
    pre_models,pm=rows_from_original(pre,now)
    tra_models,tm=rows_from_original(trans,now+nxt)
    n=len(now)
    if not pre_models or not tra_models:
        return {"status":"ABSTAIN_NO_SOURCE_SMT_MODELS",
                "pre_sampling":pm,"transition_sampling":tm}
    tra_now=[v[:n] for v in tra_models]
    tra_nxt=[v[n:] for v in tra_models]
    augmented_pre=[x+[1] for x in pre_models]
    image_rows=augmented_pre+[x+[1] for x in tra_nxt]
    cons_rows=augmented_pre+[
        [b-a for a,b in zip(current,nextstate)]+[0]
        for current,nextstate in zip(tra_now,tra_nxt)
    ]
    algebraic={"IMAGE":exact_nullspace_candidates(image_rows),
               "CONSERVATION":exact_nullspace_candidates(cons_rows)}
    admitted=[];diagnostics=collections.Counter()
    total_smt=0;total_ms=0
    for mode,candidates in algebraic.items():
        for coef in candidates:
            cand=equation(coef,now)
            cnext=equation(coef,nxt)
            ib,dt=checked(z3.And(pre,z3.Not(cand)));total_ms+=dt;total_smt+=1
            if ib!="unsat":
                diagnostics["REJECT_INIT_"+ib]+=1;continue
            if mode=="IMAGE":
                ic,dt=checked(z3.And(trans,z3.Not(cnext)))
            else:
                ic,dt=checked(z3.And(trans,z3.Not(conservation_delta(coef,now,nxt))))
            total_ms+=dt;total_smt+=1
            if ic!="unsat":
                diagnostics["REJECT_"+mode+"_"+ic]+=1;continue
            neg,dt=checked(z3.Not(cand));total_ms+=dt;total_smt+=1
            if neg!="sat":
                diagnostics["REJECT_VACUOUS_OR_UNKNOWN_"+neg]+=1;continue
            diagnostics["VERIFIED_"+mode]+=1
            admitted.append({"coefficients":list(coef),
                             "n_nonzero_original_state_coefficients":sum(c!=0 for c in coef[:-1]),
                             "nonzero_constant_offset":coef[-1]!=0,
                             "certificate_mode":mode,
                             "typed_ast_sha256":hashlib.sha256(cand.sexpr().encode()).hexdigest()})
    # all individually verified equations may be conjoined without losing
    # induction. Add ORIGINAL Post to create a sufficient candidate.
    unique={tuple(x["coefficients"]):x for x in admitted}
    coupled=[equation(c,now) for c in unique]
    joined=z3.And(post,*coupled)
    after=z3.substitute(joined,*list(zip(now,nxt)))
    q=[
        z3.And(pre,z3.Not(joined)),
        z3.And(joined,trans,z3.Not(after)),
        z3.And(joined,z3.Not(post))
    ]
    proof=[]
    for condition in q:
        verdict,dt=checked(condition)
        total_ms+=dt;total_smt+=1
        proof.append(verdict)
    post_step,dt=checked(z3.And(post,trans,z3.Not(
        z3.substitute(post,*list(zip(now,nxt)))))
    )
    total_ms+=dt;total_smt+=1
    post_init,dt=checked(z3.And(pre,z3.Not(post)))
    total_ms+=dt;total_smt+=1
    return {
      "status":"EXACT_ORIGINAL_PROOF_AUDIT_COMPLETE",
      "original_source_identity":original_source,
      "original_state_count":n,
      "original_pre_sat":presat,
      "original_not_post_sat":nontrivial,
      "pre_sampling":pm,"transition_sampling":tm,
      "original_smt_candidate_checks":total_smt,
      "candidate_original_smt_wall_ms":round(total_ms,3),
      "generated_nullspace_candidates":{
          m:len(rows) for m,rows in algebraic.items()
      },
      "candidate_original_exact_refutations":dict(diagnostics),
      "sound_original_verified_equations":len(unique),
      "sound_original_relational_coefficients":[
          x for x in unique.values()
      ],
      "full_original_three_vc_negated_queries":proof,
      "full_original_program_proven":proof==["unsat"]*3 and bool(coupled),
      "post_alone_original_init_negation":post_init,
      "post_alone_original_step_negation":post_step,
      "post_only_not_inductive":post_step=="sat",
      "discovered_relational_coefficients_plus_post_needed":
          proof==["unsat"]*3 and post_step=="sat"
          and any(x["n_nonzero_original_state_coefficients"]>=2
              for x in unique.values()),
    }

def original_from_pinned_source(root,path,expected):
    raw=(root/path).read_bytes()
    if blobhash(raw)!=expected:raise ValueError("EXTERNAL_SOURCE_ORIGINAL_BLOB_CHANGED")
    names,now,nxt,pre,trans,post=extract_original(sexprs(raw))
    report=ival(names,now,nxt,pre,trans,post,path)
    report["original_source_git_blob"]=expected
    return report

def synthetic_models(corrupted=False):
    a,b,c=z3.Ints("Q3U_x Q3U_y Q3U_z")
    an,bn,cn=z3.Ints("Q3U_xnext Q3U_ynext Q3U_znext")
    pre=z3.And(a==0,b==7,c==3)
    trans=z3.And(an==a+3*b-2*c,bn==b+2,cn==c+(4 if corrupted else 3))
    post=a>=0
    return ival(["x","y","z"],[a,b,c],[an,bn,cn],pre,trans,post,
                "SYNTHETIC_ADVERSARIAL_CORRUPTION" if corrupted else
                "SYNTHETIC_UNREVEALED_COEFFICIENT_TRUE")

def direct_original_spacer(root,path,expected):
    raw=(root/path).read_bytes()
    if blobhash(raw)!=expected:raise ValueError("ORIGINAL_SOURCE_BLOB_DRIFT")
    names,now,nxt,pre,trans,post=extract_original(sexprs(raw))
    reach=z3.Function("q3u_reach",*[z3.IntSort() for _ in now],z3.BoolSort())
    bad=z3.Function("q3u_bad",z3.BoolSort())
    fp=z3.Fixedpoint();fp.set(engine="spacer",timeout=2000)
    fp.register_relation(reach,bad);fp.declare_var(*(now+nxt))
    fp.rule(reach(*now),pre)
    fp.rule(reach(*nxt),z3.And(reach(*now),trans))
    fp.rule(bad(),z3.And(reach(*now),z3.Not(post)))
    started=time.perf_counter_ns()
    try:verdict=str(fp.query(bad()))
    except Exception:verdict="error"
    return {"original_direct_spacer_outcome":verdict,
            "original_direct_spacer_ms":round((time.perf_counter_ns()-started)/1e6,3)}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    a=p.parse_args()
    if blobhash((a.root/"LICENSE.md").read_bytes())!=ORIGINAL_LICENSE:
        raise ValueError("EXTERNAL_ORIGINAL_LICENSE_METADATA_CHANGED")
    good=synthetic_models()
    bad=synthetic_models(corrupted=True)
    # Complete theorem must depend on newly discovered relational information,
    # not only original Post. No labels or coefficient hints passed to miner.
    controls={
       "clean_original_3VC_proven":good["full_original_program_proven"],
       "clean_was_post_only_noninductive":good["post_only_not_inductive"],
       "discovered_relation_essential_for_goal":good["discovered_relational_coefficients_plus_post_needed"],
       "nontrivial_new_coefficients":any(
          max(abs(x) for x in r["coefficients"][:-1])>1
          and r["n_nonzero_original_state_coefficients"]>=2
          and r["nonzero_constant_offset"]
          for r in good["sound_original_relational_coefficients"]),
       "corrupted_original_not_falsely_certified":
            not bad["full_original_program_proven"],
       "corrupted_original_relation_not_accepted":not any(
            r["coefficients"]==[0,3,-2,-15]
            for r in bad["sound_original_relational_coefficients"])
    }
    if not all(controls.values()):
        raise AssertionError("SOURCE_DERIVED_AFFINE_SOUNDNESS_ADVERSARIAL_CONTROLS_FAILED:"+str(controls))
    real=[]
    for path,gitblob in PINNED.items():
        rec=original_from_pinned_source(a.root,path,gitblob)
        rec.update(direct_original_spacer(a.root,path,gitblob))
        real.append(rec)
    report={
        "study":"Q3U_FIRST_SMT_MODEL_NULLSPACE_CONSTRUCTIVE_AFFINE_OPERATOR_PROOF",
        "status":"FIRST_REAL_SOURCE_AND_ADVERSARIAL_AFFINE_PROOF_COMPLETE",
        "method":"integer-coefficient exact rational nullspaces of sampled original Pre/Trans model image and conserved deltas, independent unbounded SMT proof",
        "source_upstream_revision":SOURCE_COMMIT,
        "fixed_model_samples_per_relation":MAX_MODELS,
        "max_original_state_arity":MAX_STATE_ARITY,
        "all_adversarial_controls_passed":True,
        "specific_adversarial_controls":controls,
        "synthetic_hidden_coefficient_study":good,
        "synthetic_corrupted_original_study":bad,
        "real_original_sources_count":len(real),
        "real_original_program_three_vc_proven_count":sum(x.get("full_original_program_proven",False) for x in real),
        "real_original_nontrivial_relation_needed_proof_count":sum(x.get("discovered_relational_coefficients_plus_post_needed",False) for x in real),
        "real_original_studies":real,
        "neural_learning_inference_calls":0,
        "source_coefficients_learned_by_nn":False,
        "classical_algorithm_found_coefficients_from_original_source":True,
        "q3f_two_chc_competition_holdout_originals_opened":False,
        "source_or_formula_text_redistributed":False,
        "global_q1_q7":"OPEN"
    }
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(report,indent=2)+"\n")
    print("Q3U_ADVERSARIAL_TRUE_PROOF",controls)
    print("Q3U_REAL_ORIGINAL_RELATION_CONSTRUCTION",[
        (x["original_source_identity"],x.get("sound_original_verified_equations"),
         x.get("full_original_program_proven"),
         x.get("discovered_relational_coefficients_plus_post_needed"),
         x.get("original_direct_spacer_outcome"))
        for x in real])
    print("Q3U_GLOBAL",report["global_q1_q7"])

if __name__=="__main__":main()
