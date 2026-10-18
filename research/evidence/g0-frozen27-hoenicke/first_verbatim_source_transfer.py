"""Prospective source-body-unseen cross-origin transfer of FROZEN G0 modular verifier.

Preregd: GitHub Issue 221 before opening any original Hoenicke SMT body.
Imported proof code is pinned verbatim to ORIGINAL Ultimate evidence Git blob.
No prompt/model/inferred labels; all 27 original files are examined unchanged.
"""
import collections, gzip, hashlib, importlib.util, json, os, re, subprocess, sys, time
import urllib.request
from pathlib import Path
import ijson
import z3

ISSUE = "https://github.com/yoonsj0305/NEUMANN/issues/221"
SOURCE_REPO = "SMT-LIB/benchmark-submission-2023"
SOURCE_COMMIT = "7f993a017850ba547c6ea19a1bf3b54adf54a449"
SOURCE_FAMILY = "20230328-sqrtmodinv-hoenicke"
SOURCE_URL = (f"https://raw.githubusercontent.com/{SOURCE_REPO}/{SOURCE_COMMIT}/"
              f"non-incremental/QF_NIA/{SOURCE_FAMILY}/")
SOURCE_DIR_API=(f"https://api.github.com/repos/{SOURCE_REPO}/contents/"
                f"non-incremental/QF_NIA/{SOURCE_FAMILY}?ref={SOURCE_COMMIT}")
CHECKER_SOURCE_URL=(
    "https://raw.githubusercontent.com/yoonsj0305/NEUMANN/"
    "20bc532ce5f4f82a93ca0e85e001e6abbd7d9274/"
    "research/evidence/g0-ultimate2023-20261018/exact_original_modular_unsat.py")
CHECKER_GIT_BLOB_SHA1="ae50844955aec9e636a0a3f2986f6cc52b4ec1fd"
OFFICIAL_COMMIT="cd15cbedd4ef312d615448100797a80e922cf575"
OFFICIAL_BASE=(f"https://raw.githubusercontent.com/SMT-COMP/smt-comp.github.io/"
               f"{OFFICIAL_COMMIT}/data/")
OFFICIAL_SHA256={
    "results-sq-2026.json.gz":"7abe5cadf800cc84db00506f85176378f714cdaa8c02a0e491059835f5039c58",
    "benchmarks-2026.json.gz":"ba855e47e1ed88e2e6bb26272e84a20a0e8f0c320adc704b062f4c287e586a54"}
FROZEN_NAMES=(
"modInv128.smt2","modInv16.smt2","modInv32.smt2","modInv64.smt2",
"modInv8.smt2","modInvFull.smt2","modInvInitial.smt2","modInvStep.smt2",
"modInvStepSimplified.smt2","modInvVar1.smt2","modSimpleTest.smt2",
"sqrtStep1.smt2","sqrtStep1a.smt2","sqrtStep2.smt2","sqrtStep2a.smt2",
"sqrtStep3.smt2","sqrtStep3a.smt2","sqrtStep4.smt2","sqrtStep4a.smt2",
"sqrtStep5.smt2","sqrtStep5a.smt2","sqrtStep6.smt2","sqrtStep6a.smt2",
"sqrtStep7.smt2","sqrtStep7a.smt2","sqrtStepFinal.smt2","sqrtStepFinala.smt2")
OUT=Path("/tmp/g0_hoenicke_frozen27_first_cross_family_receipt.json")
ROOT=Path("/tmp/g0_hoenicke27")
ROOT.mkdir(exist_ok=True,parents=True)

def fetch(url,path):
    req=urllib.request.Request(url,headers={"User-Agent":"NEUMANN-G0-prospective-2026"})
    with urllib.request.urlopen(req,timeout=45) as inp,open(path,"wb") as out:
        import shutil
        shutil.copyfileobj(inp,out)
    return Path(path).read_bytes()

def check_metadata():
    root=ROOT/"folder_listing.json"
    raw=fetch(SOURCE_DIR_API,root)
    listing=json.loads(raw)
    names={x["name"] for x in listing if x["type"]=="file" and x["name"].endswith(".smt2")}
    if names!=set(FROZEN_NAMES):
        raise RuntimeError("COHORT_MUTATION_OR_DIR_MISMATCH")
    return len(names)

def load_verbatim_frozen_checker():
    dest=ROOT/"frozen_checker_original_source.py"
    source=fetch(CHECKER_SOURCE_URL,dest)
    p=subprocess.run(["git","hash-object",str(dest)],capture_output=True,text=True,check=True)
    if p.stdout.strip()!=CHECKER_GIT_BLOB_SHA1:
        raise RuntimeError("FROZEN_CHECKER_GIT_BLOB_SHA1_MISMATCH")
    sp=importlib.util.spec_from_file_location("frozen_original_unsat_ultimate",str(dest))
    mod=importlib.util.module_from_spec(sp)
    sys.modules[sp.name]=mod
    sp.loader.exec_module(mod)
    return mod,hashlib.sha256(source).hexdigest()

