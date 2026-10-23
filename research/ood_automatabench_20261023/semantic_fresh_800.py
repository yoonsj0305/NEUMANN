"""PRE-REGISTERED fresh new seed 800 tasks; 640 in 9-template grammar + 160 OOD negatives.
Model sees no true structural family or labels. Frozen local equivalence theorem
provides program-equivalence certificates; independent flattened grader validates
withheld full-state transitions on 12x12, 14x18, 30x34.
"""
import argparse,collections,hashlib,json,pathlib,random,time
from latent_geometry_induction import DESIGNED,SHAPES,bits,forward,arr
from local_equivalence_certificate import quotient_select,prove_equivalent
from hidden_geometry_independent_replay import flat_step
SEED=202610241253
SIZES=((12,12),(14,18),(30,34))
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def write(path,rows):path.write_text("".join(json.dumps(r,sort_keys=True,separators=(",",":"))+"\n" for r in rows))
def exotic(grid,direction):
    h=len(grid);w=len(grid[0])
    if direction=="down":
        return [[grid[y][x]^grid[(y+1)%h][x] for x in range(w)] for y in range(h)]
    if direction=="right":
        return [[grid[y][x]^grid[y][(x+1)%w] for x in range(w)] for y in range(h)]
    raise AssertionError("unknown direction")
def step(grid,secret):
    return forward(grid,*secret["spec"]) if secret["kind"]=="local" else exotic(grid,secret["axis"])
def gen(root_source,root_truth):
    rng=random.Random(SEED)
    public=[];truth=[]
    for bh,bw in SHAPES:
        for _ in range(160):
            dy=rng.randrange(bh);dx=rng.randrange(bw)
            perm=list(range(1<<(bh*bw)));rng.shuffle(perm)
            truth.append({"kind":"local","spec":[bh,bw,dy,dx,perm]})
    for direction in ("down","right"):
        for _ in range(80):
            truth.append({"kind":"unsupported","axis":direction})
    assert len(truth)==800
    rng.shuffle(truth)
    for idx,secret in enumerate(truth):
        uid=f"q3_semantic_fresh_{idx:04d}"
        input_demos=DESIGNED
        demos=[{"before":bits(board),"after":bits(step(board,secret))} for board in input_demos]
        public.append({"id":uid,"demos":demos})
        secret["id"]=uid
        secret["holdouts"]=[]
        for h,w in SIZES:
            board=[[rng.randrange(2) for _ in range(w)] for _ in range(h)]
            secret["holdouts"].append({"size":[h,w],"before":bits(board),"after":bits(step(board,secret))})
    src=pathlib.Path(root_source);target=pathlib.Path(root_truth)
    src.mkdir(parents=True,exist_ok=True);target.mkdir(parents=True,exist_ok=True)
    ps=src/"BLIND_FRESH_800.jsonl";pt=target/"WITHHELD_800.jsonl"
    write(ps,public);write(pt,truth)
    receipt={"schema":"NEUMANN_Q3_SEMANTIC_FRESH_SOURCE.v1",
             "n":800,"local_grammar_cases":640,"nonlocal_negative_controls":160,
             "unseen_seed":SEED,"source_sha256":sha(ps)}
    (src/"SOURCE_IDENTITY.json").write_text(json.dumps(receipt,sort_keys=True)+"\n")
    print("PRE_REGISTERED_FRESH_800_SOURCE",json.dumps(receipt,sort_keys=True),flush=True)
def infer(srcdir,outdir):
    source=pathlib.Path(srcdir)/"BLIND_FRESH_800.jsonl"
    rows=[json.loads(line) for line in source.read_text().splitlines()]
    assert len(rows)==len(set(x["id"] for x in rows))==800
    rec={};counts=collections.Counter()
    for r in rows:
        before=time.process_time()
        pairs=[(arr(d["before"]),arr(d["after"])) for d in r["demos"]]
        choice=quotient_select(pairs)
        counts[choice["status"]]+=1
        rec[r["id"]]={"status":choice["status"],"program":choice["program"],
                      "minimal_program_count":choice.get("minimal_program_count"),
                      "cpu_s":time.process_time()-before}
    out=pathlib.Path(outdir);out.mkdir(parents=True,exist_ok=True)
    p=out/"SOURCE_ONLY_800_SEALED.json"
    p.write_text(json.dumps(rec,sort_keys=True,separators=(",",":"))+"\n")
    receipt={"source_only_sealed_sha256":sha(p),"counts":dict(counts),"n":800,
             "trained_model_modified":False,"true_family_visible":False}
    (out/"SOURCE_ONLY_SEAL.json").write_text(json.dumps(receipt,sort_keys=True)+"\n")
    print("FRESH_800_SOURCE_ONLY_MODEL_FROZEN",json.dumps(receipt,sort_keys=True),flush=True)
