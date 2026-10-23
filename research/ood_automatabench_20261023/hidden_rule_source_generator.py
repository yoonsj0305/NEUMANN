"""Create source-only controlled hidden-rule tasks from another author's original CA test.

The ORIGINAL published task supplies a permutation. For THIS NEW stress
condition we remove that permutation entirely and produce independent
demonstration pairs of complete 4x4 input -> output transitions. Only the
data-construction job can see the original test labels and rule identities;
source model receives demonstration arrays and the blinded test query.
"""
import argparse,hashlib,json,pathlib,random
from reversible_ca_solver import roll_one
BUDGETS=(3,6,12)
SEED=202610230909

def create(original_file,root):
    original=pathlib.Path(original_file).read_bytes()
    rows=[json.loads(x) for x in original.splitlines()]
    assert len(rows)==300 and len(set(x["id"] for x in rows))==300
    rng=random.Random(SEED)
    task_rows=[]; manifest={"n_original":len(rows),"budgets":BUDGETS,"seed":SEED,
                          "original_raw_sha256":hashlib.sha256(original).hexdigest()}
    for original_task in rows:
        perm=original_task["rule"]["permutation"]
        assert len(perm)==16 and sorted(perm)==list(range(16))
        assert original_task["grid"]["height"]==original_task["grid"]["width"]==4
        demos=[]
        for i in range(max(BUDGETS)):
            x=[[rng.randrange(2) for _ in range(4)] for _ in range(4)]
            y=roll_one(x,0,perm)
            demos.append({"before":["".join(map(str,row)) for row in x],
                          "after":["".join(map(str,row)) for row in y]})
        blinded={k:v for k,v in original_task.items() if k not in ("answer","metadata")}
        blinded["rule"]={"type":"margolus_block_ca"}
        assert "permutation" not in blinded["rule"]
        for budget in BUDGETS:
            r={"id":original_task["id"]+"__demo"+str(budget),
               "original_id":original_task["id"],"budget":budget,
               "task":blinded,"demos":demos[:budget]}
            assert "answer" not in json.dumps(r) and "metadata" not in json.dumps(r)
            task_rows.append(r)
    assert len(task_rows)==900
    assert len(set(x["id"] for x in task_rows))==900
    root=pathlib.Path(root);root.mkdir(parents=True,exist_ok=True)
    f=root/"HIDDEN_RULE_CALIBRATION_900_SOURCE_ONLY.jsonl"
    f.write_text("".join(json.dumps(r,sort_keys=True,separators=(",",":"))+"\n" for r in task_rows))
    manifest["n_episodes"]=900
    manifest["masked_sha256"]=hashlib.sha256(f.read_bytes()).hexdigest()
    (root/"CALIBRATION_SOURCE_MANIFEST.json").write_text(json.dumps(manifest,sort_keys=True)+"\n")
    print("HIDDEN_RULE_300x3_TRUE_PERMUTATIONS_PHYSICALLY_ABSENT",json.dumps(manifest,sort_keys=True),flush=True)

if __name__=="__main__":
    a=argparse.ArgumentParser();a.add_argument("--original",required=True);a.add_argument("--out",required=True)
    ns=a.parse_args();create(ns.original,ns.out)
