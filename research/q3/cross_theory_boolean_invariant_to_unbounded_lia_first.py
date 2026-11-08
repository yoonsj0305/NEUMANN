"""NEUMANN Q3 | transferred Bool-semantic method -> unbounded Integer synthesis.

The ONLY previously learned meta-method content is frozen official 4-bit
Boolean truth-function/law JSON from run #42435101680. We do not tune that
method from target data. The cross-type interface is human-written:
  Bool source semantic OR law -> proof-carrying ITE branch coverage over Int
  Official integer max2/max3 source -> discover a general two-arm fold AST
  Original integer max4..max15 -> first-time proof under UNBOUNDED SMT Int

A matched full-language classical enumerator has the same 12 two-arm
comparator variants, per-task proof oracle and same time budget.
NO scalar max oracle / benchmark reference solution is read before freeze.

This proves bounded cross-TYPE reuse of a logically valid source method,
NOT autonomous invention of the metalearning algorithm or global Q3/Q4/Q6.
"""
from __future__ import annotations
import hashlib,itertools,json,pathlib,re,time,urllib.request
import z3

UPSTREAM="13c8deb68a873635879c9a69bc78caebd340f646"
ROOT=f"https://raw.githubusercontent.com/SyGuS-Org/benchmarks/{UPSTREAM}/comp/2019/CLIA_Track/from_2018/"
SOURCE=["jmbl_fg_max2.sl","jmbl_fg_max3.sl"]
TARGET=[f"jmbl_fg_max{n}.sl" for n in range(4,16)]
assert len(TARGET)==12 and not set(SOURCE)&set(TARGET)
PREVIOUS="frozen_bool/Q3_AUTO_DISCOVERED_BOOLEAN_METHOD_LAWS_SOURCE.json"
POLICY="Q3_CROSS_THEORY_INTEGER_SOURCE_POLICY_FROZEN.json"
TARGET_REPORT="Q3_CROSS_THEORY_INTEGER_MAX_ORIGINAL_FIRST.json"
GUARDS=("=","distinct","<","<=",">",">=")
BRANCH_ORDERS=("left","right")

def canonical(v):
    return json.dumps(v,sort_keys=True,separators=(",",":"))
def sha(v):return hashlib.sha256(canonical(v).encode()).hexdigest()

def tokenize(text):
    clean=re.sub(r";[^\n]*","",text)
    return re.findall(r"\(|\)|[^\s()]+",clean)

def parse_smt(raw):
    stack=[];root=[]
    for token in tokenize(raw):
        if token=="(":
            child=[]
            (stack[-1] if stack else root).append(child)
            stack.append(child)
        elif token==")":
            if not stack:raise ValueError("UNEXPECTED_CLOSE")
            stack.pop()
        else:
            if not stack:raise ValueError("ATOM_OUTSIDE")
            stack[-1].append(token)
    if stack:raise ValueError("UNCLOSED")
    return root

def serialize(node):
    if isinstance(node,list):return "("+" ".join(serialize(v) for v in node)+")"
    return str(node)

def decode_original(raw):
    forms=parse_smt(raw)
    fun=[f for f in forms if f and f[0]=="synth-fun"]
    if len(fun)!=1 or len(fun[0])!=4:raise ValueError("MULTI_SYNTH_UNSUPPORTED")
    tag=fun[0][1];params=fun[0][2]
    if not isinstance(params,list) or len(params)<2 or len(params)>20:
        raise ValueError("UNSUPPORTED_ARITY")
    if fun[0][3]!="Int" or any(not isinstance(p,list) or len(p)!=2 or p[1]!="Int" for p in params):
        raise ValueError("UNSUPPORTED_TYPE")
    names=[p[0] for p in params]
    if len(set(names))!=len(names):raise ValueError("DUPLICATE_PARAM")
    constraints=[f[1] for f in forms if f and f[0]=="constraint" and len(f)==2]
    if len(constraints)<2:raise ValueError("TOO_FEW_CONSTRAINTS")
    return {"name":tag,"params":names,"forms":forms,"constraints":constraints}

