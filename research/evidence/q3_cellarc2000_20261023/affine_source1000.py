"""Frozen-first original CellARC 10th1000 test of new source-fitted affine rule process."""
import argparse,collections,hashlib,json,pathlib,time
from affine_spacetime_reconstruction import combined_with_affine

def main():
    p=argparse.ArgumentParser();p.add_argument("--mode",choices=("infer","grade"),required=True)
    p.add_argument("--masked");p.add_argument("--source");p.add_argument("--sealed");p.add_argument("--out",required=True)
    a=p.parse_args()
    if a.mode=="infer":
        rows={};counts=collections.Counter();begin=time.process_time()
        for line in pathlib.Path(a.masked).read_text().splitlines():
            task=json.loads(line)
            assert "solution" not in task and "meta" not in task and "program" not in task
            assert task["id"] not in rows
            val=combined_with_affine(task);rows[task["id"]]=val
            counts["n"]+=1
            counts["route_"+val["route"]]+=1
            counts["new_"+val["affine"]["status"]]+=1
            if counts["n"]%200==0:print("TENTH1000_AFFINE_PROGRESS",counts["n"],dict(counts),flush=True)
        assert len(rows)==1000
        doc={"schema":"NEUMANN_CA_AFFINE_SOURCE_ONLY_TENTH1000.v1","n":1000,
             "original_test_answers_seen":False,"hidden_true_metadata_seen":False,
             "model_has_neural_training":False,"source_cpu_s":time.process_time()-begin,
             "counts":dict(counts),"rows":rows}
        print("SOURCE_ONLY_TENTH1000_AFFINE",json.dumps(dict(counts),sort_keys=True),flush=True)
    else:
        prefile=pathlib.Path(a.sealed);before=json.loads(prefile.read_text())
        assert before["n"]==1000 and not before["original_test_answers_seen"] and not before["hidden_true_metadata_seen"]
        counts=collections.Counter();records={}
        for line in pathlib.Path(a.source).read_text().splitlines():
            t=json.loads(line);res=before["rows"][t["id"]];target=t["solution"]
            prior=res["prior"]["combined_prediction"]
            new=res["affine"].get("prediction")
            combined=res["prediction"]
            for kind,guess in (("prior",prior),("affine",new),("combined",combined)):
                correct=guess is not None and guess==target
                counts[kind+"_attempted"]+=int(guess is not None)
                counts[kind+"_correct"]+=int(correct)
                counts[kind+"_wrong"]+=int(guess is not None and not correct)
            counts["n"]+=1
            if res["route"]=="AFFINE":
                counts["new_additional_correct"]+=int(combined==target)
                counts["new_additional_wrong"]+=int(combined!=target)
            records[t["id"]]={"route":res["route"],"affine_status":res["affine"]["status"],
                "prior_correct":prior is not None and prior==target,
                "new_correct":new is not None and new==target}
        assert counts["n"]==len(records)==1000
        doc={"schema":"NEUMANN_CA_AFFINE_SOURCE_ONLY_ORIGINAL_TENTH1000_INDEPENDENT_SCORE.v1",
            "n":1000,"counts":dict(counts),"individual":records,
            "original_source_predictions_sha256":hashlib.sha256(prefile.read_bytes()).hexdigest(),
            "hidden_metadata_forbidden_in_source_inference":True,
            "new_neural_only_primitive":"NOT_PROVED","end_to_end_10x":"OPEN"}
        print("ORIGINAL_TENTH1000_AFFINE_INDEPENDENT_GRADE",json.dumps(dict(counts),sort_keys=True),flush=True)
    out=pathlib.Path(a.out);out.parent.mkdir(exist_ok=True,parents=True)
    out.write_text(json.dumps(doc,sort_keys=True,separators=(",",":"))+"\n")
    print("TENTH1000_AFFINE_EVIDENCE_SHA256",hashlib.sha256(out.read_bytes()).hexdigest(),flush=True)
if __name__=="__main__":main()
