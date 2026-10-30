#!/usr/bin/env python3
"""Post-first STRICT semantics-preserving legacy SyGuS1 grammar → SyGuS2.

Four originally parser-rejected external SLIA benchmark sources. Add ONLY the
nonterminal declaration wrapper demanded by SyGuS2. Every original grammar
production body, source constraint, operator, constant and function binder is
byte-identical. Actual modern native CVC5 1.4.2 rerun on NORMALIZED ORIGINAL
as a separate postfirst result; independently verify only original PBE examples.
"""
import collections,json,pathlib,re,subprocess,sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from sgi_first_classical_original import top_level_forms,get_cmd,sha256
from sygus_external_four_new_tracks16_first_20261028 import PIN,FIXED
from sygus_official_multifamily_classical_first_20261027 import run_solver
from sygus_official_diverse12_independent_z3_postfirst_20261028 import independent_grade

FIRST_SHA="7acee7938ea2b8d18db2dd38058de36f7abdcf5116fbd703f6fce048b3a4418c"
ROOT=pathlib.Path("official_repo")
FIRST=pathlib.Path("external_new16_frozen_FIRST")
OUT=pathlib.Path("external_slIA4_syntax_normalized")

def normalize(original):
    forms=top_level_forms(original)
    synth=[f for f in forms if get_cmd(f[2])=="synth-fun"]
    cons=[f for f in forms if get_cmd(f[2])=="constraint"]
    assert len(synth)==1 and len(cons)>0
    first=synth[0]
    body=first[2]
    # Extract balanced top-level child groups of synth-fun f BINDERS SORT GRAMMAR.
    children=top_level_forms(body[1:-1])
    assert len(children)==2,("EXPECTED_BINDERS_AND_OLD_GRAMMAR_ONLY",len(children))
    oldgrammar=children[-1][2]
    original_rules=[f[2] for f in top_level_forms(oldgrammar[1:-1])]
    assert 3<=len(original_rules)<=10
    headers=[]
    names=set()
    for rule in original_rules:
        m=re.match(r"^\(\s*([A-Za-z_][A-Za-z0-9_]*)\s+([A-Za-z_][A-Za-z0-9_]*)\s+\(",rule)
        assert m,("UNKNOWN_LEGACY_RULE",rule[:120])
        name,sort=m.groups()
        assert sort in ("String","Int","Bool")
        assert name not in names
        names.add(name)
        headers.append("("+name+" "+sort+")")
    assert headers[0].startswith("(Start ")
    newgrammar="\n  ("+" ".join(headers)+")\n  "+oldgrammar+"\n"
    # Replace ONLY the final source grammar group text, never substitutions
    # inside original constraints or productions.
    oldstart=first[0]+1+children[-1][0]
    oldend=first[0]+1+children[-1][1]
    changed=original[:oldstart]+newgrammar+original[oldend:]
    new_forms=top_level_forms(changed)
    original_without_synth=[f[2] for f in forms if f is not first] # tuple identity not relied on
    assert len(forms)==len(new_forms)
    assert [f[2] for f in forms if get_cmd(f[2])!="synth-fun"]==[
        f[2] for f in new_forms if get_cmd(f[2])!="synth-fun"], "ORIGINAL_CONSTRAINT_CHANGED"
    norm_synth=[f for f in new_forms if get_cmd(f[2])=="synth-fun"]
    assert len(norm_synth)==1
    nc=top_level_forms(norm_synth[0][2][1:-1])
    assert len(nc)==3 # binders, grammar header, grammar rules are ADJACENT
    newheaders=[f[2] for f in top_level_forms(nc[1][2][1:-1])]
    newrules=[f[2] for f in top_level_forms(nc[2][2][1:-1])]
    assert newheaders==headers
    assert newrules==original_rules
    return changed,{
      "original_production_count":len(original_rules),
      "original_production_sha256":sha256("\n".join(original_rules).encode()),
      "new_production_sha256":sha256("\n".join(newrules).encode()),
      "production_bytewise_equal":True,
      "source_constraint_bytewise_equal":True,
      "only_new_nonterminal_header_sorts":headers,
    }

