#!/usr/bin/env python3
"""Q3 exact source-only partition: provable known vs constructive ambiguous CA interior.
Original target truth and hidden model metadata are physically unavailable.
"""
import argparse,collections,hashlib,json,pathlib
from version_space_certifier import infer
from active_identifiability_bound import profile

def main():
    a=argparse.ArgumentParser();a.add_argument("--masked-dir",required=True);a.add_argument("--out",required=True)
    x=a.parse_args();result={"schema":"NEUMANN_CA_REAL2000_SOURCE_INFORMATION_CONSERVATION.v1",
        "n":2000,"source_only":True,"source_truth_seen":False,"oracle_metadata_seen":False,
        "conditional_class":"fixed radius3 one-step deterministic CA with arbitrary binary-capable lookup",
        "splits":{},"individual_certificates_sha256":{}}
    for split in ("test_interpolation","test_extrapolation"):
        rows=[json.loads(v) for v in (pathlib.Path(x.masked_dir)/(split+".jsonl")).read_text().splitlines()]
        assert len(rows)==1000
        stats=collections.Counter()
        records={}
        for task in rows:
            assert "solution" not in task and "meta" not in task and "program" not in task
            uid=task["id"];assert uid not in records
            pos=profile(task);certainty=infer(task)["variants"]["3"]
            stats["n"]+=1
            if pos["status"] in ("CONSTRUCTIVE_AMBIGUITY","ALL_R3_QUERY_INTERIOR_KNOWN"):
                assert pos["known_r3"]+pos["missing_r3_cells"]==pos["interior_cells"],uid
                assert certainty["certified_cells"]==pos["known_r3"],uid
                assert sum(z is not None for z in certainty["outputs"])==pos["known_r3"],uid
                stats["eligible_tasks"]+=1
                stats["eligible_interior_cells"]+=pos["interior_cells"]
                stats["certified_known_cells"]+=pos["known_r3"]
                stats["constructively_ambiguous_cells"]+=pos["missing_r3_cells"]
                stats["unique_new_transitions_required"]+=pos["missing_distinct"]
                if pos["witness"]:stats["constructive_two_rule_tasks"]+=1
            else:
                assert certainty["certified_cells"]==0,uid
                stats[pos["status"]]+=1
            records[uid]={"status":pos["status"],"R3_all_source_models_agree":certainty["certified_cells"],
              "actual_query_r3_known":pos["known_r3"],"source_indistinguishable":pos["missing_r3_cells"],
              "minimum_labels":pos["missing_distinct"],"source_length":pos["n"]}
        assert stats["eligible_interior_cells"]==stats["certified_known_cells"]+stats["constructively_ambiguous_cells"]
        result["splits"][split]=dict(stats)
        result["individual_certificates_sha256"][split]=hashlib.sha256(json.dumps(records,sort_keys=True,separators=(",",":")).encode()).hexdigest()
        print("EXACT_SOURCE_INFORMATION_PARTITION",split,json.dumps(dict(stats),sort_keys=True),flush=True)
    combined=collections.Counter()
    for d in result["splits"].values():combined.update(d)
    assert combined["n"]==2000
    assert combined["eligible_tasks"]+combined["UNSUPPORTED_SHORT_DEMONSTRATION_CONTEXT"]==2000
    assert combined["eligible_interior_cells"]==10135
    assert combined["certified_known_cells"]==1155
    assert combined["constructively_ambiguous_cells"]==8980
    assert combined["unique_new_transitions_required"]==8922
    assert combined["constructive_two_rule_tasks"]==1577
    assert combined["UNSUPPORTED_SHORT_DEMONSTRATION_CONTEXT"]==406
    result["total"]=dict(combined)
    out=pathlib.Path(x.out);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,sort_keys=True,separators=(",",":"))+"\n")
    print("INFORMATION_CONSERVATION_REAL2000_COMPLETE_PASS",json.dumps(result["total"],sort_keys=True),flush=True)
    print("SOURCE_ONLY_INFORMATION_CONSERVATION_SHA256",hashlib.sha256(out.read_bytes()).hexdigest(),flush=True)
if __name__=="__main__":main()
