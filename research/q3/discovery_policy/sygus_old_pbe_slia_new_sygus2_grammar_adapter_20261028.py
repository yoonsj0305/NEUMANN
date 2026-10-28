#!/usr/bin/env python3
"""POSTFIRST original euphony PBE SLIA syntax-only old→new SyGuS grammar.

First original native parser-HOLD is immutable. Transform only the one old
synth-fun grammar into (typed NT declarations) + (production rules).
All original typed f signature, every production and all authored constraint
source expressions preserved. Native solver one attempt/task budget capped.
"""
import collections,json,pathlib,re,subprocess,sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from sgi_first_classical_original import top_level_forms,get_cmd,sha256
from sygus_official_multifamily_classical_first_20261027 import run_solver

PIN="13c8deb68a873635879c9a69bc78caebd340f646"
FIRST_SHA="7acee7938ea2b8d18db2dd38058de36f7abdcf5116fbd703f6fce048b3a4418c"
FILES=(
"lib/PBE_SLIA_Track/euphony/get-last-name-from-name-with-comma.sl",
"lib/PBE_SLIA_Track/euphony/count-consecutive-monthly-orders.sl",
"lib/PBE_SLIA_Track/euphony/get-first-word.sl",
"lib/PBE_SLIA_Track/euphony/25239569.sl",
)
ROOT=pathlib.Path("official_repo")
FIRST=pathlib.Path("external_4track16_FROZEN_FIRST")
OUT=pathlib.Path("external_string4_format_repaired")

def span(t,start):
    assert t[start]=='('
    depth=0;quoted=False;bar=False;i=start
    while i<len(t):
        c=t[i]
        if quoted:
            if c=='"':
                if i+1<len(t) and t[i+1]=='"':i+=2;continue
                quoted=False
        elif bar:
            if c=='|':bar=False
        elif c=='"':quoted=True
        elif c=='|':bar=True
        elif c=='(':
            depth+=1
        elif c==')':
            depth-=1
            if depth==0:return i+1
        i+=1
    raise ValueError("UNBALANCED_OLD_GRAMMAR")

def convert(old):
    forms=top_level_forms(old)
    synths=[f for f in forms if get_cmd(f[2])=="synth-fun"]
    assert len(synths)==1,"EXACTLY_ONE_ORIGINAL_SYNTH_FUN_REQUIRED"
    start,end,orig=synths[0]
    head=re.match(r"^\(\s*synth-fun\s+([^\s()]+)\s+",orig)
    assert head,"SYNTH_NAME_MISSING"
    args_start=head.end()
    assert orig[args_start]=='('
    args_end=span(orig,args_start)
    # These four original tasks' typed result sort is String (not guessed).
    m=re.match(r"\s+String\s+",orig[args_end:])
    assert m,"NOT_ORIGINAL_STRING_FUNCTION"
    gr_start=args_end+m.end()
    assert orig[gr_start]=='('
    gr_end=span(orig,gr_start)
    assert orig[gr_end:].strip()==')',"SOURCE_SYNTH_TRAILING_TOKENS"
    old_grammar=orig[gr_start:gr_end]
    rule_forms=[r[2] for r in top_level_forms(old_grammar[1:-1])]
    assert 2<=len(rule_forms)<=8,"ORIGINAL_GRAMMAR_NT_COUNT"
    extracted=[]
    for rule in rule_forms:
        q=re.fullmatch(r"\(\s*([^\s()]+)\s+([^\s()]+)\s+(\(.*\))\s*\)",rule,re.S)
        if q is None:raise ValueError("NOT_OLD_3FIELD_GRAMMAR_RULE")
        extracted.append((q.group(1),q.group(2),q.group(3)))
    assert len({a for a,_,_ in extracted})==len(extracted),"DUPLICATE_NONTERMINAL"
    typed='('+' '.join('('+a+' '+b+')' for a,b,_ in extracted)+')'
    productions='('+' '.join('('+a+' '+expr[1:-1]+')' for a,b,expr in extracted)+')'
    # Lossless production extraction+reconstruction, independent of whitespace.
    decls=top_level_forms(typed[1:-1])
    bodies=top_level_forms(productions[1:-1])
    assert len(decls)==len(bodies)==len(extracted)
    for src,d,b in zip(extracted,decls,bodies):
        assert d[2].strip()=='('+src[0]+' '+src[1]+')'
        assert re.sub(r"\s+","",b[2])==re.sub(r"\s+","",'('+src[0]+' '+src[2][1:-1]+')')
    converted=orig[:gr_start]+typed+"\n"+productions+orig[gr_end:]
    output=old[:start]+converted+old[end:]
    original=[(get_cmd(f[2]),f[2]) for f in forms if get_cmd(f[2])!="synth-fun"]
    new=[(get_cmd(f[2]),f[2]) for f in top_level_forms(output) if get_cmd(f[2])!="synth-fun"]
    assert original==new,"OTHER_ORIGINAL_FORMS_CHANGED"
    assert len([a for a,b in new if a=="constraint"])>0
    assert orig[:gr_start]==converted[:gr_start]
    return output,{"original_synth_name":head.group(1),"original_nonterminal_count":len(extracted),
        "original_grammar_rule_names":[a for a,_,_ in extracted],
        "original_production_texts_sha256":[sha256(expr.encode()) for _,_,expr in extracted],
        "every_original_constraint_form_identical":True,
        "all_source_forms_other_than_synth_identical":True,
        "source_synth_signature_unchanged":True,
        "source_grammar_converted_into_two_lists":True}

