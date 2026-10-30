#!/usr/bin/env python3
"""POST-FIRST strict SyGuS1→modern SyGuS2 string grammar compatibility v2.

Explicit permitted grammar changes: original old grammar wrapper→NT sort header,
int.to.str→str.from_int, str.to.int→str.to_int, old -1→(- 1).
NO edits to original constraints, formal parameters, constants or other operators.
NEVER claim independently derived intended output for absent PBE examples.
"""
import collections,json,pathlib,re,subprocess,sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from sgi_first_classical_original import top_level_forms,get_cmd,sha256
from sygus_external4_legacy_slIA_grammar_adapter_20261028 import normalize
from sygus_external_four_new_tracks16_first_20261028 import PIN,FIXED
from sygus_official_multifamily_classical_first_20261027 import run_solver
from sygus_official_diverse12_independent_z3_postfirst_20261028 import independent_grade

ROOT=pathlib.Path("official_repo")
FIRST=pathlib.Path("external_new16_frozen_FIRST")
OUT=pathlib.Path("external_slIA4_semantics_preserving_v2")
FIRST_SHA="7acee7938ea2b8d18db2dd38058de36f7abdcf5116fbd703f6fce048b3a4418c"

def translate(original):
    legacy,previous=normalize(original)
    forms=top_level_forms(legacy)
    orig_forms=top_level_forms(original)
    assert len(forms)==len(orig_forms)
    synth=[f for f in forms if get_cmd(f[2])=="synth-fun"]
    assert len(synth)==1
    old=synth[0][2]
    # No arbitrary text substitution: ONLY exact SMT identifier tokens,
    # excluding string literals (all original source strings checked unchanged).
    text=old
    replacements=(
        (r"(?<![a-zA-Z0-9_])int\.to\.str(?![a-zA-Z0-9_])","str.from_int",1),
        (r"(?<![a-zA-Z0-9_])str\.to\.int(?![a-zA-Z0-9_])","str.to_int",1),
        (r"(?<![a-zA-Z0-9_])-1(?![0-9])","(- 1)",1),
    )
    counts={}
    for pattern,repl,expected in replacements:
        text,count=re.subn(pattern,repl,text)
        if count!=expected:
            raise ValueError("UNEXPECTED_LEGACY_GRAMMAR_TOKEN_COUNT "+repr((pattern,count,expected)))
        counts[repl]=count
    if len(text)==len(old):raise ValueError("NO_MODERNIZATION")
    adapted=legacy[:synth[0][0]]+text+legacy[synth[0][1]:]
    new_forms=top_level_forms(adapted)
    assert len(new_forms)==len(orig_forms)
    # Every original non-synth form must be BYTE-IDENTICAL in both translations.
    src_non=[f[2] for f in orig_forms if get_cmd(f[2])!="synth-fun"]
    dst_non=[f[2] for f in new_forms if get_cmd(f[2])!="synth-fun"]
    assert src_non==dst_non
    # For independent validation prove translating backward produces exactly
    # the first output of old adapter; no unintended grammar substitutions.
    reverse=text.replace("str.from_int","int.to.str").replace(
        "str.to_int","str.to.int").replace("(- 1)","-1")
    assert reverse==old
    return adapted,{
      "original_non_synth_forms_all_byte_identical":True,
      "old_adapter_grammar_only_certificate":previous,
      "new_grammar_changes_exactly":counts,
      "no_original_PBE_example_or_signature_changed":True,
      "reversible_grammar_translation_exact":True,
      "new_synth_sha256":sha256(text.encode()),
    }

