"""No family label: infer a minimum finite-grammar local block program from transitions.
Nine geometric templates (1x1; two 1x2; two 2x1; four 2x2) are HUMAN-PREDEFINED.
Cannot establish neural-exclusive or open-ended structural invention.
"""
import argparse,collections,hashlib,json,pathlib,random,time
SHAPES=((1,1),(1,2),(2,1),(2,2))
SPLITS=("public_dev","public_eval")
PIN="7d86373fdb63fe1bd3592ddf71d923ceebc5acd9"
def bits(x):return ["".join(map(str,row)) for row in x]
def arr(x):return [[int(c) for c in row] for row in x]
def blocks(h,w,bh,bw,dy,dx):
    for y in range(dy,h,bh):
        for x in range(dx,w,bw):
            yield [((y+i)%h,(x+j)%w) for i in range(bh) for j in range(bw)]
def forward(board,bh,bw,dy,dx,perm):
    h=len(board);w=len(board[0]);out=[[0]*w for _ in range(h)]
    for loc in blocks(h,w,bh,bw,dy,dx):
        v=sum(board[y][x]<<k for k,(y,x) in enumerate(loc))
        z=perm[v]
        for k,(y,x) in enumerate(loc):out[y][x]=(z>>k)&1
    return out
def design(dy,dx):
    b=[[0]*8 for _ in range(8)]
    for i,loc in enumerate(blocks(8,8,2,2,dy,dx)):
        for k,(y,x) in enumerate(loc):b[y][x]=(i>>k)&1
    return b
DESIGNED=tuple(design(y,x) for y in range(2) for x in range(2))
def candidates(samples):
    ans=[]
    for bh,bw in SHAPES:
        for dy in range(bh):
            for dx in range(bw):
                mp={};rev={};ok=True
                for before,after in samples:
                    for loc in blocks(8,8,bh,bw,dy,dx):
                        src=sum(before[y][x]<<k for k,(y,x) in enumerate(loc))
                        dst=sum(after[y][x]<<k for k,(y,x) in enumerate(loc))
                        if (src in mp and mp[src]!=dst) or (dst in rev and rev[dst]!=src):
                            ok=False;break
                        mp[src]=dst;rev[dst]=src
                    if not ok:break
                if ok and len(mp)==(1<<(bh*bw)):
                    ans.append([bh,bw,dy,dx,[mp[k] for k in range(1<<(bh*bw))]])
    return ans
def choose(samples):
    all=candidates(samples)
    if not all:return None,"UNKNOWN_NO_SUPPORTED_PROGRAM",0
    complexity=min(p[0]*p[1] for p in all)
    small=[p for p in all if p[0]*p[1]==complexity]
    return (small[0],"MINIMUM_LOCAL_PROGRAM",len(all)) if len(small)==1 else (None,"UNKNOWN_MINIMUM_AMBIGUOUS",len(all))
