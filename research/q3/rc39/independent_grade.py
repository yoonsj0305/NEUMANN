"""RC39 independent POST-FIRST original-source semantic proof audit.

This module neither imports nor reruns the RC39 proposer/bench source.
Only reads frozen original first receipt and independently reconstructs
the synthetic task author using its public deterministic seed contract.
The author reference program is NOT supplied to the original proposer.
A correct exact pair mapping conditionally proves equivalence for ALL finite
ABC words (3<=length<=4097) and center coordinates under that grammar.
"""
from __future__ import annotations
from hashlib import sha1,sha256
from pathlib import Path
from time import process_time_ns
import json,random,sys

FIRST_SHA256="8be501ee87f432ffdededb093421095ea8438befc8cafe497a08aa502648cab3"
LEARNER_GIT_BLOB="bcfd1a6ac52f8e6e806fbf35bef5a0f7f2b48411"
AUTHOR_GIT_BLOB="74e8af2676ac50fc418546e9f271a4f5413799a7"
LOCK_GIT_BLOB="de760637917bc5aaddd603a9394b8d2ea7f77318"
SCHEMA="neumann.q3.rc39.sparse-causal-program.v1"
K=(0,1,2,3,4,4,2,1,3,4,0,3)
ALPHABET="ABC"
def git_blob(path):
    b=Path(path).read_bytes()
    return sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()
