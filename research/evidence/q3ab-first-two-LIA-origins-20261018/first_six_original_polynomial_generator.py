"""Q3AB: frozen Q3Z exact structural relation generator, first TWO LIA source origins.
Q3Z theorem code unchanged; only NEW fully path-selected original source cohort.
Preregistered issue #235 before source-body access, no tuning after results.
This is classical out-of-fixed-candidate-grammar construction, NOT trained Q3.
"""
import argparse,collections,hashlib,importlib.util,json,subprocess,sys,time
from pathlib import Path

PREREG="https://github.com/yoonsj0305/NEUMANN/issues/235"
UPSTREAM="6ac90265b11431c9477dfbd33e3e3380234c0499"
EXPECTED_Q3Z_GIT_BLOB="869271c35fad857ebd7889291bfe1c74e0ca59fc"
FAMILIES=[
 "benchmarks/LIA/Lustre",
 "benchmarks/LIA/others",
]
EACH=3
ROOT_CODE=Path(__file__).resolve().parents[1]/"q3z-polynomial-20261018"/"first_polynomial_original.py"

def pinned_import():
    assert ROOT_CODE.is_file(),"FROZEN_Q3Z_CODE_NOT_PRESENT"
    r=subprocess.run(["git","hash-object",str(ROOT_CODE)],
      check=True,capture_output=True,text=True,timeout=8)
    if r.stdout.strip()!=EXPECTED_Q3Z_GIT_BLOB:
        raise RuntimeError("EXACT_FROZEN_Q3Z_GIT_BLOB_CHANGED")
    spec=importlib.util.spec_from_file_location("frozen_q3ab_original_q3z",str(ROOT_CODE))
    mod=importlib.util.module_from_spec(spec)
    sys.modules[spec.name]=mod;spec.loader.exec_module(mod)
    return mod

def run(root,out):
    begin=time.perf_counter()
    data={"experiment":"Q3AB_FROZEN_NON_NIA_SOURCE_CONDITIONED_POLYNOMIAL_PROPOSAL",
      "status":"Q3AB_FIRST_NOT_COMPLETE",
      "registration":PREREG,
      "source_git":UPSTREAM,
      "generator_git_blob_sha1":EXPECTED_Q3Z_GIT_BLOB,
      "cohort_rule":"original external LIA/Lustre and LIA/others, alphabetical first 3 .sl per group; no source-based re-selection",
      "source_body_unread_when_algorithm_frozen":True,
      "no_training":True,"no_neural_forwards":True,"no_gold_proof_or_sygus_solution":True,
      "GLOBAL_Q3":"OPEN","GLOBAL_Q1_Q7":"OPEN",
      "groups":FAMILIES,"manifest":[],"cases":[]}
    def save():
        out.parent.mkdir(parents=True,exist_ok=True)
        out.write_text(json.dumps(data,indent=2,sort_keys=True)+"\n")
    save()
    try:
        q3z=pinned_import()
        entries=[]
        for group in FAMILIES:
            d=root/group
            if not d.is_dir():raise RuntimeError("FROZEN_GROUP_MISSING:"+group)
            files=sorted((p for p in d.iterdir() if p.is_file() and p.suffix==".sl"),
                         key=lambda x:x.name)
            if len(files)<EACH:raise RuntimeError("UNEXPECTED_ORIGINAL_GROUP_TOO_SMALL")
            selected=files[:EACH]
            for p in selected:
                raw=p.read_bytes()
                row={"original_path":p.relative_to(root).as_posix(),
                     "origin_group":group,
                     "git_blob":q3z.core.blobhash(raw),
                     "original_sha256":hashlib.sha256(raw).hexdigest(),
                     "original_size_bytes":len(raw)}
                data["manifest"].append(row)
                entries.append((group,p,row))
        if len(entries)!=6 or len({x["original_sha256"] for x in data["manifest"]})!=6:
            raise RuntimeError("WRONG_EXACT_PROSPECTIVE_ORIGINAL_COHORT")
        save()
        for group,path,meta in entries:
            rec=q3z.case(root,path,"Q3AB_SOURCE_BODY_UNSEEN_OTHER_LIA_ORIGIN")
            if rec.get("source_git_blob")!=meta["git_blob"]:
                raise RuntimeError("ORIGINAL_SOURCE_CHANGED_DURING_RUN")
            if rec.get("new_original_proof_beyond_source_post"):
                if rec.get("original_pre_sat")!="sat" or rec.get("original_not_post_sat")!="sat":
                    raise RuntimeError("VACUOUS_ORIGINAL_RESULT_REJECTED")
                if sorted(rec.get("independent_original_source_native_xor",{}).values())!=["unsat"]*3:
                    raise RuntimeError("ORIGINAL_NATIVE_PARITY_NOT_PROVEN")
                if rec.get("original_transition_affine_graph_implied_by_source") is not True:
                    raise RuntimeError("MATHEMATICAL_TRANSITION_NOT_ORIGINAL_CERTIFIED")
                if not any(v.get("original_vcs")==["unsat"]*3 for v in
                           rec["candidate_mode_results"].values()):
                    raise RuntimeError("ORIGINAL_3VC_NOT_INDEPENDENTLY_PROVEN")
                if rec["original_post_only_three_vcs"]==["unsat"]*3:
                    raise RuntimeError("NOT_GENUINELY_BEYOND_SOURCE_POST")
            data["cases"].append(rec);save()
        sums={}
        for group in FAMILIES:
            rows=[q for q in data["cases"] if q["original_path"].startswith(group+"/")]
            sums[group]={"total_originals":len(rows),
              "full_original_3vc_proofs_beyond_post":sum(x.get("new_original_proof_beyond_source_post",False) for x in rows),
              "all_original_3vc_proofs":sum(x.get("any_full_original_three_vc",False) for x in rows),
              "abstains":sum(x["status"]=="ABSTAIN_NO_CERTIFIED_ORIGINAL_THEOREM" for x in rows),
              "by_abstain_reason":dict(collections.Counter(
                 x.get("reason_category","") for x in rows if x["status"]=="ABSTAIN_NO_CERTIFIED_ORIGINAL_THEOREM"))}
        group_pass=sum(v["full_original_3vc_proofs_beyond_post"]>0 for v in sums.values())
        data["summary"]={"each_group":sums,"new_original_source_groups_with_proofs":group_pass,
          "two_group_registered_structure_generation":"PASS" if group_pass==2 else "FAIL",
          "no_neural_model_learned_new_relation":True,
          "this_is_an_executed_cross_source_classical_algorithm_gate_only":True,
          "global_q3":"OPEN"}
        data["status"]="Q3AB_FIRST_SIX_AUTHENTIC_ORIGINAL_EXACT_PROOF_STUDY_COMPLETE"
        data["total_elapsed_wall_s_excluding_setup"]=round(time.perf_counter()-begin,6)
        save()
        print("Q3AB_FROZEN_FIRST_TWO_SOURCE_ORIGIN_VERDICT",json.dumps(data["summary"],sort_keys=True),flush=True)
    except Exception as ex:
        data["status"]="Q3AB_FIRST_EXECUTION_FAILED_OR_BLOCKED"
        data["failure"]=type(ex).__name__+":"+str(ex)[:250]
        save();raise

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--root",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    a=p.parse_args()
    run(a.root,a.out)
