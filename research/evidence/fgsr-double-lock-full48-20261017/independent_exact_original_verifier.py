"""Independent Z3Py authority for a source-inspected classical 1366-tuple CHC proof.
No imports from the state explorer or synthesis code. No source alterations.
Full original source SHA and complete generated invariant SHA are pinned.
"""
import base64,hashlib,json,pathlib,time,urllib.request,zlib
import z3

HERE=pathlib.Path(__file__).resolve().parent
REV="b4fa7a708e5863bbcdb5de50d692ead3a67cbedc"
SOURCE="ultimate/LIA-NonLin/33_double_lock_p1_vs_simplified_000.smt2"
SRC_SHA="2dfd3f531151113401aca614ad3e4176dae77ebcb326abbbcc456551a9a8f645"
CERT_SHA="1cfc481f8ec97cc382d99bcd468a8f43ddd63ff4943d00b0f3a2516c1c2582c8"

def extract_actual_original_assertions(data):
    src=data.decode()
    forms=[];at=0
    while (start:=src.find("(assert",at))>=0:
        level=0
        for end in range(start,len(src)):
            if src[end]=="(":level+=1
            if src[end]==")":
                level-=1
                if level==0:
                    forms.append(src[start+7:end].strip())
                    at=end+1
                    break
        else:raise ValueError("SOURCE_UNBALANCED")
    if len(forms)!=48:raise ValueError("CHANGED_ORIGINAL_CLAUSE_COUNT")
    return forms

def check_smt(source,timeout=5000):
    q=z3.Solver()
    q.set(timeout=timeout)
    q.from_string(source)
    return str(q.check())

def erase_inv_body(cert):
    # Intentionally sabotaged invariant for an independent fail-closed test.
    pos=cert.find(" Bool ")
    if pos<0:raise ValueError("INV_DEFINE_NOT_FOUND")
    start=pos+len(" Bool ")
    level=0
    for end in range(start,len(cert)):
        if cert[end]=="(":level+=1
        elif cert[end]==")":
            level-=1
            if not level:
                return cert[:start]+"false"+cert[end+1:]
    raise ValueError("CERT_INV_UNBALANCED")

def main():
    t=time.perf_counter()
    b64=(HERE/"FROZEN_EXPLICIT_1366_STATE_CERTIFICATE.b64z").read_text().strip()
    cert=zlib.decompress(base64.b64decode(b64)).decode()
    if hashlib.sha256(cert.encode()).hexdigest()!=CERT_SHA:
        raise ValueError("WRONG_FROZEN_CERT_SHA")
    url=f"https://raw.githubusercontent.com/chc-comp/chc-comp26-benchmarks/{REV}/{SOURCE}"
    with urllib.request.urlopen(url,timeout=30) as resp:
        original=resp.read()
    if hashlib.sha256(original).hexdigest()!=SRC_SHA:
        raise ValueError("NOT_THE_EXACT_ORIGINAL")
    original_clauses=extract_actual_original_assertions(original)
    check=[]
    for idx,clause in enumerate(original_clauses,1):
        started=time.perf_counter()
        sat=check_smt(cert+"(assert (not "+clause+"))\n")
        check.append(dict(rule=idx,negated_original_clause=sat,
                          wall_ms=round(1000*(time.perf_counter()-started),3)))
        if sat!="unsat":
            raise ValueError("NOT_AN_UNBOUNDED_PROOF_OF_ORIGINAL_"+str(idx)+"_"+sat)
    # Sabotaged witnesses MUST fail. No heuristic/BMC proof substitutions.
    bad_empty=check_smt(erase_inv_body(cert)+"(assert (not "+original_clauses[2]+"))\n")
    bad_goal=check_smt(cert.replace(
        "(define-fun |CHC_COMP_FALSE| () Bool false)",
        "(define-fun |CHC_COMP_FALSE| () Bool true)")+
        "(assert (not "+original_clauses[47]+"))\n")
    modified=original_clauses[45].replace("(= 0 v_7)","(= (- 1) v_7)")
    if modified==original_clauses[45]:raise ValueError("GOAL_MUTATION_NOOP")
    reachable_bad=check_smt(cert+"(assert (not "+modified+"))\n")
    if [bad_empty,bad_goal,reachable_bad]!=["sat"]*3:
        raise ValueError("FAIL_OPEN_NEGATIVE_CONTROL")
    out={"verdict":"EXTERNAL_ORIGINAL_COMPLETE_INDUCTIVE_SAFETY_CERTIFIED",
         "upstream_revision":REV,"original_path":SOURCE,
         "exact_original_sha256":SRC_SHA,
         "fixed_certificate_sha256":CERT_SHA,
         "actual_solver":"Z3Py "+z3.get_version_string(),
         "unmodified_original_count":len(check),
         "independently_unsat_original_count":len(check),
         "whole_original_rule_checks":check,
         "negative_control_empty_inv":bad_empty,
         "negative_control_bad_false_goal":bad_goal,
         "negative_control_reachable_forbidden_state":reachable_bad,
         "candidate_contains_1366_explicit_stage4_states":True,
         "complete_unbounded_certificate":True,
         "origin":"CLASSICAL_SOURCE_INSPECTED_FINITE_ABSTRACTION_WITH_HUMAN_RESEARCHER_DESIGN",
         "neural_calls":0,"learned_operator_invention_claim":False,
         "transfer_to_new_problem_families_claim":False,
         "Q1_Q7":"OPEN",
         "wall_ms":round(1000*(time.perf_counter()-t),3)}
    (HERE/"INDEPENDENT_GITHUB_48_OF_48_RECEIPT.json").write_text(json.dumps(out,indent=2)+"\n")
    print("PINNED_ORIGINAL",SRC_SHA)
    print("PINNED_CERTIFICATE",CERT_SHA)
    print("INDEPENDENT_48_RULES",len(check),"/48","UNSAT")
    print("NEGATIVE_CONTROLS",bad_empty,bad_goal,reachable_bad)
    print("Q1_Q7","OPEN")
if __name__=="__main__":main()
