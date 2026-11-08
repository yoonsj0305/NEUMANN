"""Q3 no-hidden-teacher-oracle audit of previous 48 synthetic transfer tasks.

Use only source example pairs to choose an AST. Exhaustive teacher truth
evaluation is performed AFTER program selection, never inside the search.
This corrects a methodological weakness in earlier full-oracle experiments.
Human-written grammars and synthetic task families remain visible limits.
"""
from __future__ import annotations
import hashlib,itertools,json,pathlib,time
import executable_affine_metagrammar_cross_type as old

def select_source_only(n,examples,candidates):
    tested=0
    for ast in candidates:
        tested+=1
        if all(old.calc(ast,x,n)==y for x,y in examples):
            return ast,tested
    return None,tested

def run():
    start=time.perf_counter_ns()
    source=[];source_rows=[]
    for family in ("complement","same-index"):
        for n in (4,6):
            for hidden_k in range(1,n):
                examples=old.source_examples(n,hidden_k,family)
                program,checks=select_source_only(n,examples,old.ast_stream(n))
                # independent full-domain verification happens only AFTER selection
                verified=bool(program and old.exact(program,n,hidden_k,family))
                source_rows.append({"family":family,"n":n,"hidden_k":hidden_k,
                                   "source_checks":checks,
                                   "selected_ast":program,
                                   "post_selection_exact":verified})
                if not verified:
                    raise AssertionError("NONORACLE_SOURCE_NOT_VERIFIED")
                source.append((n,program))
    method=old.method_invention(source)
    if set(map(tuple,method["relations"]))!={(0,1,0),(1,-1,0)}:
        raise AssertionError("NONORACLE_NEW_METHOD_NOT_FOUND")
    out=[]
    for family in ("complement","same-index"):
        for n in (8,9,10):
            for hidden_k in range(1,n):
                examples=old.source_examples(n,hidden_k,family)
                learned,learned_checks=select_source_only(
                    n,examples,old.learned_bit_candidates(method,n))
                cold,cold_checks=select_source_only(n,examples,old.ast_stream(n))
                # IMPORTANT: full-domain exactness used for reporting only.
                out.append({"width":n,"private_family":family,"private_k":hidden_k,
                    "learned_checks":learned_checks,"cold_checks":cold_checks,
                    "learned_post_selection_exact":bool(learned and old.exact(learned,n,hidden_k,family)),
                    "cold_post_selection_exact":bool(cold and old.exact(cold,n,hidden_k,family)),
                    "learned_ast":learned,"cold_ast":cold})
    result={"schema":"neumann.q3.no-teacher-query-during-selection.v1",
        "source_asts":source_rows,"learned_method":method,
        "source_verified":sum(r["post_selection_exact"] for r in source_rows),
        "target_rows":out,
        "summary":{"source_full_domain_after_selection":len(source),
            "target_n":len(out),
            "learned_full_domain_exact":sum(r["learned_post_selection_exact"] for r in out),
            "strong_cold_full_domain_exact":sum(r["cold_post_selection_exact"] for r in out),
            "learned_candidate_checks":sum(r["learned_checks"] for r in out),
            "cold_candidate_checks":sum(r["cold_checks"] for r in out),
            "evaluation_oracle_invocations_before_selection":0,
            "runtime_ns":time.perf_counter_ns()-start},
        "limitations":"Source/target belong to two human-designed synthetic families; full-domain labels used after selection are experimenter-known truth functions; no independent-author task transfer."}
    pathlib.Path("Q3_NO_ORACLE_METHOD_DISCOVERY.json").write_text(json.dumps(result,indent=2))
    print(json.dumps(result["summary"],indent=2))
    assert result["summary"]["learned_full_domain_exact"]==48
    assert result["summary"]["strong_cold_full_domain_exact"]==36
    return result

if __name__=="__main__":run()
