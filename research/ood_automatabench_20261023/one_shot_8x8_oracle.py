"""One 8x8 full-state intervention packs sixteen 2x2 rule inputs into ONE call.

Scope: an accessible phase-0 8x8 complete one-step CA oracle and a KNOWN
2x2 reversible Margolus family. Total observed bit/cell volume equals four
4x4 calls (64 input + 64 output bits). Query count 4 -> 1, NOT a 4x
physical CPU/energy claim and NOT an unmodified author's benchmark.
Separately sealed source inference and independent author grading.
"""
from __future__ import annotations
import argparse,collections,hashlib,json,pathlib,time

UPSTREAM = "7d86373fdb63fe1bd3592ddf71d923ceebc5acd9"
SPLITS = ("public_dev", "public_eval")

def packed8():
    from reversible_ca_solver import blocks
    board = [[0]*8 for _ in range(8)]
    for pattern,block in enumerate(blocks(8,8,0)):
        assert pattern < 16
        for j,(y,x) in enumerate(block):
            board[y][x] = (pattern>>j)&1
    return board

def to_virtual_four(before,after):
    assert len(before)==len(after)==8
    result=[]
    for y0 in (0,4):
        for x0 in (0,4):
            result.append({
                "before":["".join(str(before[y][x]) for x in range(x0,x0+4)) for y in range(y0,y0+4)],
                "after":["".join(str(after[y][x]) for x in range(x0,x0+4)) for y in range(y0,y0+4)]
            })
    return result

def prepare(original_dir,source_dir):
    from reversible_ca_solver import roll_one
    from hidden_rule_inference import source_pair_mapping
    from optimal_four_probe_generator import design_probe
    out=pathlib.Path(source_dir);out.mkdir(parents=True,exist_ok=True)
    p8=packed8()
    bysplit={}
    allrules=[]
    for split in SPLITS:
        raw=(pathlib.Path(original_dir)/(split+".jsonl")).read_bytes()
        tasks=[json.loads(line) for line in raw.splitlines()]
        assert len(tasks)==300 and len({t["id"] for t in tasks})==300
        rows=[]
        for t in tasks:
            perm=t["rule"]["permutation"]
            assert sorted(perm)==list(range(16))
            after=roll_one(p8,0,perm)  # EXACTLY ONE real 8x8 oracle invocation
            beforetxt=["".join(map(str,row)) for row in p8]
            aftertxt=["".join(map(str,row)) for row in after]
            demos=to_virtual_four(p8,after)
            mapping,error=source_pair_mapping(demos)
            assert error is None and len(mapping)==16 and all(mapping[i]==perm[i] for i in range(16))
            masked={k:v for k,v in t.items() if k not in ("answer","metadata")}
            masked["rule"]={"type":"margolus_block_ca"}
            r={"id":t["id"],"task":masked,"intervention":{"before":beforetxt,"after":aftertxt},
               "actual_full_grid_source_oracle_calls":1,"input_bits":64,"output_bits":64}
            assert "permutation" not in json.dumps(r) and "answer" not in json.dumps(r)
            rows.append(r)
            allrules.append(perm)
        target=out/(split+"_ONE8_SOURCE_ONLY.jsonl")
        target.write_text("".join(json.dumps(r,sort_keys=True,separators=(",",":"))+"\n" for r in rows))
        bysplit[split]={"source_sha256":hashlib.sha256(target.read_bytes()).hexdigest(),
                        "original_raw_sha256":hashlib.sha256(raw).hexdigest(),"count":300}
    # Paired source generator compute only; no claims about physical oracle overhead.
    four=[design_probe(i) for i in range(4)]
    measures={"4x4_four_calls":[],"8x8_one_call":[]}
    for trial in range(7):
        order=("4x4_four_calls","8x8_one_call") if trial%2==0 else ("8x8_one_call","4x4_four_calls")
        for kind in order:
            start=time.process_time()
            for rule in allrules:
                if kind=="4x4_four_calls":
                    for board in four:roll_one(board,0,rule)
                else:roll_one(p8,0,rule)
            measures[kind].append(time.process_time()-start)
    import statistics
    audit={"schema":"NEUMANN_ONE8_INTERVENTION_SOURCE_SEAL.v1","splits":bysplit,
           "native_oracle_calls_per_original_task":1,
           "four_4x4_baseline_calls_per_task":4,"total_input_bits_each_strategy":64,
           "total_output_bits_each_strategy":64,"controlled_grid_8x8_is_extra_assumption":True,
           "source_generation_cpu_seconds_seven_runs":measures,
           "source_generation_cpu_medians_s":{k:statistics.median(v) for k,v in measures.items()},
           "total_task_count":600,"neural_exclusive_novelty":"NOT_PROVED",
           "whole_system_10x":"NOT_PROVED"}
    (out/"SOURCE_SEAL.json").write_text(json.dumps(audit,sort_keys=True)+"\n")
    print("ONE8_SOURCE_PREPARED_600",json.dumps(audit,sort_keys=True),flush=True)

