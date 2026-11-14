"""RC44 SCOPED operator copied as a reviewed deterministic implementation.
The *original* GPT-6 source was separately SHA-frozen BEFORE seeing the
target gold; see complete exact archived source and receipt in conversation ZIP.
No NEUMANN ownweight neural call, proof of global ARC transformation, or Q3 PASS.
"""
def marker_periodic_fill(g):
    if type(g)!=list or not g or type(g[0])!=list or not g[0]:
        raise ValueError("nonempty rectangular grid required")
    if any(type(row)!=list or len(row)!=len(g[0]) for row in g):
        raise ValueError("ragged grid")
    if any(type(v)!=int or v<0 or v>9 for row in g for v in row):
        raise ValueError("only bounded ARC colors")
    marker=g[0][0]
    if marker==0:raise ValueError("missing marker")
    k=0
    while k<len(g) and g[k][0]==marker:k+=1
    if k==len(g):raise ValueError("no separator/marker end")
    last=max((i for i,row in enumerate(g) if any(row)),default=-1)
    if last==len(g)-1:raise ValueError("no trailing empty rows")
    out=[list(row) for row in g]
    for i in range(last+1,len(g)):
        src=g[(i-last-1)%k]
        out[i]=[0]+list(src[1:])
    return out

def source_gate(training):
    if type(training)!=list or not training:
        return {"status":"UNKNOWN_NO_DEMONSTRATIONS"}
    for ex in training:
        if type(ex)!=dict or not {"input","output"}.issubset(ex):
            return {"status":"UNKNOWN_MALFORMED_IO"}
        try:pred=marker_periodic_fill(ex["input"])
        except (ValueError,TypeError,IndexError,ZeroDivisionError):
            return {"status":"UNKNOWN_OUTSIDE_OPERATOR_CONTRACT"}
        if pred!=ex["output"]:
            return {"status":"UNKNOWN_SOURCE_MISMATCH"}
    return {"status":"SOURCE_FIT_ONLY",
            "permission":"CANDIDATE_NOT_UNIVERSALLY_CERTIFIED",
            "operator":"GENERIC_MARKER_PERIODIC_FILL",
            "new_neural_forwards":0}
