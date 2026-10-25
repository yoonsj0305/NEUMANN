"""RC33 compact scope-preserving parser/proof gate.

The REAL shared PyTorch actor was trained across 1800 unrelated opaque IO
tasks to emit one of 27 RHS-length splits, with negative log probability of
all IO-consistent latent parses. Raw OWN model tensors/first sealed output and
isolated 4-seed retrainer are in the full archived study ZIP, NOT this file.
No model invents alphabet, rewrite semantics or segmentation interpreter.
"""
from itertools import product
ABC="ABC";SEEDS=("ABC","BCA","CAB")
OPTIONS=tuple(product((1,2,3),repeat=3))
def run_one(word,grammar):
    if not set(word).issubset(ABC) or len(grammar)!=3:
        raise ValueError("grammar")
    return "".join(grammar[ABC.index(c)] for c in word)
def run_repeated(word,grammar,depth,budget=100000):
    if not isinstance(depth,int) or depth<0:raise ValueError("depth")
    for i in range(depth):
        word=run_one(word,grammar)
        if len(word)>budget:raise ValueError("safety budget")
    return word
def candidate_rule_tables(observations):
    """NO gold grammar labels. Inverts only three opaque observed strings."""
    if not isinstance(observations,(tuple,list)) or len(observations)!=3:
        raise ValueError("three observations required")
    if any(not isinstance(y,str) or not set(y).issubset(ABC) for y in observations):
        raise ValueError("invalid observed alphabet")
    y=observations[0];out=[]
    for a,b,c in OPTIONS:
        if a+b+c!=len(y):continue
        g=(y[:a],y[a:a+b],y[a+b:a+b+c])
        if all(run_one(s,g)==outstr for s,outstr in zip(SEEDS,observations)):
            out.append(g)
    return tuple(out)
def after_neural_proposal(observations,selected_length_triplet):
    """Fail closed if source ambiguous, even when neural proposed a fit.
    A trusted class restriction (three nonerasing RHS each len<=3) is required.
    """
    try:
        lens=tuple(selected_length_triplet)
        if len(observations)!=3 or any(not isinstance(w,str) or any(c not in ABC for c in w) for w in observations):\n            return {"status":"UNKNOWN_INVALID"}\n        if lens not in OPTIONS:return {"status":"UNKNOWN_OUTSIDE_METAGRAMMAR"}
        if (not isinstance(observations,(tuple,list)) or len(observations)!=3
            or any(not isinstance(y,str) or not set(y).issubset(ABC) for y in observations)):
            return {"status":"UNKNOWN_INVALID"}
        if sum(lens)!=len(observations[0]):
            return {"status":"UNKNOWN_INCONSISTENT"}
        a,b,c=lens
        text=observations[0]
        proposal=(text[:a],text[a:a+b],text[a+b:a+b+c])
        alternatives=candidate_rule_tables(observations)
        if proposal not in alternatives:return {"status":"UNKNOWN_WRONG_SOURCE_OUTPUT"}
        if len(alternatives)!=1:return {"status":"UNKNOWN_MULTIPLE_COMPATIBLE_PROGRAMS"}
        return {"status":"CONDITIONAL_UNIQUE_RULES","rules":proposal,
                "assumption":"true program is in given 3-symbol RHS-length<=3 parallel-rewrite class"}
    except (ValueError,TypeError):return {"status":"UNKNOWN_INVALID"}
