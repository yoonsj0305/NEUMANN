"""Q3S: genuine new-families learned source-bound affine relation AST construction.

One fixed first execution on two origin groups whose source bodies were NOT
opened in Q3P/Q/R. Generate pair-affine relational atoms outside Q3Q grammar,
train a tiny actual CPU neural atom scorer ONLY on original TRAIN family
classical verified covers, choose TOP12 prior to any original target proof,
compare source Post alone / untrained / static / original grammar / full
affine grammar / source-only SPACER using the same exact SyGuS 3 VCs.

User-facing science boundary: researcher designed affine grammar, neural
ranking did not invent a new operator, regardless of test outcome.
"""
from __future__ import annotations
import argparse,collections,hashlib,json,random,re,sys,time
from pathlib import Path
import torch
from torch import nn
import z3,z3.z3util

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/"q3q-learned-atom-assembly-20261018"))
sys.path.insert(0,str(HERE.parent/"q3r-fresh-origin-20261018"))
sys.path.insert(0,str(HERE.parent/"q3p-trained-typed-20261018"))
from first_constructive_learner import (
    source_atoms as old_source_atoms,valid_teacher_labels,
    atom_feature,join_houdini,EVAL_VC_MS,K_ATOMS,TRAIN_EPOCHS
)
from first_unseen_source_family_neural_proof import original_spec,sat_status
from first_trained_typed_proposer import (
    SEED,load_specs,extract_template,proof_vc,direct_original_proof,
    Scorer,EXPECTED_LICENSE_BLOB,blobhash
)

FIRST_Q3Q_SHA="cc921c0f08fd9c16ea4fa6e6a9a34eae4365f619b6e28fea5c88f2926b6c9521"
FIRST_Q3R_SHA="5675e5487cfc54395119855267bbeec6d6c0af82109b6609296c100953d14880"
ORIGINAL_COMMIT="6ac90265b11431c9477dfbd33e3e3380234c0499"
FIRST_GROUP_CAP=2
PER_GROUP_CAP=8
OLD_ATOMS_CAP=120
NEW_AFFINE_CAP=180
TOTAL_ATOMS_CAP=300
CONSTANT_CAP=8
PROVEN="ALL_THREE_ORIGINAL_VCS_UNSAT_NONTRIVIAL"

def require_sha_json(path,sha,expected_study_status):
    raw=path.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=sha:
        raise ValueError("IMMUTABLE_FIRST_ORIGINAL_JSON_SHA_CHANGED")
    body=json.loads(raw)
    if body["status"]!=expected_study_status:
        raise ValueError("PRIOR_FROZEN_FIRST_STUDY_STATUS_CHANGED")
    return body

def select_new_original_paths(root,old_specs,old_q3r):
    # This step uses filename strings ONLY and never reads target contents.
    forbidden={x["group"] for x in old_specs}
    previous_groups=set(old_q3r["new_uninspected_origin_groups_selected"])
    if len(previous_groups)!=3:
        raise ValueError("Q3R_EXCLUSION_PREVIOUS_THREE_GROUPS_CHANGED")
    forbidden|=previous_groups
    families=collections.defaultdict(list)
    for original in (root/"benchmarks"/"LIA").rglob("*.sl"):
        parts=original.relative_to(root).parts
        if len(parts)<4:continue
        group="/".join(parts[:3])
        if group not in forbidden:
            families[group].append(original)
    available=sorted(f for f,p in families.items() if len(p)>=2)
    chosen=available[:FIRST_GROUP_CAP]
    selected=[
        path for f in chosen for path in sorted(
            families[f],key=lambda p:p.relative_to(root).as_posix()
        )[:PER_GROUP_CAP]
    ]
    if not selected:raise ValueError("NO_UNUSED_SOURCE_ORIGIN_GROUPS_LEFT")
    return chosen,selected,available,sorted(forbidden)

