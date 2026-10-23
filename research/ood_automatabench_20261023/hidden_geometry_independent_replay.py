"""After-grade independent-code replay of ALREADY SEALED 960 predictions.
Does not run, fit or modify the source learner. Checks common-mode risk by
implementing toroidal block updates via a NEW flattened-array indexing path.
Fresh 14x18 and 30x34 exact-program transfer are extra GENERATED tests.
"""
import argparse,collections,hashlib,json,pathlib,random
SPLITS=("public_dev","public_eval","generated")
SEALED={
"public_dev":"3d97016409efd9b625caff30378f478cbd17f09983ec50783647f0438cc1388f",
"public_eval":"71f2aaac4e62d629a84a63b4d398ad100b52f55d6d21b15b3a72fd42633f4144",
"generated":"f5c608f26143f3e64d07d0cf69d6ec3715536a4d6c70fe3641beb257d625cf28"}
def hashfile(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def flat_step(lines,spec):
    bh,bw,dy,dx,perm=spec
    h=len(lines);w=len(lines[0])
    assert h%bh==0 and w%bw==0 and 0<=dy<bh and 0<=dx<bw
    assert all(len(line)==w and set(line)<=set("01") for line in lines)
    input_buffer=[int(c) for line in lines for c in line]
    output_buffer=[-1]*(h*w)
    for gy in range(h//bh):
        for gx in range(w//bw):
            address=[]
            for row in range(bh):
                for col in range(bw):
                    y=(dy+gy*bh+row)%h;x=(dx+gx*bw+col)%w
                    address.append(y*w+x)
            pattern=sum(input_buffer[idx]*(1<<bit) for bit,idx in enumerate(address))
            mapped=perm[pattern]
            for bit,idx in enumerate(address):
                assert output_buffer[idx]<0,"duplicate torus assignment"
                output_buffer[idx]=(mapped>>bit)&1
    assert all(z in (0,1) for z in output_buffer)
    return ["".join(str(z) for z in output_buffer[y*w:(y+1)*w]) for y in range(h)]
def audit(truth_dir,pred_dir,out):
    count=collections.Counter();mistakes=[]
    for split in SPLITS:
        predfile=pathlib.Path(pred_dir)/(split+"_BLIND_PREDICTION.json")
        assert hashfile(predfile)==SEALED[split],f"source receipt altered: {split}"
        pred=json.loads(predfile.read_text())
        truth={j["id"]:j for j in (json.loads(line) for line in
            (pathlib.Path(truth_dir)/(split+".jsonl")).read_text().splitlines())}
        assert len(pred)==len(truth)==(360 if split=="generated" else 300)
        for uid,p in pred.items():
            t=truth[uid];true=t["spec"];learned=p["program"]
            count["total"]+=1
            trueout=flat_step(t["hold_before"],true)
            count["author_constructed_12x12_truth_flat_match"]+=int(trueout==t["hold_after"])
            if trueout!=t["hold_after"]:mistakes.append(uid+":TRUE_ORACLE_MISMATCH")
            if learned is None:
                count["UNKNOWN"]+=1;continue
            good=flat_step(t["hold_before"],learned)==t["hold_after"]
            count["previous_12x12_submission_pass"]+=int(good)
            count["previous_12x12_submission_fail"]+=int(not good)
            if not good:mistakes.append(uid+":PREDICTION_MISMATCH")
            exactly_same=learned==true
            count["exact_local_program"]+=int(exactly_same)
            if learned!=true:count["alternative_local_program"]+=1
            for h,w in ((14,18),(30,34)):
                # Never generate tests from inferences; same test board used for both models.
                rng=random.Random(int(hashlib.sha256(
                    (uid+":"+str(h)+":"+str(w)+":NEUMANN20261023").encode()).hexdigest()[:16],16))
                input_grid=["".join(str(rng.randrange(2)) for _ in range(w)) for _ in range(h)]
                correct=flat_step(input_grid,learned)==flat_step(input_grid,true)
                label=str(h)+"x"+str(w)
                count[label+":pass"]+=int(correct)
                count[label+":fail"]+=int(not correct)
                if not correct:
                    count[label+":nonidentical_explanation_fail"]+=int(not exactly_same)
                    mistakes.append(uid+":NEW_SIZE_"+label)
                if exactly_same:
                    assert correct,"same exact program must agree on arbitrary grid"
    result={"schema":"NEUMANN_Q3_HIDDEN_GEOMETRY_960_POSTGRADE_INDEPENDENT_FLAT_CA.v1",
            "original_prediction_sha256":SEALED,"counts":dict(count),
            "new_size_tested_on_sealed_programs":["14x18","30x34"],
            "common_mode_reduced":"NEW_SEPARATE_FLAT_INDEX_IMPLEMENTATION",
            "remaining_common_mode":"SAME_FINITE_GRAMMAR_ASSUMPTION_AND_GENERATED_12X12_TRUE_SPEC",
            "scientific_scope":"POSTGRADE_FROZEN_PREDICTION_AUDIT",
            "source_model_retrained":False,"new_external_author_benchmark":False,
            "mistakes":mistakes,
            "neural_exclusive_novelty":"NOT_PROVED","whole_system_10x":"NOT_PROVED"}
    target=pathlib.Path(out);target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(result,sort_keys=True,separators=(",",":"))+"\n")
    print("INDEPENDENT_FLAT_REPLAY_EXISTING_960_AND_NEW_RECTANGLES",json.dumps(result,sort_keys=True),flush=True)
    assert count["total"]==960
    assert count["author_constructed_12x12_truth_flat_match"]==960
    assert count["previous_12x12_submission_pass"]==948
    assert count["previous_12x12_submission_fail"]==0
    assert count["UNKNOWN"]==12
    assert count["exact_local_program"]==935
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--truth-dir",required=True)
    p.add_argument("--pred-dir",required=True)
    p.add_argument("--out",required=True)
    a=p.parse_args()
    audit(a.truth_dir,a.pred_dir,a.out)
