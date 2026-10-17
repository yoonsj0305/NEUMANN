"""Independent GHA original 48-to-41 stage-cut proof using z3py, not local C wrapper.
Opened authentic benchmark; CLASSICAL human-designed inductive predicate; Q1-Q7 OPEN.
"""
import hashlib,json,pathlib,re,time,urllib.request,z3
REV="b4fa7a708e5863bbcdb5de50d692ead3a67cbedc"
PATH="ultimate/LIA-NonLin/33_double_lock_p1_vs_simplified_000.smt2"
SHA="2dfd3f531151113401aca614ad3e4176dae77ebcb326abbbcc456551a9a8f645"
PREFIX_M="""(set-logic ALL)
(define-fun |Inv| ((A Int) (B Int) (C Int) (D Int) (E Int) (F Int) (G Int) (H Int)) Bool
(and (<= 0 H) (<= H 4)
  (=> (< H 4) (and (= D (- 1)) (= E (- 1)) (= F (- 1)) (= G (- 1))))
  (=> (and (>= H 1) (< H 4)) (= A 0))
  (=> (and (>= H 2) (< H 4)) (= C 0))
  (=> (and (>= H 3) (< H 4)) (= B 0))
  (=> (= H 4) (or (= D (- 1)) (= E (- 1))))))
(define-fun |CHC_COMP_FALSE| () Bool false)
"""
PREFIX_RAW="""(set-logic ALL)
(declare-fun |Inv| (Int Int Int Int Int Int Int Int) Bool)
(declare-fun |CHC_COMP_FALSE| () Bool)
"""
def forms(src):
    result=[];i=0
    while (start:=src.find("(assert",i))>=0:
        depth=0
        for j in range(start,len(src)):
            if src[j]=="(":depth+=1
            if src[j]==")":
                depth-=1
                if not depth:
                    result.append(src[start+len("(assert"):j].strip());i=j+1;break
        else:raise ValueError("unbalanced source")
    if len(result)!=48:raise ValueError("wrong source clause count")
    return result

def result(prefix,body):
    sol=z3.Solver();sol.set(timeout=5000)
    sol.from_string(prefix+"(assert "+body+")")
    v=str(sol.check())
    return v

def head_to_false(assertion):
    indices=list(re.finditer(r"\(Inv\s",assertion))
    if not indices:raise ValueError("expected original Inv head")
    start=indices[-1].start();depth=0;end=None
    for i in range(start,len(assertion)):
        if assertion[i]=="(":depth+=1
        if assertion[i]==")":
            depth-=1
            if not depth:end=i+1;break
    if end is None:raise ValueError("no head close")
    return assertion[:start]+"false"+assertion[end:]

def main():
    t=time.perf_counter()
    u=f"https://raw.githubusercontent.com/chc-comp/chc-comp26-benchmarks/{REV}/{PATH}"
    with urllib.request.urlopen(u,timeout=30) as f:data=f.read()
    assert hashlib.sha256(data).hexdigest()==SHA
    a=forms(data.decode())
    induction=[result(PREFIX_M,"(not "+x+")") for x in a[:45]]
    assert len(induction)==45 and all(x=="unsat" for x in induction),[(i+1,x) for i,x in enumerate(induction) if x!="unsat"]
    six=[27,30,31,33,34,45]
    taut=[(i,result(PREFIX_RAW,"(not "+a[i-1]+")")) for i in six]
    assert all(v=="unsat" for _,v in taut)
    num28=result(PREFIX_M,"(not "+head_to_false(a[27])+")")
    assert num28=="unsat"
    not_eliminable=[(i,result(PREFIX_M,"(not "+head_to_false(a[i-1])+")")) for i in (29,32,35,36)]
    assert all(v=="sat" for _,v in not_eliminable)
    goals=[(i,result(PREFIX_M,"(not "+a[i-1]+")")) for i in (46,47,48)]
    assert [x[1] for x in goals]==["sat","sat","unsat"]
    orig_keep=[i for i in range(1,49) if i not in {27,28,30,31,33,34,45}]
    canonical="\n".join(["(set-logic HORN)",
       "(declare-fun |CHC_COMP_FALSE| () Bool)",
       "(declare-fun |Inv| (Int Int Int Int Int Int Int Int) Bool)",
       *["(assert "+a[i-1]+")" for i in orig_keep],"(check-sat)","(exit)"])+"\n"
    assert hashlib.sha256(canonical.encode()).hexdigest()=="4a6f0f2af8f2ee979fcab12bda0256b30c2bafb2eafd526095e27a8a18cc2303"
    record={"scope":"OPENED_ORIGINAL_CLASSICAL_LFP_EQUIVALENCE_NOT_FULL_SAFETY",
      "upstream_original_sha256":SHA,"native_z3py_version":z3.get_version_string(),
      "original_generative_inductive_unsat":len(induction),
      "old_uninterpreted_tautologies":taut,"new_infeasible_rule28":num28,
      "retained_difficult_joint_premises":not_eliminable,
      "original_safety_goal_checks":goals,"retained_count":len(orig_keep),
      "derived_41_source_sha256":hashlib.sha256(canonical.encode()).hexdigest(),
      "full_original_safety":"UNKNOWN","learned_model_contribution":False,
      "global_Q1_Q7":"OPEN",
      "elapsed_ms":round((time.perf_counter()-t)*1000,2)}
    out=pathlib.Path("independent_48_to_41_receipt.json")
    out.write_text(json.dumps(record,indent=2)+"\n")
    print("INDUCTIVE_ORIGINAL",len(induction),"/45")
    print("FIRST_ORDER_TAUT",len(taut),"/6")
    print("NEW_SAFE_LFP_REDUCTION",num28)
    print("RETAINED_3_PREMISE",not_eliminable)
    print("SOURCE",48,"=>",len(orig_keep))
    print("GLOBAL_QUESTIONS","OPEN")
if __name__=="__main__":main()
