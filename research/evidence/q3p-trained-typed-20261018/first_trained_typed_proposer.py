"""Q3P first ACTUAL learned neural scorer proposing source-bound typed AST invariants.

- Train ONLY on 3 source-origin LIA groups.
- Evaluate on a disjoint 2016 LIA origin and NIA diagnostic origin.
- No model access to heldout source-derived SPACER covers or published labels.
- All proposed ASTs must independently pass ORIGINAL 3 VCs.
- Equal candidate-budget popularity and untrained ablations, strong SPACER.
- True Q3 novel operator invention remains OPEN: source-group templates transfer.
"""
from __future__ import annotations
import argparse,collections,hashlib,json,math,random,re,sys,time
from pathlib import Path

import torch
from torch import nn
import z3,z3.z3util

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/"q3o-real-sygus-20261018"))
from first_two_originals import extract_original,sexprs,blobhash

SEED=20261018
ORIGIN_COMMIT="6ac90265b11431c9477dfbd33e3e3380234c0499"
SOURCE_COUNTS={"LIA":40,"NIA":16}
TRAIN_GROUPS={
 "benchmarks/LIA/2005.ICALP_PolyRank",
 "benchmarks/LIA/2013.OOPSLA_Hola",
 "benchmarks/LIA/2015.FMCAD_Acceleration",
}
EVAL_GROUPS={"benchmarks/LIA/2016.SyGuS-Comp"}
EXPECTED_LICENSE_BLOB="1e853cd500e1317b7c2ad0a2514b548c32c46f5e"
K=(1,3)
SCORER_EPOCHS=50
HIDDEN=16
FEATURE_SIZE=100
TEMPLATE_FP_TIMEOUT=2000
TRAIN_VC_TIMEOUT=450
TEST_VC_TIMEOUT=3000

def h(token,dimensions):
    return int.from_bytes(hashlib.blake2s(token.encode(),digest_size=4).digest(),"big")%dimensions

def token_features(terms,variables,nxt):
    current=[z3.Int("Q3P_source_state_"+str(i)) for i in range(len(variables))]
    following=[z3.Int("Q3P_source_next_"+str(i)) for i in range(len(variables))]
    normalized=[]
    for term in terms:
        normalized.append(z3.substitute(term, *(
          [(a,b) for a,b in zip(variables,current)]+
          [(a,b) for a,b in zip(nxt,following)]
        )).sexpr())
    text=" ".join(normalized)
    tokens=re.findall(r"[a-zA-Z_][a-zA-Z_0-9]*|[-]?[0-9]+|[^\s()]+",text)
    out=[0.0]*64
    for token in tokens:
        # Large numerals are feature-clipped, test source words not answers.
        value=token if len(token)<7 else token[:7]
        out[h(value,64)]+=1.0
    scale=max(1,sum(out))
    return [v/scale for v in out]

def candidate_features(candidate):
    tokens=re.findall(r"[a-zA-Z_][a-zA-Z_0-9]*|[-]?[0-9]+|[^\s()]+",candidate.sexpr())
    out=[0.0]*32
    for token in tokens:
        out[h(token if len(token)<7 else token[:7],32)]+=1.0
    total=max(1,sum(out))
    return [v/total for v in out]

def synth_features(source,templ,arith_vars,vars_after):
    s=token_features(source["original_formulas"],source["now"],source["next"])
    c=candidate_features(templ["canonical"])
    candidates=source["variables"]
    c2=[
      min(candidates,12)/12,
      min(source["syntactic_size"],600)/600,
      min(templ["nodes"],250)/250,
      min(len(z3.z3util.get_vars(templ["canonical"])),12)/12
    ]
    out=s+c+c2
    if len(out)!=FEATURE_SIZE:raise ValueError("INPUT_FEATURE_DIMENSION_CHANGED")
    return out

