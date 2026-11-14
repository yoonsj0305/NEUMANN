#!/usr/bin/env python3
"""POST-FIRST exactly ONE source-language normalization for original Euphony.

Convert an old one-list SyGuS grammar into two-block nonterminal-list and
production-list, without changing any production or authored PBE constraint.
All output still UNVERIFIED until independent whole-original Z3 proof.
"""
import collections,json,pathlib,re,subprocess,sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from sgi_first_classical_original import top_level_forms,get_cmd,sha256
from sygus_official_multifamily_classical_first_20261027 import run_solver
from sygus_external_four_new_tracks16_first_20261028 import PIN,FIXED

FIRST_SHA="7acee7938ea2b8d18db2dd38058de36f7abdcf5116fbd703f6fce048b3a4418c"
ROOT=pathlib.Path("official_repo")
FIRST=pathlib.Path("external_fourtrack16_frozen_first")
OUT=pathlib.Path("external_euphony_four_normalized_postfirst")
FIRST_FILE="NEUMANN_G1_EXTERNAL_NEW16_FOUR_TRACKS_CVC5_FIRST.json"

def normalize_one_source(raw):
    original=raw.decode("utf8")
    fs=[(get_cmd(x[2]),x[2]) for x in top_level_forms(original)]
    syn=[f for command,f in fs if command=="synth-fun"]
    assert len(syn)==1,"NOT_ONE_SYNTHESIS_GRAMMAR"
    f=syn[0]
    m=re.match(r"^\(\s*synth-fun\s+f\s+\(\(_arg_0\s+String\)\)\s+(String|Int)\s+",f)
    assert m,"UNEXPECTED_SYNTHESIZED_FUNCTION_HEADER"
    tail=f[m.end():].strip()
    assert tail.startswith("(") and tail.endswith(")"),"NO_SINGLE_GRAMMAR_BLOCK"
    block=tail[:-1].strip()
    assert block.startswith("(") and block.endswith(")"),"GRAMMAR_UNBALANCED"
    rules=[part[2] for part in top_level_forms(block[1:-1])]
    assert len(rules)==4,("NONTERMINAL_COUNT_CHANGED",len(rules))
    nonterm=[]
    for rule in rules:
        matcher=re.match(r"^\(\s*([^\s()]+)\s+(String|Int|Bool)\s+(\()",rule,re.S)
        assert matcher,("NONTERM_RULE_HEADER",rule[:100])
        nonterm.append((matcher.group(1),matcher.group(2)))
    assert [x[0] for x in nonterm]==["Start","ntString","ntInt","ntBool"],nonterm
    assert nonterm[0][1]==m.group(1)
    declared="("+" ".join(f"({name} {sort})" for name,sort in nonterm)+")"
    modern=f[:m.end()]+declared+"\n "+block+")"
    result=original.replace(f,modern,1)
    assert result!=original
    nfs=[(get_cmd(x[2]),x[2]) for x in top_level_forms(result)]
    assert len(fs)==len(nfs)
    assert [f for c,f in fs if c=="constraint"]==[f for c,f in nfs if c=="constraint"]
    assert [f for c,f in fs if c!="synth-fun"]==[f for c,f in nfs if c!="synth-fun"]
    assert [p[2] for p in top_level_forms(block[1:-1])]==rules
    assert modern.endswith(block+")"),"PRODUCTIONS_MUST_BE_VERBATIM"
    return result.encode(),nonterm,sha256(block.encode()),sum(c=="constraint" for c,_ in fs)