def affine_atom_pool(spec):
    # Already-opened source ORIGINAL solely determines candidate formulas.
    prior,source_constants=old_source_atoms(spec)
    integer_vars=spec["now"]
    consts=list(dict.fromkeys(source_constants))[:CONSTANT_CAP]
    originals=list(prior[:OLD_ATOMS_CAP])
    original_hashes={x["sha"] for x in originals}
    # Preserve the original source Post as an explicit nontrivial candidate
    # when Boolean/variable-bound and not otherwise in first 120.
    post=z3.simplify(spec["post"])
    if (z3.is_bool(post) and not z3.is_true(post) and
        not z3.is_false(post) and
        not (set(z3.z3util.get_vars(post))-set(integer_vars))):
        digest=hashlib.sha256(post.sexpr().encode()).hexdigest()
        if digest not in original_hashes:
            if len(originals)>=OLD_ATOMS_CAP:
                removed=originals.pop()
                original_hashes.remove(removed["sha"])
            originals.append({
                "expr":post,"sha":digest,"origin":"SOURCE_POST_AS_ATOM",
                "nodes":post.sexpr().count("(")
            })
            original_hashes.add(digest)
    affine=[];seen=set(original_hashes)
    def add(test,origin):
        expr=z3.simplify(test)
        if z3.is_true(expr) or z3.is_false(expr) or not z3.is_bool(expr):
            return
        if set(z3.z3util.get_vars(expr))-set(integer_vars):
            raise ValueError("UNBOUND_OR_NEXT_VARIABLE_IN_TYPED_AFFINE_ATOM")
        key=expr.sexpr()
        signature=hashlib.sha256(key.encode()).hexdigest()
        if signature in seen:return
        if len(affine)>=NEW_AFFINE_CAP:return
        seen.add(signature)
        affine.append({
            "expr":expr,"sha":signature,
            "origin":"NEW_SOURCE_PAIR_AFFINE_"+origin,
            "nodes":key.count("(")
        })
    for i,a in enumerate(integer_vars):
        for b in integer_vars[i+1:]:
            for term,kind in ((a+b,"SUM"),(a-b,"DIFFERENCE"),
                              (b-a,"REVERSED_DIFFERENCE")):
                for constant in consts:
                    for comparison in ("GE","LE","EQ"):
                        if len(affine)>=NEW_AFFINE_CAP:break
                        add(term>=constant if comparison=="GE" else
                            term<=constant if comparison=="LE" else
                            term==constant,kind+"_"+comparison)
    all_atoms=originals+affine
    if len(all_atoms)>TOTAL_ATOMS_CAP:
        raise ValueError("AFFINE_ATOM_GLOBAL_CAP_VIOLATED")
    if len({a["sha"] for a in all_atoms})!=len(all_atoms):
        raise ValueError("DUPLICATE_SOURCE_BOUND_TYPED_AFFINE_ATOM")
    return all_atoms,{"old_grammar_atom_count":len(originals),
                      "new_affine_atom_count":len(affine),
                      "source_only_constant_count":len(consts)}