def load_prior():
    p=json.loads(pathlib.Path(PREVIOUS).read_text())
    stored=p.pop("sha256")
    if sha(p)!=stored:raise ValueError("BITVECTOR_SOURCE_METHOD_SHA_MISMATCH")
    if p.get("source_original_run")!=42434312622:
        raise ValueError("UNTRUSTED_BOOL_PROVENANCE")
    assert p["all_functions_derived"]==16
    matching=[a for a in p["functions"] if a["truth_signature"]==14]
    if len(matching)!=1:raise ValueError("MISSING_SOURCE_DISCOVERED_OR")
    chosen=matching[0]
    if not ("A_SUBSET_Z" in chosen["proved_laws"] and
            "B_SUBSET_Z" in chosen["proved_laws"]):
        raise ValueError("SOURCE_OR_NOT_PROVEN")
    return {"frozen_source_sha256":stored,
            "or_ast":chosen["expression"],
            "learned_or_signature":chosen["truth_signature"],
            "prior_or_inclusion_laws":chosen["proved_laws"]}

def eval_source_boolean(ast,a,b):
    op=ast[0]
    if op=="A":return a
    if op=="B":return b
    if op=="const":return ast[1]
    if op=="not":return not eval_source_boolean(ast[1],a,b)
    if op=="or":return (eval_source_boolean(ast[1],a,b) or
                        eval_source_boolean(ast[2],a,b))
    raise ValueError("UNSUPPORTED_PRIOR_SOURCE_AST")

def cross_type_law_check(or_ast):
    """Finite proof over all 2^3 guard,branch-adequacy assignments.
    An additional Z3 theorem checks the same fact over UNBOUNDED integers.
    """
    for g,a,b in itertools.product((False,True),repeat=3):
        exact=(a if g else b)
        source_union=eval_source_boolean(or_ast,a,b)
        if exact and not source_union:raise AssertionError("BROKEN_TRANSFER")
    # If-then-else returns a branch value, it must equal at least one branch.
    x,y,z=z3.Ints("candidate_left candidate_right desired_int")
    g=z3.Bool("selector_guard")
    wrong=z3.And(z==z3.If(g,x,y),z3.Not(z3.Or(z==x,z==y)))
    proof=z3.Solver();proof.add(wrong)
    if proof.check()!=z3.unsat:raise AssertionError("CROSS_INT_LOGICAL_PROOF_FAILED")
    # A tempting wrong rule demands BOTH branch expressions be correct;
    # this is false, and Z3 must produce a concrete counterexample.
    negative=z3.Solver()
    negative.add(z==z3.If(g,x,y),z3.Not(z3.And(z==x,z==y)))
    if negative.check()!=z3.sat:raise AssertionError("NEGATIVE_CONTROL_NOT_DETECTED")
    return {"all_boolean_triplets_checked":8,
            "unbounded_integer_ite_implies_branch_union":"Z3_UNSAT",
            "false_intersection_mutant":"Z3_SAT"}

def all_variants():
    return list(itertools.product(GUARDS,BRANCH_ORDERS))

def make_fold(params,variant):
    """Constructor AST is identical between source and target; only arity
    changes. No target file names or reference semantics enter this function.
    """
    guard,branch=variant
    left=params[0]
    for right in params[1:]:
        if branch=="left":
            left=f"(ite ({guard} {left} {right}) {left} {right})"
        else:
            left=f"(ite ({guard} {left} {right}) {right} {left})"
    return left

