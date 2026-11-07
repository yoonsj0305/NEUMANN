"""Q3 POSTFIRST finite semantic stress of TWO learned cross-subgroup programs.

Original first scores are IMMUTABLE. Domain constraints of each new probe
are explicitly authored after seeing original solutions (development only);
they are not proof of arbitrary original function correctness.
"""
from __future__ import annotations
import hashlib,json,pathlib
import typed_domain_interface_postfirst as typed

IN="previous/Q3_TYPED_METAGRAMMAR_FRESH_37_ORIGINAL_FIRST.json"

def assert_model(report,ident):
    item=next(x for x in report["per_task"] if x["id"]==ident)
    out=item["arms"]["learned_typed_meta"]
    if not out["heldout"]["exact"] or out["program_ast"] is None:
        raise ValueError("NO_VERIFIED_SOURCE_PROGRAM")
    return out["program_ast"]

def inspect():
    base=json.loads(pathlib.Path(IN).read_text())
    if base.get("original_count")!=37:raise ValueError("MISMATCH_PRIOR_PROOF")
    stack=assert_model(base,"stackoverflow1.sl")
    file=assert_model(base,"remove-file-extension-from-filename.sl")
    prefixes=[f"Module{a}_Series{b}" for a in range(1,26) for b in range(1,9)]
    suffixes=["", ".", ", LLC", " and Partners"]
    extensions=["txt","csv","log","tar.gz","jpeg","xls.pdf"]
    count_stack=count_file=mut_fail_stack=0
    for pre in prefixes:
        for suffix in suffixes:
            x=pre+" Inc"+suffix
            got=typed.execute(stack,(x,))
            if got!=pre:raise AssertionError(("COMPANY_PREFIX_MISMATCH",x,got,pre))
            count_stack+=1
            # A deliberately incorrect position mutation must be detected.
            mutation=["substr",["arg",0],["num",0],
                      ["index",["arg",0],["lit","Inc"],["num",0]]]
            if typed.execute(mutation,(x,))!=pre:mut_fail_stack+=1
        for ext in extensions:
            x=pre+"."+ext
            got=typed.execute(file,(x,))
            if got!=pre:raise AssertionError(("FILENAME_PREFIX_MISMATCH",x,got,pre))
            count_file+=1
    # Scope check: original learned company program lacks semantics for
    # inputs without the token ' Inc'; preserve ABSTAIN outside domain.
    ood=["No company suffix","Acme LLC","Incorporated","Small Holdings"]
    unsupported=[{"input":a,"generated_result":typed.execute(stack,(a,)),
                  "status":"OUT_OF_DOMAIN_NO_REFERENCE_GOLD"} for a in ood]
    report={"schema":"neumann.q3.metagrammar-cross-cohort-postfirst-metamorphic.v1",
      "science_status":"POSTFIRST_DEVELOPMENT_NOT_BLIND_ORIGINAL",
      "prior_original_run":42373905695,
      "source_program_ids":["stackoverflow1.sl","remove-file-extension-from-filename.sl"],
      "scoped_domain_company":"x=P+' Inc'+S; P excludes substring Inc and S is a listed suffix",
      "scoped_domain_file":"x=P+'.'+ext; P excludes dot and ext is a listed suffix",
      "company_positive_cases":count_stack,"file_positive_cases":count_file,
      "company_incorrect_mutation_rejected":mut_fail_stack,
      "unsupported_domain_cases":unsupported,
      "proof_note":"If P lacks 'Inc', indexof(P+' Inc'+S,'Inc')=len(P)+1, so substr(x,0,indexof-1)=P. If P lacks '.', indexof(P+'.'+ext,'.')=len(P), so substr(x,0,indexof)=P. These are scoped algebraic identities, not an unrestricted semantic proof.",
      "source_first_sha256":base["frozen_source_grammar_sha256"],
      "original_programs_hash":[hashlib.sha256(json.dumps(x,sort_keys=True).encode()).hexdigest() for x in [stack,file]]}
    pathlib.Path("Q3_POSTFIRST_METAMORPHIC_SEMANTICS.json").write_text(json.dumps(report,indent=2))
    print(json.dumps({"company_positive":count_stack,"file_positive":count_file,
       "bad_mutation_rejected":mut_fail_stack,"OOD":len(unsupported)},indent=2))

if __name__=="__main__":inspect()
