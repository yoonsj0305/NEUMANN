"""RC39 independent read-only audit of the IMMUTABLE first 24.

No imports from learner or first grader. Alternative AST interpreter and
product-machine verifier; independent reference reconstructed from precommitted
family/seed contract. Reads existing first receipt, NEVER refits learner.
"""
from __future__ import annotations
from collections import deque
from hashlib import sha1,sha256
from pathlib import Path
import json,random,sys

FIRST_SHA="829bab136751cc72f972d489d25ace9bde9cae0b29208a3c99a04d1fe66f1a05"
ROOT=Path(__file__).resolve().parents[3]

def gitblob(p):
    raw=p.read_bytes()
    return sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()

def external_reference(family,seed):
    # Independence: no import and no function call to the first model author.
    if family=="prefix_parity":
        n=2
        g={(q,a):((q+int(a=="A"))%2,str((q+int(a=="A"))%2))
           for q in range(n) for a in "ABC"}
    elif family=="prefix_mod3":
        n=3
        g={(q,a):((q+int(a=="A"))%3,str(int((q+int(a=="A"))%3==0)))
           for q in range(n) for a in "ABC"}
    elif family=="presence":
        n=2
        g={(q,a):(max(q,int(a=="B")),str(max(q,int(a=="B"))))
           for q in range(n) for a in "ABC"}
    elif family in ("random_3state","random_4state","random_5state"):
        n=int(family[len("random_")])
        h=sha256(("RC39|"+family+"|"+str(seed)+"|2026-11-06").encode()).digest()
        r=random.Random(int.from_bytes(h,"big"))
        g={(q,a):(r.randrange(n),str(r.randrange(2)))
           for q in range(n) for a in "ABC"}
    else:raise ValueError("bad family")
    return n,g

def parse_independent(src):
    if type(src) is not dict or set(src)!={"schema","alphabet","outputs","initial","states","transitions","emissions"}:
        raise ValueError("malformed generated ISA")
    if src["schema"]!="neumann.rc39.mealy-ast.v1" or src["alphabet"]!=["A","B","C"] or src["outputs"]!=["0","1"]:
        raise ValueError("grammar source corruption")
    n=src["states"];trans=src["transitions"];emit=src["emissions"];initial=src["initial"]
    if (type(n)!=int or not 1<=n<=8 or type(initial)!=int or not 0<=initial<n or
        type(trans)!=list or type(emit)!=list or len(trans)!=n or len(emit)!=n):
        raise ValueError("invalid source state count")
    for ts,es in zip(trans,emit):
        if (type(ts)!=list or type(es)!=list or len(ts)!=3 or len(es)!=3 or
            any(type(i)!=int or not 0<=i<n for i in ts) or
            any(v not in ("0","1") for v in es)):
            raise ValueError("invalid source table")
    return initial,trans,emit

def prove_independent(reference,source):
    (_,hidden), (initial,trans,emit)=reference,parse_independent(source)
    q=deque([(0,initial,"")]);seen={(0,initial)};visited=0
    while q:
        a,b,w=q.popleft();visited+=1
        for idx,symbol in enumerate("ABC"):
            hn,ho=hidden[a,symbol]
            if emit[b][idx]!=ho:
                return False,w+symbol,visited
            nxt=hn,trans[b][idx]
            if nxt not in seen:
                seen.add(nxt);q.append((hn,trans[b][idx],w+symbol))
    return True,None,visited

