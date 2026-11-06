"""Independent original specialist second stage, using OFFICIAL SyGuS-Org 1→2 converter.

The prior specialist attempt on all eight original tasks failed before any
search because old SyGuS1 grammar requires an upfront nonterminal list in
SyGuS2. That byte-locked original diagnosis is immutable. This stage keeps
the original task denominator, grammar meaning, model checkpoint and original
source split fixed; only uses the *official publisher's converter*.

All candidate programs must pass a separate original TRAIN and withheld-LAST
ground cvc5 SMT validity check. No original scoring change or NN retraining.
"""
from __future__ import annotations

import hashlib,json,os,re,subprocess,sys,tempfile,time
from pathlib import Path
from urllib.request import Request,urlopen

from research.g1.postfirst_real_cvc5_specialist import (
    gitblob,sha,prepare_original,professional_solver,ground_verify,
    parse_constraint,top_forms
)

ROOT=Path(__file__).resolve().parents[2]
PRE=ROOT/"docs/experiments/G1_OWNWEIGHT_STRING_AST_EXTERNAL_FIRST_PREREG_2026_11_06.json"
ERR=ROOT/"docs/experiments/G1_EXTERNAL_SYGUS_FIRST_METADATA_SHA_ERRATUM_2026_11_06.json"
CON=ROOT/"docs/experiments/G1_OFFICIAL_SYGUS1_TO_2_CVC5_POSTFIRST_PREREG_2026_11_06.json"
OFFICIAL_TOOLS_SHA="9f5cc084b77ce172a22c646dc54528b639ffb139"


def strict_original_train_examples(prepped:dict)->list[tuple[tuple[str,...],str]]:
    out=[]
    for row in prepped["train_constraints"]:
        parsed=parse_constraint(row)
        if parsed is None:raise ValueError("ORIGINAL_TRAIN_HAS_UNSUPPORTED_CONSTRAINT")
        args,target=parsed
        out.append((tuple(args),target))
    return out


def convert_original_training(original_train:str,tools_root:Path)->dict:
    if not (tools_root/"sygus/bin/convert.py").is_file():
        raise ValueError("OFFICIAL_SYGUS_TOOLS_CHECKOUT_ABSENT")
    begin=time.perf_counter_ns()
    with tempfile.NamedTemporaryFile("w",encoding="utf-8",suffix=".sl") as src:
        src.write(original_train)
        src.flush()
        env=os.environ.copy()
        env["PYTHONPATH"]=str(tools_root)
        proc=subprocess.run(
          [sys.executable,"-m","sygus.bin.convert","-s","1","-t","2",src.name],
          env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
          text=True,timeout=12,check=False
        )
    if proc.returncode!=0:
        return {"ok":False,"status":"OFFICIAL_PUBLISHER_FORMAT_CONVERTER_FAILED",
            "exit":proc.returncode,"stderr_tail":proc.stderr[-600:],
            "wall_ms":round((time.perf_counter_ns()-begin)/1e6,3)}
    converted=proc.stdout
    if "(check-synth)" not in converted or "(synth-fun" not in converted:
        return {"ok":False,"status":"NO_VALID_FORMAT_CONVERSION",
                "stderr_tail":proc.stderr[-500:]}
    return {"ok":True,"status":"SYGUS2_OFFICIAL_CONVERTED",
        "converted":converted,
        "converted_sha256":sha(converted.encode()),
        "converter_wall_ms":round((time.perf_counter_ns()-begin)/1e6,3),
        "converter_stderr_tail":proc.stderr[-400:]}


def canonicalize_legacy_string_builtins(source:str)->tuple[str,dict[str,int]]:
    """Replace ONLY operator tokens, outside strings/comments; keep I/O exact.

    SyGuS-IF 2016 "int.to.str" and "str.to.int" correspond to modern
    SMT-LIB "str.from_int" and "str.to_int". Not adding new operators.
    """
    names={"int.to.str":"str.from_int","str.to.int":"str.to_int"}
    counts={key:0 for key in names}
    out=[]
    i=0
    quote=False
    comment=False
    while i<len(source):
        c=source[i]
        if comment:
            out.append(c)
            if c in "\r\n":comment=False
            i+=1
            continue
        if quote:
            out.append(c)
            if c=='"':
                if i+1<len(source) and source[i+1]=='"':
                    out.append(source[i+1])
                    i+=2
                    continue
                quote=False
            i+=1
            continue
        if c==";":
            comment=True
            out.append(c)
            i+=1
            continue
        if c=='"':
            quote=True
            out.append(c)
            i+=1
            continue
        if c=="(":
            out.append("(")
            i+=1
            while i<len(source) and source[i].isspace():
                out.append(source[i])
                i+=1
            replaced=False
            for old,new in names.items():
                if source.startswith(old,i) and (
                    i+len(old)==len(source) or
                    source[i+len(old)].isspace() or
                    source[i+len(old)]==")"
                ):
                    out.append(new)
                    counts[old]+=1
                    i+=len(old)
                    replaced=True
                    break
            if replaced:continue
            continue
        out.append(c)
        i+=1
    return "".join(out),counts