def frozen_neural_train(old):
    # Train BEFORE any newly selected original problem BODY is read.
    random.seed(SEED);torch.manual_seed(SEED);torch.set_num_threads(2)
    train=[s for s in old if s["split"]=="TRAIN" and
           s["parse_status"]=="OK" and s["input_precondition_sat"]=="sat"]
    inputs=[];labels=[];sources=[]
    begin=time.perf_counter_ns()
    for src in train:
        teacher,_=extract_template(src)
        if teacher is None:continue
        slots=[z3.Int("Q3P_CANONICAL_SLOT_"+str(i))
               for i in range(len(src["now"]))]
        formula=z3.substitute(
            teacher["canonical"],*list(zip(slots,src["now"]))
        )
        if proof_vc(formula,src,EVAL_VC_MS)[0]!="ALL_THREE_ORIGINAL_VCS_UNSAT":
            raise ValueError("TRAIN_ORIGINAL_CLASSICAL_TEACHER_NOT_PROVEN")
        atoms,distribution=affine_atom_pool(src)
        labeled,unknown=valid_teacher_labels(src,atoms,formula)
        good=sum(y for _,y in labeled)
        sources.append({
            "original_sha":src["source_sha"],
            "original_train_source_group":src["group"],
            "train_original_3VC_certified":True,
            "candidate_atoms":len(atoms),
            "new_affine_grammar_count":distribution["new_affine_atom_count"],
            "train_candidate_labels":len(labeled),
            "positive_labels":good,
            "unknown_teacher_implications":unknown,
        })
        for atom,yes in labeled:
            inputs.append(atom_feature(src,atom))
            labels.append(yes)
    teacher_ms=round((time.perf_counter_ns()-begin)/1e6,3)
    if not labels or len(set(labels))!=2:
        raise ValueError("NOT_ENOUGH_POSITIVE_AND_NEGATIVE_ORIGINAL_TRAIN_LABELS")
    if len(sources)!=11:
        raise ValueError("ORIGINAL_TRAIN_SOURCE_TEACHER_COUNT_CHANGED")
    nn_model=Scorer()
    nn_untrained=Scorer()
    nn_untrained.load_state_dict(nn_model.state_dict())
    if sum(p.numel() for p in nn_model.parameters())!=1633:
        raise ValueError("ORIGINAL_SCORER_ARCHITECTURE_PARAMETER_COUNT_CHANGED")
    X=torch.tensor(inputs,dtype=torch.float32)
    Y=torch.tensor(labels,dtype=torch.float32)
    npos=int(Y.sum().item())
    nneg=len(labels)-npos
    loss_fn=nn.BCEWithLogitsLoss(
        pos_weight=torch.tensor(max(1.0,nneg/max(npos,1)))
    )
    opt=torch.optim.AdamW(nn_model.parameters(),lr=0.008,weight_decay=0.0001)
    losses=[];t0=time.perf_counter_ns()
    for epoch in range(TRAIN_EPOCHS):
        nn_model.train()
        logit=nn_model(X)
        loss=loss_fn(logit,Y)
        opt.zero_grad();loss.backward();opt.step()
        if epoch in (0,TRAIN_EPOCHS-1):
            losses.append(round(float(loss.item()),6))
    train_ms=round((time.perf_counter_ns()-t0)/1e6,3)
    nn_model.eval();nn_untrained.eval()
    return nn_model,nn_untrained,{
        "training_source_count":len(train),
        "original_train_source_proven_teacher_count":len(sources),
        "original_train_teacher_receipts":sources,
        "training_atom_pairs":len(labels),
        "positive":npos,"negative":nneg,
        "source_only_classical_teacher_extraction_ms":teacher_ms,
        "neural_train_ms":train_ms,
        "exact_epochs":TRAIN_EPOCHS,
        "initial_final_loss":losses,
        "neural_parameters":1633,
        "candidate_formula_source_bodies_not_exported":True
    }

