"""Exact original-source 3x3 magic-power linear structural skeleton.

Original SMT-LIB source A x^k = t constraints remain authentic.
Introduce Y_x=x^k as ONLY formal features; compute exact rational rowspace
and independently prove equality of original LINEAR-SKELETON and minimum
row-basis with Z3 and cvc5. All positive/distinct/nonlinear ORIGINAL
constraints remain original and are NOT claimed solved by this proof.

POSTHOC five previously opened actual original programs, no new blind count,
no neural training or novel row-reduction algorithm. Direct with same linear
algebra equals this module's structural capability.
"""
from __future__ import annotations
import argparse, fractions, json, subprocess, time
from pathlib import Path
import z3
from sympy import Matrix
from research.evidence.q3_power_feature_20261021.first_ten_unchanged_power_magic_original_unbounded_unsat import single_symbol_monomial
from research.evidence.g0_official_original_four_20261021.original_four_2026_union_smt_direct_recheck import git_blob_sha1,sha256

FIRST_OPENED_SOURCE_FREEZE="941ec4d16357cb9120490506e7c45cc60c76e74a"
SOURCE_UPSTREAM="81a39628827f61fbd74c6f3e67feb5c1b740d2f0"

def parse_true_source_linear_skeleton(source):
    assertions=list(source.assertions())
    recognized=[]
    all_powers=set()
    discarded=0
    for a in assertions:
        if not z3.is_eq(a):
            discarded+=1;continue
        left,right=a.children()
        good=None
        for form,target in ((left,right),(right,left)):
            if form.decl().kind()!=z3.Z3_OP_ADD:continue
            if target.num_args()!=0 or target.decl().kind()!=z3.Z3_OP_UNINTERPRETED:continue
            if target.sort().kind()!=z3.Z3_INT_SORT:continue
            monomials=[single_symbol_monomial(c) for c in form.children()]
            if len(monomials)<2 or any(m is None for m in monomials):
                continue
            if len({m["name"] for m in monomials})!=len(monomials):
                continue
            if len({m["exponent"] for m in monomials})!=1:
                continue
            good={"source_ast_sha256":sha256(a.sexpr().encode()),
                  "target":str(target),
                  "source_feature_cell_names":[m["name"] for m in monomials],
                  "source_feature_power_k":monomials[0]["exponent"],
                  "source_feature_mononomial_ast_sha256":[m["original_source_ast_sha256"] for m in monomials]}
            break
        if good is not None:
            recognized.append(good)
            all_powers.update((name,good["source_feature_power_k"]) for name in good["source_feature_cell_names"])
        else:discarded+=1
    targets={r["target"] for r in recognized}
    if len(targets)!=1 or len(all_powers)!=9 or len(recognized)<6:
        raise ValueError(f"SOURCE_NATIVE_3X3_SKELETON_INVALID sums={len(recognized)} powers={len(all_powers)} targets={targets}")
    name_target=next(iter(targets))
    feat=sorted(all_powers)
    column_names=[f"{name}^{k}" for name,k in feat]+[name_target]
    rows=[]
    for rr in recognized:
        powers={(n,rr["source_feature_power_k"]) for n in rr["source_feature_cell_names"]}
        rows.append([1 if f in powers else 0 for f in feat]+[-1])
    return {"assertion_count":len(assertions),
            "matched_source_sum_ast_count":len(recognized),
            "other_actual_original_conjuncts_not_discarded_from_FULL_TASK":discarded,
            "native_power_exponents":sorted({p[1] for p in feat}),
            "columns":column_names,
            "source_rows":recognized},rows

def frac_rank_exact(rows):
    a=[[fractions.Fraction(x) for x in row] for row in rows]
    rank=0;ncol=len(a[0])
    for col in range(ncol):
        pivot=next((i for i in range(rank,len(a)) if a[i][col]),None)
        if pivot is None:continue
        a[rank],a[pivot]=a[pivot],a[rank]
        q=a[rank][col];a[rank]=[v/q for v in a[rank]]
        for j in range(len(a)):
            if j==rank:continue
            q=a[j][col]
            if q:
                a[j]=[v-q*w for v,w in zip(a[j],a[rank])]
        rank+=1
        if rank==len(a):break
    return rank

