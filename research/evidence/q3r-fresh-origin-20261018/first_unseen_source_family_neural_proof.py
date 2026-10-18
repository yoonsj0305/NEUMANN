"""Q3R FIRST genuinely previously uninspected origin-group SyGuS proof test.

Recreate EXACT Q3Q train-side neural construction procedure; hold model fixed
before reading any newly selected original program body. Evaluate predeclared
fresh first three source origin groups excluded from all Q3P/Q3Q 56 files.

Full ORIGINAL Pre/Trans/Post 3 VCs, Post-only source control and
matched neural untrained/static, strongest classical ALL grammar + SPACER.
No source-specific tuning, source text export or CHC-COMP Q3F leakage.
"""
from __future__ import annotations
import argparse,collections,hashlib,json,re,sys,time,random
from pathlib import Path
import torch
from torch import nn
import z3
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/"q3q-learned-atom-assembly-20261018"))
sys.path.insert(0,str(HERE.parent/"q3p-trained-typed-20261018"))
sys.path.insert(0,str(HERE.parent/"q3o-real-sygus-20261018"))

from first_constructive_learner import (
    K_ATOMS, MAX_ATOMS,TRAIN_EPOCHS,EVAL_VC_MS,source_atoms,
    valid_teacher_labels,atom_feature,join_houdini
)
from first_trained_typed_proposer import (
    SEED,load_specs,extract_template,proof_vc,direct_original_proof,
    Scorer,EXPECTED_LICENSE_BLOB,blobhash
)
from first_two_originals import extract_original,sexprs

ORIGINAL_FIRST_Q3Q_SHA="cc921c0f08fd9c16ea4fa6e6a9a34eae4365f619b6e28fea5c88f2926b6c9521"
UPSTREAM="6ac90265b11431c9477dfbd33e3e3380234c0499"
NEW_FAMILIES=3
FILES_PER_FAMILY=8
SMT_MS=3000
PROVEN="ALL_THREE_ORIGINAL_VCS_UNSAT_NONTRIVIAL"

def sat_status(q,timeout_ms=SMT_MS):
    sol=z3.Solver();sol.set(timeout=timeout_ms);sol.add(q)
    try:return str(sol.check())
    except Exception:return "error"

def choose_fresh_paths(root,old_specs):
    """File path selection ONLY; zero benchmark source bodies read here."""
    old_groups={s["group"] for s in old_specs}
    old_paths={s["path"] for s in old_specs}
    grouped=collections.defaultdict(list)
    for p in (root/"benchmarks"/"LIA").rglob("*.sl"):
        relative=p.relative_to(root).as_posix()
        parts=p.relative_to(root).parts
        if len(parts)<4:continue
        family="/".join(parts[:3])
        if family in old_groups:continue
        if relative in old_paths:raise ValueError("PREVIOUSLY_OPENED_SOURCE_IN_FRESH_GROUP")
        grouped[family].append(p)
    available=sorted(k for k,v in grouped.items() if len(v)>=2)
    selected_families=available[:NEW_FAMILIES]
    paths=[p for g in selected_families
           for p in sorted(grouped[g],key=lambda q:q.relative_to(root).as_posix())[:FILES_PER_FAMILY]]
    if not paths:raise ValueError("NO_ACTUALLY_FRESH_LIA_ORIGIN_FAMILY_FOUND")
    return paths,selected_families,len(available),sorted(old_groups)

def original_spec(path,root,number,old_source_identities):
    data=path.read_bytes()
    sha=blobhash(data)
    if sha in old_source_identities:
        raise ValueError("EXACT_OLD_56_SOURCE_BYTES_REUSED_IN_FRESH_TEST")
    rel=path.relative_to(root).as_posix()
    grp="/".join(path.relative_to(root).parts[:3])
    row={"path":rel,"source_sha":sha,"group":grp,"number":number,
         "split":"NEVER_BEFORE_USED_FAMILY_TEST","logic":"LIA"}
    try:
        names,now,nxt,pre,trans,post=extract_original(sexprs(data))
        pre_check=sat_status(pre,1500)
        row.update({"names":names,"variables":len(names),"now":now,"next":nxt,
                    "pre":pre,"trans":trans,"post":post,
                    "original_formulas":(pre,trans,post),
                    "syntactic_size":sum(len(x.sexpr()) for x in (pre,trans,post)),
                    "input_precondition_sat":pre_check,"parse_status":"OK"})
    except Exception as exc:
        row["parse_status"]="ABSTAIN"
        row["original_parse_rejection_type"]=type(exc).__name__
    return row

