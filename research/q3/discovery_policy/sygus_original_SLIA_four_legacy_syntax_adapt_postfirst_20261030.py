#!/usr/bin/env python3
"""POST-FIRST format-only four legacy String PBE synth grammars.

Preserve original full examples and every original production AST. Re-render
the old one-list SyGuS grammar as modern two-list (symbols, productions)
without altering target specification. Strong classical cvc5 1.4.2 once/file.
Independent Z3 semantics on returned programs, no pretend oracle output.
"""
import collections,hashlib,json,pathlib,re,subprocess,sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from sgi_first_classical_original import sha256
from sygus_official_multifamily_classical_first_20261027 import run_solver
from sygus_external_four_new_tracks16_first_20261028 import PIN,FIXED
from sygus_official_diverse12_independent_z3_postfirst_20261028 import independent_grade

FIRST_SHA="7acee7938ea2b8d18db2dd38058de36f7abdcf5116fbd703f6fce048b3a4418c"
FIRST=pathlib.Path("external_new16_sealed_FIRST")
ROOT=pathlib.Path("official_repo")
OUT=pathlib.Path("external_SLIA4_legacy_grammar_adapter_POSTFIRST")
FIRST_FILE="NEUMANN_G1_EXTERNAL_NEW16_FOUR_TRACKS_CVC5_FIRST.json"

def parse_all(src):
    stripped="\n".join(l for l in src.splitlines() if not l.lstrip().startswith(";"))
    tokens=re.findall(r'"(?:\\.|[^"\\])*"|[()]|[^\s()]+',stripped)
    ptr=0
    def element():
        nonlocal ptr
        if ptr>=len(tokens):raise ValueError("UNEXPECTED_END")
        t=tokens[ptr];ptr+=1
        if t==")":raise ValueError("UNEXPECTED_CLOSE")
        if t!="(":return t
        a=[]
        while ptr<len(tokens) and tokens[ptr]!=")":
            a.append(element())
        if ptr>=len(tokens):raise ValueError("MISSING_CLOSE")
        ptr+=1
        return a
    acc=[]
    while ptr<len(tokens):acc.append(element())
    return acc

def smt(x):
    if isinstance(x,list):return "("+" ".join(smt(k) for k in x)+")"
    return x

def convert(raw):
    old=parse_all(raw.decode("utf8"))
    originals=[x for x in old if isinstance(x,list) and x and x[0]=="synth-fun"]
    assert len(originals)==1
    old_s=originals[0]
    assert len(old_s)==5 and old_s[1]=="f" and len(old_s[3])>=1
    original_rules=old_s[4]
    assert len(original_rules)==4
    nts=[(r[0],r[1]) for r in original_rules]
    assert len(set(nt for nt,_ in nts))==4
    assert [nt for nt,_ in nts]==["Start","ntString","ntInt","ntBool"]
    assert all(len(r)==3 and isinstance(r[2],list) for r in original_rules)
    new_s=old_s[:4]+[[list(x) for x in nts],original_rules]
    result=[new_s if x is old_s else x for x in old]
    assert result.index(new_s)==old.index(old_s)
    assert [r[2] for r in new_s[5]]==[r[2] for r in old_s[4]]
    assert [r[:2] for r in new_s[5]]==[list(x) for x in nts]
    assert [x for x in old if x is not old_s]==[x for x in result if x is not new_s]
    # Critically no source original example or helper is changed, only the
    # grammar declaration/prod LIST SHAPE. Original strings lexed intact.
    transformed="\n".join(smt(x) for x in result)+"\n"
    assert [x for x in parse_all(transformed) if x[0]!="synth-fun"]==[
        x for x in old if x[0]!="synth-fun"]
    return transformed,old_s,new_s

