"""Postgrade-only audit of frozen eighth and ninth original CellARC cohort receipts.

Never imported by either inference stage. Original test truth + secret generator
metadata are acquired ONLY after two separate preregistered original scorers PASS.
"""
import argparse,collections,hashlib,itertools,json,pathlib,urllib.request

REPO="mireklzicar/cellarc_100k"
META="mireklzicar/cellarc_100k_meta"
PIN="76040e6aef0edc4982e53c13a85ef227378ed171"
COHORTS=((7000,8000,"eighth"),(8000,9000,"ninth"))
SEALS={"eighth":"3c7c212291fe708e05e98c8c3524215f841d507f73419868206d46be4a76fb75",
       "ninth":"f7512cb4b3cd6a53b7659e4a1cdf27f86bcf0d1025d4091dbd244125e2ccfdf4"}

def fetch_slice(repo,rev,start,stop):
    url=f"https://huggingface.co/datasets/{repo}/resolve/{rev}/data/train.jsonl"
    request=urllib.request.Request(url,headers={"User-Agent":"NEUMANN-POSTGRADE-ONLY-CA-META-AUDIT/1.0"})
    with urllib.request.urlopen(request,timeout=120) as stream:
        raw=b"".join(itertools.islice(stream,start,stop))
    lines=[json.loads(s) for s in raw.splitlines()]
    assert len(lines)==stop-start
    return lines,hashlib.sha256(raw).hexdigest()

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--eighth-sealed",required=True)
    p.add_argument("--ninth-sealed",required=True)
    p.add_argument("--out",required=True)
    a=p.parse_args()
    metadata_revision=json.loads(urllib.request.urlopen(
        urllib.request.Request("https://huggingface.co/api/datasets/"+META,
                               headers={"User-Agent":"NEUMANN-postgrade-metadata"}),timeout=120).read())["sha"]
    assert len(metadata_revision)==40
    overview={};alltypes=collections.Counter()
    for (lo,hi,name),prior_path in zip(COHORTS,[a.eighth_sealed,a.ninth_sealed]):
        pth=pathlib.Path(prior_path);actual_sha=hashlib.sha256(pth.read_bytes()).hexdigest()
        assert actual_sha==SEALS[name],(name,actual_sha)
        pre=json.loads(pth.read_text())
        assert pre["n"]==1000 and not pre["test_truth_seen"] and not pre["hidden_metadata_seen"]
        original,original_sha=fetch_slice(REPO,PIN,lo,hi)
        meta,meta_sha=fetch_slice(META,metadata_revision,lo,hi)
        originals={d["id"]:d for d in original}
        assert len(originals)==1000 and len({x["id"] for x in meta})==1000
        counter=collections.Counter();new_cases=[]
        for m in meta:
            uid=m["id"]
            d=originals[uid]
            for key in ("train","query","solution"):assert m[key]==d[key],(name,uid,key)
            q=pre["predictions"][uid]
            old=q["base"].get("prediction")
            new=q["reconstructed"].get("prediction")
            correct_old=old is not None and old==d["solution"]
            correct_new=new is not None and new==d["solution"]
            counter["n"]+=1;counter["baseline_correct"]+=int(correct_old)
            counter["baseline_wrong"]+=int(old is not None and not correct_old)
            if q["route"]=="SPACETIME":
                counter["novel_attempted"]+=1
                counter["novel_correct"]+=int(correct_new)
                counter["novel_wrong"]+=int(not correct_new)
                t=m["meta"]
                key=(str(t["construction"]),int(t["steps"]),int(t["radius"]),str(t["family"]))
                counter["construction_"+key[0]]+=1
                counter["steps_"+str(key[1])]+=1
                counter["family_"+key[3]]+=1
                alltypes[key]+=1
                new_cases.append({"id":uid,"true_construction":key[0],
                                  "true_steps":key[1],"true_radius":key[2],"true_family":key[3],
                                  "correct":correct_new,
                                  "proposed_full_rule_candidates":q["reconstructed"].get("full_rule_candidates"),
                                  "admitted_global_models":q["reconstructed"].get("viable_global_models")})
        assert counter["n"]==1000
        if name=="eighth":assert (counter["baseline_correct"],counter["baseline_wrong"],counter["novel_correct"],counter["novel_wrong"])==(167,1,8,0)
        else:assert (counter["baseline_correct"],counter["baseline_wrong"],counter["novel_correct"],counter["novel_wrong"])==(207,1,11,0)
        overview[name]={"counts":dict(counter),"source_original_sha256":original_sha,
                        "metadata_original_sha256":meta_sha,
                        "source_only_prediction_sha256":actual_sha,
                        "novel_task_strata":new_cases}
        print("POSTGRADE_REAL_HIDDEN_CA_CONSTRUCTION",name,json.dumps(dict(counter),sort_keys=True),flush=True)
    doc={"schema":"NEUMANN_FIRST_TWO_FROZEN_SPACETIME_POSTGRADE_META_IDENTITIES.v1",
         "n":2000,"original_repo_revision":PIN,"metadata_repo_revision":metadata_revision,
         "metadata_access_after_two_independent_grades":True,
         "all_2000_original_train_query_solution_matched_meta":True,
         "eighth_and_ninth":overview,
         "exact_19_additional_solution_true_generator_distribution":
             [{"construction":k[0],"steps":k[1],"radius":k[2],"family":k[3],"n":v} for k,v in sorted(alltypes.items())],
         "global_Q3_neural_exclusive":"NOT_PROVED","global_Q4_total10x":"OPEN"}
    out=pathlib.Path(a.out);out.parent.mkdir(exist_ok=True,parents=True)
    out.write_text(json.dumps(doc,sort_keys=True,separators=(",",":"))+"\n")
    print("POSTGRADE_TOTAL_NEW_GENERATOR_TYPES",json.dumps(doc["exact_19_additional_solution_true_generator_distribution"],sort_keys=True),flush=True)
    print("POSTGRADE_GENERATOR_AUDIT_SHA256",hashlib.sha256(out.read_bytes()).hexdigest(),flush=True)
if __name__=="__main__":main()
