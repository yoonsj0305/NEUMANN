"""Independent external original 48-rule verifier for new factored SMT relation.
No source-specific state explorer, tree trainer, or DAG optimizer is imported.
"""
import base64,hashlib,json,pathlib,time,urllib.request,zlib
import z3

HERE=pathlib.Path(__file__).resolve().parent
BANCH=pathlib.Path(__file__).resolve().parents[1]/"fgsr-double-lock-full48-20261017"
REV="b4fa7a708e5863bbcdb5de50d692ead3a67cbedc"
ORIG="ultimate/LIA-NonLin/33_double_lock_p1_vs_simplified_000.smt2"
ORIG_SHA="2dfd3f531151113401aca614ad3e4176dae77ebcb326abbbcc456551a9a8f645"
PARENT_SHA="1cfc481f8ec97cc382d99bcd468a8f43ddd63ff4943d00b0f3a2516c1c2582c8"
DAG_SHA="06d520490ddf43a45846f7ff56f4eafa4f6b7cedefbb796d3d6357c97e86c64c"

def unpack(path,digest):
    text=zlib.decompress(base64.b64decode(path.read_text().strip())).decode()
    if hashlib.sha256(text.encode()).hexdigest()!=digest:
        raise ValueError("PROOF_SHA256_MISMATCH")
    return text

def negated_original(proof,orig,i):
    # Freshly reparse source under exact, separately scoped candidate.
    quant=z3.parse_smt2_string(proof+"\n(assert "+orig[i].sexpr()+")")
    if len(quant)!=1 or not z3.is_quantifier(quant[0]):
        raise ValueError("ORIGINAL_NOT_QUANTIFIER_"+str(i))
    q=quant[0]
    fresh=[z3.Const(f"indepex_{i}_{j}",q.var_sort(j)) for j in range(q.num_vars())]
    body=z3.substitute_vars(q.body(),*fresh)
    solver=z3.Solver();solver.set(timeout=5000);solver.add(z3.Not(body))
    return str(solver.check())

def check_equivalent(parent,dag):
    renamed=dag.replace("(set-logic ALL)","").replace(
        "(define-fun |Inv|","(define-fun |Inv_Factored|").replace(
        "(define-fun |CHC_COMP_FALSE| () Bool false)","")
    declarations="\n".join(f"(declare-const {c} Int)" for c in "ABCDEFGH")
    args=" ".join("ABCDEFGH")
    expr=parent+"\n"+renamed+"\n"+declarations+f"\n(assert (xor (Inv {args}) (Inv_Factored {args})))"
    sol=z3.Solver();sol.set(timeout=15000);sol.from_string(expr)
    return str(sol.check())

def check_negative(proof,original):
    # Never accept meaningless empty Inv or a broken false reachability witness.
    name="ABCDEFGH"
    inv_args=" ".join(f"({v} Int)" for v in name)
    empty=f"(set-logic ALL)\n(define-fun |Inv| ({inv_args}) Bool false)\n(define-fun |CHC_COMP_FALSE| () Bool false)"
    no_init=negated_original(empty,original,2)
    wrong_false=proof.replace(
        "(define-fun |CHC_COMP_FALSE| () Bool false)",
        "(define-fun |CHC_COMP_FALSE| () Bool true)")
    if wrong_false==proof:raise ValueError("FALSE_GOAL_MUTATION_DID_NOT_HAPPEN")
    false_link=negated_original(wrong_false,original,47)
    return {"empty_inv_init":no_init,"incorrect_false_goal":false_link}

def main():
    started=time.perf_counter()
    with urllib.request.urlopen(
        f"https://raw.githubusercontent.com/chc-comp/chc-comp26-benchmarks/{REV}/{ORIG}",
        timeout=30) as r:blob=r.read()
    if hashlib.sha256(blob).hexdigest()!=ORIG_SHA:
        raise ValueError("CHANGED_EXTERNAL_ORIGINAL")
    original=z3.parse_smt2_string(blob.decode())
    if len(original)!=48:
        raise ValueError("NOT_ORIGINAL_48")
    parent=unpack(BANCH/"FROZEN_EXPLICIT_1366_STATE_CERTIFICATE.b64z",PARENT_SHA)
    dag=unpack(HERE/"COMPRESSED_EXACT_ORIGINAL_INV_2196_BYTES.b64z",DAG_SHA)
    checks=[]
    for i in range(48):
        t=time.perf_counter()
        val=negated_original(dag,original,i)
        checks.append(dict(source_clause=i+1,result=val,ms=round((time.perf_counter()-t)*1000,3)))
        if val!="unsat":raise ValueError("ORIGINAL_NOT_CERTIFIED_"+str(i+1)+"_"+val)
    exact=check_equivalent(parent,dag)
    if exact!="unsat":raise ValueError("INVARIANT_EQUIVALENCE_NOT_PROVED_"+exact)
    bad=check_negative(dag,original)
    if list(bad.values())!=["sat","sat"]:
        raise ValueError("FAIL_OPEN_NEGATIVE_CONTROL")
    result={
       "status":"ACTUAL_FULL_48_ORIGINAL_AND_EXACT_FORMULA_EQUIVALENCE_CERTIFIED",
       "source_external_pinned":ORIG_SHA,
       "parent_certificate_sha256":PARENT_SHA,
       "factored_certificate_sha256":DAG_SHA,
       "parent_bytes":len(parent.encode()),
       "factored_bytes":len(dag.encode()),
       "certificate_byte_ratio":round(len(parent.encode())/len(dag.encode()),4),
       "original_horn_clause_proofs":len(checks),
       "per_original_rule":checks,
       "full_relational_formula_xor_equivalence":exact,
       "tamper_controls":bad,
       "learned_neural_operator_invention":False,
       "origin":"EXACT_CLASSICAL_MULTI_VALUED_DECISION_DAG_FROM_OPENED_SOURCE_STATES",
       "cross_family_transfer_proven":False,
       "global_Q1_Q7":"OPEN",
       "z3":z3.get_version_string(),
       "total_ms":round((time.perf_counter()-started)*1000,3)}
    (HERE/"INDEPENDENT_GITHUB_48_DAG_RECEIPT.json").write_text(
         json.dumps(result,indent=2)+"\n")
    print("INDEPENDENT_48_ORIGINAL",len(checks),"/48")
    print("COMPLETE_INVARIANT_XOR",exact)
    print("SMT_SOURCE_TEXT_COMPRESSION",result["certificate_byte_ratio"])
    print("ALL_Q","OPEN")

if __name__=="__main__":main()