def evaluate_first_new_original(spec,model,untrained):
    rec={
      "original_path":spec["path"],
      "original_source_sha":spec["source_sha"],
      "new_origin_group":spec["group"],
      "original_parser":"STRICT_TYPED_SYGUS",
      "original_input_precondition":spec.get("input_precondition_sat"),
      "source_text_or_formula_exported":False,
    }
    if spec["parse_status"]!="OK" or spec["input_precondition_sat"]!="sat":
        rec["status"]="ABSTAIN_UNSUPPORTED_OR_EMPTY_ORIGINAL_PRE"
        return rec
    post_nontrivial=sat_status(z3.Not(spec["post"]),3000)
    rec["negated_original_post_sat"]=post_nontrivial
    if post_nontrivial!="sat":
        rec["status"]="ABSTAIN_VACUOUS_OR_UNKNOWN_ORIGINAL_POST"
        return rec
    atoms,grammar=affine_atom_pool(spec)
    rec["new_original_typed_grammar"]=grammar
    rec["all_candidate_atoms"]=len(atoms)
    if not atoms:
        rec["status"]="ABSTAIN_NO_SOURCE_GRAMMAR_CANDIDATES"
        return rec
    features=torch.tensor([atom_feature(spec,a) for a in atoms],dtype=torch.float32)
    fw0=time.perf_counter_ns()
    with torch.no_grad():
        learned_scores=model(features).tolist()
        prior_scores=untrained(features).tolist()
    rec["neural_forward_ms"]=round((time.perf_counter_ns()-fw0)/1e6,3)
    choices={
        "TRAINED_TOP12":sorted(range(len(atoms)),key=lambda i:(-learned_scores[i],atoms[i]["sha"]))[:K_ATOMS],
        "UNTRAINED_TOP12":sorted(range(len(atoms)),key=lambda i:(-prior_scores[i],atoms[i]["sha"]))[:K_ATOMS],
        "STATIC_TOP12":sorted(range(len(atoms)),key=lambda i:atoms[i]["sha"])[:K_ATOMS],
        "FULL_AFFINE_GRAMMAR_CLASSICAL":list(range(len(atoms))),
    }
    results={}
    for method,picks in choices.items():
        results[method]=join_houdini(spec,[atoms[i] for i in picks])
    # Compare strongest PREVIOUS Q3Q grammar under same original goal and
    # verification method, to measure representation expansion contribution.
    old_atoms,_=old_source_atoms(spec)
    results["OLD_Q3Q_FULL_GRAMMAR_CLASSICAL"]=join_houdini(spec,old_atoms)
    rec["all_original_three_vc_results"]=results
    post_start=time.perf_counter_ns()
    pstatus,pqueries=proof_vc(spec["post"],spec,EVAL_VC_MS)
    rec["SOURCE_POST_ALONE_3VC"]=pstatus
    rec["SOURCE_POST_ALONE_VC_QUERIES"]=pqueries
    rec["SOURCE_POST_ALONE_WALL_MS"]=round((time.perf_counter_ns()-post_start)/1e6,3)
    _,_,specialist,reason,wall=direct_original_proof(spec)
    rec["DIRECT_SPACER_BAD_STATE"]=specialist
    rec["DIRECT_SPACER_REASON"]=reason
    rec["DIRECT_SPACER_WALL_MS"]=round(wall,3)
    ispass=lambda name:results[name]["status"]==PROVEN
    new_ok=ispass("TRAINED_TOP12")
    rec["trained_complete_original_3VC_proof"]=new_ok
    rec["trained_final_affine_relation_used"]=(
        new_ok and any(
            k.startswith("NEW_SOURCE_PAIR_AFFINE_") and v>0
            for k,v in results["TRAINED_TOP12"].get(
                "selected_source_atom_types",{}).items()
        )
    )
    rec["trained_beyond_source_post"]=(
        new_ok and pstatus!="ALL_THREE_ORIGINAL_VCS_UNSAT"
    )
    rec["trained_only_vs_matched_ablations"]=new_ok and not (
        ispass("UNTRAINED_TOP12") or ispass("STATIC_TOP12")
    )
    rec["trained_beyond_all_strong_classical"]=new_ok and not (
        ispass("FULL_AFFINE_GRAMMAR_CLASSICAL") or
        ispass("OLD_Q3Q_FULL_GRAMMAR_CLASSICAL") or
        specialist=="unsat"
    )
    rec["strict_learned_affine_distinct_capability_admission"]=all([
        rec["trained_final_affine_relation_used"],
        rec["trained_beyond_source_post"],
        rec["trained_only_vs_matched_ablations"],
        rec["trained_beyond_all_strong_classical"]
    ])
    rec["status"]="COMPLETE_ACTUAL_ORIGINAL_3VC_CROSS_COMPARISON"
    return rec