def infer(source_dir,pred_dir):
    from hidden_rule_inference import source_pair_mapping,discover
    out=pathlib.Path(pred_dir);out.mkdir(parents=True,exist_ok=True)
    proofs={}
    for split in SPLITS:
        rows=[json.loads(line) for line in
              (pathlib.Path(source_dir)/(split+"_ONE8_SOURCE_ONLY.jsonl")).read_text().splitlines()]
        result={}
        for r in rows:
            assert "answer" not in r["task"] and "metadata" not in r["task"]
            assert "permutation" not in r["task"]["rule"]
            q=r["intervention"]
            before=[[int(z) for z in row] for row in q["before"]]
            after=[[int(z) for z in row] for row in q["after"]]
            begin=time.process_time()
            virtual=to_virtual_four(before,after)
            mapping,error=source_pair_mapping(virtual)
            assert error is None and len(mapping)==16
            wrapper={"task":r["task"],"demos":virtual}
            guess=discover(wrapper,policy="lookup") # PRE-EXISTING FROZEN SOLVER
            cpu=time.process_time()-begin
            result[r["id"]]={"rule_prediction":[mapping[i] for i in range(16)],
                             "status":guess["status"],"prediction":guess["prediction"],
                             "cpu_s":cpu,"actual_oracle_calls":1}
        assert len(result)==300
        p=out/(split+"_ONE8_PRE_GRADE.json")
        p.write_text(json.dumps(result,sort_keys=True,separators=(",",":"))+"\n")
        proofs[split]={"predictions_sha256":hashlib.sha256(p.read_bytes()).hexdigest(),
                       "predictions":len(result),"cpu_s":sum(v["cpu_s"] for v in result.values())}
    (out/"PREDICTION_SEAL.json").write_text(json.dumps(proofs,sort_keys=True)+"\n")
    print("ONE8_BLIND_PREDICTIONS_600",json.dumps(proofs,sort_keys=True),flush=True)

def grade(original_dir,source_dir,pred_dir,grade_dir):
    from source_then_official_grade import official_verifier
    authentic,auth_sha=official_verifier(UPSTREAM)
    out=pathlib.Path(grade_dir);out.mkdir(parents=True,exist_ok=True)
    report={"schema":"NEUMANN_ONE8_TWO_SPLIT_INDEPENDENT_AUTHOR_GRADE.v1",
            "upstream_pinned":UPSTREAM,"official_verifier_sha256":auth_sha,
            "counts":{},"failures":[],"blind_source_no_true_rule":True,
            "extra_8x8_one_step_oracle":"YES_NOT_OFFICIAL_RAW_BENCHMARK",
            "fully_new_neural_structure":"NOT_PROVED","full_system_10x":"NOT_PROVED"}
    stats=collections.Counter()
    for split in SPLITS:
        orig=(pathlib.Path(original_dir)/(split+".jsonl")).read_bytes()
        truth={x["id"]:x for x in (json.loads(z) for z in orig.splitlines())}
        source=(pathlib.Path(source_dir)/(split+"_ONE8_SOURCE_ONLY.jsonl")).read_text().splitlines()
        assert len(source)==len(truth)==300
        records=json.loads((pathlib.Path(pred_dir)/(split+"_ONE8_PRE_GRADE.json")).read_text())
        assert set(records)==set(truth)
        for ident,result in records.items():
            tr=truth[ident]
            assert authentic(tr,tr["answer"])
            ruleok=result["rule_prediction"]==tr["rule"]["permutation"]
            initial=result.get("prediction")
            initialok=initial==tr["answer"]["initial_state"] and bool(authentic(tr,initial)) if initial else False
            stats[split+":total"]+=1
            stats[split+":rule_correct"]+=bool(ruleok)
            stats[split+":initial_correct"]+=bool(initialok)
            stats[split+":wrong_submitted"]+=bool(initial is not None and not initialok)
            if not (ruleok and initialok):report["failures"].append(ident)
    assert sum(stats[s+":total"] for s in SPLITS)==600
    report["counts"]=dict(stats)
    report["all_600_correct"]=not report["failures"]
    p=out/"ONE8_INDEPENDENT_ORIGINAL_600_GRADE.json"
    p.write_text(json.dumps(report,sort_keys=True,separators=(",",":"))+"\n")
    print("ONE8_INDEPENDENT_AUTHENTIC_600_RESULT",json.dumps(report,sort_keys=True),flush=True)

def selftest():
    import random,math
    from reversible_ca_solver import roll_one
    from hidden_rule_inference import source_pair_mapping
    rng=random.Random(202610231111)
    first=packed8()
    trials=10000
    for trial in range(trials):
        perm=list(range(16));rng.shuffle(perm)
        future=roll_one(first,0,perm)
        mapping,error=source_pair_mapping(to_virtual_four(first,future))
        assert error is None and len(mapping)==16
        assert [mapping[i] for i in range(16)]==perm
    print("ONE8_ALL_10000_HIDDEN_RULES_EXACT_PASS",trials,flush=True)

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--mode",required=True,choices=("prepare","infer","grade","selftest"))
    p.add_argument("--original-dir")
    p.add_argument("--source-dir")
    p.add_argument("--pred-dir")
    p.add_argument("--grade-dir")
    args=p.parse_args()
    if args.mode=="prepare":prepare(args.original_dir,args.source_dir)
    elif args.mode=="infer":infer(args.source_dir,args.pred_dir)
    elif args.mode=="grade":grade(args.original_dir,args.source_dir,args.pred_dir,args.grade_dir)
    else:selftest()