def main():
    import z3
    assert subprocess.check_output(["git","-C",str(ROOT),"rev-parse","HEAD"],
           text=True).strip()==PIN
    version=subprocess.check_output(["cvc5","--version"],text=True).splitlines()[0]
    assert version.startswith("cvc5 1.4.2 ")
    fb=(FIRST/"NEUMANN_G1_EXTERNAL_NEW16_FOUR_TRACKS_CVC5_FIRST.json").read_bytes()
    assert sha256(fb)==FIRST_SHA
    frozen=json.loads(fb)
    assert len(frozen["rows"])==16
    assert tuple(r["original"] for r in frozen["rows"])==FIXED
    OUT.mkdir(exist_ok=True)
    rows=[]
    for i in range(12,16):
        old=frozen["rows"][i]
        original_b=(ROOT/old["original"]).read_bytes()
        assert sha256(original_b)==old["source_sha256"]
        record={"index":i,"original":old["original"],"original_source_sha256":old["source_sha256"],
          "original_native_first_status":old["status"],"frozen_original_first_sha256":FIRST_SHA,
          "status":"HOLD","postfirst_translation_only":True}
        try:
            modern,proof=translate(original_b.decode("utf8"))
            record.update(proof)
            fn=OUT/(f"{i:02d}_SYGUS2_OPERATORS_AND_GRAMMAR.sl")
            fn.write_text(modern)
            record["adapted_source_sha256"]=sha256(fn.read_bytes())
            stdout,stderr,cost=run_solver(fn)
            (OUT/(f"{i:02d}.stdout")).write_text(stdout)
            (OUT/(f"{i:02d}.stderr")).write_text(stderr)
            record["solver_cost"]=cost
            record["stdout_sha256"]=sha256(stdout.encode())
            record["stderr_excerpt"]=stderr[-500:]
            record["native_define_fun_count"]=stdout.count("(define-fun")
            if cost["forced"]:
                record["status"]="C_POSTFIRST_BUDGET_HOLD"
            elif cost["returncode"]!=0 or record["native_define_fun_count"]==0:
                record["status"]="HOLD_NATIVE_NO_CANDIDATE_OR_PARSE"
            else:
                # Original source: independently check ALL author-provided examples
                # even though source grammar uses legacy spellings.
                verified=independent_grade({},original_b.decode("utf8"),stdout)
                record["independent_source_Z3_grade"]=verified
                record["status"]=(
                  "PROVED_ALL_ORIGINAL_PBE_EXAMPLES_POSTFIRST"
                  if verified["grade"]=="VERIFIED_FULL_ORIGINAL_SEMANTIC_CONSTRAINTS"
                  else "HOLD_Z3_OR_INCORRECT_CANDIDATE")
        except Exception as e:
            record["status"]="HOLD_EXECUTOR_OR_GRAMMAR_PROOF"
            record["error"]=type(e).__name__+":"+str(e)[:380]
        rows.append(record)
        print("SLIA_COMPAT_V2",i,record["status"],record.get("stderr_excerpt","")[:180],flush=True)
    res={
      "science":"POSTFIRST_ONLY_LEGACY_STRING_SYGUS_COMPATIBILITY",
      "source_original_git":PIN,"original_first_16_SHA256":FIRST_SHA,
      "native_solver_version":version,
      "new_operator_spellings":"int.to.str→str.from_int; str.to.int→str.to_int; -1→(- 1)",
      "all_four_original_source_constraints_byte_identical":all(
          r.get("original_non_synth_forms_all_byte_identical",False) for r in rows),
      "all_four_backward_grammar_reversibility_exact":all(
          r.get("reversible_grammar_translation_exact",False) for r in rows),
      "original_label_oracle_for_arbitrary_input":False,
      "counts":dict(collections.Counter(r["status"] for r in rows)),
      "new_neural_model":False,"G1":"HOLD","Q1_Q7":"OPEN","G2":"NOT_RUN",
      "rows":rows}
    p=OUT/"EXTERNAL4_SLIA_MODERN_OPERATOR_ONLY_COMPATIBILITY_POSTFIRST.json"
    p.write_text(json.dumps(res,sort_keys=True,indent=2))
    print("SLIA_COMPAT_V2_SHA256",sha256(p.read_bytes()))
    print("SLIA_COMPAT_V2_SUMMARY",json.dumps(res["counts"],sort_keys=True))
if __name__=="__main__":main()