def direct_original_proof(spec):
    ns=spec["now"]
    nt=spec["next"]
    rel=z3.Function("q3p_Reach_"+str(spec["number"]),*[z3.IntSort() for _ in ns],z3.BoolSort())
    bad=z3.Function("q3p_Bad_"+str(spec["number"]),z3.BoolSort())
    fp=z3.Fixedpoint()
    fp.set(engine="spacer",timeout=TEMPLATE_FP_TIMEOUT)
    fp.register_relation(rel,bad);fp.declare_var(*(ns+nt))
    fp.rule(rel(*ns),spec["pre"])
    fp.rule(rel(*nt),z3.And(rel(*ns),spec["trans"]))
    fp.rule(bad(),z3.And(rel(*ns),z3.Not(spec["post"])))
    t0=time.perf_counter_ns()
    try:
        result=str(fp.query(bad()))
        extra=fp.reason_unknown() if result=="unknown" else None
    except Exception as exc:
        result="ERROR_"+type(exc).__name__
        extra=str(exc)[:100]
    wall=(time.perf_counter_ns()-t0)/1e6
    return fp,rel,result,extra,wall

def proof_vc(expr,spec,timeout_ms):
    if not z3.is_bool(expr):return "ABSTAIN_NOT_BOOLEAN",0
    now,nxt=spec["now"],spec["next"]
    if set(z3.z3util.get_vars(expr))-set(now):
        return "ABSTAIN_UNBOUND_SOURCE_VARIABLE",0
    # Fast & strict: independent original base, inductive step, post.
    after=z3.substitute(expr,*list(zip(now,nxt)))
    checks=[
      z3.And(spec["pre"],z3.Not(expr)),
      z3.And(expr,spec["trans"],z3.Not(after)),
      z3.And(expr,z3.Not(spec["post"]))
    ]
    done=0
    for query in checks:
        smt=z3.Solver();smt.set(timeout=timeout_ms);smt.add(query)
        done+=1
        try:status=str(smt.check())
        except Exception:return "ABSTAIN_BACKEND_ERROR",done
        if status=="sat":return "INVALID_OR_NOT_INDUCTIVE",done
        if status!="unsat":return "ABSTAIN_UNKNOWN",done
    return "ALL_THREE_ORIGINAL_VCS_UNSAT",done

def load_specs(root):
    specs=[];seen=set()
    for logic,cap in SOURCE_COUNTS.items():
        paths=sorted((root/"benchmarks"/logic).rglob("*.sl"))[:cap]
        if not paths:raise ValueError("EMPTY_FIXED_ORIGIN_"+logic)
        for path in paths:
            raw=path.read_bytes();blob=blobhash(raw)
            rel=path.relative_to(root).as_posix()
            group="/".join(path.relative_to(root).parts[:3])
            split=("TRAIN" if group in TRAIN_GROUPS else
                   "HELDOUT" if group in EVAL_GROUPS else "DIAGNOSTIC")
            if blob in seen:raise ValueError("EXACT_ORIGINAL_DUPLICATE_NOT_ALLOWED")
            seen.add(blob)
            row={"path":rel,"source_sha":blob,"group":group,"split":split,"logic":logic,
                 "number":len(specs)}
            try:
                names,now,nxt,pre,trans,post=extract_original(sexprs(raw))
                ps=z3.Solver();ps.set(timeout=1500);ps.add(pre)
                prestatus=str(ps.check())
                row.update({"names":names,"variables":len(names),
                   "now":now,"next":nxt,"pre":pre,"trans":trans,"post":post,
                   "original_formulas":(pre,trans,post),
                   "syntactic_size":sum(len(x.sexpr()) for x in (pre,trans,post)),
                   "input_precondition_sat":prestatus,"parse_status":"OK"})
            except Exception as e:
                row["parse_status"]="ABSTAIN"
                row["parse_failure_type"]=type(e).__name__
            specs.append(row)
    return specs