def verify_exact_train_conservation(original_train:list,converted_source:str)->dict:
    """Same list of ground PBE examples, no hidden test in source."""
    try:
        forms=top_forms(converted_source)
        converted=[]
        for _,_,form in forms:
            if re.match(r"^\(\s*constraint\b",form):
                parsed=parse_constraint(form)
                if parsed is None:return {"pass":False,"error":"UNPARSABLE_CONVERTED_CONSTRAINT"}
                args,target=parsed
                converted.append((tuple(args),target))
        ok=converted==original_train
        return {"pass":ok,"original_train_examples":len(original_train),
            "converted_train_examples":len(converted),
            "error":None if ok else "TRAIN_EXAMPLES_CHANGED_DURING_CONVERSION"}
    except ValueError as e:
        return {"pass":False,"error":str(e)}


def run(tools_root:Path)->dict:
    pre=json.loads(PRE.read_text())
    err=json.loads(ERR.read_text())["actual_source_error"]
    contract=json.loads(CON.read_text())
    operator_contract=json.loads((ROOT/"docs/experiments/G1_CVC5_LEGACY_STRING_OPERATOR_TOKEN_ERRATUM_2026_11_06.json").read_text())
    if operator_contract["exact_source_compatibility_fix"]["tokens"]!={"int.to.str":"str.from_int","str.to.int":"str.to_int"}:
        raise ValueError("UNAUTHORIZED_LEGACY_OPERATOR_MAP")
    if len(pre["external_original"]["tasks"])!=8 or contract["originals"]["original_n"]!=8:
        raise ValueError("ORIGINAL_TARGET_DENOMINATOR_DRIFT")
    # The official repository is cloned with a pinned Git SHA by CI. Never
    # take a floating converter or modify old source grammar manually.
    rev=subprocess.run(["git","-C",str(tools_root),"rev-parse","HEAD"],
        capture_output=True,text=True,timeout=8,check=True).stdout.strip()
    if rev!=OFFICIAL_TOOLS_SHA:
        raise ValueError("OFFICIAL_CONVERTER_VERSION_DRIFT")
    begin=time.perf_counter_ns()
    rows=[]
    corrected=err["correct_original_github_blob_40_hex"]
    for target in pre["external_original"]["tasks"]:
        url="https://raw.githubusercontent.com/"+pre["external_original"]["repo"]+"/"+pre["external_original"]["commit"]+"/"+pre["external_original"]["subdir"]+"/"+target["name"]
        with urlopen(Request(url,headers={"User-Agent":"NEUMANN-real-G1-specialist-official-converter"}),timeout=40) as resp:
            raw=resp.read(50000)
        expected=(corrected if target["name"]==err["file"] else target["git_blob"])
        original_blob=gitblob(raw)
        if len(original_blob)!=40 or original_blob!=expected:
            raise ValueError("EXTERNAL_ORIGINAL_GIT_BLOB_CHANGED_"+target["name"])
        row={"name":target["name"],"original_git_blob":original_blob,
             "original_bytes":len(raw),"source_only_inference":True}
        try:
            prepared=prepare_original(raw)
            originals=strict_original_train_examples(prepared)
        except (UnicodeError,ValueError) as e:
            row.update({"status":"UNSUPPORTED_ORIGINAL_SOURCE",
                        "reason":str(e),"verified_heldout":False})
            rows.append(row)
            continue
        row.update({
          "original_constraints":prepared["original_constraint_count"],
          "original_train_constraints":len(originals),
          "original_source_train_sha256":prepared["train_source_sha256"],
          "withheld_last_constraint_sha256":prepared["heldout_form_sha256"]
        })
        converted=convert_original_training(prepared["train_source"],tools_root)
        if not converted["ok"]:
            row.update({"status":converted["status"],"conversion":converted,
                        "verified_heldout":False})
            rows.append(row)
            continue
        mapped=verify_exact_train_conservation(originals,converted["converted"])
        if not mapped["pass"]:
            row.update({"status":"SYNTAX_CONVERSION_NOT_PROVEN_LOSSLESS",
                 "conversion_audit":mapped,"verified_heldout":False})
            rows.append(row)
            continue
        source=converted.pop("converted")
        source,operator_alias_counts=canonicalize_legacy_string_builtins(source)
        # The publisher converter made the V2 syntax, and this exact,
        # separately registered modern SMT-LIB operator renaming completes
        # the dialect adapter. Both keep all original PBE examples.
        after_alias=verify_exact_train_conservation(originals,source)
        if not after_alias["pass"]:
            row.update({"status":"OPERATOR_RENAME_CHANGED_ORIGINAL_EXAMPLES",
                "source_verified":after_alias,"verified_heldout":False})
            rows.append(row)
            continue
        row["conversion"]={**converted,"original_PBE_examples_preserved":True,
            "legacy_builtins_renamed":operator_alias_counts,
            "converted_plus_alias_sha256":sha(source.encode()),
            "post_alias_original_train_examples_preserved":True}
        specialist=professional_solver(source,12.)
        if specialist["status"]=="CANDIDATE_UNVERIFIED":
            solution=specialist.pop("candidate")
            specialist["independent_check"]=ground_verify(
                solution, prepared["train_constraints"],prepared["heldout_form"],12.
            )
            specialist["verified_heldout"]=(
                specialist["independent_check"]["status"]==
                "CANDIDATE_TRAIN_AND_HELDOUT_VERIFIED"
            )
        else:
            specialist["verified_heldout"]=False
        row.update({"status":"OFFICIAL_FORMAT_CONVERTED_CVC5_ATTEMPTED",
             "specialist":specialist,"verified_heldout":specialist["verified_heldout"]})
        rows.append(row)
    checked=[r for r in rows if r["status"]=="OFFICIAL_FORMAT_CONVERTED_CVC5_ATTEMPTED"]
    supported=[r for r in rows if r["status"]!="UNSUPPORTED_ORIGINAL_SOURCE"]
    stats={
        "original_external_denominator":len(rows),
        "strict_source_conversion_proven":len(checked),
        "source_conversion_errors":len(supported)-len(checked),
        "supported_cvc5_candidates":sum(r["specialist"]["status"]=="CANDIDATE_UNVERIFIED" for r in checked),
        "independently_original_heldout_verified":sum(r["verified_heldout"] for r in rows),
        "official_converter_git_sha":rev,
        "original_training_weights_retrained":False,
        "published_old_grammar_preserved":True,
        "external_correctness_claim":"FINITE_ORIGINAL_HELDOUT_EXAMPLES_ONLY",
        "total_wall_ms":round((time.perf_counter_ns()-begin)/1e6,3),
        "ARC_public_eval_originals_consumed":0
    }
    return {
     "schema":"neumann.g1.cvc5-official-sygus2-postfirst-original-specialist.v1",
     "scientific_status":"POST_FIRST_STRONG_SPECIALIST_RESULTS_RECORDED",
     "global_Q3":"OPEN","global_Q4":"OPEN","global_Q6":"OPEN","global_Q7":"OPEN",
     "no_learned_exclusive_neumann_claim":True,
     "already_opened_originals_not_blind":True,
     "previous_syntax_only_cvc5_attempt_run":42160877103,
     "previous_syntax_only_cvc5_attempt_sha256":"6862e598419ab2d3563f1db9ff442aa5b07d0f6bb1a6e43e43e6d7da6de119e3",
     "student_unchanged_checkpoint_sha256":"ae5e291d525098b05ade6eaaf5be76c5fc432fb20a39306be8b782377e4c1641",
     "stats":stats,"rows":rows
    }


if __name__=="__main__":
    try:
        if len(sys.argv)!=2:
            raise ValueError("USAGE: python -m research.g1.postfirst_official_converter_cvc5 /path/to/SyGuS-Org/tools")
        result=run(Path(sys.argv[1]))
        print(json.dumps(result,indent=2,sort_keys=True))
    except Exception as e:
        print(json.dumps({"scientific_status":"OFFICIAL_CONVERTER_SPECIALIST_INFRASTRUCTURE_FAIL_CLOSED",
           "error":type(e).__name__,"message":str(e)[:500]},indent=2))
        raise SystemExit(2)
