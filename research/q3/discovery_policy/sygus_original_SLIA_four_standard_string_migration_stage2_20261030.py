#!/usr/bin/env python3
"""Stage2 AFTER published failure of format-only legacy four String grammars.

Translate only known old SMT-LIB 2.5/old SyGuS surface syntax, pin prior
negative receipts and original source specs, and separately measure native
1.4.2 program synthesis and independent actual original PBE examples.
"""
import collections,json,pathlib,re,subprocess,sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from sgi_first_classical_original import sha256
from sygus_external_four_new_tracks16_first_20261028 import PIN,FIXED
from sygus_original_SLIA_four_legacy_syntax_adapt_postfirst_20261030 import parse_all,smt,convert
from sygus_official_multifamily_classical_first_20261027 import run_solver
from sygus_official_diverse12_independent_z3_postfirst_20261028 import independent_grade

FIRST=pathlib.Path("external_new16_sealed_FIRST")
STAGE1=pathlib.Path("external_slia_stage1_sealed")
ROOT=pathlib.Path("official_repo")
OUT=pathlib.Path("external_SLIA4_legacy_string_standard_stage2")
F1="NEUMANN_G1_EXTERNAL_NEW16_FOUR_TRACKS_CVC5_FIRST.json"
S1="SLIA_FOUR_ORIGINAL_LEGACY_GRAMMAR_FORMAT_ONLY_NATIVE_CVC5.json"
SHA1="7acee7938ea2b8d18db2dd38058de36f7abdcf5116fbd703f6fce048b3a4418c"
SHA2="1f36ad87c1091d54a09b1b2aa8b21739e96e368f04f2098d5dcd03a0765c0344"
RENAMES={"int.to.str":"str.from_int","str.to.int":"str.to_int"}

def migrate(ast):
    if isinstance(ast,str):
        return RENAMES.get(ast,["-","1"] if ast=="-1" else ast)
    if isinstance(ast,list):return [migrate(v) for v in ast]
    raise TypeError(type(ast))

def main():
    import z3
    assert subprocess.check_output(["git","-C",str(ROOT),"rev-parse","HEAD"],text=True).strip()==PIN
    assert subprocess.check_output(["cvc5","--version"],text=True).splitlines()[0].startswith("cvc5 1.4.2 ")
    b1=(FIRST/F1).read_bytes();b2=(STAGE1/S1).read_bytes()
    assert sha256(b1)==SHA1 and sha256(b2)==SHA2
    first=json.loads(b1);prior=json.loads(b2)
    assert tuple(x["original"] for x in first["rows"])==FIXED
    assert len(prior["rows"])==4 and all(
         x["native_result"]=="CVC5_ADAPTED_ERROR" for x in prior["rows"])
    OUT.mkdir(exist_ok=True)
    records=[]
    for i in range(12,16):
        ref=first["rows"][i]
        raw=(ROOT/ref["original"]).read_bytes()
        assert sha256(raw)==ref["source_sha256"]
        converted,old_s,modern_s=convert(raw)
        modern=parse_all(converted)
        sy=[x for x in modern if x[0]=="synth-fun"]
        assert len(sy)==1 and sy[0]==modern_s
        original_productions=modern_s[5]
        migrated_productions=migrate(original_productions)
        new_s=modern_s[:5]+[migrated_productions]
        assert new_s[5]==migrate(original_productions)
        assert new_s[:5]==modern_s[:5]
        result=[new_s if f is sy[0] else f for f in modern]
        assert [k for k in result if k[0]!="synth-fun"]==[
               k for k in modern if k[0]!="synth-fun"]
        assert len(new_s[5])==4
        text="\n".join(smt(x) for x in result)+"\n"
        assert parse_all(text)==result
        path=OUT/(f"{i:02d}_two_list_standard_strings_full_original.sygus")
        path.write_text(text)
        out,err,cost=run_solver(path)
        (OUT/(f"{i:02d}_native.stdout")).write_text(out)
        (OUT/(f"{i:02d}_native.stderr")).write_text(err)
        if cost["forced"] or cost["returncode"] in (-6,-9,-24):
            status="FORMAT_PLUS_RENAMING_C_BUDGET_HOLD"
        elif cost["returncode"]!=0:
            status="FORMAT_PLUS_RENAMING_C_ERROR"
        elif "(define-fun" in out:
            status="FORMAT_PLUS_RENAMING_C_CANDIDATE_UNVERIFIED"
        else:status="FORMAT_PLUS_RENAMING_C_OTHER"
        proof="NOT_APPLICABLE"
        prooferr=None
        if status=="FORMAT_PLUS_RENAMING_C_CANDIDATE_UNVERIFIED":
            try:
                original="\n".join(l for l in raw.decode().splitlines()
                    if not l.lstrip().startswith(";"))
                grade=independent_grade(ref,original,out)
                proof=grade["grade"]
            except Exception as e:
                proof="HOLD_CHECKER_ERROR"
                prooferr=type(e).__name__+":"+str(e)[:300]
        record={
            "index":i,"original":ref["original"],"source_sha256":sha256(raw),
            "adapted_sha256":sha256(text.encode()),
            "original_initial_first_parser_ERROR_unchanged":True,
            "stage1_format_only_parser_ERROR_unchanged":True,
            "only_standard_legacy_string_operator_and_negative_literal_syntax_migrated":True,
            "original_example_and_other_source_forms_AST_unchanged":True,
            "all_original_nonterminal_typed_heads_unmodified":True,
            "status":status,"original_candidate_semantics_independent_Z3":proof,
            "proof_error":prooferr,
            "native_cost":cost,"stderr_excerpt":err[-350:]
        }
        records.append(record)
        print("POSTFIRST_STRING_STAGE2",i,status,proof,flush=True)
    report={
        "study":"AFTER_STAGE1_LEGACY_FORMAT_REJECTED__STANDARD_STRING_OPERATOR_RENAMING",
        "prior_original_first_SHA256":SHA1,
        "prior_four_format_only_STAGE1_SHA256":SHA2,
        "source_pinned_git":PIN,
        "n_original_four":4,
        "status_counts":dict(collections.Counter(x["status"] for x in records)),
        "n_semantically_verified":sum(x["original_candidate_semantics_independent_Z3"]==
               "VERIFIED_FULL_ORIGINAL_SEMANTIC_CONSTRAINTS" for x in records),
        "no_prospective_neural_generalization_claim":True,
        "source_target_oracle_rights":"LISTED_EXAMPLES_ONLY",
        "G1":"HOLD","global_Q1_Q7":"OPEN","G2":"NOT_RUN",
        "rows":records}
    p=OUT/"SLIA4_ORIGINAL_STANDARD_STRING_SYNTAX_STAGE2_ACTUAL.json"
    p.write_text(json.dumps(report,sort_keys=True,indent=2))
    print("SLIA_STAGE2_RESULT_SHA256",sha256(p.read_bytes()))
    print("SLIA_STAGE2_COUNTS",json.dumps(report["status_counts"],sort_keys=True))
if __name__=="__main__":main()