def main():
    import z3
    assert subprocess.check_output(["git","-C",str(ROOT),"rev-parse","HEAD"],text=True).strip()==PIN
    version=subprocess.check_output(["cvc5","--version"],text=True).splitlines()[0]
    assert version.startswith("cvc5 1.4.2 ")
    first_bytes=(FIRST/"NEUMANN_G1_EXTERNAL_NEW16_FOUR_TRACKS_CVC5_FIRST.json").read_bytes()
    assert sha256(first_bytes)==FIRST_SHA
    data=json.loads(first_bytes)
    assert tuple(x["original"] for x in data["rows"])==FIXED
    OUT.mkdir(exist_ok=True)
    cases=[]
    for i in range(12,16):
        row=data["rows"][i]
        assert row["status"]=="HOLD_NATIVE_EXCEPTION_OR_UNSUPPORTED"
        original_b=(ROOT/row["original"]).read_bytes()
        assert sha256(original_b)==row["source_sha256"]
        case={"index":i,"original":row["original"],
              "original_source_sha256":row["source_sha256"],
              "first_native_status":row["status"],
              "native_output_original_unmodified":True,
              "new_postfirst_syntactic_adaptation":True,
              "result":"HOLD"}
        try:
            adapted,cert=normalize(original_b.decode("utf8"))
            case.update(cert)
            infile=OUT/(f"{i:02d}_SYGUS2_GRAMMAR_ONLY_ADAPTER.sl")
            infile.write_text(adapted)
            case["adapted_source_sha256"]=sha256(infile.read_bytes())
            stdout,stderr,cost=run_solver(infile)
            (OUT/(f"{i:02d}_native.stdout")).write_text(stdout)
            (OUT/(f"{i:02d}_native.stderr")).write_text(stderr)
            case["native_cost"]=cost
            case["native_stderr_excerpt"]=stderr[-340:]
            case["native_define_fun_count"]=stdout.count("(define-fun")
            if cost["forced"]:
                case["result"]="HOLD_NATIVE_BUDGET_AFTER_NORMALIZATION"
            elif cost["returncode"]!=0 or case["native_define_fun_count"]==0:
                case["result"]="HOLD_NATIVE_SYNTAX_OR_INDETERMINATE_AFTER_NORMALIZATION"
            else:
                # Actual author PBE constraints unchanged. Z3 independently
                # checks each. No proof of intended unseen target outputs.
                grade=independent_grade({},original_b.decode(),stdout)
                case["independent_original_examples"]=grade
                case["result"]=(
                    "POSTFIRST_NATIVE_PROGRAM_PROVED_ALL_AUTHORED_EXAMPLES"
                    if grade["grade"]=="VERIFIED_FULL_ORIGINAL_SEMANTIC_CONSTRAINTS"
                    else "HOLD_NATIVE_PROGRAM_NOT_INDEPENDENTLY_VERIFIED")
        except Exception as e:
            case["result"]="HOLD_ADAPTER_OR_CHECKER_FAILURE"
            case["error"]=type(e).__name__+":"+str(e)[:360]
        cases.append(case)
        print("SLIA4_GRAMMAR_ONLY",i,case["result"],
              case.get("native_stderr_excerpt","")[:150],flush=True)
    out={
      "experiment":"POSTFIRST_LEGACY_SOURCE_GRAMMAR_WRAPPER_TO_SYGUS2_ONLY",
      "original_pinned_git":PIN,"original_unchanged_first_sha256":FIRST_SHA,
      "native_version":version,"case_count":4,
      "results":dict(collections.Counter(c["result"] for c in cases)),
      "no_operator_or_source_constraint_change":all(
          c.get("production_bytewise_equal") and c.get("source_constraint_bytewise_equal")
          for c in cases),
      "semantic_scope":"Only original author supplied examples, no ideal unseen target oracle",
      "new_neural_ownweight_model":False,"G1":"HOLD","Q1_Q7":"OPEN","G2":"NOT_RUN",
      "cases":cases}
    p=OUT/"EXTERNAL4_SLIA_LEGACY_GRAMMAR_ONLY_POSTFIRST_RESULTS.json"
    p.write_text(json.dumps(out,sort_keys=True,indent=2))
    print("SLIA4_GRAMMAR_ONLY_SHA256",sha256(p.read_bytes()))
    print("SLIA4_GRAMMAR_ONLY_SUMMARY",json.dumps(out["results"],sort_keys=True))
if __name__=="__main__":main()