def canonical(data):
    return json.dumps(data,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
def reauthor_without_source_import():
    # Separate independent reconstruction of the first author; only
    # provenance, not original inference or oracle references are replayed.
    for t,k in enumerate(K):
        rng=random.Random(0x39c700+t*17971)
        w="".join(rng.choice(ALPHABET) for _ in range(1025))
        w=w[:512]+"B"+w[513:]
        choices=[j for j in range(-512,513) if j!=0]
        positions=sorted(rng.sample(choices,k))
        target=[[j,w[512+j]] for j in positions]
        yield {"id":f"AUTHOR_NEW_{t:02d}","witness":w,
               "secret":target,"center":512}
def ref(hidden,word,center):
    """Independently implement original specification, no code import."""
    if center<0 or center>=len(word) or any(c not in ALPHABET for c in word):
        raise ValueError("BAD_INDEPENDENT_TEST")
    if word[center]!="B":return word[center]
    if all(0<=center+delta<len(word) and word[center+delta]==char
           for delta,char in hidden["secret"]):
        return "A"
    return "B"
def run_independent(ast,word,center):
    if (type(ast) is not dict or set(ast)!={"schema","kind","reads"} or
       ast["schema"]!=SCHEMA or ast["kind"]!="RELATIVE_EXACT_CONJUNCTION"):
        return None
    if type(ast["reads"]) is not list or len(ast["reads"])>1024:return None
    used=set()
    for item in ast["reads"]:
        if type(item) not in (tuple,list) or len(item)!=2:return None
        d,x=item
        if type(d) is not int or d==0 or d in used or x not in ALPHABET:return None
        used.add(d)
        if center+d<0 or center+d>=len(word) or word[center+d]!=x:
            return word[center]
    return "A" if word[center]=="B" else word[center]
def structural_mutation_rejected(hidden,compiled):
    # A distinct true conditional program must have a distinguishing input.
    witness=hidden["witness"]
    ast=dict(compiled)
    ast["reads"]=[list(x) for x in compiled["reads"]]
    if ast["reads"]:
        removed=ast["reads"].pop()
        d=removed[0]
        w=list(witness)
        x=w[512+d]
        w[512+d]=ALPHABET[(ALPHABET.index(x)+1)%3]
    else:
        ast["reads"]=[[1,witness[513]]]
        w=list(witness)
        x=w[513];w[513]=ALPHABET[(ALPHABET.index(x)+1)%3]
    trial="".join(w)
    return run_independent(ast,trial,512)!=ref(hidden,trial,512)
def grade(root,first_path):
    start=process_time_ns()
    root=Path(root);src=Path(first_path).read_bytes()
    receipt=json.loads(src)
    errors=[]
    def check(ok,reason):
        if not ok:errors.append(reason)
    check(sha256(src).hexdigest()==FIRST_SHA256,"ORIGINAL_FIRST_RECEIPT_HASH_CHANGED")
    check(git_blob(root/"research/q3/rc39/active_sparse.py")==LEARNER_GIT_BLOB,"PROPOSER_CHANGED")
    check(git_blob(root/"research/q3/rc39/first_author_source.py")==AUTHOR_GIT_BLOB,"ORIGINAL_AUTHOR_CHANGED")
    check(git_blob(root/"docs/experiments/q3_RC39_FIRST_SOURCE_BLOB_LOCK_2026_11_06.json")==LOCK_GIT_BLOB,"PRIOR_SOURCE_LOCK_CHANGED")
    check(receipt.get("schema")=="neumann.q3.rc39.first-before-independent-grade.v1","RECEIPT_SCHEMA")
    recorded=receipt.get("tasks",[])
    check(len(recorded)==12,"NOT_ORIGINAL_12")
    independent_correct=0
    baseline_correct=0
    strong_correct=0
    structural_counterexamples=0
    target_proof=0
    tested_cases=0
    cases=[]
    for i,hidden in enumerate(reauthor_without_source_import()):
        if i>=len(recorded):
            errors.append("MISSING_FIRST_PROGRAM")
            break
        first=recorded[i]
        tid=hidden["id"]
        check(first.get("id")==tid,"FIRST_TASK_ID_CHANGED:"+tid)
        check(sha256(hidden["witness"].encode()).hexdigest()==first.get("positive_witness_sha256"),
              "POSITIVE_SOURCE_BYTES_CHANGED:"+tid)
        check(sha256(canonical(hidden["secret"])).hexdigest()==first.get("hidden_author_spec_commitment"),
              "FROZEN_AUTHOR_SPEC_CHANGED:"+tid)
        r=first["candidate"]
        c=first["classical_single_site"]
        a=first["classical_strong_adaptive"]
        algos=[("RC39",r),("SINGLE",c),("ADAPTIVE",a)]
        correct=[]
        for kind,p in algos:
            ast=p.get("program")
            accepted=(p.get("status")=="SOURCE_CONSISTENT_EXECUTABLE" and
                      ast is not None and run_independent(ast,hidden["witness"],512)=="A" and
                      ast["reads"]==hidden["secret"])
            correct.append(accepted)
            check(accepted,kind+"_INCORRECT_HIDDEN_CAUSAL_MAP:"+tid)
        independent_correct+=int(correct[0])
        baseline_correct+=int(correct[1])
        strong_correct+=int(correct[2])
        if correct[0]:
            # Logic certificate: both programs have the SAME complete finite
            # membership decision expression and the same inferred positional
            # predicate set. Therefore they produce the same output for ANY
            # well-typed word/center by propositional substitution.
            target_proof+=1
        mutated_rejected=bool(correct[0] and structural_mutation_rejected(hidden,r["program"]))
        structural_counterexamples+=int(mutated_rejected)
        check(mutated_rejected,"MUTATED_OPCODE_ACCEPTED:"+tid)
        rng=random.Random(0x3f91+a_seed(i))
        full_correct=0
        for j in range(240):
            # New length/center setting, not available to the first proposer.
            n=rng.randint(1025,3500)
            center=rng.randint(512,n-513)
            word=list("".join(rng.choice(ALPHABET) for _ in range(n)))
            word[center]="B"
            positive=j%3==0
            if positive:
                for d,sym in hidden["secret"]:word[center+d]=sym
            elif j%3==1 and hidden["secret"]:
                for d,sym in hidden["secret"]:word[center+d]=sym
                d=hidden["secret"][rng.randrange(len(hidden["secret"]))][0]
                letter=word[center+d];word[center+d]=ALPHABET[(ALPHABET.index(letter)+1)%3]
            elif j%3==2:
                # Original non-satisfying center may be another source symbol.
                word[center]="C"
            word="".join(word)
            expected=ref(hidden,word,center)
            actual=run_independent(r["program"],word,center)
            if actual==expected:full_correct+=1
        tested_cases+=240
        check(full_correct==240,"HELDOUT_NEW_LENGTH_OR_CONTEXT_FAILURE:"+tid)
        cases.append({"id":tid,"hidden_schema_commitment":first["hidden_author_spec_commitment"],
          "k":len(hidden["secret"]), "first_source_program_sha256":sha256(canonical(r["program"])).hexdigest() if r.get("program") else None,
          "all_domain_conditional_proof":bool(correct[0]),
          "new_240_context_tests_correct":full_correct,
          "mutation_counterexample_rejected":mutated_rejected,
          "learner_oracle_calls":r["oracle_calls"],
          "single_site_calls":c["oracle_calls"],
          "strong_adaptive_calls":a["oracle_calls"]})
    sums=receipt.get("summary",{})
    check(sums.get("N")==12,"FIRST_N_AGGREGATE_CHANGED")
    check(sums.get("candidate_source_queries")==sum(x["learner_oracle_calls"] for x in cases),"FIRST_GROUP_CALLS_AGG_CHANGED")
    check(sums.get("classical_single_site_queries")==sum(x["single_site_calls"] for x in cases),"FIRST_SINGLE_CALLS_AGG_CHANGED")
    check(sums.get("classical_strong_adaptive_queries")==sum(x["strong_adaptive_calls"] for x in cases),"FIRST_STRONG_CALLS_AGG_CHANGED")
    check(sums.get("candidate_source_queries")==644 and sums.get("classical_single_site_queries")==12300
          and sums.get("classical_strong_adaptive_queries")==644,"FIRST_FIXED_NUMBERS_CHANGED")
    check(independent_correct==baseline_correct==strong_correct==12,"NOT_ALL_12_INDEPENDENTLY_CORRECT")
    check(tested_cases==2880,"NOT_ALL_2880_NEW_CONTEXTS")
    check(target_proof==12,"NOT_ALL_12_COMPLETE_SPEC_EQUIVALENCE")
    check(structural_counterexamples==12,"NEGATIVE_MUTATION_GATE")
    return {"schema":"neumann.q3.rc39.independent-after-first-grade.v1",
        "frozen_first_sha256":sha256(src).hexdigest(),
        "audit_pass":not errors,"errors":errors,
        "fresh_separate_author_synthetic_tasks":12,
        "candidate_original_full_mapping_correct":independent_correct,
        "single_site_classical_full_mapping_correct":baseline_correct,
        "strong_equal_rights_classical_full_mapping_correct":strong_correct,
        "candidate_original_queries":sums.get("candidate_source_queries"),
        "single_site_original_queries":sums.get("classical_single_site_queries"),
        "strong_adaptive_original_queries":sums.get("classical_strong_adaptive_queries"),
        "query_saving_vs_single_site":sums.get("classical_single_site_queries",0)/max(1,sums.get("candidate_source_queries",1)),
        "exclusive_advantage_over_equal_rights_strong_classical":False,
        "independent_new_words_and_centers":tested_cases,
        "independent_new_context_exact":tested_cases if not errors else None,
        "all_domain_proof_condition":"Source family exactly one sparse exact-character conjunction; author mapping equals compiled mapping. Conditional to 3<=length<=4097 and ABC finite words.",
        "all_domain_proved_programs":target_proof,
        "different_program_mutation_counterexamples":structural_counterexamples,
        "model_weights_used":0,"model_training_samples":0,
        "neural_invention":"NOT_PROVEN",
        "q3_autonomous_base_opcode":"OPEN","q4_all_in_10x":"NOT_PROVEN",
        "q6_independently_authored_external_semantic_family":"OPEN",
        "full_frontier_parity":"NOT_PROVEN",
        "audit_cpu_ms":(process_time_ns()-start)/1e6,
        "cases":cases}
def a_seed(i):
    return (i+1)*301
if __name__=="__main__":
    if len(sys.argv)!=3:raise SystemExit("Usage: python -m research.q3.rc39.independent_grade ROOT FIRST_JSON")
    out=grade(*sys.argv[1:])
    print(json.dumps(out,sort_keys=True,indent=2))
    if not out["audit_pass"]:raise SystemExit(1)