def row_qflia(row,var_names):
    terms=[]
    for coefficient,name in zip(row,var_names):
        if coefficient==0:continue
        elif coefficient==1:terms.append(name)
        elif coefficient==-1:terms.append(f"(- {name})")
        else:terms.append(f"(* {coefficient} {name})")
    expr=terms[0] if len(terms)==1 else "(+ "+" ".join(terms)+")"
    return f"(= {expr} 0)"

def independent_source_rowspace_dual(rows,selected):
    """The selected basis must equal ALL rows over arbitrary integer formal
    feature variables. Z3 and cvc5 each show source skeleton basis∧¬original
    is UNSAT, not by assuming a proof claim.
    """
    ncol=len(rows[0]);v=[z3.Int(f"linear_feature_{i}") for i in range(ncol)]
    eqs=[z3.Sum(*[c*vv for c,vv in zip(row,v)])==0 for row in rows]
    valid=z3.Solver();valid.set(timeout=5000)
    valid.add(*[eqs[i] for i in selected])
    valid.add(z3.Not(z3.And(*eqs)))
    z3state=str(valid.check()).upper()
    names=[f"linear_feature_{i}" for i in range(ncol)]
    lines=["(set-logic QF_LIA)"]
    for name in names:lines.append("(declare-fun "+name+" () Int)")
    for i in selected:lines.append("(assert "+row_qflia(rows[i],names)+")")
    all_rels="(and "+" ".join(row_qflia(row,names) for row in rows)+")"
    lines.append("(assert (not "+all_rels+"))")
    lines+=["(check-sat)","(exit)"]
    text="\n".join(lines)+"\n"
    p=subprocess.run(["cvc5","--lang=smt2","--tlimit-per=5000","-"],
                     input=text,text=True,capture_output=True,timeout=7)
    found=[line.strip().upper() for line in p.stdout.splitlines()
           if line.strip().lower() in ("sat","unsat","unknown")]
    cvcstatus=found[0] if p.returncode==0 and found else "UNKNOWN"
    return {"z3":z3state,"cvc5":cvcstatus,
            "cvc5_exit":p.returncode,
            "both_actual_independent_skeleton_equivalence":z3state==cvcstatus=="UNSAT",
            "proof_original_exact_basis_to_all_QFLIA_sha256":sha256(text.encode()),
            "source_original_all_implies_basis_by_exact_subsetting":True,
            "this_is_NOT_a_full_original_QF_NIA_model_or_UNSAT_proof":True}

def independent_removed_necessary_row_negative(rows,selected):
    # Proper basis compression must not incorrectly certify arbitrary deletion
    # of an INDEPENDENT equation.
    n=len(rows[0]);v=[z3.Int(f"drop_feature_{i}") for i in range(n)]
    eqs=[z3.Sum(*[c*x for c,x in zip(row,v)])==0 for row in rows]
    tested=[]
    for dropped in selected[:min(len(selected),3)]:
        s=z3.Solver();s.set(timeout=4000)
        s.add(*[eqs[i] for i in selected if i!=dropped])
        s.add(z3.Not(eqs[dropped]))
        outcome=str(s.check()).upper()
        tested.append({"source_basis_index_removed":dropped,"independent_Z3_countermodel_SAT":outcome=="SAT"})
    return tested

