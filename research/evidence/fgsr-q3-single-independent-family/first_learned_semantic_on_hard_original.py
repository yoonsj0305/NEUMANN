"""NEUMANN FGSR single PRETRAINED learned semantic conjecture (OPENED HARD ORIGINAL).

This is a frozen one-shot discovery-mechanism diagnostic, NOT trained NEUMANN.
The *only* neural output is one whole Boolean SMT term. No gold lemma/template.
The formula is never repaired by classical code; original 48 Horn clauses are
independently checked in full. Competing restricted classical Houdini already
reached 46/48 (not an iso-capability speed or accuracy claim).
"""
import hashlib,json,os,re,time,urllib.request
from pathlib import Path

SOURCE_COMMIT="b4fa7a708e5863bbcdb5de50d692ead3a67cbedc"
SOURCE="ultimate/LIA-NonLin/33_double_lock_p1_vs_simplified_000.smt2"
SOURCE_SHA256="2dfd3f531151113401aca614ad3e4176dae77ebcb326abbbcc456551a9a8f645"
MODEL="Qwen/Qwen2.5-0.5B-Instruct"
MODEL_REV="7ae557604adf67be50417f59c2c2f167def9a775"
SEED=20261017
MAX_NEW_TOKENS=192
PROMPT='''The following text is the COMPLETE ORIGINAL set of 48 constrained Horn clauses for a program-safety verification task, with a predicate Inv(Int x0, Int x1, Int x2, Int x3, Int x4, Int x5, Int x6, Int x7). Invent exactly ONE new, nontrivial, genuinely source-appropriate *inductive invariant* describing the reachable Inv states. Your proposal must hold for ALL initial rules and be preserved under ALL Horn transition rules, including multi-premise rules, and should help prove the error goals unreachable.

Return ONLY one valid SMT-LIB2 Bool s-expression. Its only free variables may be x0 x1 x2 x3 x4 x5 x6 x7, each an Int. You may use SMT Bool arithmetic connectives, implies, comparisons, and, or, not, +, -, =, <=, >=, ite. Do NOT write an assertion, a declaration, a code block, JSON, additional text, or a second candidate.

Exact untouched original source:
'''
OUT=Path(os.environ.get("FGSR_RESULT","learned_semantic_first_receipt.json"))

def top_level_single(text):
    text=text.strip()
    if not text.startswith("("):raise ValueError("NOT_A_SINGLE_S_EXPR")
    depth=0;index=-1
    for i,c in enumerate(text):
        if c=="(":depth+=1
        if c==")":
            depth-=1
            if depth<0:raise ValueError("UNBALANCED_TERM")
            if depth==0:
                index=i
                break
    if index != len(text)-1 or depth!=0:raise ValueError("EXTRANEOUS_TEXT_OR_UNBALANCED_TERM")
    return text

def independent_original_checker(original,model_expression):
    import z3
    form=top_level_single(model_expression)
    vars_=[z3.Int(f"x{i}") for i in range(8)]
    declarations="".join(f"(declare-const x{i} Int)\n" for i in range(8))
    parsed=z3.parse_smt2_string(declarations+"(assert "+form+")")
    if len(parsed)!=1 or parsed[0].sort()!=z3.BoolSort():raise ValueError("NOT_ONE_TYPED_BOOL")
    predicate=parsed[0]
    nontrivial=z3.Solver();nontrivial.set(timeout=2000)
    nontrivial.add(predicate)
    if nontrivial.check()!=z3.sat:raise ValueError("EMPTY_RELATION_NOT_CERTIFICATE")
    nontrivial=z3.Solver();nontrivial.set(timeout=2000)
    nontrivial.add(z3.Not(predicate))
    if nontrivial.check()!=z3.sat:raise ValueError("TAUTOLOGICAL_RELATION_NOT_STRUCTURE")

    from z3 import parse_smt2_string,is_quantifier,is_implies,is_and,is_app
    clauses=parse_smt2_string(original)
    if len(clauses)!=48:raise ValueError("AUTHENTIC_ORIGINAL_COUNT_CHANGED")
    records=[]
    for ix,q in enumerate(clauses,1):
        if not is_quantifier(q) or not q.is_forall():raise ValueError("NON_FORALL_ORIGINAL_RULE")
        locals_=[z3.Const(f"original_{ix}_var_{j}",q.var_sort(j)) for j in range(q.num_vars())]
        implies=z3.substitute_vars(q.body(),*locals_)
        if not is_implies(implies):raise ValueError("NON_HORN_ORIGINAL")
        premise,consequence=implies.children()
        atoms=[]
        def flatten(x):
            if is_and(x):
                for arg in x.children():flatten(arg)
            else:atoms.append(x)
        flatten(premise)
        originals=[a for a in atoms if is_app(a) and a.decl().name()=="Inv"]
        guards=[a for a in atoms if not(is_app(a) and a.decl().name()=="Inv")]

        def applied(a):
            if a.num_args()!=8:raise ValueError("BAD_RELATION_ARITY")
            return z3.substitute(predicate,*[(vars_[j],a.arg(j)) for j in range(8)])
        def replace_error(x):
            if is_app(x) and x.decl().name()=="CHC_COMP_FALSE":return z3.BoolVal(False)
            return x
        antecedents=[replace_error(x) for x in guards]+[applied(a) for a in originals]
        if is_app(consequence) and consequence.decl().name()=="Inv":
            goal=z3.Not(applied(consequence))
        elif is_app(consequence) and consequence.decl().name()=="CHC_COMP_FALSE":
            goal=z3.BoolVal(True)
        elif z3.is_false(consequence):
            goal=z3.BoolVal(True)
        else:raise ValueError("UNSUPPORTED_CLAUSE_HEAD")
        s=z3.Solver()
        s.set(timeout=2000)
        s.add(*antecedents,goal)
        start=time.perf_counter_ns()
        v=str(s.check())
        records.append({"original_clause_index":ix,"verdict":v,
                        "wall_ms":round((time.perf_counter_ns()-start)/1e6,3)})
    return {
        "model_formula_exact_unmodified":form,
        "z3_version":z3.get_version_string(),
        "all_original_48_clause_checks":records,
        "certified_unsat":sum(x["verdict"]=="unsat" for x in records),
        "first_unproven_rule":next((x for x in records if x["verdict"]!="unsat"),None),
        "original_all_48_certified":all(x["verdict"]=="unsat" for x in records),
        "verifier_only_not_model_discovery":False
    }

