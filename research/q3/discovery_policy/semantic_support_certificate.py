"""Scoped, fail-closed semantic-grammar support certificate.

Only correct for original NEUMANN classical source-conditioned ASCII
extract/split/case/decimal-normalize/concatenate DSL. It does not prove that
some other classical program or any neural algorithm cannot solve a task.
Never grants neural model authority or closes Q1-Q7.
"""

def _characters(x):
    if isinstance(x,str):return set(x)
    if isinstance(x,list):
        out=set()
        for element in x:out|=_characters(element)
        return out
    return set()

def semantic_support_certificate(source,feedback):
    if not isinstance(source,list) or len(source)<2 or not isinstance(feedback,(tuple,list)) or len(feedback)!=2:
        return {"status":"UNKNOWN_PREMISE","witness":[]}
    fx,fy=feedback
    if not isinstance(fy,str) or not all(
        isinstance(pair,(tuple,list)) and len(pair)==2 and isinstance(pair[1],str)
        and (isinstance(pair[0],str) or pair[0] is None) for pair in source
    ) or not (isinstance(fx,str) or fx is None):
        return {"status":"UNKNOWN_PREMISE","witness":[]}
    if any(ord(c)>=128 for pair in [*source,feedback] for part in pair for c in _characters(part)):
        return {"status":"UNKNOWN_NONASCII","witness":[]}
    proof=[]
    if fx is None and len({y for _,y in source})>1:
        proof.append({"type":"NULL_TOTALITY_BARRIER"})
    present=_characters(fx)
    for x,y in source:present|=_characters(x)|_characters(y)
    available_letters={c.lower() for c in present if c.isalpha()}
    absent=sorted(c for c in set(fy) if c not in present and
                  (not c.isalpha() or c.lower() not in available_letters))
    if absent:proof.append({"type":"CHARACTER_SUPPORT_BARRIER","missing":absent})
    return {"status":"PROVEN_NO_PROGRAM_IN_THIS_DSL" if proof else "UNKNOWN",
            "witness":proof,"automatically_call_neural":False,
            "global_questions_closed":[]}
