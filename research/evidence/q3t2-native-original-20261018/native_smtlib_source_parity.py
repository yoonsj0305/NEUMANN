"""Q3T2 independent NATIVE Z3 SMT-LIB input parser vs Q3T typed source parser.

One formerly unsupported authentic source (now Q3T classical SAFE) is
re-read without editing any original define-fun or mathematical assertion.
Only SyGuS orchestration statements are omitted from *native SMT* input,
where synth-inv/check-synth are not valid SMT-LIB 2 commands.
"""
from __future__ import annotations
import argparse,hashlib,json,sys,time
from pathlib import Path
import z3

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/"q3t-mixed-original-20261018"))
from mixed_sygus_original import (
    extract_mixed_original,check_formula,check_cover,run_original,
    blobhash,sexprs,SPACER_TIMEOUT_MS
)

FIRST_Q3T_SHA256="9f267e16a3615126bf3d1003cd016af3d00b8bba41d14f98ae2fa68ca0acb52b"
SOURCE="benchmarks/LIA/others/pldi18_seahorn_Fig3.sl"
SOURCE_SHA1="223c65d07b2cff707cfb21a078c17f6841b30cad"
EXPECTED_UPSTREAM="6ac90265b11431c9477dfbd33e3e3380234c0499"
LIC_SHA="1e853cd500e1317b7c2ad0a2514b548c32c46f5e"

def emit_sexpr(value):
    if isinstance(value,str):
        # Parsed atoms are re-serialized unchanged, never edited.
        if not value or any(c.isspace() or c in "()" for c in value):
            raise ValueError("UNSAFE_SMT_ATOM_IN_NATIVE_SERIALIZATION")
        return value
    if not isinstance(value,list):
        raise ValueError("NON_SEXPR_FROM_ORIGINAL_SOURCE")
    return "("+" ".join(emit_sexpr(x) for x in value)+")"

def native_original_relations(forms,custom):
    originals=[x for x in forms if isinstance(x,list) and x and x[0] in ("set-logic","define-fun")]
    inv=[x for x in forms if isinstance(x,list) and x and x[0]=="inv-constraint"]
    if len(inv)!=1 or len(inv[0])!=5:
        raise ValueError("NOT_UNIQUE_ORIGINAL_INV_SPEC")
    pre,tr,post=inv[0][2:]
    declared_def_names={x[1] for x in originals if x[0]=="define-fun"}
    if not {pre,tr,post}<=declared_def_names:
        raise ValueError("NATIVE_SOURCE_MISSING_ORIGINAL_DEFINITIONS")
    intro="\n".join(emit_sexpr(f) for f in originals)+"\n"
    now=custom["now"];nxt=custom["next"]
    full_vars=now+nxt
    declarations="\n".join(
        "(declare-const "+str(v)+" "+v.sort().name()+")"
        for v in full_vars
    )+"\n"
    script=intro+declarations
    def call(name,args):
        return "("+name+" "+" ".join(str(x) for x in args)+")"
    refs={
       "pre":call(pre,now),
       "trans":call(tr,full_vars),
       "post":call(post,now)
    }
    result={}
    for kind,expr in refs.items():
        # This is Z3's own NATIVE SMT-LIB source parser, not the handwritten
        # recursive Q3T term compiler. All actual define-fun bodies preserved.
        parse=z3.parse_smt2_string(script+"(assert "+expr+")")
        if len(parse)!=1:raise ValueError("NATIVE_PARSE_NOT_ONE_ORIGINAL_ASSERTION")
        result[kind]=parse[0]
        if not z3.is_bool(result[kind]):
            raise ValueError("NATIVE_SOURCE_RELATION_NONBOOLEAN")
    return result

def independent_native_bad_query(relations,state,nxt):
    reach=z3.Function(
        "q3t2_native_reach",
        *[v.sort() for v in state],
        z3.BoolSort()
    )
    bad=z3.Function("q3t2_native_bad",z3.BoolSort())
    fp=z3.Fixedpoint()
    fp.set(engine="spacer",timeout=SPACER_TIMEOUT_MS)
    fp.register_relation(reach,bad)
    fp.declare_var(*(state+nxt))
    fp.rule(reach(*state),relations["pre"])
    fp.rule(reach(*nxt),z3.And(reach(*state),relations["trans"]))
    fp.rule(bad(),z3.And(reach(*state),z3.Not(relations["post"])))
    start=time.perf_counter_ns()
    try:
        verdict=str(fp.query(bad()))
        reason=fp.reason_unknown() if verdict=="unknown" else None
    except Exception as exc:
        verdict="error";reason=type(exc).__name__+":"+str(exc)[:150]
    return {"status":verdict,"reason":reason,
        "native_solver_wall_ms":round((time.perf_counter_ns()-start)/1e6,3)}