def main():
    import z3
    assert subprocess.check_output(["git","-C",str(ROOT),"rev-parse","HEAD"],text=True).strip()==PIN
    assert subprocess.check_output(["cvc5","--version"],text=True).splitlines()[0].startswith("cvc5 1.4.2 ")
    first_raw=(FIRST/FIRST_FILE).read_bytes()
    assert sha256(first_raw)==FIRST_SHA
    first=json.loads(first_raw)
    assert tuple(x["original"] for x in first["rows"])==FIXED
    OUT.mkdir(exist_ok=True)
    reports=[]
    for i in range(12,16):
        previous=first["rows"][i]
        assert previous["status"]=="HOLD_NATIVE_EXCEPTION_OR_UNSUPPORTED"
        path=previous["original"]
        raw=(ROOT/path).read_bytes()
        assert sha256(raw)==previous["source_sha256"]
        new_s,old_rule,new_rule=convert(raw)
        adapted=OUT/(f"{i:02d}_converted_full_original.sygus")
        adapted.write_text(new_s)
        stdout,stderr,cost=run_solver(adapted)
        (OUT/(f"{i:02d}_adapted.stdout")).write_text(stdout)
        (OUT/(f"{i:02d}_adapted.stderr")).write_text(stderr)
        native="HOLD"
        semantic="NOT_RETURNED"
        pcount=stdout.count("(define-fun")
        if cost["forced"] or cost["returncode"] in (-6,-9,-24):
            native="CVC5_ADAPTED_BUDGET_HOLD"
        elif cost["returncode"]!=0:
            native="CVC5_ADAPTED_ERROR"
        elif pcount>0:
            native="CVC5_ADAPTED_PROGRAM_UNVERIFIED"
            try:
                grade=independent_grade(previous,
                    "\n".join(l for l in raw.decode().splitlines()
                              if not l.lstrip().startswith(";")),
                    stdout)
                semantic=grade["grade"]
            except Exception as e:
                semantic="HOLD_Z3_PARSER_OR_ORIGINAL"
                err=str(e)[:250]
        else:native="CVC5_ADAPTED_NO_PROGRAM"
        item={"index":i,"original_path":path,
          "original_source_sha256":sha256(raw),
          "adapted_source_sha256":sha256(new_s.encode()),
          "original_sygus_native_first":"PARSER_ERROR_UNCHANGED",
          "one_listing_to_two_listings_only":True,
          "original_program_signature_unchanged":True,
          "original_grammar_four_production_sets_unchanged":True,
          "original_full_pbe_constraints_unchanged":True,
          "native_result":native,"native_def_fun_count":pcount,
          "native_cost":cost,"native_stderr_excerpt":stderr[-450:],
          "independent_source_semantics":semantic}
        if "err" in locals():
            item["independent_error"]=err;del err
        reports.append(item)
        print("SLIA_LEGACY_ADAPTER",i,native,semantic,flush=True)
    output={"study":"POST_FIRST_SOURCE_GRAMMAR_SYNTAX_ONLY_ADAPTER",
        "original_git_pin":PIN,"first_immutable_json_sha256":FIRST_SHA,
        "new_attempts":4,
        "results":dict(collections.Counter(x["native_result"] for x in reports)),
        "verified_original_semantics":sum(x["independent_source_semantics"]==
              "VERIFIED_FULL_ORIGINAL_SEMANTIC_CONSTRAINTS" for x in reports),
        "original_no_arbitrary_target_output_oracle":True,
        "not_neural_learning":True,"global_Q1_Q7":"OPEN","G1":"HOLD","G2":"NOT_RUN",
        "rows":reports}
    p=OUT/"SLIA_FOUR_ORIGINAL_LEGACY_GRAMMAR_FORMAT_ONLY_NATIVE_CVC5.json"
    p.write_text(json.dumps(output,sort_keys=True,indent=2))
    print("LEGACY_FORMAT_ADAPTER_RESULT_SHA",sha256(p.read_bytes()))
    print("LEGACY_FORMAT_SUMMARY",json.dumps(output["results"],sort_keys=True),flush=True)
if __name__=="__main__":main()