def restore_original_teacher(spec,template):
    slots=[z3.Int("Q3P_CANONICAL_SLOT_"+str(i)) for i in range(len(spec["now"]))]
    return z3.substitute(template["canonical"],*list(zip(slots,spec["now"])))

def freeze_same_neural_training(sources,first):
    """Exactly same train only as Q3Q first. Fail-closed on receipt mismatch."""
    random.seed(SEED);torch.manual_seed(SEED);torch.set_num_threads(2)
    train=[s for s in sources if s["split"]=="TRAIN" and s["parse_status"]=="OK"
           and s["input_precondition_sat"]=="sat"]
    raw_features=[];train_labels=[]
    teachers=[]
    start=time.perf_counter_ns()
    for spec in train:
        template,_=extract_template(spec)
        if template is None:continue
        teacher=restore_original_teacher(spec,template)
        if proof_vc(teacher,spec,EVAL_VC_MS)[0]!="ALL_THREE_ORIGINAL_VCS_UNSAT":
            raise ValueError("FROZEN_TRAIN_TEACHER_ORIGINAL_THEOREM_CHANGED")
        atom_list,_=source_atoms(spec)
        pairs,unknown=valid_teacher_labels(spec,atom_list,teacher)
        teachers.append({"original_sha":spec["source_sha"],
                         "candidate_atoms":len(atom_list),
                         "original_label_pairs":len(pairs),
                         "positive":sum(x for _,x in pairs),
                         "uncertain":unknown})
        for atom,target in pairs:
            raw_features.append(atom_feature(spec,atom))
            train_labels.append(target)
    teacher_ms=(time.perf_counter_ns()-start)/1e6
    n=len(train_labels)
    positives=sum(train_labels)
    if n!=first["training_atom_labels"]["total"] or positives!=first["training_atom_labels"]["positive"]:
        raise ValueError("FIRST_Q3Q_ATOM_TRAIN_LABEL_COUNTS_CHANGED")
    if (n,positives)!=(1247,56):
        raise ValueError("FROZEN_Q3Q_EXPECTED_EXACT_LABEL_IDENTITY_CHANGED")
    x=torch.tensor(raw_features,dtype=torch.float32)
    y=torch.tensor(train_labels,dtype=torch.float32)
    model=Scorer();zero=Scorer()
    zero.load_state_dict(model.state_dict())
    if sum(p.numel() for p in model.parameters())!=1633:
        raise ValueError("FIRST_Q3Q_NEURAL_ARCHITECTURE_CHANGED")
    weight=max(1.,(n-positives)/positives)
    loss_fn=nn.BCEWithLogitsLoss(pos_weight=torch.tensor(weight))
    opt=torch.optim.AdamW(model.parameters(),lr=0.008,weight_decay=0.0001)
    trainstart=time.perf_counter_ns()
    losses=[]
    for epoch in range(TRAIN_EPOCHS):
        model.train(); logits=model(x); loss=loss_fn(logits,y)
        opt.zero_grad();loss.backward();opt.step()
        if epoch in (0,TRAIN_EPOCHS-1):losses.append(round(float(loss.item()),6))
    neural_train_ms=(time.perf_counter_ns()-trainstart)/1e6
    if any(abs(a-b)>0.0001 for a,b in zip(losses,first["learned_loss_first_last"])):
        raise ValueError("FROZEN_LEARNED_MODEL_LOSS_REPLAY_MISMATCH")
    model.eval();zero.eval()
    return model,zero,{
        "train_original_count":len(train),
        "train_teacher_receipts":teachers,
        "teacher_classical_generation_ms":round(teacher_ms,3),
        "training_neural_ms":round(neural_train_ms,3),
        "train_atom_examples":n,
        "train_true_labels":positives,
        "first_final_losses":losses,
        "learned_parameters":1633,
        "original_first_training_replayed_exactly":True
    }