def extract_template(spec):
    fp,relation,result,why,wall=direct_original_proof(spec)
    meta={"classical_first_outcome":result,"classical_wall_ms":round(wall,3)}
    if result!="unsat" or spec["input_precondition_sat"]!="sat":
        return None,meta
    try:
        cover=fp.get_cover_delta(-1,relation)
        for orientation in ("FORWARD","REVERSED"):
            mapped=z3.simplify(z3.substitute_vars(
                cover,*(spec["now"] if orientation=="FORWARD" else list(reversed(spec["now"])))
            ))
            outcome,calls=proof_vc(mapped,spec,TEST_VC_TIMEOUT)
            if outcome!="ALL_THREE_ORIGINAL_VCS_UNSAT" or z3.is_true(mapped) or z3.is_false(mapped):
                continue
            slots=[z3.Int("Q3P_CANONICAL_SLOT_"+str(i)) for i in range(len(spec["now"]))]
            canonical=z3.simplify(z3.substitute(mapped,*list(zip(spec["now"],slots))))
            if set(z3.z3util.get_vars(canonical))-set(slots):
                continue
            checksum=hashlib.sha256(canonical.sexpr().encode()).hexdigest()
            return {"canonical":canonical,"arity":len(slots),"sha256":checksum,
                    "nodes":len(re.findall(r"\(",canonical.sexpr())),
                    "original_training_source_sha":spec["source_sha"]},meta
    except Exception as e:
        meta["cover_failure_type"]=type(e).__name__
    return None,meta

def transfer(template,spec):
    if template["arity"]!=len(spec["now"]):return None
    slots=[z3.Int("Q3P_CANONICAL_SLOT_"+str(i)) for i in range(len(spec["now"]))]
    result=z3.simplify(z3.substitute(template["canonical"],*list(zip(slots,spec["now"]))))
    if set(z3.z3util.get_vars(result))-set(spec["now"]):
        raise ValueError("TYPED_TEMPLATE_TRANSFER_HAS_UNBOUND_VARIABLE")
    return result

class Scorer(nn.Module):
    def __init__(self):
        super().__init__()
        self.net=nn.Sequential(nn.Linear(FEATURE_SIZE,HIDDEN),
                               nn.Tanh(),nn.Linear(HIDDEN,1))
    def forward(self,x):return self.net(x).flatten()

def evaluate_models(specs,templates,trained,init,popularity):
    out=[];counts=collections.Counter();candidate_queries=collections.Counter()
    for spec in specs:
        row={"original_path":spec["path"],"original_sha":spec["source_sha"],
             "split":spec["split"],"group":spec["group"],"logic":spec["logic"],
             "eligible_candidates":0,"comparable_source_only_classical_specialist":"NOT_EXECUTED"}
        if spec["parse_status"]!="OK":
            row["status"]="ABSTAIN_ORIGINAL_PARSE"
            out.append(row);continue
        fp,relation,result,why,wall=direct_original_proof(spec)
        row["comparable_source_only_classical_specialist"]=result
        row["classical_run_wall_ms"]=round(wall,3)
        active=[]
        for t in templates:
            cand=transfer(t,spec)
            if cand is None:continue
            active.append((t,cand))
        row["eligible_candidates"]=len(active)
        if not active:
            row["status"]="NO_TRAINING_SOURCE_ARITY_COMPATIBLE_TYPED_AST"
            out.append(row);continue
        feats=torch.tensor([synth_features(spec,t,None,None) for t,_ in active],
                           dtype=torch.float32)
        with torch.no_grad():
            score_trained=trained(feats).tolist()
            score_init=init(feats).tolist()
        methods={
            "TRAINED":sorted(range(len(active)),key=lambda i:(-score_trained[i],active[i][0]["sha256"])),
            "UNTRAINED":sorted(range(len(active)),key=lambda i:(-score_init[i],active[i][0]["sha256"])),
            "POPULARITY":sorted(range(len(active)),key=lambda i:(-popularity[active[i][0]["sha256"]],active[i][0]["sha256"]))
        }
        results={}
        for method,order in methods.items():
            ms={}
            for quota in K:
                selected=order[:quota]
                if not selected:
                    ms[str(quota)]=0
                    continue
                p=0
                for i in selected:
                    status,calls=proof_vc(active[i][1],spec,TEST_VC_TIMEOUT)
                    candidate_queries[method]+=calls
                    if status=="ALL_THREE_ORIGINAL_VCS_UNSAT":p+=1
                ms[str(quota)]=int(p>0)
                counts[(method,quota)]+=int(p>0)
            results[method]=ms
        row["independently_original_VC_successes_by_method"]=results
        row["status"]="EVALUATED_COMPLETE_ORIGINAL_3VC"
        out.append(row)
    return out,counts,candidate_queries