def audit(receiptfile):
    raw=Path(receiptfile).read_bytes()
    p=json.loads(raw)
    lock=json.loads((ROOT/"docs/experiments/q3_RC39_FIRST_LEARNER_SOURCE_LOCK.json").read_text())
    lockgrader=json.loads((ROOT/"docs/experiments/q3_RC39_FIRST_GRADER_LOCK.json").read_text())
    prereg=json.loads((ROOT/"docs/experiments/q3_RC39_ACTIVE_AUTOMATA_FIRST_PREREG_2026_11_06.json").read_text())
    errors=[]
    def assert_or_log(cause,claim):
        if not claim:errors.append(cause)
    assert_or_log("FIRST_RECEIPT_SHA",sha256(raw).hexdigest()==FIRST_SHA)
    assert_or_log("ORIGINAL_LEARNER_SOURCE_DRIFT",gitblob(ROOT/"research/q3/rc39/active_mealy.py")==lock["original_source_git_blob"])
    assert_or_log("ORIGINAL_FIRST_GRADER_DRIFT",gitblob(ROOT/"research/q3/rc39/independent_first_grader.py")==lockgrader["grader_sha"])
    assert_or_log("PREREG_DRIFT",gitblob(ROOT/"docs/experiments/q3_RC39_ACTIVE_AUTOMATA_FIRST_PREREG_2026_11_06.json")==lock["preregistered_experiment_git_blob"])
    cases=[(family,seed) for family in prereg["benchmark"]["families"] for seed in prereg["benchmark"]["seeds"]]
    assert_or_log("FIRST_TASK_COHORT",len(cases)==24 and len(p["rows"])==24)
    rows=[];actual=0;bad=0;mutation_rejected=0;product_nodes=0
    for (family,seed),row in zip(cases,p["rows"]):
        identifier=family,str(seed)
        assert_or_log("FIRST_TASK_REORDER",row["family"]==family and row["seed"]==seed)
        reference=external_reference(family,seed)
        original=row["generated_executable_program"]
        if original is None:
            bad+=1;continue
        try:
            proof=prove_independent(reference,original)
            actual+=int(proof[0])
            product_nodes+=proof[2]
            assert_or_log("FAILED_ORIGINAL_INDEPENDENT_PROOF:"+family+str(seed),proof[0])
            assert_or_log("WRONG_ORIGINAL_FIRST_FLAG:"+family+str(seed),
                          row["first_exact_all_finite_words"]==proof[0])
            assert_or_log("WRONG_ORIGINAL_COMPILER_STATE_COUNT",row["compiled_states"]==original["states"])
            clone=json.loads(json.dumps(original))
            init=clone["initial"]
            clone["emissions"][init][0]="0" if clone["emissions"][init][0]=="1" else "1"
            changed=prove_independent(reference,clone)
            mutation_rejected+=int(not changed[0] and changed[1] is not None)
        except Exception as e:
            errors.append("PROGRAM_MALFORMED:"+family+str(seed)+":"+str(e))
            bad+=1
        rows.append({"family":family,"seed":seed,"independent_exact":proof[0] if 'proof' in locals() else False,
                     "product_nodes":proof[2] if 'proof' in locals() else 0})
    assert_or_log("COUNT_TAMPER",p["all_finite_word_proven"]==actual)
    assert_or_log("FIRST_TOTAL_WRONG",actual==24 and bad==0)
    assert_or_log("FIRST_MUTATION_GUARD",mutation_rejected==24)
    asserts=[
      ("MEMBERSHIP_CALLS_TAMPER",sum(x["membership_calls"] for x in p["rows"])==p["metrics"]["membership_calls"]),
      ("MEMBERSHIP_SYMBOLS_TAMPER",sum(x["membership_total_symbols"] for x in p["rows"])==p["metrics"]["membership_symbols"]),
      ("EQUIVALENCE_CALLS_TAMPER",sum(x["equivalence_calls"] for x in p["rows"])==p["metrics"]["equivalence_calls"]),
      ("FIRST_SCOPE_VERDICT_TAMPER",p["science_status"]=="SCOPED_CLASSICAL_STRUCTURAL_LEARNING_PASS")
    ]
    for name,okay in asserts:assert_or_log(name,okay)
    return {"schema":"neumann.q3.rc39.independent-readonly-audit.v1",
            "original_first_sha256":sha256(raw).hexdigest(),
            "independent_audit_PASS":not errors,"errors":errors,
            "verified_24_executable_generated_programs":actual,
            "mutated_first_programs_rejected":mutation_rejected,
            "independently_visited_product_pairs":product_nodes,
            "original_membership_calls":p["metrics"]["membership_calls"],
            "original_equivalence_calls":p["metrics"]["equivalence_calls"],
            "original_membership_symbols":p["metrics"]["membership_symbols"],
            "Q3":"OPEN","Q6":"OPEN","Q7":"OPEN",
            "all_length_proof_scope":"deterministic finite-state Mealy source class with strong equivalence oracle, no neural policy",
            "original_model_frozen_before_independent_grade":True,
            "no_new_learning_or_inference":True,
            "rows":rows}
if __name__=="__main__":
    if len(sys.argv)!=2:raise SystemExit("Usage: python -m research.q3.rc39.independent_readonly_audit FIRST_RC39.json")
    out=audit(sys.argv[1])
    print(json.dumps(out,indent=2,sort_keys=True))
    if not out["independent_audit_PASS"]:raise SystemExit(1)
