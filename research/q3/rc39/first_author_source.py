"""RC39 AFTER-LOCK synthetic task author and FIRST source-only inference.

The learner's source byte hash is locked in a pre-existing file BEFORE this
module was written. The author contains hidden target mappings, but passes
only (satisfying string, center index, membership oracle) to proposers.
The FIRST output contains proposals and SHA commitments, NOT original maps
or any independently graded holdout labels. Grader authored separately.
"""
from __future__ import annotations
from pathlib import Path
from hashlib import sha256,sha1
from time import process_time_ns
import json,random,sys
from research.q3.rc39.active_sparse import (
    ALPHABET,SCHEMA,discover,perturb,classical_single_site
)

TASK_COUNT=12
CENTER=512
RADIUS=512
SALT="NEUMANN-RC39-FIRST-SYNTHETIC-EXTERNAL-AUTHOR-20261106"
K_VALUES=(0,1,2,3,4,4,2,1,3,4,0,3)
SOURCE_EXPECTED_GIT_BLOB="bcfd1a6ac52f8e6e806fbf35bef5a0f7f2b48411"
ORIGINAL_SOURCE=Path("research/q3/rc39/active_sparse.py")
PREREG=Path("docs/research/q3_RC39_ACTIVE_CAUSAL_DISCOVERY_PREREG_2026_11_06.json")
PREREG_EXPECTED="e7469632595727d1d6ad108c8b34b60305c6e483"
LOCK=Path("docs/experiments/q3_RC39_FIRST_SOURCE_BLOB_LOCK_2026_11_06.json")
def blob(p):
    b=Path(p).read_bytes()
    return sha1(b"blob "+str(len(b)).encode()+b"\0").hexdigest()