def evaluate(spec,learned,initial):
    result={
       "source_path":spec["path"],"source_sha":spec["source_sha"],
       "source_origin":spec["group"],"source_family_fresh":True,
       "original_parse_status":spec["parse_status"],
       "original_pre_sat":spec.get("input_precondition_sat"),
       "source_text_or_formula_exported":False
    }
    if spec["parse_status"]!="OK" or spec["input_precondition_sat"]!="sat":
        result["status"]="ABSTAIN_UNSUPPORTED_ORIGINAL_OR_EMPTY_PRE"
        return result
    if sat_status(z3.Not(spec["post"]))!="sat":
        result["status"]="ABSTAIN_TRIVIAL_OR_UNKNOWN_POST"
        return result
    atoms,constants=source_atoms(spec)
    if not atoms:
        result["status"]="NO_SOURCE_TYPED_CONSTRUCTIBLE_ATOMS"
        return result
    if len(atoms)>MAX_ATOMS:raise ValueError("CANDIDATE_CAP_BREACH")
    result["source_original_typed_atom_count"]=len(atoms)
    result["source_only_constants"]=len(constants)
    feats=torch.tensor([atom_feature(spec,a) for a in atoms],dtype=torch.float32)
    time0=time.perf_counter_ns()
    with torch.no_grad():
        ls=learned(feats).tolist()
        zs=initial(feats).tolist()
    result["all_neural_forward_ms"]=round((time.perf_counter_ns()-time0)/1e6,3)
    choices={
      "LEARNED_TOP12":sorted(range(len(atoms)),key=lambda i:(-ls[i],atoms[i]["sha"]))[:K_ATOMS],
      "UNTRAINED_TOP12":sorted(range(len(atoms)),key=lambda i:(-zs[i],atoms[i]["sha"]))[:K_ATOMS],
      "STATIC_TOP12":sorted(range(len(atoms)),key=lambda i:atoms[i]["sha"])[:K_ATOMS],
      "CLASSICAL_ALL_GRAMMAR":list(range(len(atoms)))
    }
    result["original_methods"]={}
    for name,indices in choices.items():
        proof=join_houdini(spec,[atoms[i] for i in indices])
        result["original_methods"][name]=proof
    post_start=time.perf_counter_ns()
    pstatus,pcalls=proof_vc(spec["post"],spec,EVAL_VC_MS)
    result["source_post_only_original_3VC_verdict"]=pstatus
    result["source_post_only_ms"]=round((time.perf_counter_ns()-post_start)/1e6,3)
    result["source_post_only_vcs_executed"]=pcalls
    _,_,cp,why,wall=direct_original_proof(spec)
    result["strong_direct_original_SPACER_bad_state"]=cp
    result["strong_direct_original_SPACER_reason"]=why
    result["strong_direct_original_SPACER_wall_ms"]=round(wall,3)
    yes=lambda k:result["original_methods"][k]["status"]==PROVEN
    learned_ok=yes("LEARNED_TOP12")
    result["learned_verified_full_original_3VC"]=learned_ok
    result["learned_beyond_source_post_only"]=learned_ok and pstatus!="ALL_THREE_ORIGINAL_VCS_UNSAT"
    result["learned_only_vs_equal_budget"]=learned_ok and not (
        yes("UNTRAINED_TOP12") or yes("STATIC_TOP12")
    )
    result["learned_not_solved_by_classical"]=learned_ok and not yes(
        "CLASSICAL_ALL_GRAMMAR") and cp!="unsat"
    result["status"]="COMPLETE_ORIGINAL_3VC_COMPARISON"
    return result

