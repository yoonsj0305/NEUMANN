#!/usr/bin/env python3
"""Prospective eight same-author danger-loop sibling originals: fail-closed
hand-designed template T vs modern native 1.4.2 C. NOT ownweight AI.

Prereg exact list and grammar/constraint skeleton BEFORE reading any task body.
Requires original upstream pin, original parent exact SHA and official CVC5 1.4.2
SHA-pinned binary (ensured by workflow). No code changes based on 8 test contents.
"""
import collections,hashlib,json,pathlib,re,subprocess,sys,time
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from sgi_first_classical_original import top_level_forms,get_cmd,sha256
from sygus_official_multifamily_classical_first_20261027 import run_solver
from sygus_dangerloop21_analytic_z3_exact_original_20261027 import PROGRAMS

PIN="13c8deb68a873635879c9a69bc78caebd340f646"
ROOT=pathlib.Path("official_repo")
PARENT="lib/General_Track/cegist-cav18/inv/danger-loop21.sl"
PARENT_SHA="8b3fa6aa436f67ec10b1112c3f7e8ffb1eb0e920b0268bcae5d3adf8cced539c"
OUT=pathlib.Path("official_danger8_first")
PREFIX="neumann1-g0-unseen-danger-sibling-v1/"
FROZEN_ORDER=[
  "lib/General_Track/cegist-cav18/inv/danger-loop42.sl",
  "lib/General_Track/cegist-cav18/inv/danger-loop29.sl",
  "lib/General_Track/cegist-cav18/inv/danger-loop36.sl",
  "lib/General_Track/cegist-cav18/inv/danger-loop39.sl",
  "lib/General_Track/cegist-cav18/inv/danger-loop20.sl",
  "lib/General_Track/cegist-cav18/inv/danger-loop37.sl",
  "lib/General_Track/cegist-cav18/inv/danger-loop35.sl",
  "lib/General_Track/cegist-cav18/inv/danger-loop30.sl",
]
FROZEN_ORDER_SHA="bc6fec2674f0593697b4515b595173d7f7454102fbb5a49f2ff55e48bd472065"
ALLOWED_HELPERS=("if0","expand","G","B_x","B_y","A")
ALLOWED_SYNTH=("D","R","S")
CVC5_ZIP_SHA="0af677313c8277dc558d3049b192389db4d975d31c968fbd6f31cf0849ee411d"

def norm(s):
    return re.sub(r"\s+"," ",s).strip()

def raw_forms(s):
    forms=top_level_forms(s)
    return [(get_cmd(f[2]),f[2]) for f in forms]

def only_symbol(form,command):
    m=re.match(r"^\(\s*"+command+r"\s+([^\s()]+)",form)
    if not m:raise ValueError("CANNOT_READ_DECLARATION_NAME")
    return m.group(1)

def split_source(raw):
    fr=raw_forms(raw)
    helpers={only_symbol(x,"define-fun"):x for c,x in fr if c=="define-fun"}
    synth={only_symbol(x,"synth-fun"):x for c,x in fr if c=="synth-fun"}
    constraints=[x for c,x in fr if c=="constraint"]
    declares=[x for c,x in fr if c=="declare-var"]
    return fr,helpers,synth,constraints,declares

def family_paths():
    files=subprocess.check_output(["git","-C",str(ROOT),"ls-tree","-r","--name-only","HEAD"],text=True).splitlines()
    cand=[x for x in files if x.startswith(
        "lib/General_Track/cegist-cav18/inv/danger-loop") and x.endswith(".sl")
        and x not in (PARENT,"lib/General_Track/cegist-cav18/inv/danger-loop33.sl")]
    cand.sort(key=lambda x:(sha256((PREFIX+x).encode()),x))
    paths=cand[:8]
    assert paths==FROZEN_ORDER
    assert sha256("\n".join(paths).encode())==FROZEN_ORDER_SHA
    return paths

