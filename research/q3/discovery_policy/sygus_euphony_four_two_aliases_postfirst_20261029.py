#!/usr/bin/env python3
"""POSTFIRST second syntax repair, EXACTLY two SMT-LIB 2.5 to 2.6 operator
alias heads, on top of preserved grammar-only normalizer. NOT blind C baseline.
"""
import collections,json,pathlib,re,subprocess,sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from sgi_first_classical_original import top_level_forms,get_cmd,sha256
from sygus_official_multifamily_classical_first_20261027 import run_solver
from sygus_euphony_four_grammar_normalize_postfirst_20261029 import normalize_one_source
from sygus_external_four_new_tracks16_first_20261028 import PIN,FIXED

ROOT=pathlib.Path("official_repo")
OUT=pathlib.Path("external_euphony_four_2alias_postfirst")
FIRST=pathlib.Path("external_fourtrack16_frozen_first")
FIRST_SHA="7acee7938ea2b8d18db2dd38058de36f7abdcf5116fbd703f6fce048b3a4418c"
MAPPING=(("(int.to.str ","(str.from_int "),("(str.to.int ","(str.to_int "))

def main():
    assert subprocess.check_output(["git","-C",str(ROOT),"rev-parse","HEAD"],text=True).strip()==PIN
    assert subprocess.check_output(["cvc5","--version"],text=True).startswith("cvc5 1.4.2 ")
    first_file=FIRST/"NEUMANN_G1_EXTERNAL_NEW16_FOUR_TRACKS_CVC5_FIRST.json"
    first_raw=first_file.read_bytes()
    assert sha256(first_raw)==FIRST_SHA
    frozen=json.loads(first_raw)
    assert [r["original"] for r in frozen["rows"]]==list(FIXED)
    OUT.mkdir(exist_ok=True)
    rows=[]
    for i in (12,13,14,15):
        originalrow=frozen["rows"][i]
        original=(ROOT/originalrow["original"]).read_bytes()
        assert sha256(original)==originalrow["source_sha256"]
        entry={"index":i,"original_path":originalrow["original"],
            "original_sha256":sha256(original),"postfirst_stage":2,
            "native_original_first_status":originalrow["status"],
            "no_changes_to_original_first":True,"status":"HOLD"}
        try:
            grammar_first,nonterm,raw_grammar_sha,ncons=normalize_one_source(original)
            data=grammar_first.decode("utf8")
            counts=[]
            for old,new in MAPPING:
                n=data.count(old)
                assert n>=1,("LEGACY_ALIAS_NOT_PRESENT",old)
                data=data.replace(old,new)
                counts.append(n)
            assert all(old not in data for old,_ in MAPPING)
            rewritten=data.encode()
            ori=[x[2] for x in top_level_forms(original.decode()) if get_cmd(x[2])=="constraint"]
            final=[x[2] for x in top_level_forms(data) if get_cmd(x[2])=="constraint"]
            assert ori==final and len(final)==ncons
            # Existing original source grammar productions only have two alias
            # op-head replacements. All other characters kept unchanged.
            (OUT/(f"{i:02d}.modern_operator_aliases.sl")).write_bytes(rewritten)
            stdout,stderr,cost=run_solver(OUT/(f"{i:02d}.modern_operator_aliases.sl"))
            (OUT/(f"{i:02d}.native.stdout")).write_text(stdout)
            (OUT/(f"{i:02d}.native.stderr")).write_text(stderr)
            entry.update({
                "normalized_source_sha256":sha256(rewritten),
                "grammar_only_intermediate_sha256":sha256(grammar_first),
                "original_grammar_rules_sha256":raw_grammar_sha,
                "only_new_mapping":list(MAPPING),
                "replacement_count":counts,
                "unchanged_authored_source_constraints":True,
                "native_cost":cost,
                "native_returned_programs":stdout.count("(define-fun"),
                "stderr_excerpt":stderr[-250:]})
            if cost["forced"] or cost["returncode"] in (-9,-6,-24):
                entry["status"]="C_POSTFIRST_BUDGET_HOLD"
            elif cost["returncode"]!=0 or "(error " in stdout+stderr:
                entry["status"]="HOLD_PARSER_OR_UNSUPPORTED"
            elif entry["native_returned_programs"]>0:
                entry["status"]="C_POSTFIRST_PROGRAM_UNVERIFIED"
            elif "infeasible" in stdout.lower():
                entry["status"]="HOLD_INFEASIBLE_CLAIM_UNPROVED"
            else:
                entry["status"]="HOLD_NO_PROGRAM"
        except Exception as e:
            entry["status"]="HOLD_TRANSLATOR_EXCEPTION"
            entry["error"]=type(e).__name__+":"+str(e)[:240]
        rows.append(entry)
        print("EUPHONY_TWO_ALIASES",i,entry["status"],entry.get("stderr_excerpt",""),flush=True)
    receipt={
       "stage":"POSTFIRST_SEMANTICS_EQUIVALENT_SMTLIB26_OPERATOR_RENAME",
       "source_repository_git":PIN,"first_original_sha256":FIRST_SHA,
       "four_original_entries":4,"original_problems_not_changed":True,
       "source_original_examples_unchanged":all(r.get("unchanged_authored_source_constraints",False) for r in rows),
       "summary":dict(collections.Counter(x["status"] for x in rows)),
       "C_programs_independently_verified":"NOT_RUN",
       "global_Q1_Q7":"OPEN","G1":"HOLD","G2":"NOT_RUN","rows":rows}
    f=OUT/"G1_EUPHONY4_POSTFIRST_ALIAS_MODERN_CVC5_SOURCE_REPAIR.json"
    f.write_text(json.dumps(receipt,indent=2,sort_keys=True))
    print("EUPHONY2_SHA256",sha256(f.read_bytes()))
    print("EUPHONY2_COUNTS",json.dumps(receipt["summary"],sort_keys=True))
if __name__=="__main__":main()
