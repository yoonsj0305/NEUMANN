"""NEUMANN RC39.1 AFTER source lock: first 16 synthetic author cases.

Hidden exact constraints exist in this module but not in the proposed
algorithm import. The proposer receives only the callable "first violated
offset or accepted", NOT desired symbol, satisfying example, or model labels.
This is a synthetic independent-author TASK generator, not external Q6.
"""
from __future__ import annotations
from pathlib import Path
from hashlib import sha1,sha256
from time import process_time_ns
import json,random,sys
from research.q3.rc39.explainable_no_witness import discover_without_positive,ALPHABET,PROGRAM_SCHEMA
SCHEMA="neumann.q3.rc39.1.first-author-source.v1"
K=(0,1,2,3,4,5,6,7,8,8,7,6,5,4,3,2)
SOURCE_SHA="da6d4f5ec5b5826683bd867e40c0590828d1b727"
PREREG_SHA="fbd3a88a61e39c233dcda8baabd4315bd0c0235a"
LOCK="docs/experiments/q3_RC39_1_FIRST_SOURCE_LOCK.json"
def blob(p):
    b=Path(p).read_bytes()
    return sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()
def canonical(x):
    return json.dumps(x,sort_keys=True,separators=(",",":")).encode()
def private_author_tasks():
    for i,k in enumerate(K):
        rng=random.Random(0x39e100+i*30011)
        offsets=list(range(-512,0))+list(range(1,513))
        chosen=sorted(rng.sample(offsets,k))
        spec=[[d,rng.choice(ALPHABET)] for d in chosen]
        yield {"id":f"RC39_1_NEW_{i:02d}","secret":spec}
def teacher_only(hidden,word,center):
    """Returns first OFFENDING OFFSET in stable ascending signed order."""
    assert len(word)==1025 and center==512 and word[center]=="B"
    for delta,expected in hidden["secret"]:
        if word[center+delta]!=expected:
            return {"status":"VIOLATION","offset":delta}
    return {"status":"ACCEPTED"}
def strong_classical_explanation(oracle,radius=512):
    """Independent, same-rights classical repair algorithm."""
    started=process_time_ns();calls=0;found={}
    def ask(word):
        nonlocal calls
        calls+=1
        return oracle("".join(word),radius)
    for _ in range(2*radius+1):
        changed=False
        for char in "ABC":
            row=[char]*(2*radius+1);row[radius]="B"
            for d,val in found.items():row[radius+d]=val
            answer=ask(row)
            if answer["status"]=="ACCEPTED":continue
            if answer["status"]!="VIOLATION":return {"status":"ABSTAIN"}
            d=answer["offset"]
            if d in found:return {"status":"ABSTAIN"}
            for trial in "ABC":
                if trial==char:continue
                row[radius+d]=trial
                follow=ask(row)
                if follow["status"]=="ACCEPTED" or follow.get("offset")!=d:
                    found[d]=trial;changed=True;break
            if not changed:return {"status":"ABSTAIN"}
            break
        if not changed:
            return {"status":"SOURCE_CONSISTENT_EXECUTABLE",
                "program":{"schema":PROGRAM_SCHEMA,"kind":"RELATIVE_EXACT_CONJUNCTION",
                    "reads":[[d,found[d]] for d in sorted(found)]},
                "oracle_calls":calls,"cpu_us":(process_time_ns()-started)/1000}
    return {"status":"ABSTAIN"}
def first():
    assert blob("research/q3/rc39/explainable_no_witness.py")==SOURCE_SHA
    assert blob("docs/experiments/q3_RC39_1_NO_POSITIVE_WITNESS_EXPLAINABLE_ORACLE_PREREG.json")==PREREG_SHA
    lock=json.loads(Path(LOCK).read_text())
    assert lock["source_git_blob"]==SOURCE_SHA
    rows=[]
    for target in private_author_tasks():
        def oracle(word,center):return teacher_only(target,word,center)
        candidate=discover_without_positive(oracle,radius=512,max_queries=64)
        classical=strong_classical_explanation(oracle,radius=512)
        rows.append({"id":target["id"],
            "hidden_author_spec_commitment":sha256(canonical(target["secret"])).hexdigest(),
            "oracle_first_failure_offset_only":True,
            "satisfying_witness_given":False,
            "candidate":candidate,"strong_equal_rights_classical":classical,
            "author_hidden_spec_not_passed_to_proposers":True})
    cs=sum(x["candidate"].get("oracle_calls",0) for x in rows)
    bs=sum(x["strong_equal_rights_classical"].get("oracle_calls",0) for x in rows)
    return {"schema":SCHEMA,
      "source_program_git_blob":SOURCE_SHA,"prereg_git_blob":PREREG_SHA,
      "author_style":"SYNTHETIC_AUTHOR_AFTER_SOURCE_LOCK",
      "new_no_positive_examples":True,
      "oracle_feedback":"FIRST_OFFENDING_OFFSET_ONLY_NO_EXPECTED_SYMBOL",
      "new_model_training_calls":0,"Q3":"OPEN","Q6":"OPEN",
      "counts":{"tasks":len(rows),
        "candidate_source_consistent":sum(x["candidate"]["status"]=="SOURCE_CONSISTENT_EXECUTABLE" for x in rows),
        "strong_classical_consistent":sum(x["strong_equal_rights_classical"]["status"]=="SOURCE_CONSISTENT_EXECUTABLE" for x in rows),
        "candidate_query_calls":cs,"strong_classical_query_calls":bs,
        "max_candidate_calls":max(x["candidate"]["oracle_calls"] for x in rows),
        "candidate_cpu_us_total":sum(x["candidate"].get("cpu_us",0) for x in rows),
        "strong_classical_cpu_us_total":sum(x["strong_equal_rights_classical"].get("cpu_us",0) for x in rows)
      },"rows":rows}
if __name__=="__main__":
    if len(sys.argv)!=2:raise SystemExit("python -m research.q3.rc39.first_explainable_author OUT.json")
    out=first()
    Path(sys.argv[1]).write_text(json.dumps(out,sort_keys=True,indent=2)+"\n")
    print(json.dumps({"schema":out["schema"],"counts":out["counts"],"source_only":True},sort_keys=True),flush=True)