def run(root,old_q3q_file,old_q3r_file):
    a=require_sha_json(old_q3q_file,FIRST_Q3Q_SHA,
        "FIRST_CONSTRUCTIVE_NEURAL_TYPED_AST_ORIGINAL_PROOFS_RECORDED")
    b=require_sha_json(old_q3r_file,FIRST_Q3R_SHA,
        "FIRST_FIXED_NEW_ORIGIN_RESULT_RECORDED")
    if blobhash((root/"LICENSE.md").read_bytes())!=EXPECTED_LICENSE_BLOB:
        raise ValueError("SOURCE_REPOSITORY_LICENSE_BLOB_MISMATCH")
    old=load_specs(root)
    if len(old)!=56:raise ValueError("FROZEN_OLD_56_SOURCE_COUNT_CHANGED")
    chosen,paths,available,excluded=select_new_original_paths(root,old,b)
    # CRITICAL: model has been trained and its parameters FROZEN
    # before reading ANY new original program bytes.
    nn_model,control,training=frozen_neural_train(old)
    if training["training_source_count"]!=a["original_train_count"]:
        raise ValueError("Q3Q_ORIGINAL_TRAIN_COUNT_DRIFT")
    forbid={x["source_sha"] for x in old}|{
      r["source_sha"] for r in b["new_test_original_3VC_results"]
    }
    new=[]
    for i,path in enumerate(paths):
        obj=original_spec(path,root,1500+i,forbid)
        if obj["source_sha"] in forbid:raise ValueError("PRIOR_EXPOSED_SOURCE_FILE_REUSED")
        new.append(obj)
    if len(set(x["source_sha"] for x in new))!=len(new):
        raise ValueError("NEW_TEST_SOURCE_DUPLICATE")
    started=time.perf_counter_ns()
    receipts=[evaluate_first_new_original(x,nn_model,control) for x in new]
    multi_ms=round((time.perf_counter_ns()-started)/1e6,3)
    family_result={}
    methods=("TRAINED_TOP12","UNTRAINED_TOP12","STATIC_TOP12",
             "FULL_AFFINE_GRAMMAR_CLASSICAL","OLD_Q3Q_FULL_GRAMMAR_CLASSICAL")
    for group in chosen:
        items=[x for x in receipts if x["new_origin_group"]==group]
        scores={
            method:sum(x.get("all_original_three_vc_results",{}).get(
                method,{}).get("status")==PROVEN for x in items)
            for method in methods
        }
        scores["DIRECT_SPACER"]=sum(x.get("DIRECT_SPACER_BAD_STATE")=="unsat" for x in items)
        scores["SOURCE_POST_ALONE"]=sum(x.get("SOURCE_POST_ALONE_3VC")=="ALL_THREE_ORIGINAL_VCS_UNSAT" for x in items)
        scores["TRAINED_WITH_FINAL_AFFINE"]=sum(x.get("trained_final_affine_relation_used",False) for x in items)
        scores["TRAINED_BEYOND_POST"]=sum(x.get("trained_beyond_source_post",False) for x in items)
        scores["STRICT_LEARNED_AFFINE_CLASSICAL_GAP"]=sum(x.get("strict_learned_affine_distinct_capability_admission",False) for x in items)
        family_result[group]={"selected":len(items),"original_complete_proofs":scores,
          "unsupported_or_unknown_originals":sum(x["status"]!="COMPLETE_ACTUAL_ORIGINAL_3VC_CROSS_COMPARISON" for x in items)}
    witnesses=[
        r for r in receipts if r.get("strict_learned_affine_distinct_capability_admission")
    ]
    return {
        "study":"Q3S_FIRST_TWO_UNUSED_SOURCE_FAMILIES_LEARNED_AFFINE_RELATIONAL_TYPED_ORIGINAL_PROOFS",
        "status":"COMPLETE_FIRST_FROZEN_AFFINE_STUDY",
        "pinned_upstream_git_commit":ORIGINAL_COMMIT,
        "original_first_q3q_sha256":FIRST_Q3Q_SHA,
        "original_first_q3r_sha256":FIRST_Q3R_SHA,
        "all_old_corpus_original_count":len(old),
        "newly_selected_origin_groups":chosen,
        "available_previously_unused_origin_groups":available,
        "all_excluded_previous_origin_groups":excluded,
        "new_unique_original_file_count":len(new),
        "training_from_old_originals_completed_before_new_target_body_read":True,
        "original_training":training,
        "source_declared_operators_are_HUMAN_DESIGNED_not_model_invented":True,
        "total_multi_method_original_eval_ms":multi_ms,
        "per_group_results":family_result,
        "strict_learned_affine_witnesses":len(witnesses),
        "strict_learned_affine_distinct_group_count":len({x["new_origin_group"] for x in witnesses}),
        "preregistered_two_group_strong_learned_gap_pass":len({x["new_origin_group"] for x in witnesses})>=2,
        "all_first_exact_original_receipts":receipts,
        "no_original_external_source_or_formula_redistributed":True,
        "individual_benchmark_training_redistribution_rights_confirmed":False,
        "q3f_escrow_competition_problem_source_opened":False,
        "global_q1_q7":"OPEN"
    }

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,required=True)
    p.add_argument("--old-q3q",type=Path,required=True)
    p.add_argument("--old-q3r",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    report=run(a.root,a.old_q3q,a.old_q3r)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(report,indent=2)+"\n")
    print("Q3S_FIRST_NEW_SOURCE_FAMILY_IDENTITIES",report["newly_selected_origin_groups"])
    print("Q3S_ACTUAL_NEURAL_TRAINING", {k:report["original_training"][k] for k in (
      "training_atom_pairs","positive","negative","neural_parameters",
      "initial_final_loss","source_only_classical_teacher_extraction_ms"
    )})
    print("Q3S_FULL_ORIGINAL_3VC_STRONG_COMPARISON",report["per_group_results"])
    print("Q3S_PREDECLARED_TWO_FAMILY_CAUSAL_Q3_CAPABILITY_GAP",report["preregistered_two_group_strong_learned_gap_pass"])
    print("Q3S_GLOBAL_Q1_Q7",report["global_q1_q7"])
