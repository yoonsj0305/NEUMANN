#!/usr/bin/env python3
"""Third independent METHOD (pure Python interpreter) on original inv106.sl.

Read exactly published author source, parse only its integer Boolean formulae,
evaluate pre-f/trans-f/post-f at the 28 integers precommitted BEFORE formal
SMT proof. This directly certifies an unsafe one-transition trace, without
importing a theorem solver or using human-transcribed source helper clauses.
"""
import hashlib,json,pathlib,re,subprocess,time

PIN="13c8deb68a873635879c9a69bc78caebd340f646"
PATH="lib/Inv_Track/xujie_code2inv/106.c.sl"
ORIGINAL=pathlib.Path("official_repo")/PATH
VARS="a j k m a_0 j_0 k_0 k_1 k_2 k_3 m_0 m_1 m_2 m_3".split()
S0=[0,0,0,1,0,0,0,0,0,1,1,1,0,1]
S1=[0,0,1,1,0,0,0,0,1,0,1,1,0,0]

def read_program(text):
    tokens=re.findall(r"\(|\)|[^\s()]+",text)
    pos=0
    def read():
        nonlocal pos
        if pos>=len(tokens):raise ValueError("UNEXPECTED_EOF")
        t=tokens[pos];pos+=1
        if t!="(":return t
        result=[]
        while pos<len(tokens) and tokens[pos]!=")":
            result.append(read())
        if pos>=len(tokens):raise ValueError("UNBALANCED_OPEN")
        pos+=1
        return result
    forms=[]
    while pos<len(tokens):forms.append(read())
    assert [f[0] for f in forms if isinstance(f,list) and f[0]=="define-fun"]==[
        "define-fun"]*3
    return {form[1]:form for form in forms if isinstance(form,list) and form[0]=="define-fun"}

def eval_ast(n,env):
    if isinstance(n,str):
        if re.fullmatch(r"-?[0-9]+",n):return int(n)
        if n=="true":return True
        if n=="false":return False
        return env[n]
    op=n[0]
    args=[eval_ast(a,env) for a in n[1:]]
    if op=="and":return all(args)
    if op=="or":return any(args)
    if op=="not":return not args[0]
    if op=="=":return all(x==args[0] for x in args)
    if op=="<":return args[0]<args[1]
    if op=="<=":return args[0]<=args[1]
    if op==">":return args[0]>args[1]
    if op==">=":return args[0]>=args[1]
    if op=="+":return sum(args)
    raise ValueError("UNSUPPORTED_SOURCE_OPERATOR:"+str(op))

def evaluate_precommitted_witness():
    t=time.process_time()
    assert subprocess.check_output(
        ["git","-C","official_repo","rev-parse","HEAD"],text=True).strip()==PIN
    raw=ORIGINAL.read_bytes()
    forms=read_program(raw.decode("utf8"))
    assert set(forms)=={"pre-f","trans-f","post-f"}
    for name,expected in [("pre-f",14),("trans-f",28),("post-f",14)]:
        f=forms[name]
        assert len(f[2])==expected
        if expected==14:assert [b[0] for b in f[2]]==VARS
        assert all(b[1]=="Int" for b in f[2])
    def call(name,values):
        f=forms[name]
        names=[b[0] for b in f[2]]
        return eval_ast(f[4],dict(zip(names,values)))
    original_pre=call("pre-f",S0)
    original_transition=call("trans-f",S0+S1)
    original_post=call("post-f",S1)
    proved=original_pre is True and original_transition is True and original_post is False
    result={
        "kind":"SOURCE_PARSED_PURE_PYTHON_CONCRETE_ORIGINAL_UNSAFE_TRACE",
        "original_git_sha":PIN,"original_path":PATH,
        "original_sha256":hashlib.sha256(raw).hexdigest(),
        "source_definitions_parsed_verbatim":True,
        "state_names":VARS,"state0":S0,"state1":S1,
        "original_pre":original_pre,"original_trans":original_transition,
        "original_post_after_step":original_post,
        "result":"ONE_STEP_UNSAFE_REACHABLE_NO_VALID_INDUCTIVE_SAFETY_INVARIANT"
             if proved else "HOLD_OR_FALSIFIED",
        "source_eval_CPU_seconds":round(time.process_time()-t,7),
        "does_not_claim_ownweight_neural_intelligence":True,
        "G1":"HOLD","Q1_Q7":"OPEN","G2":"NOT_RUN",
    }
    pathlib.Path("INV106_ORIGINAL_SOURCE_PURE_INTERPRETER_WITNESS.json").write_text(
        json.dumps(result,sort_keys=True,indent=2))
    print("ORIGINAL_SOURCE_GROUND_UNSAFETY",result["result"])
    assert proved, result
    return result
if __name__=="__main__":evaluate_precommitted_witness()