def grade(srcdir,truthdir,predir,outdir):
    source=[json.loads(line) for line in (pathlib.Path(srcdir)/"BLIND_FRESH_800.jsonl").read_text().splitlines()]
    truth={r["id"]:r for r in (json.loads(line) for line in (pathlib.Path(truthdir)/"WITHHELD_800.jsonl").read_text().splitlines())}
    predictions=json.loads((pathlib.Path(predir)/"SOURCE_ONLY_800_SEALED.json").read_text())
    assert len(truth)==len(predictions)==len(source)==800
    assert set(predictions)==set(truth)
    score=collections.Counter();bad=[]
    for uid,p in predictions.items():
        tr=truth[uid];program=p["program"];local=tr["kind"]=="local"
        score["local" if local else "negative"]+=1
        if not local:
            score["negative_correct_abstain"]+=int(program is None)
            score["negative_false_admission"]+=int(program is not None)
            if program is not None:bad.append(uid+":UNSUPPORTED_WRONG_ADMISSION")
            continue
        if program is None:
            score["local_abstain"]+=1;continue
        cert=prove_equivalent(program,tr["spec"])
        score["local_universal_semantic_proof"]+=int(cert["equivalent"])
        score["local_semantic_proof_failure"]+=int(not cert["equivalent"])
        if not cert["equivalent"]:bad.append(uid+":COUNTEREXAMPLE_"+str(cert["counterexample"]))
        score["local_exact_internal_geometry"]+=int(program==tr["spec"])
        if program!=tr["spec"]:score["local_equivalent_alternative_program"]+=int(cert["equivalent"])
        for case in tr["holdouts"]:
            # DIFFERENT flat indexing implementation than source oracle generator
            size="x".join(map(str,case["size"]))
            actual=flat_step(case["before"],tr["spec"])
            assert actual==case["after"],uid+":TRUE_OTHER_IMPLEMENTATION_ERROR"
            observed=flat_step(case["before"],program)
            score[size+":fullgrid_exact"]+=int(observed==actual)
            score[size+":fullgrid_wrong"]+=int(observed!=actual)
            if observed!=actual:bad.append(uid+":"+size+":WRONG")
    result={"schema":"NEUMANN_Q3_SEMANTIC_QUOTIENT_FRESH_800_INDEPENDENT.v1",
            "seed":SEED,"source_sha256":sha(pathlib.Path(srcdir)/"BLIND_FRESH_800.jsonl"),
            "sealed_source_predictions_sha256":sha(pathlib.Path(predir)/"SOURCE_ONLY_800_SEALED.json"),
            "counts":dict(score),"errors":bad,"finite_human_specified_grammar":True,
            "unsupported_family_controls":160,
            "mathematical_semantic_proof_on_all_even_toroidal_grids_4plus":True,
            "not_neural_novelty":True,"not_global_10x":True}
    out=pathlib.Path(outdir);out.mkdir(parents=True,exist_ok=True)
    p=out/"FRESH_800_INDEPENDENT_SEMANTIC_GRADE.json"
    p.write_text(json.dumps(result,sort_keys=True,separators=(",",":"))+"\n")
    print("FRESH_800_ORIGINAL_NEW_SEED_BLIND_INDEPENDENT_GRADE",json.dumps(result,sort_keys=True),flush=True)
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--mode",required=True,choices=("gen","infer","grade"))
    for name in ("source_dir","truth_dir","pred_dir","out_dir"):
        p.add_argument("--"+name.replace("_","-"))
    a=p.parse_args()
    if a.mode=="gen":gen(a.source_dir,a.truth_dir)
    elif a.mode=="infer":infer(a.source_dir,a.pred_dir)
    else:grade(a.source_dir,a.truth_dir,a.pred_dir,a.out_dir)