def template_compare(parent_struct,source):
    """Exact parent structure up to a single nonzero guard constant."""
    fr,helper,synth,con,dec=split_source(source)
    pr,phelp,psynth,pcon,pdec=parent_struct
    expected=[c for c,_ in pr]
    actual=[c for c,_ in fr]
    if expected!=actual:raise ValueError("TOP_LEVEL_FORM_COMMANDS_DIFFER")
    if len(con)!=3 or len(dec)!=2:raise ValueError("CONSTRAINT_OR_VARIABLE_COUNT_MISMATCH")
    if tuple(sorted(helper))!=tuple(sorted(ALLOWED_HELPERS)):
        raise ValueError("HELPER_SET_MISMATCH")
    if tuple(sorted(synth))!=tuple(sorted(ALLOWED_SYNTH)):
        raise ValueError("SYNTH_FUNCTION_NAMES_DIFFER")
    for op in ALLOWED_SYNTH:
        if norm(synth[op])!=norm(psynth[op]):
            raise ValueError("SYNTH_SIGNATURE_OR_GRAMMAR_DIFF_"+op)
    for i,(a,b) in enumerate(zip(con,pcon)):
        if norm(a)!=norm(b):raise ValueError("ORIGINAL_CONSTRAINT_FORM_DIFF_"+str(i))
    for i,(a,b) in enumerate(zip(dec,pdec)):
        if norm(a)!=norm(b):raise ValueError("ORIGINAL_VARIABLE_DECL_DIFF_"+str(i))
    for name in ALLOWED_HELPERS:
        if name!="G" and norm(helper[name])!=norm(phelp[name]):
            raise ValueError("ORIGINAL_HELPER_DIFF_"+name)
    original_G=phelp["G"]
    assert norm(original_G).count("#x00010003")==1
    matches=re.findall(r"\(bvult\s+x\s+(#x[0-9a-fA-F]{8})\)",helper["G"])
    if len(matches)!=1:raise ValueError("GUARD_NOT_SIMPLE_32BIT_LITERAL")
    target=matches[0]
    if norm(helper["G"]).replace(target,"<N>")!=norm(original_G).replace("#x00010003","<N>"):
        raise ValueError("GUARD_FORM_NOT_PARENT_MATCH")
    n=int(target[2:],16)
    if n==0:raise ValueError("N_IS_ZERO_PREMISE_NOT_APPLICABLE")
    return (n,target,fr,con)

def z3_all_actual(fr,con,candidate_defs):
    import z3
    defs=[]
    for cmd,form in fr:
        if cmd=="declare-var":
            defs.append(re.sub(r"^\(\s*declare-var\b","(declare-const",form,count=1))
        if cmd in ("set-logic","define-fun"):
            defs.append(form)
    defs.extend(candidate_defs)
    base="\n".join(defs)+"\n"
    outcomes=[]
    for i in range(4):
        cur=con[i] if i<3 else "(constraint (and "+" ".join(re.match(
            r"^\(\s*constraint\s+(.+)\s*\)$",p,re.S).group(1) for p in con)+"))"
        expr=re.match(r"^\(\s*constraint\s+(.+)\s*\)$",cur,re.S).group(1)
        text=base+"(assert (not "+expr+"))\n"
        start=time.perf_counter()
        solver=z3.Solver()
        solver.set(timeout=10000)
        solver.add(*z3.parse_smt2_string(text))
        state=str(solver.check())
        outcomes.append({"check":i,"z3":state,
          "script_sha256":sha256(text.encode()),
          "wall_seconds":round(time.perf_counter()-start,6)})
    return outcomes

def parse_native_candidate(stdout):
    # CVC5 output is SMT-LIB define-fun triples, possibly wrapped by whitespace.
    triples=[f[2] for f in top_level_forms(stdout) if get_cmd(f[2])=="define-fun"]
    if len(triples)!=3:
        raise ValueError("NOT_EXACTLY_THREE_COMPLETE_DEFINE_FUN")
    names=[only_symbol(x,"define-fun") for x in triples]
    if sorted(names)!=sorted(ALLOWED_SYNTH):raise ValueError("OUTPUT_TRIPLE_WRONG_NAMES")
    return triples