def digest(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def write_rows(p,items):p.write_text("".join(json.dumps(x,sort_keys=True,separators=(",",":"))+"\n" for x in items))
def generate(original_dir,source_dir,truth_dir):
    rng=random.Random(202610231431)
    source=pathlib.Path(source_dir); truth=pathlib.Path(truth_dir)
    source.mkdir(parents=True,exist_ok=True);truth.mkdir(parents=True,exist_ok=True)
    report={}
    for split in SPLITS:
        original=(pathlib.Path(original_dir)/(split+".jsonl")).read_bytes()
        tasks=[json.loads(z) for z in original.splitlines()]
        assert len(tasks)==len(set(t["id"] for t in tasks))==300
        exposed=[];secret=[]
        for task in tasks:
            p=task["rule"]["permutation"];assert sorted(p)==list(range(16))
            spec=[2,2,0,0,p]; hold=[[rng.randrange(2) for _ in range(12)] for _ in range(12)]
            exposed.append({"id":task["id"],"demos":[{"before":bits(b),"after":bits(forward(b,*spec))} for b in DESIGNED],
                            "task":{k:v for k,v in task.items() if k not in ("answer","metadata","rule")}})
            secret.append({"id":task["id"],"spec":spec,"hold_before":bits(hold),
                           "hold_after":bits(forward(hold,*spec))})
        sf=source/(split+".jsonl");tf=truth/(split+".jsonl")
        write_rows(sf,exposed);write_rows(tf,secret)
        report[split]={"count":300,"original_sha":hashlib.sha256(original).hexdigest(),"source_sha":digest(sf)}
    exposed=[];secret=[]
    for bh,bw in SHAPES:
        for ix in range(90):
            dy=rng.randrange(bh);dx=rng.randrange(bw)
            p=list(range(1<<(bh*bw)));rng.shuffle(p);spec=[bh,bw,dy,dx,p]
            uid=f"generated_{bh}_{bw}_{ix}"
            hold=[[rng.randrange(2) for _ in range(12)] for _ in range(12)]
            exposed.append({"id":uid,"demos":[{"before":bits(b),"after":bits(forward(b,*spec))} for b in DESIGNED]})
            secret.append({"id":uid,"spec":spec,"hold_before":bits(hold),"hold_after":bits(forward(hold,*spec))})
    sf=source/"generated.jsonl";tf=truth/"generated.jsonl"
    write_rows(sf,exposed);write_rows(tf,secret)
    report["generated"]={"count":360,"source_sha":digest(sf)}
    (source/"SOURCE_MANIFEST.json").write_text(json.dumps(report,sort_keys=True)+"\n")
    print("SOURCE_CREATED_WITHOUT_RULE_FAMILY",json.dumps(report,sort_keys=True),flush=True)
def predict(source_dir,pred_dir):
    from hidden_rule_inference import discover
    from one_shot_8x8_oracle import to_virtual_four
    out=pathlib.Path(pred_dir);out.mkdir(parents=True,exist_ok=True)
    summary={}
    for split in (*SPLITS,"generated"):
        rows=[json.loads(x) for x in (pathlib.Path(source_dir)/(split+".jsonl")).read_text().splitlines()]
        answers={}
        for row in rows:
            assert "rule" not in row.get("task",{}) and "answer" not in row.get("task",{})
            ts=time.process_time()
            pairs=[(arr(d["before"]),arr(d["after"])) for d in row["demos"]]
            spec,status,count=choose(pairs)
            initial=None
            if "task" in row and spec is not None and spec[:4]==[2,2,0,0]:
                d=to_virtual_four(*pairs[0])
                wrapper={"task":{**row["task"],"rule":{"type":"margolus_block_ca"}},"demos":d}
                initial=discover(wrapper,policy="lookup")["prediction"]
            answers[row["id"]]={"program":spec,"status":status,"n_candidates":count,"initial":initial,
                                 "cpu_s":time.process_time()-ts}
        p=out/(split+"_BLIND_PREDICTION.json")
        p.write_text(json.dumps(answers,sort_keys=True,separators=(",",":"))+"\n")
        summary[split]={"count":len(answers),"sha":digest(p),"programs":sum(bool(x["program"]) for x in answers.values()),
                         "source_cpu_s":sum(x["cpu_s"] for x in answers.values())}
    (out/"PRE_GRADE_RECEIPT.json").write_text(json.dumps(summary,sort_keys=True)+"\n")
    print("BLIND_GEOMETRY_PREDICTIONS_FROZEN",json.dumps(summary,sort_keys=True),flush=True)
def grade(original_dir,pred_dir,truth_dir,out_dir):
    from source_then_official_grade import official_verifier
    verify,verifier_sha=official_verifier(PIN)
    counts=collections.Counter();wrong=[]
    for split in (*SPLITS,"generated"):
        raw=(pathlib.Path(truth_dir)/(split+".jsonl")).read_text().splitlines()
        truth={z["id"]:z for z in (json.loads(x) for x in raw)}
        pred=json.loads((pathlib.Path(pred_dir)/(split+"_BLIND_PREDICTION.json")).read_text())
        assert set(truth)==set(pred)
        if split in SPLITS:
            original={z["id"]:z for z in (json.loads(x) for x in (pathlib.Path(original_dir)/(split+".jsonl")).read_text().splitlines())}
        for uid,estimate in pred.items():
            counts[split+":total"]+=1
            if estimate["program"] is None:
                counts[split+":abstain"]+=1;continue
            spec=estimate["program"];actual=truth[uid]["spec"]
            exact_structure=spec[:4]==actual[:4]
            counts[split+":geometry_exact"]+=int(exact_structure)
            counts[split+":rule_exact"]+=int(spec==actual)
            projected=bits(forward(arr(truth[uid]["hold_before"]),*spec))
            good=projected==truth[uid]["hold_after"]
            counts[split+":holdout_12x12_correct"]+=int(good)
            counts[split+":holdout_12x12_wrong"]+=int(not good)
            if not good:wrong.append(uid+":holdout")
            if split in SPLITS:
                t=original[uid];prediction=estimate["initial"]
                correct=prediction==t["answer"]["initial_state"] and bool(verify(t,prediction)) if prediction else False
                counts[split+":initial_correct"]+=int(correct)
                counts[split+":initial_wrong"]+=int(prediction is not None and not correct)
                if prediction is not None and not correct:wrong.append(uid+":initial")
    report={"schema":"NEUMANN_Q3_FINITE_GRAMMAR_HIDDEN_GEOMETRY.v1",
            "original_author_pinned":PIN,"original_author_verifier_sha256":verifier_sha,
            "total_original":600,"generated_other_family":360,"counts":dict(counts),
            "submitted_wrong":wrong,"finite_grammar_human_specified":True,
            "holdout_12x12_seen_by_source":False,"neural_exclusive_discovery":"NOT_PROVED",
            "frontier_generalization":"NOT_PROVED","end_to_end_10x":"NOT_PROVED"}
    out=pathlib.Path(out_dir);out.mkdir(parents=True,exist_ok=True)
    p=out/"INDEPENDENT_STRUCTURE_AND_12x12_GRADE.json"
    p.write_text(json.dumps(report,sort_keys=True,separators=(",",":"))+"\n")
    print("INDEPENDENT_HIDDEN_GEOMETRY_600_AND_SYNTHETIC_360",json.dumps(report,sort_keys=True),flush=True)
def selftest():
    rng=random.Random(202610231432);c=collections.Counter()
    for bh,bw in SHAPES:
        for _ in range(250):
            dy=rng.randrange(bh);dx=rng.randrange(bw)
            p=list(range(1<<(bh*bw)));rng.shuffle(p)
            spec=[bh,bw,dy,dx,p]
            f,status,n=choose([(b,forward(b,*spec)) for b in DESIGNED])
            if f is None:c["UNKNOWN"]+=1;continue
            b=[[rng.randrange(2) for _ in range(12)] for _ in range(12)]
            good=forward(b,*f)==forward(b,*spec)
            c["PASS" if good else "FAIL"]+=1
    assert c["FAIL"]==0
    print("HIDDEN_GEOMETRY_1000_SELFTEST",dict(c),flush=True)
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--mode",required=True,choices=("selftest","generate","predict","grade"))
    for key in ("original_dir","source_dir","truth_dir","pred_dir","out_dir"):
        p.add_argument("--"+key.replace("_","-"))
    a=p.parse_args()
    if a.mode=="selftest":selftest()
    elif a.mode=="generate":generate(a.original_dir,a.source_dir,a.truth_dir)
    elif a.mode=="predict":predict(a.source_dir,a.pred_dir)
    else:grade(a.original_dir,a.pred_dir,a.truth_dir,a.out_dir)
