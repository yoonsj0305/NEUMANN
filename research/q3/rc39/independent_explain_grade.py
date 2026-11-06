"""RC39.1 independent after-FIRST exact author logic and context audit.

Neither imports nor reruns the hypothesis learner or the first author/source
generator. Reconstructs author task secrets from a separate deterministic
author rule after FIRST proposals were byte-frozen. Grades source-derived
program ASTs with a separate executable oracle and tests heldout contexts.
Synthetic, human-specified grammar and richer oracle. Global Q3/Q6 OPEN.
"""
from __future__ import annotations
import hashlib,json,random,sys
from pathlib import Path
from time import process_time_ns

FIRST_SHA256="5b3e7a69914e1da6c73b25caa35aa60a03ca0b4b85c2f8d5389dda4af914bc06"
LEARNER_SOURCE="da6d4f5ec5b5826683bd867e40c0590828d1b727"
AUTHOR_SOURCE="c465321116cb7268fb216027ce658710694719de"
PRIOR_LOCK="2199e43403860325cb46d052889c81fa30c42392"
ALPHABET="ABC"
K=(0,1,2,3,4,5,6,7,8,8,7,6,5,4,3,2)
def git_blob(file):
    b=Path(file).read_bytes()
    return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()
def canon(x):
    return json.dumps(x,sort_keys=True,separators=(",",":")).encode()
def independent_reauthor():
    for i,k in enumerate(K):
        rng=random.Random(0x39e100+i*30011)
        universe=list(range(-512,0))+list(range(1,513))
        selected=sorted(rng.sample(universe,k))
        secret=[[d,rng.choice(ALPHABET)] for d in selected]
        yield f"RC39_1_NEW_{i:02d}",secret
def author_reference(reads,word,center):
    if center<0 or center>=len(word) or any(c not in ALPHABET for c in word):
        raise ValueError("INVALID_REFERENCE_WORD")
    if word[center]!="B":return word[center]
    for d,c in reads:
        ix=center+d
        if ix<0 or ix>=len(word) or word[ix]!=c:return "B"
    return "A"
def independent_program(code,word,center):
    if (type(code) is not dict or set(code)!={"schema","kind","reads"} or
        code["schema"]!="neumann.q3.rc39.sparse-causal-program.v1" or
        code["kind"]!="RELATIVE_EXACT_CONJUNCTION"):
        return None
    seen=set()
    if type(code["reads"]) is not list or len(code["reads"])>1024:return None
    for d,c in code["reads"]:
        if type(d) is not int or d==0 or d in seen or c not in ALPHABET:return None
        seen.add(d)
        ix=center+d
        if ix<0 or ix>=len(word) or word[ix]!=c:return word[center]
    return "A" if word[center]=="B" else word[center]
def mutation_witness(reads,program):
    # Build a satisfying witness after FIRST output, unavailable to proposers.
    witness=["A"]*1025;witness[512]="B"
    for d,c in reads:witness[512+d]=c
    corrupt=dict(program);corrupt["reads"]=[list(x) for x in program["reads"]]
    if reads:
        deleted=corrupt["reads"].pop()
        d,c=deleted
        witness[512+d]=next(x for x in ALPHABET if x!=c)
    else:
        corrupt["reads"]=[[1,"A"]]
        witness[513]="B"
    source="".join(witness)
    return independent_program(corrupt,source,512)!=author_reference(reads,source,512)
