"""NEUMANN RC39.1 | No-positive-witness explanatory counterexample discovery.

The new oracle returns either ACCEPTED or one deterministically FIRST
(ascending signed offset) violated position. It does NOT tell the expected
symbol, complete constraints, or an example of a satisfying input.

Human preprogrammed the relative-address conjunction ISA AND the richer
explanatory oracle. The system learns exact d->symbol requirements via
active interventions. This is CLASSICAL CEGIS, not own-weight neural Q3.
"""
from __future__ import annotations
from time import process_time_ns

ALPHABET="ABC"
SCHEMA="neumann.q3.rc39.explainable-source-receipt.v1"
PROGRAM_SCHEMA="neumann.q3.rc39.sparse-causal-program.v1"
def _parse(raw,radius):
    if type(raw) is not dict or raw.get("status") not in ("ACCEPTED","VIOLATION"):
        raise ValueError("MALFORMED_ORACLE_RESPONSE")
    if raw["status"]=="VIOLATION":
        d=raw.get("offset")
        if type(d) is not int or d==0 or not -radius<=d<=radius:
            raise ValueError("INVALID_CAUSAL_OFFSET")
        if set(raw)!={"status","offset"}:raise ValueError("HIDDEN_CHAR_OR_OTHER_PRIVILEGED_DATA_LEAK")
    elif set(raw)!={"status"}:
        raise ValueError("ORACLE_EXPLANATION_NOT_SPEC")
    return raw

def discover_without_positive(oracle,*,radius=512,max_queries=64):
    started=process_time_ns()
    calls=0
    known={}
    def result(status,reason=None):
        o={"schema":SCHEMA,"status":status,"reason":reason,"oracle_calls":calls,
           "cpu_us":(process_time_ns()-started)/1000,"positive_witness_supplied":False,
           "source_rights":"FIRST_OFFENDING_OFFSET_ONLY","neural_model_calls":0}
        if status=="SOURCE_CONSISTENT_EXECUTABLE":
            o["program"]={"schema":PROGRAM_SCHEMA,"kind":"RELATIVE_EXACT_CONJUNCTION",
                          "reads":[[d,known[d]] for d in sorted(known)]}
            o["found_reads"]=len(known)
            o["conditional_all_domain_proof"]="REQUIRES_EXTERNAL_AUTHOR_REFERENCE_EQUALITY"
        return o
    if (type(radius) is not int or radius<1 or radius>1024 or
       type(max_queries) is not int or max_queries<1 or max_queries>10000):
        return result("ABSTAIN","BAD_BUDGET_OR_RADIUS")
    def ask(letters):
        nonlocal calls
        if calls>=max_queries:raise RuntimeError("SOURCE_QUERY_BUDGET")
        calls+=1
        return _parse(oracle("".join(letters),radius),radius)
    try:
        for _ in range(2*radius+1):
            progressed=False
            # If every unknown offset is assigned ALL THREE symbols across
            # these three probes and all passes, no unregistered requirement
            # can remain under the source contract.
            for letter in ALPHABET:
                word=[letter]*(2*radius+1)
                word[radius]="B"
                for delta,char in known.items():
                    word[radius+delta]=char
                answer=ask(word)
                if answer["status"]=="ACCEPTED":
                    continue
                d=answer["offset"]
                if d in known:raise ValueError("KNOWN_REQUIREMENT_STILL_REPORTED")
                for candidate in ALPHABET:
                    if candidate==letter:continue
                    word[radius+d]=candidate
                    changed=ask(word)
                    if changed["status"]=="ACCEPTED" or changed["offset"]!=d:
                        known[d]=candidate
                        progressed=True
                        break
                if not progressed:raise ValueError("NO_POSSIBLE_EXPECTED_CHARACTER")
                break
            if not progressed:return result("SOURCE_CONSISTENT_EXECUTABLE")
        return result("ABSTAIN","ITERATION_LIMIT_REACHED")
    except (RuntimeError,ValueError,TypeError,KeyError) as e:
        return result("ABSTAIN",type(e).__name__+":"+str(e)[:65])