def clean_bytes(o):
    return json.dumps(o,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
def reference(author,word,center):
    """This hidden author operation must NEVER be imported into proposer."""
    if type(word) is not str or not 0<=center<len(word):raise ValueError("INVALID_REFERENCE_QUERY")
    if word[center]!="B":return word[center]
    for d,letter in author["secret_reads"]:
        p=center+d
        if p<0 or p>=len(word) or word[p]!=letter:return "B"
    return "A"
def author_tasks():
    """All 12 completely source-independent fresh task secrets."""
    for i,k in enumerate(K_VALUES):
        rng=random.Random(0x39c700+i*17971)
        witness="".join(rng.choice(ALPHABET) for _ in range(2*RADIUS+1))
        witness=witness[:CENTER]+"B"+witness[CENTER+1:]
        options=[x for x in range(-RADIUS,RADIUS+1) if x!=0]
        chosen=sorted(rng.sample(options,k))
        target=[[d,witness[CENTER+d]] for d in chosen]
        hidden={"id":f"AUTHOR_NEW_{i:02d}", "secret_reads":target,
                "positive_witness":witness,"center":CENTER}
        assert reference(hidden,witness,CENTER)=="A"
        yield hidden
def strong_equal_rights_adaptive(witness,center,oracle):
    """Independently written optimized classical group search.

    Exactly the same witness, syntax rights, membership oracle and safe
    validation probes as the RC39 candidate. No secret mapping access.
    This is the strong classical baseline and can tie/be faster.
    """
    begin=process_time_ns();calls=[0]
    def ask(probe):
        calls[0]+=1
        return oracle(probe,center)
    if ask(witness)!="A":return {"status":"ABSTAIN","oracle_calls":calls[0]}
    positions=[i-center for i in range(len(witness)) if i!=center]
    hits=[]
    def visit(sub):
        if not sub:return
        result=ask(perturb(witness,sub,center))
        if result=="A":return
        if result!="B":raise ValueError("NOT_CONJUNCTION")
        if len(sub)==1:
            hits.append(sub[0]);return
        m=len(sub)//2
        visit(sub[:m]);visit(sub[m:])
    visit(positions)
    hits.sort()
    code={"schema":SCHEMA,"kind":"RELATIVE_EXACT_CONJUNCTION",
          "reads":[[d,witness[center+d]] for d in hits]}
    distinct=set(hits)
    checks=[positions, [x for x in positions if x not in distinct],hits]
    for d in list(range(-5,0))+list(range(1,6)):
        if d in positions:checks.append([d])
    for block in checks:
        sample=perturb(witness,block,center)
        predicted=strong_codegen(code,sample,center)
        if predicted!=ask(sample):return {"status":"ABSTAIN","oracle_calls":calls[0]}
    return {"status":"SOURCE_CONSISTENT_EXECUTABLE","program":code,
            "oracle_calls":calls[0],"cpu_us":(process_time_ns()-begin)/1000}
def strong_codegen(program,word,center):
    # Independent local implementation for parity; not calling learner.
    if word[center]!="B":return word[center]
    for d,v in program["reads"]:
        if not 0<=center+d<len(word) or word[center+d]!=v:return "B"
    return "A"
def run_first():
    assert blob(ORIGINAL_SOURCE)==SOURCE_EXPECTED_GIT_BLOB
    assert blob(PREREG)==PREREG_EXPECTED
    frozen=json.loads(LOCK.read_text())
    assert frozen["source_git_blob_sha1"]==SOURCE_EXPECTED_GIT_BLOB
    out=[]
    for target in author_tasks():
        # "target" is not an argument to the proposal and is never printed.
        witness=target["positive_witness"];center=target["center"]
        def oracle(word,index):return reference(target,word,index)
        new=discover(witness,center,oracle,max_queries=256)
        classic=classical_single_site(witness,center,oracle)
        equal=strong_equal_rights_adaptive(witness,center,oracle)
        out.append({
          "id":target["id"],
          "positive_witness_sha256":sha256(witness.encode()).hexdigest(),
          "hidden_author_spec_commitment":sha256(clean_bytes(target["secret_reads"])).hexdigest(),
          "positive_witness_supplied_by_author":True,
          "candidate":new,
          "classical_single_site":classic,
          "classical_strong_adaptive":equal,
          "hidden_author_mapping_in_first_receipt":False
        })
    summary={"N":len(out),"candidate_fitted":sum(x["candidate"]["status"]=="SOURCE_CONSISTENT_EXECUTABLE" for x in out),
      "baseline_single_site_fitted":sum(x["classical_single_site"]["status"]=="SOURCE_CONSISTENT_EXECUTABLE" for x in out),
      "baseline_strong_adaptive_fitted":sum(x["classical_strong_adaptive"]["status"]=="SOURCE_CONSISTENT_EXECUTABLE" for x in out),
      "candidate_source_queries":sum(x["candidate"]["oracle_calls"] for x in out),
      "classical_single_site_queries":sum(x["classical_single_site"]["oracle_calls"] for x in out),
      "classical_strong_adaptive_queries":sum(x["classical_strong_adaptive"]["oracle_calls"] for x in out),
      "candidate_sum_cpu_us":sum(x["candidate"].get("cpu_us",0) for x in out),
      "classical_single_site_sum_cpu_us":sum(x["classical_single_site"].get("cpu_us",0) for x in out),
      "classical_strong_adaptive_sum_cpu_us":sum(x["classical_strong_adaptive"].get("cpu_us",0) for x in out)}
    return {"schema":"neumann.q3.rc39.first-before-independent-grade.v1",
     "prereg_blob":PREREG_EXPECTED,"source_program_blob":SOURCE_EXPECTED_GIT_BLOB,
     "author_family":"SYNTHETIC_AUTHOR_SEPARATE_AFTER_SOURCE_LOCK",
     "reference_hidden_until_independent_grading":True,
     "human_supplied_conjunction_grammar":True,
     "positive_witness_plus_membership_oracle":True,
     "no_neural_model_training_or_inference":True,
     "genuinely_external_semantic_family":False,
     "goal_10x_all_in_cost":False,
     "q3_global":"OPEN","q6_cross_semantic_family":"OPEN",
     "summary":summary,"tasks":out}
if __name__=="__main__":
    if len(sys.argv)!=2:raise SystemExit("Usage: python -m research.q3.rc39.first_author_source FIRST_JSON_OUT")
    doc=run_first()
    Path(sys.argv[1]).write_text(json.dumps(doc,sort_keys=True,indent=2)+"\n")
    print(json.dumps({"schema":doc["schema"],"summary":doc["summary"],"statuses":
      [x["candidate"]["status"] for x in doc["tasks"]],"Q3":doc["q3_global"]},
      sort_keys=True),flush=True)
