"""Q3Q real source-conditioned variable-arity typed AST atom construction and neural selection.

Source-only grammar atoms are assembled into NEW conjunctive ASTs. Trained
weights choose 12 atoms; original SyGuS Pre/Trans/Post are independently
checked without labels or solutions from test origin groups.

This tests bounded learnt grammar selection. It is NOT novel primitive
operator invention, Q4 efficiency superiority or Q7 frontier parity.
"""
from __future__ import annotations
import argparse,collections,hashlib,json,re,sys,time,random
from pathlib import Path
import torch
from torch import nn
import z3,z3.z3util

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/"q3p-trained-typed-20261018"))
from first_trained_typed_proposer import (
    SEED,load_specs,extract_template,proof_vc,direct_original_proof,
    token_features,candidate_features,Scorer,TRAIN_GROUPS,
    EXPECTED_LICENSE_BLOB,blobhash
)

K_ATOMS=12
MAX_ATOMS=300
MAX_CONSTANTS=8
TRAIN_EPOCHS=50
H_VC_MS=1000
TRAIN_TEACHER_MS=450
MAX_HOUDINI_ROUNDS=8
EVAL_VC_MS=3000

def check(query,timeout=H_VC_MS):
    solver=z3.Solver()
    solver.set(timeout=timeout)
    solver.add(query)
    try:return str(solver.check())
    except Exception:return "error"

def source_atoms(source):
    """Construct candidate Bool typed ASTs ONLY from source signature+spec."""
    now=source["now"]; nxt=source["next"]
    allowed=set(now)
    constants=[0,1,-1]
    # Original input source integers are public problem parameters, not labels.
    for term in (source["pre"],source["trans"],source["post"]):
        for num in re.findall(r"(?<![a-zA-Z_])(?<![0-9])[-]?[0-9]+",term.sexpr()):
            try:v=int(num)
            except ValueError:continue
            if abs(v)<=1000 and v not in constants:
                constants.append(v)
            if len(constants)>=MAX_CONSTANTS:break
        if len(constants)>=MAX_CONSTANTS:break
    atoms=[];seen=set()
    def admit(expr,origin):
        expr=z3.simplify(expr)
        if not z3.is_bool(expr) or z3.is_true(expr) or z3.is_false(expr):
            return
        if set(z3.z3util.get_vars(expr))-allowed:return
        key=expr.sexpr()
        if key in seen:return
        if len(atoms)>=MAX_ATOMS:return
        seen.add(key)
        atoms.append({"expr":expr,"sha":hashlib.sha256(key.encode()).hexdigest(),
                      "origin":origin,"nodes":key.count("(")})
    for v in now:
        for c in constants:
            for op in ("GE","LE","EQ"):
                admit(v>=c if op=="GE" else v<=c if op=="LE" else v==c,"VAR_CONST_"+op)
    for i,a in enumerate(now):
        for b in now[i+1:]:
            for op in ("GE","LE","EQ"):
                admit(a>=b if op=="GE" else a<=b if op=="LE" else a==b,"VAR_PAIR_"+op)
    # Derive partial typed Boolean constraints from ORIGINAL current/next
    # source specification. Next-state names are converted to current-state
    # names ONLY for AST *candidate generation*, with full proof later.
    def traverse(ast,seen_nodes):
        if len(seen_nodes)>2048:return
        if not z3.is_app(ast):return
        if z3.is_bool(ast):
            # No test-source theorem solver labels are accessed here.
            admit(ast,"ORIGINAL_BOOLEAN_SUBEXPR")
        for child in ast.children():traverse(child,seen_nodes+[1])
    for part in (source["pre"],source["post"]):
        traverse(part,[])
    # Original post condition is itself available to every equal-info
    # baseline; proof of post is not assumed inductive.
    admit(source["post"],"ORIGINAL_POST")
    for term in (source["trans"],):
        mapped=z3.substitute(term,*list(zip(nxt,now)))
        traverse(mapped,[])
    return atoms[:MAX_ATOMS],constants

def atom_feature(spec,atom):
    s=token_features((spec["pre"],spec["trans"],spec["post"]),
                     spec["now"],spec["next"])
    c=candidate_features(atom["expr"])
    dims=[
        min(spec["variables"],12)/12,
        min(spec["syntactic_size"],600)/600,
        min(atom["nodes"],250)/250,
        min(len(z3.z3util.get_vars(atom["expr"])),12)/12,
    ]
    features=s+c+dims
    if len(features)!=100:raise ValueError("NEURAL_FEATURE_SHAPE_FAILURE")
    return features