def independent(first_path,root="."):
    start=process_time_ns()
    data=Path(first_path).read_bytes()
    rec=json.loads(data)
    errors=[]
    def check(cond,reason):
        if not cond:errors.append(reason)
    check(hashlib.sha256(data).hexdigest()==FIRST_SHA256,"ORIGINAL_FIRST_SHA_CHANGED")
    root=Path(root)
    check(git_blob(root/"research/q3/rc39/explainable_no_witness.py")==LEARNER_SOURCE,"LEARNER_SOURCE_CHANGED")
    check(git_blob(root/"research/q3/rc39/first_explainable_author.py")==AUTHOR_SOURCE,"ORIGINAL_AUTHOR_SOURCE_CHANGED")
    check(git_blob(root/"docs/experiments/q3_RC39_1_FIRST_SOURCE_LOCK.json")==PRIOR_LOCK,"PRIOR_LOCK_CHANGED")
    rows=rec.get("rows",[])
    check(len(rows)==16,"NOT_16_FIRST_TASKS")
    all_grade=[];replayed=0;independent_correct=0;strong_correct=0;mutation_reject=0
    for index,(identifier,secret) in enumerate(independent_reauthor()):
        if index>=len(rows):break
        item=rows[index]
        check(item["id"]==identifier,"AUTHOR_ID_DRIFT:"+identifier)
        check(hashlib.sha256(canon(secret)).hexdigest()==item["hidden_author_spec_commitment"],
              "HIDDEN_AUTHOR_SPEC_DRIFT:"+identifier)
        answers=[]
        for key in ["candidate","strong_equal_rights_classical"]:
            src=item[key];program=src.get("program")
            good=(src["status"]=="SOURCE_CONSISTENT_EXECUTABLE" and
                  program is not None and program["reads"]==secret and
                  independent_program(program,"B"*1025,512) in ("A","B"))
            check(good,"INDEPENDENT_PROGRAM_MAP_FAILURE:"+key+":"+identifier)
            answers.append(good)
        if answers[0]:independent_correct+=1
        if answers[1]:strong_correct+=1
        candidate=item["candidate"]["program"]
        changed_detected=mutation_witness(secret,candidate)
        check(changed_detected,"CHANGED_PROGRAM_NOT_REJECTED:"+identifier)
        mutation_reject+=int(changed_detected)
        rng=random.Random(0x391cafe+index*717)
        correct_count=0
        for t in range(160):
            n=rng.randint(1025,3500);center=rng.randint(512,n-513)
            word=[rng.choice(ALPHABET) for _ in range(n)]
            word[center]="B"
            if t%4==0:
                for d,char in secret:word[center+d]=char
            elif t%4==1 and secret:
                for d,char in secret:word[center+d]=char
                d,c=secret[rng.randrange(len(secret))]
                word[center+d]=next(x for x in ALPHABET if x!=c)
            elif t%4==2:
                word[center]="C"
            text="".join(word)
            expected=author_reference(secret,text,center)
            actual=independent_program(candidate,text,center)
            if expected==actual:correct_count+=1
        check(correct_count==160,"INDEPENDENT_CONTEXT_ERROR:"+identifier)
        replayed+=correct_count
        all_grade.append({"id":identifier,"hidden_k":len(secret),
          "candidate_exact_mapping":answers[0],
          "strong_equal_rights_exact_mapping":answers[1],
          "new_contexts_exact":correct_count,
          "changed_program_counterexample_rejected":changed_detected,
          "original_oracle_calls":item["candidate"]["oracle_calls"],
          "original_strong_classical_calls":item["strong_equal_rights_classical"]["oracle_calls"]})
    s=rec.get("counts",{})
    check(s.get("tasks")==16,"ORIGINAL_COUNT_CHANGED")
    check(s.get("candidate_query_calls")==sum(x["original_oracle_calls"] for x in all_grade),
          "ORIGINAL_PROPOSER_QUERIES_CHANGED")
    check(s.get("strong_classical_query_calls")==sum(x["original_strong_classical_calls"] for x in all_grade),
          "ORIGINAL_BASELINE_QUERIES_CHANGED")
    check(s.get("candidate_query_calls")==s.get("strong_classical_query_calls")==240,
          "ORIGINAL_240_QUERY_CLAIM_CHANGED")
    check(s.get("max_candidate_calls")==24,"ORIGINAL_MAX24_CHANGED")
    check(independent_correct==16 and strong_correct==16,"INDEPENDENT_NOT_16_EXACT")
    check(replayed==2560,"INDEPENDENT_CONTEXTS_NOT_ALL_PASS")
    check(mutation_reject==16,"MUTATION_NEGATIVE_16_FAILED")
    check(rec.get("new_no_positive_examples") is True,"POSITIVE_WITNESS_LEAK_FLAG")
    return {"schema":"neumann.q3.rc39.1.independent-first-no-witness-grade.v1",
      "first_sha256":hashlib.sha256(data).hexdigest(),
      "audit_pass":not errors,"errors":errors,
      "new_hidden_author_tasks":16,"original_executable_programs_proved":independent_correct,
      "strong_same_rights_classical_programs_proved":strong_correct,
      "new_random_contexts_exact":replayed,
      "all_domain_grammar_conditional_proof_count":independent_correct,
      "mutation_counterexamples":mutation_reject,
      "number_of_positive_witnesses_given":0,
      "oracle_feedback_first_offending_offset_not_correct_symbol":True,
      "candidate_original_queries":s.get("candidate_query_calls"),
      "strong_baseline_original_queries":s.get("strong_classical_query_calls"),
      "max_queries_per_case":s.get("max_candidate_calls"),
      "candidate_cpu_us_total_from_original_first":s.get("candidate_cpu_us_total"),
      "strong_baseline_cpu_us_total_from_original_first":s.get("strong_classical_cpu_us_total"),
      "oracle_information_content_upper_bits_each":11,
      "oracle_upper_reply_alphabet_size":1025,
      "native_explanatory_oracle_operation_cost":"NOT_MEASURED_SEPARATELY",
      "all_domain_scope":"ABC, human-supplied relative-exact AND predicates, all welltyped word lengths and centers where required offsets may be absent, by exact map equivalence",
      "source_library_human_defined":True,
      "neural_training_executed":False,
      "independently_authored_external_family":False,
      "scientific_status":"SCOPED_NO_POSITIVE_WITNESS_CAUSAL_DISCOVERY_PASS_CLASSICAL_PARITY",
      "Q3_global":"OPEN","Q6_new_semantic_family":"OPEN",
      "Q4_all_in_10x":"NOT_PROVEN",
      "grader_cpu_ms":(process_time_ns()-start)/1e6,
      "cases":all_grade}
if __name__=="__main__":
    if len(sys.argv)!=3:raise SystemExit("python -m research.q3.rc39.independent_explain_grade ROOT FIRST.json")
    r=independent(sys.argv[2],sys.argv[1])
    print(json.dumps(r,sort_keys=True,indent=2))
    if not r["audit_pass"]:raise SystemExit(1)