def run(root,firstfile):
    raw_first=firstfile.read_bytes()
    if hashlib.sha256(raw_first).hexdigest()!=FIRST_Q3T_SHA256:
        raise ValueError("FIRST_Q3T_RECEIPT_SHA_DRIFT")
    old=json.loads(raw_first)
    matching=[x for x in old["first_original_file_receipts"] if x["source_path"]==SOURCE]
    if len(matching)!=1 or old["original_source_count"]!=10:
        raise ValueError("FIRST_Q3T_ORIGINAL_GROUP_IDENTITY_CHANGED")
    first=matching[0]
    if not (first.get("original_direct_safety_proven")
            and first.get("original_proof_carried_typed_ast")
            and first["original_source_git_blob"]==SOURCE_SHA1):
        raise ValueError("FIRST_MIXED_SOURCE_ORIGINAL_CERTIFICATE_UNEXPECTED")
    if blobhash((root/"LICENSE.md").read_bytes())!=LIC_SHA:
        raise ValueError("ORIGINAL_REPOSITORY_LICENSE_CHANGED")
    raw=(root/SOURCE).read_bytes()
    if blobhash(raw)!=SOURCE_SHA1:
        raise ValueError("SOURCE_EXACT_ORIGINAL_GIT_BLOB_CHANGED")
    forms=sexprs(raw)
    custom=extract_mixed_original(forms)
    native=native_original_relations(forms,custom)
    parity={}
    for key in ("pre","trans","post"):
        same=z3.Xor(custom[key],native[key])
        parity[key]=check_formula(same)
    corruption=check_formula(z3.Xor(native["pre"],z3.Not(custom["pre"])))
    pre_sat=check_formula(native["pre"])
    not_post_sat=check_formula(z3.Not(native["post"]))
    proof=independent_native_bad_query(native,custom["now"],custom["next"])
    if not all(parity[key]=="unsat" for key in ("pre","trans","post")):
        raise ValueError("ORIGINAL_SOURCE_NATIVE_PARSER_SEMANTICS_MISMATCH")
    if corruption!="sat":
        raise ValueError("NATIVE_NEGATIVE_PARSER_DIFFERENCE_CONTROL_FAILED")
    if pre_sat!="sat" or not_post_sat!="sat":
        raise ValueError("ORIGINAL_PROGRAM_VACUOUS_OR_UNKNOWN")
    if proof["status"]!="unsat":
        raise ValueError("NATIVE_DIRECT_ORIGINAL_SAFETY_NOT_ESTABLISHED")
    # Original cover reconstructed from actual Q3T style direct source
    # rules. Then *NATIVE* source relations certify the resulting lemma.
    rel=z3.Function("q3t2_custom_extract",*[v.sort() for v in custom["now"]],z3.BoolSort())
    goal=z3.Function("q3t2_custom_goal",z3.BoolSort())
    fp=z3.Fixedpoint();fp.set(engine="spacer",timeout=SPACER_TIMEOUT_MS)
    fp.register_relation(rel,goal)
    fp.declare_var(*(custom["now"]+custom["next"]))
    fp.rule(rel(*custom["now"]),custom["pre"])
    fp.rule(rel(*custom["next"]),z3.And(rel(*custom["now"]),custom["trans"]))
    fp.rule(goal(),z3.And(rel(*custom["now"]),z3.Not(custom["post"])))
    if str(fp.query(goal()))!="unsat":
        raise ValueError("ORIGINAL_CUSTOM_PROOF_REGRESSION")
    mixed_native={"now":custom["now"],"next":custom["next"],**native}
    covers=[]
    try:
        cover=fp.get_cover_delta(-1,rel)
        for name,bindings in [
           ("FORWARD",custom["now"]),
           ("REVERSED",list(reversed(custom["now"]))),
        ]:
            try:
                candidate=z3.substitute_vars(cover,*bindings)
                result=check_cover(candidate,mixed_native)
                result["binding"]=name
                if result.get("status")=="ORIGINAL_FULL_3VC_CERTIFIED":
                    covers.append(result)
            except z3.Z3Exception:
                # Original mixed Int/Bool relation binders cannot be reversed
                # when that violates their sorts. Explicitly reject this
                # counterfactual order; never downgrade genuine forward proof.
                continue
    except Exception as exc:
        raise ValueError("FAILED_TO_NATIVE_RECERTIFY_SOURCE_ORIGINAL_INVARIANT:"+type(exc).__name__) from exc
    if not covers:raise ValueError("NATIVE_PARSER_ORIGINAL_3VC_INVARIANT_NOT_PROVEN")
    return {
      "study":"Q3T2_INDEPENDENT_NATIVE_SMTLIB_SOURCE_PARSER_ORIGINAL_SYGUS_PROOF",
      "status":"ONE_AUTHENTIC_MIXED_INT_BOOL_SOURCE_NATIVE_SEMANTIC_PARITY_AND_3VC_PROVEN",
      "source_path":SOURCE,
      "source_git_blob":SOURCE_SHA1,
      "first_q3t_raw_receipt_sha256":FIRST_Q3T_SHA256,
      "original_int_state_vars":custom["num_int"],
      "original_bool_state_vars":custom["num_bool"],
      "independently_native_parsed_pre_trans_post_xor":parity,
      "intentionally_negated_pre_semantic_control":corruption,
      "native_original_pre_sat":pre_sat,
      "native_original_not_post_sat":not_post_sat,
      "native_direct_spacer_original_proof":proof,
      "native_source_original_3vc_proven_cover_count":len(covers),
      "native_source_original_3vc_proven_cover_certificates":covers,
      "native_parser_is_different_implementation_from_custom_compiler":True,
      "solver_backend_is_same_Z3_not_independent_theorem_provers":True,
      "new_neural_model_training_or_inference":0,
      "original_source_code_or_generated_formula_republished":False,
      "q3f_two_sealed_chc_benchmarks_opened":False,
      "global_q1_q7":"OPEN"
    }

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,required=True)
    p.add_argument("--q3t-first",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    result=run(args.root,args.q3t_first)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2)+"\n")
    print("Q3T2_SOURCE_PARSER_PARITY",result["independently_native_parsed_pre_trans_post_xor"])
    print("Q3T2_ORIGINAL_NATIVE_DIRECT",result["native_direct_spacer_original_proof"])
    print("Q3T2_NATIVE_TYPED_ORIGINAL_3VC_COVERS",result["native_source_original_3vc_proven_cover_count"])
    print("Q3T2_Q1_Q7",result["global_q1_q7"])
