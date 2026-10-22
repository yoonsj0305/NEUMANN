"""Independent POSTGRADE-ONLY true generator audit for first source-affine new solve."""
import argparse,collections,hashlib,itertools,json,pathlib,urllib.request
SOURCE_COMMIT="76040e6aef0edc4982e53c13a85ef227378ed171"
SEALED_SHA="ce57c770864126008f819e7fad59926011d15008af0586c5314b9ec0c836dd72"
def fetch(repo,rev):
    url=f"https://huggingface.co/datasets/{repo}/resolve/{rev}/data/train.jsonl"
    req=urllib.request.Request(url,headers={"User-Agent":"NEUMANN-POSTGRADE-AFFINE-TRUE-FAMILY/1.0"})
    with urllib.request.urlopen(req,timeout=120) as f:raw=b"".join(itertools.islice(f,9000,10000))
    rows=[json.loads(x) for x in raw.splitlines()];assert len(rows)==1000
    return rows,hashlib.sha256(raw).hexdigest()
def main():
    p=argparse.ArgumentParser();p.add_argument("--sealed",required=True);p.add_argument("--out",required=True)
    a=p.parse_args();file=pathlib.Path(a.sealed);sha=hashlib.sha256(file.read_bytes()).hexdigest()
    assert sha==SEALED_SHA,(sha,SEALED_SHA)
    frozen=json.loads(file.read_text());assert frozen["n"]==1000 and not frozen["original_test_answers_seen"]
    orig,rawsha=fetch("mireklzicar/cellarc_100k",SOURCE_COMMIT)
    mr="mireklzicar/cellarc_100k_meta"
    req=urllib.request.Request("https://huggingface.co/api/datasets/"+mr,headers={"User-Agent":"NEUMANN-postgrade-ca"})
    with urllib.request.urlopen(req,timeout=120) as f:meta_rev=json.load(f)["sha"]
    meta,metasha=fetch(mr,meta_rev)
    true={q["id"]:q for q in orig}
    assert len(true)==1000 and len(set(q["id"] for q in meta))==1000
    cases=[];counts=collections.Counter()
    for item in meta:
        uid=item["id"];real=true[uid];r=frozen["rows"][uid]
        for key in ("train","query","solution"):assert item[key]==real[key],uid
        counts["original_count"]+=1
        prior=r["prior"]["combined_prediction"];new=r["affine"]["prediction"]
        counts["prior_correct"]+=int(prior is not None and prior==real["solution"])
        if r["route"]=="AFFINE":
            m=item["meta"]
            correct=new is not None and new==real["solution"]
            counts["new_attempted"]+=1;counts["new_correct"]+=int(correct)
            counts["new_true_"+str(m["family"])]+=1
            counts["new_construction_"+str(m["construction"])]+=1
            cases.append({"id":uid,"correct":correct,"true_family":m["family"],
                         "true_radius":m["radius"],"true_steps":m["steps"],
                         "true_construction":m["construction"],
                         "affine_status":r["affine"]["status"],
                         "admitted_models":r["affine"].get("trajectory_admitted_models")})
    assert counts["original_count"]==1000 and counts["prior_correct"]==195 and counts["new_attempted"]==counts["new_correct"]==1
    report={"schema":"NEUMANN_FIRST_AFFINE_CA_POSTGRADE_TRUE_ORIGINAL_FAMILY.v1",
            "all_original_1000_training_query_solution_match_meta":True,
            "original_source_commit":SOURCE_COMMIT,"original_dataset_sha256":rawsha,
            "metadata_revision":meta_rev,"metadata_sha256":metasha,
            "frozen_source_prediction_sha256":sha,"n":1000,
            "counts":dict(counts),"novel_source_task":cases,
            "metadata_unavailable_during_source_inference":True,
            "global_neural_only_discovery":"OPEN"}
    out=pathlib.Path(a.out);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,sort_keys=True)+"\n")
    print("AFFINE_POSTGRADE_TRUE_GENERATOR",json.dumps(dict(counts),sort_keys=True),flush=True)
    print("AFFINE_POSTGRADE_ONE_CASE",json.dumps(cases,sort_keys=True),flush=True)
    print("AFFINE_POSTGRADE_RECEIPT_SHA256",hashlib.sha256(out.read_bytes()).hexdigest(),flush=True)
if __name__=="__main__":main()