def valid_teacher_labels(source,candidates,teacher):
    """Label whether original PROVEN train invariant IMPLIES atom."""
    out=[];unknown=0
    for atom in candidates:
        result=check(z3.And(teacher,z3.Not(atom["expr"])),TRAIN_TEACHER_MS)
        if result=="unknown" or result=="error":
            unknown+=1
            continue
        out.append((atom,int(result=="unsat")))
    return out,unknown

def join_houdini(spec,selected):
    """Prove source-derived conjunction by exact original SyGuS VCs."""
    start=time.perf_counter_ns()
    out={"selected":len(selected),"candidate_calls":0,"rounds":0}
    if spec["input_precondition_sat"]!="sat":
        out["status"]="ABSTAIN_EMPTY_OR_UNKNOWN_PRECONDITION"
        return out
    current=[]
    for item in selected:
        outcome=check(z3.And(spec["pre"],z3.Not(item["expr"])))
        out["candidate_calls"]+=1
        if outcome=="unsat":current.append(item)
    for cycle in range(MAX_HOUDINI_ROUNDS):
        out["rounds"]=cycle+1
        conjunction=z3.And(*[x["expr"] for x in current])
        updated=[]
        for item in current:
            nxt_expr=z3.substitute(item["expr"],*list(zip(spec["now"],spec["next"])))
            query=z3.And(conjunction,spec["trans"],z3.Not(nxt_expr))
            outcome=check(query)
            out["candidate_calls"]+=1
            if outcome=="unsat":updated.append(item)
        if len(updated)==len(current):
            break
        current=updated
    else:
        out["status"]="ABSTAIN_HOUDINI_ROUND_LIMIT"
        return out
    inv=z3.And(*[x["expr"] for x in current])
    verdict,checks=proof_vc(inv,spec,EVAL_VC_MS)
    # No vacuous 'true post' or empty true invariant accepted.
    postnontrivial=check(z3.Not(spec["post"]),EVAL_VC_MS)=="sat"
    out.update({
        "status":"ALL_THREE_ORIGINAL_VCS_UNSAT_NONTRIVIAL"
                 if verdict=="ALL_THREE_ORIGINAL_VCS_UNSAT" and
                 current and postnontrivial else
                 "NO_COMPLETE_ORIGINAL_PROOF",
        "strict_original_3vc_status":verdict,
        "nonvacuous_source_postcondition":postnontrivial,
        "final_conjunction_atom_count":len(current),
        "assembled_original_AST_sha256":hashlib.sha256(z3.simplify(inv).sexpr().encode()).hexdigest(),
        "final_exact_vc_queries":checks,
        "full_wall_ms":round((time.perf_counter_ns()-start)/1e6,3),
        "selected_source_atom_types":dict(collections.Counter(x["origin"] for x in current)),
    })
    return out