def one_source(root,row,group):
    start=time.perf_counter_ns()
    out={"original_source":row["path"],"group":group,"true_source_authenticated":False,
         "linear_skeleton_dual_equivalent":False,"status":"ABSTAIN"}
    try:
        raw=(root/row["path"]).read_bytes()
        if len(raw)!=row["bytes"] or git_blob_sha1(raw)!=row["sha1_git_blob"]:
            raise RuntimeError("TRUE_ORIGINAL_GIT_SHA_OR_BYTES_CHANGED")
        out["true_source_authenticated"]=True
        out["original_sha256"]=sha256(raw)
        parse=z3.Solver();parse.from_string(raw.decode("utf-8"))
        spec,rows=parse_true_source_linear_skeleton(parse)
        out["source_true_linear_skeleton"]=spec
        full=Matrix(rows);rank=int(full.rank())
        assert frac_rank_exact(rows)==rank
        _,indices=full.T.rref()
        indices=list(indices)
        assert len(indices)==rank
        theorem=independent_source_rowspace_dual(rows,indices)
        out["dual_Z3_cvc5_exact_linear_equivalence"]=theorem
        out["linear_skeleton_dual_equivalent"]=theorem["both_actual_independent_skeleton_equivalence"]
        out["numeric_skeleton_rank"]=rank
        out["feature_variable_count_including_magic_target"]=len(rows[0])
        out["exact_rational_free_feature_dimensions"]=len(rows[0])-rank
        out["original_linear_equality_count"]=len(rows)
        out["rank_basis_eq_count"]=rank
        out["reduced_source_basis_rows_original_AST_SHA"]=[
            spec["source_rows"][i]["source_ast_sha256"] for i in indices]
        out["source_basis_row_indexes"]=indices
        negative=independent_removed_necessary_row_negative(rows,indices)
        out["positive_negative_geometry_controls"]=negative
        out["status"]="TRUE_ORIGINAL_LINEAR_SKELETON_EQUIVALENT_DUAL" if (
           out["linear_skeleton_dual_equivalent"] and all(
              x["independent_Z3_countermodel_SAT"] for x in negative)) else "ABSTAIN_PROOF_OR_NEGATIVE_CONTROL"
    except Exception as e:
        out["status"]="ABSTAIN_SOURCE_OR_THEOREM_ERROR"
        out["error"]=type(e).__name__+":"+str(e)[:420]
    out["entire_source_parse_rref_independent_two_solver_wall_ms"]=(time.perf_counter_ns()-start)/1e6
    print("Q3_ORIGINAL_3X3_EXACT_FEATURE_RANK",row["path"].split("/")[-1],
          "RANK",out.get("numeric_skeleton_rank"),
          "FREE",out.get("exact_rational_free_feature_dimensions"),
          "DUAL",out["linear_skeleton_dual_equivalent"],
          "STATUS",out["status"],"ERROR",out.get("error"),flush=True)
    return out

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,required=True)
    p.add_argument("--freeze",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    opts=p.parse_args()
    q=json.loads(opts.freeze.read_text())
    if q["schema"]!="neumann.q3.first_original_10_power_features_magic_semimagic_geometric_injective.v1" or q["source"].split("@")[-1]!=SOURCE_UPSTREAM:
        raise RuntimeError("PREVIOUS_ORIGINAL_GIT_SHA_IDENTITY_CHANGED")
    rows=[one_source(opts.root,c,"THREE_BY_THREE_POSTHOC") for c in q["five_original_3x3_controls"]]
    old=[one_source(opts.root,c,"TWO_BY_TWO_PRIOR_DEVELOPMENT") for c in q["two_previously_opened_development_controls"]]
    report={"schema":"neumann.q3.posthoc_real_original_3x3_exact_feature_rowspace_dual.v1",
            "source_corpus_first_sha_lock_from_previous_original_STUDY":FIRST_OPENED_SOURCE_FREEZE,
            "all_real_originals_previously_opened_NOT_new_unseen":True,
            "five_3x3_source_cases_kept":len(rows)==5,
            "five_3x3_original_SHA_verified":sum(x["true_source_authenticated"] for x in rows),
            "five_3x3_original_exact_linear_skeleton_dual_certified":sum(x["linear_skeleton_dual_equivalent"] for x in rows),
            "no_original_3x3_non_linear_SAT_or_UNSAT_status_claim":True,
            "classical_rref_can_be_direct_strongest_algorithm":True,
            "no_trained_neural_core_model_calls":True,
            "global_Q3":"OPEN","global_Q4":"OPEN","global_Q5":"OPEN",
            "five_real_3x3_source_proofs":rows,
            "prior_two_original_2x2_development_controls":old}
    opts.out.parent.mkdir(parents=True,exist_ok=True)
    opts.out.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print("Q3_TRUE_ORIGINAL_3X3_AUTHENTIC",report["five_3x3_original_SHA_verified"],"/5")
    print("Q3_TRUE_ORIGINAL_3X3_LINEAR_SKELETON_DUAL",report["five_3x3_original_exact_linear_skeleton_dual_certified"],"/5")
    print("Q3_TRUE_ORIGINAL_3X3_RANK_FREE",[(x.get("numeric_skeleton_rank"),x.get("exact_rational_free_feature_dimensions")) for x in rows])
    print("Q3_GLOBAL_Q3_Q4_OPEN",report["global_Q3"],report["global_Q4"])
if __name__=="__main__":
    main()
