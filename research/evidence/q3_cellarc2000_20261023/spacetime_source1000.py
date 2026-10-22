"""Original source 8th1000 unseen real CellARC, 3-job masked/grade experiment."""
import argparse,collections,hashlib,json,pathlib,time
from latent_spacetime_reconstruction import combined

def main():
    p=argparse.ArgumentParser();p.add_argument("--mode",choices=("infer","grade"),required=True)
    p.add_argument("--masked");p.add_argument("--source");p.add_argument("--sealed");p.add_argument("--out",required=True)
    a=p.parse_args()
    if a.mode=="infer":
        results={};counts=collections.Counter();start=time.process_time()
        for line in pathlib.Path(a.masked).read_text().splitlines():
            task=json.loads(line)
            assert "solution" not in task and "meta" not in task and "program" not in task
            uid=task["id"];assert uid not in results
            answer=combined(task);results[uid]=answer
            counts["n"]+=1;counts["route_"+answer["route"]]+=1
            counts["new_"+answer["reconstructed"]["status"]]+=1
            if counts["n"]%200==0:print("UNSEEN_SPACETIME_SOURCE_ONLY",counts["n"],dict(counts),flush=True)
        assert len(results)==1000
        report={"schema":"NEUMANN_CA_UNROLLED_TIME_RECON_ORIGINAL_EIGHTH1000.v1",
                "n":1000,"test_truth_seen":False,"hidden_metadata_seen":False,
                "neural_forwards":0,"source_only_cpu_s":time.process_time()-start,
                "status_counts":dict(counts),"predictions":results}
        print("NEW_SPACE_TIME_BEFORE_GRADE",json.dumps(dict(counts),sort_keys=True),flush=True)
    else:
        sealed=pathlib.Path(a.sealed);before=json.loads(sealed.read_text())
        assert before["n"]==1000 and not before["test_truth_seen"] and not before["hidden_metadata_seen"]
        counts=collections.Counter();records={}
        for line in pathlib.Path(a.source).read_text().splitlines():
            t=json.loads(line);entry=before["predictions"][t["id"]];actual=t["solution"]
            base=entry["base"].get("prediction");new=entry["reconstructed"].get("prediction")
            joint=entry["combined_prediction"]
            bc=base is not None and base==actual
            nc=new is not None and new==actual
            jc=joint is not None and joint==actual
            counts["n"]+=1
            for prefix,pred,correct in (("base",base,bc),("new",new,nc),("combined",joint,jc)):
                counts[prefix+"_attempted"]+=int(pred is not None)
                counts[prefix+"_correct"]+=int(correct)
                counts[prefix+"_wrong"]+=int(pred is not None and not correct)
            if entry["route"]=="SPACETIME":
                counts["new_recovered_from_old_abstain"]+=int(nc)
                counts["new_wrong_from_old_abstain"]+=int(not nc)
            records[t["id"]]={"route":entry["route"],"base_right":bc,"new_right":nc,"combined_right":jc}
        assert counts["n"]==len(records)==1000
        report={"schema":"NEUMANN_CA_UNROLLED_TIME_RECON_ORIGINAL_EIGHTH1000_INDEPENDENT.v1",
            "n":1000,"scores":dict(counts),"individual":records,
            "sealed_source_receipt_sha256":hashlib.sha256(sealed.read_bytes()).hexdigest(),
            "no_hidden_meta_or_targets_exposed_to_source_solver":True,
            "prior_dataset_disclosure":"published same-source CellARC generated release",
            "global_neural_exclusive_Q3":"OPEN","end_to_end_10x_Q4":"OPEN"}
        print("UNSEEN_SPACETIME_REAL_ORIGINAL_SCORE",json.dumps(dict(counts),sort_keys=True),flush=True)
    path=pathlib.Path(a.out);path.parent.mkdir(exist_ok=True,parents=True)
    path.write_text(json.dumps(report,sort_keys=True,separators=(",",":"))+"\n")
    print("SPACETIME_REAL_RECEIPT_SHA256",hashlib.sha256(path.read_bytes()).hexdigest(),flush=True)
if __name__=="__main__":main()
