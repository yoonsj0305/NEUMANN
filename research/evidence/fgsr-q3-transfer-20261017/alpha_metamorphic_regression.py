"""Metamorphic source-IR regression ONLY on already-opened square_twice.

This is NOT a clean transfer holdout. It tests alpha-renaming preservation of
frozen coefficients + human-designed source-only Houdini formula selection.
The earlier 2/2 cross-family experiment remains 0/2 with no regrading.
"""
import hashlib,importlib.util,json,os,time,urllib.request
from pathlib import Path
from predicate_alpha_normalizer import normalize,restore_definitions,_rename_tokens

REV="b4fa7a708e5863bbcdb5de50d692ead3a67cbedc"
PATH="eldarica-misc/LIA/llreve/square_twice_safe.c-1_000.smt2"
SHA="f62d0fb72140e6bd7e953dcebd131a4e9498cc9c0c150588ca79944962e9e748"
OUT=Path(os.getenv("FGSR_RESULT","alpha_regression_receipt.json"))
CORE=Path(__file__).parent.parent/"fgsr-q3-automatic-scaffold-20261017"/"autonomous_scaffold_once.py"
spec=importlib.util.spec_from_file_location("frozen_auto_original",CORE)
core=importlib.util.module_from_spec(spec);spec.loader.exec_module(core)

def verify_source(source,case_name):
    norm,mapping=normalize(source)
    rules,relations=core.parse(norm)
    loops=core.infer_loop_candidates(rules)
    start=time.monotonic()
    full=core.solve_source(rules,relations,loops,"LEARNED",time.monotonic())
    if full["original_unsat_count"]!=9:
        raise RuntimeError("AUTO_PROOF_NOT_9_OF_9_"+case_name)
    proof=restore_definitions(full["explicit_original_relation_definitions_smt2"],mapping)
    independently=core.independently_replay_original(source,proof)
    if not independently["verified"]:
        raise RuntimeError("ORIGINAL_REPLAY_REJECTED_"+case_name)
    return dict(original_sha256=hashlib.sha256(source.encode()).hexdigest(),
                canonical_sha256=hashlib.sha256(norm.encode()).hexdigest(),
                renamed_relation_count=len(mapping),
                frozen_loop_coefficients={n:list(v["learned"]) for n,v in loops.items()},
                source_only_houdini_queries=full["houdini_queries"],
                invariant_conjuncts=sum(map(len,full["selected_conjuncts"].values())),
                original_9_of_9=independently["verified"],
                original_smt_definitions_sha256=hashlib.sha256(proof.encode()).hexdigest(),
                compute_wall_ms=round((time.monotonic()-start)*1000,3))

def main():
    started=time.monotonic()
    out={"scope":"ALPHA_RENAMING_METAMORPHIC_REGRESSION_ON_OPENED_DEVELOPMENT_SOURCE",
         "status":"BLOCKED","global_q1_q7":"OPEN",
         "previous_2_source_transfer_count":"0/2_UNCHANGED",
         "model_train_steps_added":0,
         "operator_family_newly_invented":False}
    try:
        u=f"https://raw.githubusercontent.com/chc-comp/chc-comp26-benchmarks/{REV}/{PATH}"
        with urllib.request.urlopen(u,timeout=25) as f:blob=f.read()
        if hashlib.sha256(blob).hexdigest()!=SHA:
            raise ValueError("ORIGINAL_SHA_MISMATCH")
        text=blob.decode()
        canonical,mapping=normalize(text)
        aliases={item["original_symbol"]:"OtherIndependentRelation"+str(i)
                 for i,item in enumerate(mapping)}
        different_names=_rename_tokens(text,aliases)
        canonical_b,changed_mapping=normalize(different_names)
        if canonical!=canonical_b:
            raise ValueError("STRUCTURAL_IR_DEPENDS_ON_SOURCE_NAME")
        if not all(item["original_symbol"].startswith("OtherIndependentRelation")
                   for item in changed_mapping):
            raise ValueError("ALPHA_TEST_DID_NOT_ACTUALLY_RENAME")
        out["original"]=verify_source(text,"exact_original")
        out["alpha_renamed"]=verify_source(different_names,"renamed_metamorphic")
        out["canonical_alpha_invariance"]=True
        out["status"]="SOURCE_PREDICATE_RENAMING_INVARIANT_2_OF_2"
    except Exception as exc:
        out["status"]="BLOCKED_OR_INVARIANCE_FAIL"
        out["error"]=type(exc).__name__+":"+str(exc)[:900]
    out["wall_ms"]=round((time.monotonic()-started)*1000,3)
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(out,indent=2,ensure_ascii=False)+"\n")
    print("ALPHA_GENERALIZATION",out["status"])
    print("EXACT_ORIGINAL",out.get("original",{}).get("original_9_of_9"))
    print("RENAMED_SOURCE",out.get("alpha_renamed",{}).get("original_9_of_9"))
    print("CLEAN_CROSS_SOURCE_TRANSFER",out["previous_2_source_transfer_count"])
if __name__=="__main__":main()