def multiline_asserts_as_singleline(text):
    """Lossless whitespace-only input adaptation for frozen old line parser.
    No math transformations. Original file is never modified.
    """
    pattern=re.compile(r"(?m)^[ \t]*\(assert[ \t]")
    matches=list(pattern.finditer(text))
    if not matches:
        raise ValueError("ORIGINAL_SOURCE_CONTAINS_NO_ASSERTIONS")
    extracted=[]
    for match in matches:
        start=text.index("(",match.start())
        depth=0
        end=None
        for i in range(start,len(text)):
            ch=text[i]
            if ch=="(":depth+=1
            elif ch==")":
                depth-=1
                if depth==0:
                    end=i+1
                    break
        if end is None or depth!=0:raise ValueError("UNBALANCED_ORIGINAL_ASSERT")
        raw=text[start:end]
        one=" ".join(raw.split())
        # Token sequences (incl. original quoted variable names) unchanged.
        toks=lambda x: re.findall(r"\|[^|]*\||\(|\)|[^\s()]+",x)
        if toks(raw)!=toks(one):
            raise RuntimeError("ORIGINAL_ASSERT_TOKENS_CHANGED_BY_WHITESPACE_ONLY_ADAPTER")
        extracted.append(one)
    # Exact same parse on untouched original via standard SMTLIB Z3 frontend:
    solver=z3.Solver()
    solver.from_string(text)
    if len(solver.assertions())!=len(extracted):
        raise RuntimeError("ORIGINAL_ASSERTION_COVERAGE_MISMATCH")
    return "\n".join(extracted),len(extracted)

def checker_case(alg, source_file, text):
    # Exact unchanged FROZEN proof criterion. Repair only old input lexer.
    canonical, original_assert_count=multiline_asserts_as_singleline(text)
    clauses=alg.source_asserts(canonical)
    if len(clauses)!=original_assert_count:
        raise RuntimeError("CANONICAL_SOURCE_ASSERTION_COUNT_MISMATCH")
    eligible=[]
    unsupported=0
    for clause in clauses:
        for atom in alg.required(clause):
            try:
                candidate=alg.required_negative_mod_eq_zero(atom)
            except (ValueError,TypeError,AssertionError,IndexError,KeyError):
                unsupported+=1
                continue
            if candidate is not None:
                eligible.append(candidate)
    for cand in eligible:
        try:
            residues=alg.demonstrate_modular_identity(cand)
            if any(v!=0 for v in residues):
                continue
            proof=alg.verify_source_unsat_from_proven_identity(source_file,cand)
            if proof["original_plus_proved_congruence_unsat"]:
                return {"status":"ORIGINAL_UNSAT_PROVEN",
                        "source_formula_assert_count":len(clauses),
                        "required_candidates":len(eligible),
                        "unsupported_atoms":unsupported,
                        "modulus":cand["modulus"],
                        "integer_residues":[int(r) for r in residues],
                        "original_checker_status":proof}
        except (ValueError,TypeError,AssertionError,IndexError,KeyError,z3.Z3Exception) as exc:
            unsupported+=1
    return {"status":"NO_CERTIFIED_CONGRUENCE_PROOF",
            "required_candidates":len(eligible),
            "unsupported_atoms":unsupported,
            "source_formula_assert_count":len(clauses)}

def official_stats(rows):
    # Official data not opened until *all* source-body checks have completed.
    index=ROOT/"official_benchmarks.json.gz"
    results=ROOT/"official_results.json.gz"
    for name,dest in (("benchmarks-2026.json.gz",index),
                      ("results-sq-2026.json.gz",results)):
        blob=fetch(OFFICIAL_BASE+name,dest)
        if hashlib.sha256(blob).hexdigest()!=OFFICIAL_SHA256[name]:
            raise RuntimeError("OFFICIAL_DATA_SHA_MISMATCH")
    statuses={}
    with gzip.open(index,"rb") as f:
        for row in ijson.items(f,"non_incremental.item"):
            item=row["file"]
            if item.get("logic")=="QF_NIA" and item.get("family",[])[0:1]==[SOURCE_FAMILY]:
                statuses[item["name"]]=row["status"].lower()
    solverresults=collections.defaultdict(dict)
    with gzip.open(results,"rb") as f:
        for row in ijson.items(f,"results.item"):
            item=row["file"]
            if (row.get("track")=="SingleQuery" and item.get("logic")=="QF_NIA"
                and item.get("family",[])[0:1]==[SOURCE_FAMILY]):
                if row["solver"] in solverresults[item["name"]]:
                    raise RuntimeError("OFFICIAL_DUPLICATE_SOLVER")
                solverresults[item["name"]][row["solver"]]=row["result"].lower()
    if not set(solverresults).issubset(set(statuses)):
        raise RuntimeError("OFFICIAL_INDEX_ORIGINAL_INCONSISTENT")
    for row in rows:
        name=row["original_filename"]
        vals=solverresults.get(name,{})
        row["official_competition_selected"]=name in solverresults
        row["official_source_status_after_proof"]=statuses.get(name,"NOT_IN_2026_INDEX")
        row["official_any_solver_sat_unsat"]=any(v in ("sat","unsat") for v in vals.values())
        row["official_participant_count"]=len(vals)
    return {"competed":sum(row["official_competition_selected"] for row in rows),
            "competition_noanswer":sum(row["official_competition_selected"] and
                     not row["official_any_solver_sat_unsat"] for row in rows),
            "source_index_matched":sum(row["original_filename"] in statuses for row in rows)}