def main():
    import z3
    assert subprocess.check_output(["git","-C",str(ROOT),"rev-parse","HEAD"],text=True).strip()==PIN
    assert sha256((ROOT/PARENT).read_bytes())==PARENT_SHA
    parent_struct=split_source((ROOT/PARENT).read_text())
    assert len(family_paths())==8
    native=subprocess.check_output(["cvc5","--version"],text=True).strip().splitlines()[0]
    assert native.startswith("cvc5 1.4.2 ")
    OUT.mkdir(exist_ok=True)
    rows=[]
    for ix,rel in enumerate(FROZEN_ORDER):
        raw=(ROOT/rel).read_bytes()
        row={"index":ix,"original_path":rel,"original_sha256":sha256(raw),
             "upstream":PIN,"pre_content_fixed_order_sha256":FROZEN_ORDER_SHA,
             "template_status":"HOLD_NOT_APPLICABLE",
             "native_classical_status":"HOLD",
             "not_ownweight_training":True}
        source=raw.decode("utf8")
        t0=time.process_time()
        try:
            n,n_literal,fr,con=template_compare(parent_struct,source)
            programs=[p.replace("#x00010003",n_literal) for p in PROGRAMS]
            assert programs[0]==PROGRAMS[0] and programs[2]==PROGRAMS[2]
            checked=z3_all_actual(fr,con,programs)
            row["template_z3"]=checked
            row["template_n"]=n
            row["template_program_sha256"]=sha256("\n".join(programs).encode())
            (OUT/(f"{ix:02d}_template_program.smt2")).write_text("\n".join(programs)+"\n")
            row["template_status"]=(
                "PASS_SEMANTIC_FORMAL_ORIGINAL_ALL4"
                if all(c["z3"]=="unsat" for c in checked) else
                "HOLD_OR_FALSIFIED_BY_Z3")
        except Exception as e:
            row["template_reason"]=type(e).__name__+":"+str(e)[:180]
        row["template_process_cpu_seconds"]=round(time.process_time()-t0,6)
        try:
            stdout,stderr,cost=run_solver(ROOT/rel)
            (OUT/f"{ix:02d}_native.stdout").write_text(stdout)
            (OUT/f"{ix:02d}_native.stderr").write_text(stderr)
            row["native_cost"]=cost
            if cost["forced"] or cost["returncode"] in (-6,-9,-24):
                row["native_classical_status"]="C_BUDGET_HOLD"
            elif cost["returncode"]!=0 or "(error" in (stdout+stderr).lower():
                row["native_classical_status"]="HOLD_NATIVE_EXCEPTION_OR_UNSUPPORTED"
            elif "(define-fun" not in stdout:
                row["native_classical_status"]="HOLD_NATIVE_NO_PROGRAM"
            else:
                try:
                    fr,helper,synth,con,dec=split_source(source)
                    triple=parse_native_candidate(stdout)
                    if "synth-inv" in [cmd for cmd,form in fr]:
                        raise ValueError("INVARIANT_SYNTAX_SPECIAL")
                    native_proof=z3_all_actual(fr,con,triple)
                    row["native_z3"]=native_proof
                    row["native_classical_status"]=(
                        "C_PROGRAM_Z3_ORIGINAL_FULL_PASS"
                        if all(q["z3"]=="unsat" for q in native_proof) else
                        "HOLD_NATIVE_RETURNED_PROGRAM_NOT_Z3_PROVED")
                except Exception as e:
                    row["native_classical_status"]="HOLD_NATIVE_PARSE_OR_Z3"
                    row["native_reason"]=type(e).__name__+":"+str(e)[:180]
        except Exception as e:
            row["native_classical_status"]="HOLD_CLASSICAL_PROCESS"
            row["native_reason"]=type(e).__name__+":"+str(e)[:180]
        rows.append(row)
        print("PROSPECTIVE_DANGER8",rel,row["template_status"],
              row["native_classical_status"],flush=True)
    receipt={
      "status":"PROSPECTIVE_SAME_AUTHOR_TEMPLATE_AND_CLASSIC_EVALUATED",
      "exact_upstream_git_sha":PIN,"original_parent_sha256":PARENT_SHA,
      "filename_selection_sha256":FROZEN_ORDER_SHA,
      "machine_source_code_sha_not_inline":"RECOVER_GITHUB_COMMIT",
      "z3_version":z3.get_version_string(),
      "native_version":native,"official_native_release_zip_sha256":CVC5_ZIP_SHA,
      "task_denominator":8,
      "summary_template":dict(collections.Counter(r["template_status"] for r in rows)),
      "summary_native":dict(collections.Counter(r["native_classical_status"] for r in rows)),
      "global_Q1_Q7":"OPEN","G1":"HOLD","G2":"NOT_RUN",
      "no_neural_ownweight":True,
      "rows":rows}
    p=OUT/"DANGERLOOP_SAME_AUTHOR_PROSPECTIVE_EIGHT_TEMPLATE_VS_CVC5_142.json"
    p.write_text(json.dumps(receipt,sort_keys=True,indent=2))
    print("EIGHT_FIRST_AND_Z3_SHA256",sha256(p.read_bytes()))
    print("SUMMARY",json.dumps({"template":receipt["summary_template"],
                                "classical":receipt["summary_native"]},sort_keys=True))
if __name__=="__main__":main()