def main():
    assert subprocess.check_output(
        ["git","-C",str(ROOT),"rev-parse","HEAD"],text=True).strip()==PIN
    assert subprocess.check_output(["cvc5","--version"],text=True).startswith("cvc5 1.4.2 ")
    first=(FIRST/FIRST_FILE).read_bytes()
    assert sha256(first)==FIRST_SHA
    original=json.loads(first)
    assert [r["original"] for r in original["rows"]]==list(FIXED)
    OUT.mkdir(exist_ok=True)
    rows=[]
    for i in (12,13,14,15):
        r=original["rows"][i]
        assert r["index"]==i and r["status"]=="HOLD_NATIVE_EXCEPTION_OR_UNSUPPORTED"
        source=(ROOT/r["original"]).read_bytes()
        assert sha256(source)==r["source_sha256"]
        metadata={"index":i,"original_path":r["original"],
                  "original_file_sha256":sha256(source),
                  "prior_first_status":"HOLD_NATIVE_EXCEPTION_OR_UNSUPPORTED",
                  "grammar_productions_unchanged":False,
                  "original_PBE_constraints_unchanged":False,
                  "new_native_status":"HOLD"}
        try:
            converted,nonterm,grammar_sha,ncons=normalize_one_source(source)
            p=OUT/(f"{i:02d}.syntax_normalized.sl")
            p.write_bytes(converted)
            metadata.update({
                "normalized_source_sha256":sha256(converted),
                "original_grammar_rule_block_sha256":grammar_sha,
                "original_nonterminals":nonterm,
                "original_PBE_constraints":ncons,
                "grammar_productions_unchanged":True,
                "original_PBE_constraints_unchanged":True,
            })
            stdout,stderr,cost=run_solver(p)
            (OUT/(f"{i:02d}.native.stdout")).write_text(stdout)
            (OUT/(f"{i:02d}.native.stderr")).write_text(stderr)
            metadata["native_cost"]=cost
            metadata["native_candidate_count"]=stdout.count("(define-fun")
            if cost["forced"] or cost["returncode"] in (-9,-6,-24):
                metadata["new_native_status"]="C_BUDGET_HOLD"
            elif cost["returncode"]!=0 or "(error " in stdout+stderr:
                metadata["new_native_status"]="HOLD_NATIVE_UNSUPPORTED_OR_FORMAT"
            elif metadata["native_candidate_count"]>0:
                metadata["new_native_status"]="C_POSTFIRST_CANDIDATE_UNVERIFIED"
            elif "infeasible" in stdout.lower():
                metadata["new_native_status"]="HOLD_INFEASIBLE_CLAIM_UNPROVED"
            else:
                metadata["new_native_status"]="HOLD_NATIVE_OTHER"
            metadata["stderr_excerpt"]=stderr[-220:]
        except Exception as e:
            metadata["new_native_status"]="HOLD_NORMALIZER_EXCEPTION"
            metadata["error"]=type(e).__name__+":"+str(e)[:350]
        rows.append(metadata)
        print("EUPHONY_POSTFIRST_NORMALIZATION",i,metadata["new_native_status"],
              metadata.get("stderr_excerpt",""),flush=True)
    res={"status":"POSTFIRST_SOURCE_FORMAT_ONLY_REPAIR",
         "first_exact_original_json_sha256":FIRST_SHA,
         "official_original_commit":PIN,
         "modern_solver":"cvc5 1.4.2",
         "never_a_blind_new_task":True,
         "source_rights":"EXACT_AUTHORED_PBE_EXAMPLES_ONLY",
         "original_first_rewritten":False,
         "total_tasks":4,
         "statuses":dict(collections.Counter(r["new_native_status"] for r in rows)),
         "independent_original_semantics":"NOT_YET_VERIFIED",
         "G1":"HOLD","global_Q1_Q7":"OPEN","G2":"NOT_RUN",
         "rows":rows}
    p=OUT/"G1_EXTERNAL_EUPHONY4_POSTFIRST_SYGUS_GRAMMAR_COMPAT_FIRST.json"
    p.write_text(json.dumps(res,sort_keys=True,indent=2))
    print("EUPHONY_NORMALIZATION_SHA256",sha256(p.read_bytes()))
    print("EUPHONY_NORMALIZATION_COUNTS",json.dumps(res["statuses"],sort_keys=True))
if __name__=="__main__":main()