def run(root):
    random.seed(SEED);torch.manual_seed(SEED);torch.set_num_threads(2)
    if blobhash((root/"LICENSE.md").read_bytes())!=EXPECTED_LICENSE_BLOB:
        raise ValueError("UPSTREAM_LICENSE_BLOB_CHANGED")
    specs=load_specs(root)
    groups=collections.Counter(s["split"] for s in specs)
    train=[s for s in specs if s["split"]=="TRAIN" and s["parse_status"]=="OK" and s["input_precondition_sat"]=="sat"]
    testing=[s for s in specs if s["split"]!="TRAIN"]
    if not train or not testing:raise ValueError("EMPTY_TRAIN_OR_DEV_HOLDOUT")
    if {s["source_sha"] for s in train}&{s["source_sha"] for s in testing}:
        raise ValueError("TRAIN_EVAL_ORIGINAL_HASH_OVERLAP")
    templates=[];tseen=set();train_extraction=[]
    t0=time.perf_counter_ns()
    for s in train:
        templ,meta=extract_template(s)
        train_extraction.append({"source_sha":s["source_sha"],**meta,
           "verified_training_template":templ is not None})
        if templ and templ["sha256"] not in tseen:
            tseen.add(templ["sha256"])
            templates.append(templ)
    extraction_ms=(time.perf_counter_ns()-t0)/1e6
    if not templates:
        return {"study":"Q3P_FIRST_TRUE_NEURAL_TYPED_OPERATOR_REPLAY",
            "status":"BLOCKED_NO_TRAINING_ORIGINAL_CERTIFIED_AST",
            "template_count":0,"group_census":dict(groups),"global_q1_q7":"OPEN"}
    # Use ALL eligible train candidates on ALL train original programs, with
    # exact three-VC labels; NO heldout solver/label consulted during fitting.
    xy=[];labels=[];oracle=collections.Counter();counts=collections.Counter()
    for s in train:
        for templ in templates:
            proposal=transfer(templ,s)
            if proposal is None:continue
            verdict,calls=proof_vc(proposal,s,TRAIN_VC_TIMEOUT)
            counts[verdict]+=1
            if verdict not in ("ALL_THREE_ORIGINAL_VCS_UNSAT","INVALID_OR_NOT_INDUCTIVE"):
                continue
            xy.append(synth_features(s,templ,None,None))
            yes=int(verdict=="ALL_THREE_ORIGINAL_VCS_UNSAT")
            labels.append(yes)
            oracle[templ["sha256"]]+=yes
    if not xy or sum(labels)==0:
        return {"study":"Q3P_FIRST_TRUE_NEURAL_TYPED_OPERATOR_REPLAY",
            "status":"BLOCKED_NO_TYPED_TRAINING_PAIRS",
            "template_count":len(templates),"train_oracle_verdicts":dict(counts),
            "global_q1_q7":"OPEN"}
    model=Scorer()
    init=Scorer();init.load_state_dict(model.state_dict())
    X=torch.tensor(xy,dtype=torch.float32)
    Y=torch.tensor(labels,dtype=torch.float32)
    positive=float(Y.sum())
    negative=len(Y)-positive
    criterion=nn.BCEWithLogitsLoss(pos_weight=torch.tensor(max(1.,negative/max(1.,positive))))
    opt=torch.optim.AdamW(model.parameters(),lr=0.008,weight_decay=0.0001)
    time_start=time.perf_counter_ns()
    losses=[]
    for epoch in range(SCORER_EPOCHS):
        model.train()
        logits=model(X);loss=criterion(logits,Y)
        opt.zero_grad();loss.backward();opt.step()
        if epoch in (0,SCORER_EPOCHS-1):losses.append(round(float(loss.item()),6))
    train_ms=(time.perf_counter_ns()-time_start)/1e6
    model.eval();init.eval()
    out,census,querycounts=evaluate_models(testing,templates,model,init,oracle)
    # Direct input original + trained/source-only baseline EXACT proof success.
    groups_out={}
    for split in ("HELDOUT","DIAGNOSTIC"):
        subset=[r for r in out if r["split"]==split]
        status=collections.Counter(r["status"] for r in subset)
        groups_out[split]={
          "evaluated_original_count":len(subset),
          "classical_source_only_spacer_full_original_safety":sum(
             r["comparable_source_only_classical_specialist"]=="unsat" for r in subset),
          "trained_TOP1_certified":sum(r.get("independently_original_VC_successes_by_method",{}).get("TRAINED",{}).get("1",0) for r in subset),
          "trained_TOP3_certified":sum(r.get("independently_original_VC_successes_by_method",{}).get("TRAINED",{}).get("3",0) for r in subset),
          "untrained_TOP3_certified":sum(r.get("independently_original_VC_successes_by_method",{}).get("UNTRAINED",{}).get("3",0) for r in subset),
          "popularity_TOP3_certified":sum(r.get("independently_original_VC_successes_by_method",{}).get("POPULARITY",{}).get("3",0) for r in subset),
          "status_counts":dict(status),
        }
    return {
      "study":"Q3P_FIRST_TRUE_NEURAL_TYPED_OPERATOR_REPLAY",
      "status":"FIRST_FROZEN_LEARNED_TYPED_SOURCE_ONLY_PROOF_AUDIT_COMPLETE",
      "source_commit":ORIGIN_COMMIT,
      "source_file_count":len(specs),
      "train_source_count":len(train),
      "train_origin_groups":sorted(TRAIN_GROUPS),
      "trained_on_eval_origin_group":False,
      "evaluation_origins":sorted(set(r["group"] for r in out)),
      "group_census":dict(groups),
      "strict_original_proven_distinct_training_AST_templates":len(templates),
      "template_family_source_sha256":[x["original_training_source_sha"] for x in templates],
      "training_pair_labels":{"total":len(labels),"positive":int(positive),"negative":int(negative),"abstained":sum(v for k,v in counts.items() if k not in ("ALL_THREE_ORIGINAL_VCS_UNSAT","INVALID_OR_NOT_INDUCTIVE"))},
      "train_oracle_verdicts":dict(counts),
      "training_neural_parameters":sum(p.numel() for p in model.parameters()),
      "training_neural_epochs":SCORER_EPOCHS,
      "neural_train_ms":round(train_ms,3),
      "classical_teacher_train_extraction_ms":round(extraction_ms,3),
      "neural_loss_start_end":losses,
      "all_model_eval_cases":groups_out,
      "total_exact_original_VC_calls_by_method":dict(querycounts),
      "contains_original_source_text_or_invariant_formulas":False,
      "model_trained_using_test_source_solutions":False,
      "model_new_math_primitive_created":False,
      "unopened_Q3F_original_source_access":False,
      "no_paid_provider":True,
      "global_q1_q7":"OPEN",
      "training_original_proof_extraction_receipts":train_extraction,
      "evaluation_original_records":out
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    a=p.parse_args()
    report=run(a.root)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(report,indent=2)+"\n")
    print("Q3P_FIRST_TRULY_TRAINED_TYPED_OPERATOR_VERDICT",report["status"])
    print("Q3P_FROZEN_TRAIN_TEMPLATES",report["strict_original_proven_distinct_training_AST_templates"])
    print("Q3P_FROZEN_NEURAL_COUNTS",report["training_pair_labels"])
    print("Q3P_ORIGINAL_PROOF_VS_ABLATIONS",report["all_model_eval_cases"])
    print("Q3P_Q1_TO_Q7",report["global_q1_q7"])

if __name__=="__main__":main()
