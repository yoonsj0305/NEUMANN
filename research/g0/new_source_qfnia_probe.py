"""G0 first-use, hash-selected source cohort; REUSES frozen previously proven classical tools.
Scientific aim: original-headroom screening, NOT novel neural Q3. All rows preserved.
See docs/research/G0_FRESH_QFNIA_20261023.md for provenance and gates.
"""
import argparse,collections,hashlib,json,pathlib,sys,time
import z3

PIN="7f993a017850ba547c6ea19a1bf3b54adf54a449"
FAMILY="non-incremental/QF_NIA/20230328-sqrtmodinv-hoenicke"
FIRST_N=8

def sha(b):return hashlib.sha256(b).hexdigest()

def choose_without_reading(root):
    files=sorted((root/FAMILY).rglob("*.smt2"))
    order=sorted(files,key=lambda p: (sha(p.relative_to(root).as_posix().encode()),p.as_posix()))
    assert len(order)>0,"FROZEN_SOURCE_FAMILY_EMPTY"
    # No filename-based numeric/semantic heuristics; fixed deterministic cap.
    return order[:FIRST_N],len(order)

def structural_proof(s,raw,sourcepath,prior):
    begun=time.perf_counter()
    out={"status":"UNKNOWN","reason":"NO_FULL_ORIGINAL_MODULAR_CERTIFICATE"}
    try:
        expressions=prior.source_asserts(raw.decode("utf-8"))
        # Sound: only conjunction operands of actual source assert forms are required.
        candidates=[]
        for root in expressions:
            for required in prior.required(root):
                try:c=prior.required_negative_mod_eq_zero(required)
                except (ValueError,IndexError):continue
                if c is not None:candidates.append(c)
        out["candidate_count"]=len(candidates)
        for c in candidates:
            residues=prior.demonstrate_modular_identity(c)
            if any(residues):continue
            # A sound congruence theorem covers *every integer*, also negative.
            original=prior.verify_source_unsat_from_proven_identity(sourcepath,c)
            if not original["original_plus_proved_congruence_unsat"]:continue
            out={"status":"CERTIFIED_ORIGINAL_UNSAT_BY_UNIVERSAL_CONGRUENCE",
                 "candidate_count":len(candidates),"modulus":c["modulus"],
                 "coefficient_by_degree":{str(k):v for k,v in c["coefficient_by_degree"].items()},
                 "residue_count":len(residues),"every_residue_zero":True,
                 "independent_original_full_Z3_plus_proved_lemma":original,
                 "only_classical_proof":True}
            break
    except Exception as e:
        out["status"]="UNKNOWN_UNSUPPORTED_OR_PARSE"
        out["error"]=type(e).__name__+":"+str(e)[:220]
    out["proof_cpu_wall_s"]=time.perf_counter()-begun
    return out

def run(args):
    import exact_original_modular_unsat as prior
    import original_four_2026_union_smt_direct_recheck as specialist
    specialist.Z3_TIMEOUT_MS=5000
    specialist.CVC5_TIMEOUT_MS=5000
    root=pathlib.Path(args.source_root)
    files,cohort_size=choose_without_reading(root)
    paths=[p.relative_to(root).as_posix() for p in files]
    metadata_hash=sha(("\n".join(paths)+"\n").encode())
    print("COHORT_FROZEN_METADATA_BEFORE_CONTENT",json.dumps({
        "family":FAMILY,"source_repo_pin":PIN,"all_file_count":cohort_size,
        "chosen_count":len(paths),"sha256_of_selected_paths":metadata_hash,"paths":paths}),flush=True)
    # Source bodies only touched AFTER above metadata registration.
    records=[]
    for path in files:
        uid=path.relative_to(root).as_posix()
        r={"source_path":uid,"all_results_included":True}
        start=time.perf_counter()
        try:
            b=path.read_bytes()
            r["source_SHA256"]=sha(b)
            r["source_size_bytes"]=len(b)
            strong_z,s= specialist.z3_original_direct(b)
            strong_c= specialist.cvc5_original_direct(path)
            r["strong_Z3"] = strong_z
            r["strong_cvc5"] = strong_c
            # Original full assertion read via separate verified Z3 parser
            check=z3.Solver()
            check.from_file(str(path))
            r["original_assertion_count"]=len(check.assertions())
            if not check.assertions():raise RuntimeError("ORIGINAL_EMPTY")
            r["structural_classical"]=structural_proof(check,b,path,prior)
        except Exception as e:
            r["error"]=type(e).__name__+":"+str(e)[:220]
            r["structural_classical"]={"status":"UNKNOWN_EXECUTION_ERROR"}
        r["total_case_wall_s"]=time.perf_counter()-start
        records.append(r)
        print("G0_FROZEN_CASE",json.dumps({
            "source":uid,"z3":r.get("strong_Z3",{}).get("status"),
            "cvc5":r.get("strong_cvc5",{}).get("status"),
            "source_driven":r["structural_classical"]["status"],
            "full_wall_s":r["total_case_wall_s"]},sort_keys=True),flush=True)
    n=collections.Counter()
    for r in records:
        n["all_originals"]+=1
        z=r.get("strong_Z3",{}).get("status")
        c=r.get("strong_cvc5",{}).get("status")
        if z=="UNSAT" and c=="UNSAT":n["both_direct_UNSAT"]+=1
        if z=="SAT" and c=="SAT":n["both_direct_SAT_unverified"]+=1
        if r["structural_classical"]["status"]=="CERTIFIED_ORIGINAL_UNSAT_BY_UNIVERSAL_CONGRUENCE":
            n["original_UNSAT_structurally_proved"]+=1
            if z!="UNSAT" and c!="UNSAT":n["structurally_proved_but_both_direct_not_UNSAT_with_5s_cap"]+=1
        if "error" in r:n["execution_or_source_error"]+=1
    decision=("SCOPED_CLASSICAL_REPRESENTATION_HEADROOM_VS_5S_DIRECT_ONLY"
              if n["structurally_proved_but_both_direct_not_UNSAT_with_5s_cap"]
              else "NO_CLASSICAL_REPRESENTATION_HEADROOM_DEMONSTRATED")
    report={
        "schema":"NEUMANN_G0_QFNIA_SQRTMODINV_SOURCE_BLIND_CLASSICAL_REPLAY.v1",
        "source_family":FAMILY,"source_sha_revision":PIN,
        "metadata_only_selection":"first 8 sha256-order paths (or all if <8)",
        "metadata_cohort_sha256":metadata_hash,"selected_count":len(files),
        "selected_paths":paths,"counts":dict(n),"cases":records,"decision":decision,
        "prior_classical_structural_algorithm_frozen":True,
        "actual_new_learned_semantic_operator":"NOT_TESTED",
        "matched_specialist_portfolio_incomplete":True,
        "G0_admit_learning":"HOLD_UNTIL_SPECIALIST_PORTFOLIO_AND_ALL_COST",
        "global_Q1_Q7":"OPEN","never_invented_oracle_answer":True,
        "source_proof_no_label_access":True,
        "total_full_system_10x":"NOT_PROVED"}
    path=pathlib.Path(args.out)
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(report,sort_keys=True,indent=2)+"\n")
    print("G0_FIRST_ORIGINAL_FRESH_COHORT_DECISION",json.dumps({
        "decision":decision,"counts":dict(n),"sha256":sha(path.read_bytes())},sort_keys=True),flush=True)

if __name__=="__main__":
    a=argparse.ArgumentParser()
    a.add_argument("--source-root",required=True)
    a.add_argument("--out",required=True)
    run(a.parse_args())