def main():
    start=time.perf_counter()
    receipt={"status":"FIRST_RUN_INCOMPLETE","issue":ISSUE,
             "source_commit":SOURCE_COMMIT,"source_family":SOURCE_FAMILY,
             "algorithm_frozen_git_blob_sha1":CHECKER_GIT_BLOB_SHA1,
             "registered_count":27,"originals":[],
             "no_task_specific_algorithm_tuning":True,
             "no_neural_train_or_infer":True,
             "no_gold_used_in_proof":True,
             "G0_ALL_IN_HEADROOM":"UNKNOWN","G1":"HOLD_LEARNING",
             "G2":"BLOCKED","Q1_Q7_GLOBAL":"OPEN"}
    def save():OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    save()
    try:
        receipt["upstream_original_dir_nfiles"]=check_metadata()
        alg,sha=load_verbatim_frozen_checker()
        receipt["checker_raw_source_sha256"]=sha
        for fname in FROZEN_NAMES:
            p=ROOT/fname
            raw=fetch(SOURCE_URL+fname,p)
            text=raw.decode("utf-8")
            if "(set-logic QF_NIA)" not in text:
                raise RuntimeError("SOURCE_LOGIC_MISMATCH:"+fname)
            if '(set-info :license "https://creativecommons.org/licenses/by/4.0/")' not in text:
                raise RuntimeError("SOURCE_LICENSE_MISMATCH:"+fname)
            start_item=time.perf_counter()
            entry={"original_filename":fname,
                   "original_sha256":hashlib.sha256(raw).hexdigest(),
                   "original_bytes":len(raw)}
            try:
                entry.update(checker_case(alg,p,text))
            except (ValueError,IndexError,AssertionError,TypeError,z3.Z3Exception) as exc:
                entry.update(status="SOURCE_UNSUPPORTED_FAIL_CLOSED",
                             source_issue_type=type(exc).__name__)
            entry["source_algorithm_and_z3_proof_wall_s"]=round(time.perf_counter()-start_item,6)
            receipt["originals"].append(entry)
            save()
        if len(receipt["originals"])!=27:raise RuntimeError("COHORT_INCOMPLETE")
        receipt["proofs_before_official_results"]=sum(
            x["status"]=="ORIGINAL_UNSAT_PROVEN" for x in receipt["originals"])
        receipt["eligibility_after_proofs"]=official_stats(receipt["originals"])
        receipt["status"]="FIRST_FROZEN_CROSS_FAMILY_SOURCE_AUDIT_COMPLETE"
        receipt["transfer"]="PASS_PROVEN" if receipt["proofs_before_official_results"] else "FAIL_NO_NEW_CERTIFIED_SOURCE_ORIGINALS"
        receipt["total_wall_s"]=round(time.perf_counter()-start,3)
        save()
        print("G0_HOENICKE_FROZEN27_FIRST",json.dumps({
            "status":receipt["status"],"originals":len(receipt["originals"]),
            "exact_unsat_certificates":receipt["proofs_before_official_results"],
            "official_overlap":receipt["eligibility_after_proofs"],
            "transfer":receipt["transfer"],"wall_s":receipt["total_wall_s"]}),flush=True)
    except Exception as e:
        receipt["status"]="FIRST_CROSS_FAMILY_AUDIT_BLOCKED"
        receipt["first_failure"]=type(e).__name__+":"+str(e)[:350]
        receipt["total_wall_s"]=round(time.perf_counter()-start,3)
        save()
        print("G0_HOENICKE_FROZEN27_FIRST_FAILURE",receipt["first_failure"],flush=True)
        raise

if __name__=="__main__":main()