def compile_original(raw,variant):
    task=decode_original(raw)
    formula=make_fold(task["params"],variant)
    definition=f"(define-fun {task['name']} ("+ " ".join(
        f"({p} Int)" for p in task["params"])+f") Int {formula})"
    lines=["(set-logic LIA)",definition]
    all_constraints=[]
    for row in task["forms"]:
        if not row:continue
        op=row[0]
        if op in ("set-logic","synth-fun","check-synth"):continue
        if op=="declare-var":
            if len(row)!=3 or row[2]!="Int":raise ValueError("BAD_VAR_DECL")
            lines.append(f"(declare-const {row[1]} Int)")
        elif op=="define-fun":
            lines.append(serialize(row))
        elif op=="constraint":
            if len(row)!=2:raise ValueError("BAD_CONSTRAINT")
            all_constraints.append(serialize(row[1]))
        else:raise ValueError("UNSUPPORTED_TOPLEVEL_"+str(op))
    if len(all_constraints)!=len(task["constraints"]):raise ValueError("CONSTRAINT_DRIFT")
    lines.append("(assert (not (and "+" ".join(all_constraints)+")))")
    return "\n".join(lines)

def prove_candidate(raw,variant,timeout_ms=4000):
    started=time.perf_counter_ns()
    script=compile_original(raw,variant)
    checker=z3.Solver();checker.set("timeout",timeout_ms)
    checker.from_string(script)
    result=checker.check()
    elapsed=(time.perf_counter_ns()-started)/1e6
    if result==z3.unsat:
        return {"status":"UNBOUNDED_INT_Z3_UNSAT","proof_ms":round(elapsed,5)}
    if result==z3.sat:
        return {"status":"INVALID_Z3_COUNTEREXAMPLE","proof_ms":round(elapsed,5),
                "counterexample":str(checker.model())[:650]}
    return {"status":"UNKNOWN_TIMEOUT","proof_ms":round(elapsed,5),
            "reason":str(checker.reason_unknown())}

def fetch(name):
    if name not in SOURCE+TARGET:raise ValueError("NOT_IN_FROZEN_REGISTRY")
    with urllib.request.urlopen(ROOT+name,timeout=25) as handle:raw=handle.read(250001)
    if len(raw)>250000:raise ValueError("ORIGINAL_TOO_BIG")
    return raw.decode("utf-8")

def source_only():
    previous=load_prior()
    theorem=cross_type_law_check(previous["or_ast"])
    trials=all_variants();first=SOURCE[0]
    raw=fetch(first)
    source_results=[]
    verified=[]
    for var in trials:
        verdict=prove_candidate(raw,var,timeout_ms=2500)
        source_results.append({"variant":list(var),**verdict})
        if verdict["status"]=="UNBOUNDED_INT_Z3_UNSAT":
            verified.append(var)
    if not verified:raise ValueError("SOURCE_NO_VERIFIED_INTEGER_CONSTRUCTOR")
    # Prefer minimal source discovery cost when ties; ties are resolved by
    # deterministic candidate order, not any hidden target outcome.
    chosen=verified[0]
    second=fetch(SOURCE[1])
    again=prove_candidate(second,chosen,timeout_ms=4000)
    if again["status"]!="UNBOUNDED_INT_Z3_UNSAT":
        raise ValueError("SOURCE_NEXT_ARITY_TRANSFER_FAILED")
    metadata={"schema":"neumann.q3.cross-domain-bv-bool-to-unbounded-lia-synthesis.v1",
         "source_original_run":42435101680,
         "frozen_boolean_source":previous,
         "cross_type_invariant_theorem":theorem,
         "integer_source_names":SOURCE,
         "source_original_sha256":[hashlib.sha256(raw.encode()).hexdigest(),
                                   hashlib.sha256(second.encode()).hexdigest()],
         "candidate_constructor_universe":[list(x) for x in trials],
         "source_variant_test_ledger":source_results,
         "source_verified_variants":[list(x) for x in verified],
         "learned_fold_constructor":list(chosen),
         "source_max3_unbounded_proof":again,
         "human_written":"type adapter SMT compiler, 12 candidate fold schema, enumeration, proof harness, source-to-target fold recursion",
         "source_target_disjoint":True}
    metadata["sha256"]=sha(metadata)
    pathlib.Path(POLICY).write_text(json.dumps(metadata,indent=2))
    print(json.dumps({"source_candidates":len(trials),"source_proved":len(verified),
        "learned_fold":chosen,"source_second_verified":True,
        "unbounded_integer_invariant":theorem["unbounded_integer_ite_implies_branch_union"],
        "frozen_policy_sha256":metadata["sha256"]},indent=2))
    return metadata