def run(root):
    if blobhash((root/"LICENSE.md").read_bytes())!=EXPECTED_LICENSE_BLOB:
        raise ValueError("UPSTREAM_SOURCE_LICENSE_IDENTITY_CHANGED")
    torch.manual_seed(SEED);random.seed(SEED);torch.set_num_threads(2)
    allsources=load_specs(root)
    train=[s for s in allsources if s["split"]=="TRAIN" and
           s["parse_status"]=="OK" and s["input_precondition_sat"]=="sat"]
    test=[s for s in allsources if s["split"]!="TRAIN"]
    if len(allsources)!=56 or not train or len(test)!=40:raise ValueError("SOURCE_GROUP_SPLIT_IDENTITY_CHANGED")
    if {s["source_sha"] for s in train}&{s["source_sha"] for s in test}:
        raise ValueError("TRAIN_TEST_SOURCE_SHA_OVERLAP")
    samples=[];labels=[];counts=collections.Counter()
    teachers=[];train_time_start=time.perf_counter_ns()
    for spec in train:
        template,extract=extract_template(spec)
        if template is None:
            counts["NO_ORIGINAL_PROVEN_TRAIN_TEACHER"]+=1
            continue
        # Restore teacher into EXACT ORIGINAL train state names.
        slots=[z3.Int("Q3P_CANONICAL_SLOT_"+str(i)) for i in range(len(spec["now"]))]
        teacher=z3.substitute(template["canonical"],*list(zip(slots,spec["now"])))
        if proof_vc(teacher,spec,EVAL_VC_MS)[0]!="ALL_THREE_ORIGINAL_VCS_UNSAT":
            raise ValueError("TEACHER_ORIGINAL_CERTIFICATE_REGRESSION")
        atoms,constants=source_atoms(spec)
        inspected,unknown=valid_teacher_labels(spec,atoms,teacher)
        counts["TEACHER_IMPLICATION_UNKNOWN"]+=unknown
        teachers.append({"train_original_sha":spec["source_sha"],
                         "strict_original_teacher_verified":True,
                         "source_constructed_grammar_atoms":len(atoms),
                         "original_candidate_teaching_pairs":len(inspected),
                         "positive":sum(l for _,l in inspected)})
        for a,label in inspected:
            samples.append(atom_feature(spec,a));labels.append(label)
    teacher_ms=(time.perf_counter_ns()-train_time_start)/1e6
    if not labels or len(set(labels))<2:
        return {"study":"Q3Q_FIRST_LEARNED_ATOM_ASSEMBLY",
                "status":"BLOCKED_NO_BOTH_TRAIN_CLASSES",
                "train_label_count":len(labels),"global_q1_q7":"OPEN"}
    t0=time.perf_counter_ns()
    model=Scorer();untrained=Scorer()
    untrained.load_state_dict(model.state_dict())
    X=torch.tensor(samples,dtype=torch.float32)
    Y=torch.tensor(labels,dtype=torch.float32)
    weight=max(1.,(len(labels)-sum(labels))/sum(labels))
    loss_fn=nn.BCEWithLogitsLoss(pos_weight=torch.tensor(weight))
    opt=torch.optim.AdamW(model.parameters(),lr=0.008,weight_decay=0.0001)
    losses=[]
    for epoch in range(TRAIN_EPOCHS):
        model.train();pred=model(X);loss=loss_fn(pred,Y)
        opt.zero_grad();loss.backward();opt.step()
        if epoch in (0,TRAIN_EPOCHS-1):losses.append(round(float(loss.item()),6))
    learn_ms=(time.perf_counter_ns()-t0)/1e6
    model.eval();untrained.eval()
    results=[]
    evalstart=time.perf_counter_ns()
    for spec in test:
        row={"source_sha":spec["source_sha"],"original_path":spec["path"],
             "group":spec["group"],"split":spec["split"],
             "classical_source_only_spacer_result":"NOT_RUN",
             "source_grammar_total_atoms":0,"model_full_orig_proof":False}
        if spec["parse_status"]!="OK" or spec["input_precondition_sat"]!="sat":
            row["status"]="ABSTAIN_ORIGINAL_UNSUPPORTED_OR_BAD_PRE"
            results.append(row);continue
        atoms,constants=source_atoms(spec)
        row["source_grammar_total_atoms"]=len(atoms)
        row["source_constant_count"]=len(constants)
        if not atoms:
            row["status"]="NO_CONSTRUCTIBLE_SOURCE_AST"
            results.append(row);continue
        # No verification feedback is supplied to scorer before TOP12 chosen.
        features=torch.tensor([atom_feature(spec,a) for a in atoms],dtype=torch.float32)
        t0=time.perf_counter_ns()
        with torch.no_grad():
            scores=model(features).tolist()
            init_scores=untrained(features).tolist()
        row["neural_selection_ms"]=round((time.perf_counter_ns()-t0)/1e6,3)
        methods={
            "TRAINED_TOP12":sorted(range(len(atoms)),key=lambda i:(-scores[i],atoms[i]["sha"]))[:K_ATOMS],
            "UNTRAINED_TOP12":sorted(range(len(atoms)),key=lambda i:(-init_scores[i],atoms[i]["sha"]))[:K_ATOMS],
            "STATIC_TOP12":sorted(range(len(atoms)),key=lambda i:atoms[i]["sha"])[:K_ATOMS],
            "CLASSICAL_ALL_GRAMMAR":list(range(len(atoms))),
        }
        row["methods"]={}
        for name,indices in methods.items():
            row["methods"][name]=join_houdini(spec,[atoms[i] for i in indices])
        # Strongest original specialist should not be omitted from comparison.
        _,_,outcome,reason,wall=direct_original_proof(spec)
        row["classical_source_only_spacer_result"]=outcome
        row["classical_source_only_spacer_ms"]=round(wall,3)
        row["status"]="EVALUATED_ORIGINAL_SPEC_WITH_FULL_VCS"
        row["model_full_orig_proof"]=row["methods"]["TRAINED_TOP12"]["status"]=="ALL_THREE_ORIGINAL_VCS_UNSAT_NONTRIVIAL"
        results.append(row)
    bysplit={}
    for split in ("HELDOUT","DIAGNOSTIC"):
        subs=[r for r in results if r["split"]==split]
        names=("TRAINED_TOP12","UNTRAINED_TOP12","STATIC_TOP12","CLASSICAL_ALL_GRAMMAR")
        successes={name:sum(
            r.get("methods",{}).get(name,{}).get("status")=="ALL_THREE_ORIGINAL_VCS_UNSAT_NONTRIVIAL"
            for r in subs) for name in names}
        successes["SPACER_2000MS"]=sum(r["classical_source_only_spacer_result"]=="unsat" for r in subs)
        bysplit[split]={
            "originals":len(subs),
            "proofed":successes,
            "unsupported_originals":sum(r["status"]!="EVALUATED_ORIGINAL_SPEC_WITH_FULL_VCS" for r in subs),
            "trained_only_positive_vs_static_or_untrained":sum(
                r.get("methods",{}).get("TRAINED_TOP12",{}).get("status")=="ALL_THREE_ORIGINAL_VCS_UNSAT_NONTRIVIAL"
                and all(r.get("methods",{}).get(other,{}).get("status")!="ALL_THREE_ORIGINAL_VCS_UNSAT_NONTRIVIAL"
                    for other in ("UNTRAINED_TOP12","STATIC_TOP12")) for r in subs),
            "trained_proof_not_solved_by_either_strong_classical":sum(
                r.get("methods",{}).get("TRAINED_TOP12",{}).get("status")=="ALL_THREE_ORIGINAL_VCS_UNSAT_NONTRIVIAL"
                and r.get("methods",{}).get("CLASSICAL_ALL_GRAMMAR",{}).get("status")!="ALL_THREE_ORIGINAL_VCS_UNSAT_NONTRIVIAL"
                and r["classical_source_only_spacer_result"]!="unsat"
                for r in subs)
        }
    return {
      "study":"Q3Q_REAL_SOURCE_CONDITIONED_LEARNED_ATOM_AST_CONJUNCTION_FIRST",
      "status":"FIRST_CONSTRUCTIVE_NEURAL_TYPED_AST_ORIGINAL_PROOFS_RECORDED",
      "frozen_original_corpus_count":56,
      "original_train_count":len(train),
      "original_group_test_count":len(test),
      "zero_test_knowledge_in_training":True,
      "learned_AST_hypothesis_class":"source-specific typed predicates; new Boolean conjunctions; no new math primitive",
      "learned_weights":sum(p.numel() for p in model.parameters()),
      "learning_epochs":TRAIN_EPOCHS,
      "learned_loss_first_last":losses,
      "training_atom_labels":{"total":len(labels),"positive":sum(labels),"negative":len(labels)-sum(labels)},
      "teacher_classical_source_proof_data_generation_ms":round(teacher_ms,3),
      "learned_neural_training_ms":round(learn_ms,3),
      "evaluation_total_wall_ms":round((time.perf_counter_ns()-evalstart)/1e6,3),
      "train_teacher_original_receipts":teachers,
      "per_split_actual_original_proof_summary":bysplit,
      "first_original_eval_sha_only":results,
      "source_text_or_invariant_text_redistributed":False,
      "q3f_sealed_holdout_sources_accessed":False,
      "global_q1_q7":"OPEN"
    }

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--root",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    a=p.parse_args()
    result=run(a.root)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2)+"\n")
    print("Q3Q_LEARNED_AST_FIRST_STATUS",result["status"])
    print("Q3Q_TRUE_NEURAL_TRAIN_ATOMS",result["training_atom_labels"])
    print("Q3Q_ORIGINAL_PROOF_COMPARISON",result["per_split_actual_original_proof_summary"])
    print("Q3Q_GLOBAL_Q1_Q7",result["global_q1_q7"])