def main():
    assert subprocess.check_output(["git","-C",str(ROOT),"rev-parse","HEAD"],text=True).strip()==PIN
    assert subprocess.check_output(["cvc5","--version"],text=True).splitlines()[0].startswith("cvc5 1.4.2 ")
    raw=(FIRST/"NEUMANN_G1_EXTERNAL_NEW16_FOUR_TRACKS_CVC5_FIRST.json").read_bytes()
    assert sha256(raw)==FIRST_SHA
    frozen=json.loads(raw)
    assert [r["original"] for r in frozen["rows"][12:16]]==list(FILES)
    OUT.mkdir(exist_ok=True)
    rows=[]
    for idx,path in enumerate(FILES,start=12):
        original=(ROOT/path).read_bytes()
        assert sha256(original)==frozen["rows"][idx]["source_sha256"]
        assert frozen["rows"][idx]["status"]=="HOLD_NATIVE_EXCEPTION_OR_UNSUPPORTED"
        entry={"index":idx,"source":path,"exact_original_sha256":sha256(original),
               "original_FIRST_status_unchanged":frozen["rows"][idx]["status"],
               "candidate_independent_full_original_semantics":"NOT_YET_RUN",
               "postfirst":True}
        try:
            converted,meta=convert(original.decode("utf8"))
            entry.update(meta)
            dst=OUT/(f"{idx:02d}_only_grammar_syntax_reformatted.sygus2")
            dst.write_text(converted)
            entry["converted_source_sha256"]=sha256(dst.read_bytes())
            stdout,stderr,cost=run_solver(dst)
            (OUT/(f"{idx:02d}_native.stdout")).write_text(stdout)
            (OUT/(f"{idx:02d}_native.stderr")).write_text(stderr)
            entry["native_cost"]=cost
            entry["returned_function_count"]=len(re.findall(r"\(\s*define-fun\b",stdout))
            if cost["forced"] or cost["returncode"] in (-24,-9,-6):
                entry["new_status"]="ADAPTER_SOLVER_BUDGET_HOLD"
            elif cost["returncode"]!=0 or re.search(r"\(error|parse error|unsupported|exception",stdout+"\n"+stderr,re.I):
                entry["new_status"]="ADAPTER_NATIVE_FORMAT_OR_UNSUPPORTED_HOLD"
            elif entry["returned_function_count"]:
                entry["new_status"]="ADAPTER_PROGRAM_RETURNED_UNVERIFIED"
            elif "infeasible" in stdout.lower():
                entry["new_status"]="ADAPTER_INFEASIBLE_CLAIM_UNVERIFIED"
            else:entry["new_status"]="ADAPTER_NATIVE_NO_PROGRAM_HOLD"
        except Exception as e:
            entry["new_status"]="ADAPTER_SOURCE_TRANSFORM_HOLD"
            entry["error"]=type(e).__name__+":"+str(e)[:200]
        rows.append(entry)
        print("EXTERNAL_STRING4_ADAPTER",idx,entry["new_status"],flush=True)
    report={
       "purpose":"POSTFIRST_SOURCE_PRESERVING_ORIGINAL_SYGUS1_GRAMMAR_FORMAT_REPAIR",
       "source_pin":PIN,"first_original_json_sha256":FIRST_SHA,
       "original_four_source_paths":list(FILES),
       "native_binary":"CVC5 1.4.2","task_denominator":4,
       "status_count":dict(collections.Counter(x["new_status"] for x in rows)),
       "original_FIRST_four_parser_errors_preserved":True,
       "not_model_learning":True,"G1":"HOLD","global_Q1_Q7":"OPEN","G2":"NOT_RUN",
       "rows":rows}
    p=OUT/"ORIGINAL_SLIA4_POSTFIRST_DIALECT_FORMAT_REPAIR.json"
    p.write_text(json.dumps(report,indent=2,sort_keys=True))
    print("FORMAT_REPAIR_REPORT_SHA256",sha256(p.read_bytes()))
    print("FORMAT_REPAIR_COUNTS",json.dumps(report["status_count"],sort_keys=True))
if __name__=="__main__":main()