def run(root,first_file):
    raw=first_file.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=ORIGINAL_FIRST_Q3Q_SHA:
        raise ValueError("FIRST_Q3Q_REAL_CHECKPOINT_RECEIPT_SHA_CHANGED")
    first=json.loads(raw)
    if first["status"]!="FIRST_CONSTRUCTIVE_NEURAL_TYPED_AST_ORIGINAL_PROOFS_RECORDED":
        raise ValueError("FIRST_ORIGINAL_NEURAL_LEARNER_NOT_COMPLETED")
    if blobhash((root/"LICENSE.md").read_bytes())!=EXPECTED_LICENSE_BLOB:
        raise ValueError("ORIGINAL_UPSTREAM_LICENSE_CHANGED")
    old=load_specs(root)
    if len(old)!=56:raise ValueError("FROZEN_FIRST_GROUP_INPUT_COUNT_CHANGED")
    freshpaths,families,total_families,excluded=choose_fresh_paths(root,old)
    # Training frozen and weights finalized WITHOUT reading target contents.
    learned,zero,training=freeze_same_neural_training(old,first)
    previous_sha={s["source_sha"] for s in old}
    specs=[original_spec(path,root,i+1000,previous_sha)
           for i,path in enumerate(freshpaths)]
    if len({s["source_sha"] for s in specs})!=len(specs):
        raise ValueError("FRESH_TEST_ORIGINAL_SOURCE_BYTES_DUPLICATE")
    evaluated=[]
    start=time.perf_counter_ns()
    for x in specs:
        evaluated.append(evaluate(x,learned,zero))
    eval_ms=(time.perf_counter_ns()-start)/1e6
    famstat={}
    for family in families:
        sub=[x for x in evaluated if x["source_origin"]==family]
        famstat[family]={
           "selected":len(sub),
           "learned_full_original_proofs":sum(x.get("learned_verified_full_original_3VC",False) for x in sub),
           "learned_beyond_post_alone":sum(x.get("learned_beyond_source_post_only",False) for x in sub),
           "learned_only_vs_equal_budget":sum(x.get("learned_only_vs_equal_budget",False) for x in sub),
           "strong_classical_full_grammar":sum(x.get("original_methods",{}).get("CLASSICAL_ALL_GRAMMAR",{}).get("status")==PROVEN for x in sub),
           "direct_spacer_original_safe":sum(x.get("strong_direct_original_SPACER_bad_state")=="unsat" for x in sub),
           "post_alone_original_safe":sum(x.get("source_post_only_original_3VC_verdict")=="ALL_THREE_ORIGINAL_VCS_UNSAT" for x in sub)
        }
    outside=[
        x for x in evaluated if x.get("learned_beyond_source_post_only")
        and x.get("learned_only_vs_equal_budget")
    ]
    # This limited success is NOT novel primitives; hence NEVER global Q3 PASS.
    qualified={x["source_origin"] for x in outside}
    return {
        "study":"Q3R_FRESH_NEVER_BEFORE_OPENED_ORIGIN_LEARNED_TYPED_AST_FIRST",
        "status":"FIRST_FIXED_NEW_ORIGIN_RESULT_RECORDED",
        "source_repo":"SaswatPadhi/LoopInvGen",
        "upstream_commit":UPSTREAM,
        "source_selection":"first three lexicographically earliest NEW LIA groups with >=2 original sl files, first 8 each; exclude ALL first-40-LIA groups",
        "first_model_original_receipt_sha256":ORIGINAL_FIRST_Q3Q_SHA,
        "historical_first_model_training_exact_replay":training,
        "old_source_count":len(old),
        "new_uninspected_origin_groups_selected":families,
        "all_available_unused_origin_groups":total_families,
        "old_groups_excluded":excluded,
        "new_orig_source_file_count":len(evaluated),
        "actual_new_source_group_count":len(families),
        "new_test_original_3VC_results":evaluated,
        "new_family_summary":famstat,
        "qualified_learned_beyond_post_and_ablations":len(outside),
        "qualified_source_groups":sorted(qualified),
        "preregistered_two_new_origin_generalization_goal":len(qualified)>=2,
        "eval_multi_method_wall_ms":round(eval_ms,3),
        "no_test_invariant_answers_leaked_to_training":True,
        "no_original_benchmark_text_or_formula_exported":True,
        "all_benchmarks_commercial_training_rights_cleared":False,
        "no_new_primitive_math_operators":True,
        "q3f_escrow_original_source_bodies_opened":False,
        "global_q1_q7":"OPEN"
    }

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,required=True)
    p.add_argument("--first-q3q",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    report=run(a.root,a.first_q3q)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(report,indent=2)+"\n")
    print("Q3R_UNSEEN_ORIGIN_FIRST_SELECTION",report["new_uninspected_origin_groups_selected"])
    print("Q3R_EXACT_NEURAL_REPLAY",report["historical_first_model_training_exact_replay"]["first_final_losses"],report["historical_first_model_training_exact_replay"]["train_atom_examples"])
    print("Q3R_GENUINELY_FRESH_ORIGINAL_PROOFS",report["new_family_summary"])
    print("Q3R_PREREG_GROUP_SEPARATED_OUTCOME",report["preregistered_two_new_origin_generalization_goal"])
    print("Q3R_GLOBAL_Q1_Q7",report["global_q1_q7"])