def main():
    started=time.perf_counter_ns()
    receipt={
        "study":"FGSR-Q3 learned semantic content untrained_NEUMANN opened 48-chc",
        "status":"NOT_RUN",
        "scientific_gate":"LEARNED_Q3_OPEN",
        "global_q1_q7":"OPEN",
        "model_provenance":"PUBLIC_PRETRAINED_LM_NOT_NEUMANN_TRAINED_CORE",
        "one_frozen_sample":True,"training_from_this_study":False,
        "model_id":MODEL,"model_rev":MODEL_REV,"seed":SEED,
        "source_sha256":SOURCE_SHA256,"source_opened_not_holdout":True,
        "pretraining_contamination_unknown":True,
        "max_new_tokens":MAX_NEW_TOKENS,
        "original_modified":False,"model_semantics_autocompleted":False,
        "neural_generation_calls":0,
        "cost_usd":"UNKNOWN","energy_joules":"UNKNOWN","model_training_amortized":"UNKNOWN",
    }
    try:
        import torch
        from transformers import AutoModelForCausalLM,AutoTokenizer
        torch.set_num_threads(2)
        torch.manual_seed(SEED)
        url=f"https://raw.githubusercontent.com/chc-comp/chc-comp26-benchmarks/{SOURCE_COMMIT}/{SOURCE}"
        with urllib.request.urlopen(url,timeout=35) as response:raw=response.read()
        if hashlib.sha256(raw).hexdigest()!=SOURCE_SHA256:raise ValueError("SOURCE_HASH_MISMATCH")
        original=raw.decode()
        if len(re.findall(r"\(assert\s",original))!=48:raise ValueError("ORIGINAL_RULE_COUNT_CHANGED")
        tokenizer=AutoTokenizer.from_pretrained(MODEL,revision=MODEL_REV)
        model=AutoModelForCausalLM.from_pretrained(MODEL,revision=MODEL_REV,torch_dtype=torch.float32)
        model.eval()
        messages=[{"role":"user","content":PROMPT+original}]
        chat=tokenizer.apply_chat_template(messages,tokenize=False,add_generation_prompt=True)
        inputs=tokenizer(chat,return_tensors="pt")
        receipt["prompt_tokens"]=int(inputs["input_ids"].shape[-1])
        t=time.perf_counter_ns()
        with torch.inference_mode():
            outputs=model.generate(**inputs,do_sample=False,max_new_tokens=MAX_NEW_TOKENS,
                                   pad_token_id=tokenizer.eos_token_id)
        receipt["neural_generation_calls"]=1
        receipt["neural_generate_wall_ms"]=round((time.perf_counter_ns()-t)/1e6,3)
        receipt["generation_output_tokens"]=int(outputs.shape[-1])-receipt["prompt_tokens"]
        proposal=tokenizer.decode(outputs[0,receipt["prompt_tokens"]:],skip_special_tokens=True)
        receipt["exact_unedited_model_output"]=proposal
        receipt["model_output_sha256"]=hashlib.sha256(proposal.encode()).hexdigest()
        t=time.perf_counter_ns()
        try:
            audit=independent_original_checker(original,proposal)
            receipt["model_candidate_check"]=audit
            receipt["status"]=("PRETRAINED_OPEN_DEV_ORIGINAL_48_CERTIFIED_NOT_Q3" if audit["original_all_48_certified"]
                else "PRETRAINED_CANDIDATE_ORIGINAL_RULES_FAILED")
        except Exception as exc:
            receipt["status"]="PRETRAINED_CANDIDATE_TYPED_OR_LOGIC_REJECTED"
            receipt["candidate_error"]=type(exc).__name__+": "+str(exc)[:950]
        receipt["independent_verify_wall_ms"]=round((time.perf_counter_ns()-t)/1e6,3)
    except Exception as exc:
        receipt["status"]="EXPERIMENT_ENVIRONMENT_BLOCKED"
        receipt["error"]=type(exc).__name__+": "+str(exc)[:950]
    receipt["total_wall_ms"]=round((time.perf_counter_ns()-started)/1e6,3)
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+"\n")
    print("LEARNED_SEMANTIC_STUDY",receipt["status"])
    print("ORIGINAL_CERTIFIED",receipt.get("model_candidate_check",{}).get("certified_unsat"),"of 48")
    print("NEURAL_GENERATION_CALLS",receipt["neural_generation_calls"])
    print("GLOBAL_Q",receipt["global_q1_q7"])

if __name__=="__main__":main()