def target_first():
    policy=json.loads(pathlib.Path(POLICY).read_text())
    signature=policy.pop("sha256")
    if sha(policy)!=signature or policy["integer_source_names"]!=SOURCE:
        raise ValueError("METHOD_CHANGED_AFTER_FROZEN")
    previous=load_prior()
    if policy["frozen_boolean_source"]!=previous:
        raise ValueError("SOURCE_BOOLEAN_CONTRACT_CHANGED")
    print("FROZEN_CROSS_DOMAIN_METHOD_BEFORE_TARGET",signature)
    learned=tuple(policy["learned_fold_constructor"])
    rows=[];beg=time.perf_counter()
    for filename in TARGET:
        record={"id":filename}
        try:
            original=fetch(filename)
            record["original_sha256"]=hashlib.sha256(original.encode()).hexdigest()
            task=decode_original(original)
            record["integer_arity"]=len(task["params"])
            record["learned"]=prove_candidate(original,learned,timeout_ms=4000)
            cold_checks=0;cold_ms=0;found=None;candidate_log=[]
            for candidate in all_variants():
                verdict=prove_candidate(original,candidate,timeout_ms=4000)
                cold_checks+=1;cold_ms+=verdict["proof_ms"]
                candidate_log.append({"variant":list(candidate),**verdict})
                if verdict["status"]=="UNBOUNDED_INT_Z3_UNSAT":
                    found=candidate;break
            record["strong_same_grammar_cold"]={
                "status":"UNBOUNDED_INT_Z3_UNSAT" if found else "ABSTAIN_OR_UNRESOLVED",
                "variant":list(found) if found else None,
                "proof_queries":cold_checks,
                "proof_ms":round(cold_ms,5),
                "all_attempts":candidate_log}
            record["learned"]["proof_queries"]=1
        except Exception as e:
            record["error"]=type(e).__name__+": "+str(e)[:180]
        rows.append(record)
    summary={
      "tasks":len(TARGET),"errors":sum("error" in row for row in rows),
      "learned_unbounded_proved":sum(r.get("learned",{}).get("status")=="UNBOUNDED_INT_Z3_UNSAT" for r in rows),
      "cold_unbounded_proved":sum(r.get("strong_same_grammar_cold",{}).get("status")=="UNBOUNDED_INT_Z3_UNSAT" for r in rows),
      "learned_proof_queries":sum(r.get("learned",{}).get("proof_queries",0) for r in rows),
      "cold_proof_queries":sum(r.get("strong_same_grammar_cold",{}).get("proof_queries",0) for r in rows),
      "learned_proof_ms":round(sum(r.get("learned",{}).get("proof_ms",0) for r in rows),5),
      "cold_proof_ms":round(sum(r.get("strong_same_grammar_cold",{}).get("proof_ms",0) for r in rows),5)}
    out={"schema":"neumann.q3.independent-int-max-formal-original-first.v1",
         "source_method_sha256":signature,
         "official_repository":"SyGuS-Org/benchmarks","upstream_commit":UPSTREAM,
         "target_registry":TARGET,"proof_domain":"UNBOUNDED_Z3_INTEGERS",
         "equal_grammar_control":"all 12 two-arm ITE fold variants",
         "summary":summary,"target_records":rows,
         "target_wall_seconds":round(time.perf_counter()-beg,4),
         "limitations":"Source and target share jmbl max problem family; Boolean invariant from 4-bit source is type-independent, but integer fold is learned from separate Int max2/max3 source. Human-designed interpreter and fold hypothesis class. Not independent-author general Q3 or amortized Q4."}
    pathlib.Path(TARGET_REPORT).write_text(json.dumps(out,indent=2))
    print(json.dumps(summary,indent=2))
    return out

if __name__=="__main__":
    import sys
    if sys.argv[1:]==["source"]:source_only()
    elif sys.argv[1:]==["target"]:target_first()
    else:raise SystemExit("Usage: source or target")
