"""Q3 RC32 model-emitted variable-length recursive grammar (compact extract).
Fully trained PyTorch logits + frozen output bytes are archived separately.
Human supplied rewriting metatheory, 3-symbol alphabet and proof compiler.
"""
import hashlib

MODEL_WEIGHT_EMITTED={
 0:{"A":"AB","B":"CA","C":"B"},
 1:{"A":"BC","B":"AAB","C":"CA"},
 2:{"A":"CAB","B":"BC","C":"A"}}
SYMBOLS="ABC"
class GrammarRejected(ValueError):pass

def register(text):
    if type(text)!=str or len(text)>4096:raise GrammarRejected("source budget")
    result={}
    for line in text.splitlines():
        if line.count("::=")!=1:raise GrammarRejected("production")
        a,b=map(str.strip,line.split("::=",1))
        if a not in SYMBOLS or a in result or not 1<=len(b)<=3 or any(c not in SYMBOLS for c in b):
            raise GrammarRejected("unsafe or undefined symbol")
        result[a]=b
    if set(result)!=set(SYMBOLS):raise GrammarRejected("missing production")
    return result

def emit(productions):
    if set(productions)!=set(SYMBOLS):raise GrammarRejected("incomplete")
    text="\n".join(f"{x} ::= {productions[x]}" for x in SYMBOLS)
    register(text)
    return text

def execute(grammar,word,depth,output_cap=300000):
    if type(depth)!=int or not 0<=depth<=100000 or type(word)!=str or any(x not in SYMBOLS for x in word):
        raise GrammarRejected("bad request")
    for _ in range(depth):
        word="".join(grammar[c] for c in word)
        if len(word)>output_cap:raise GrammarRejected("cost cap")
    return word

def counts_by_matrix_power(grammar,word,depth):
    if type(depth)!=int or not 0<=depth<=100000 or any(c not in SYMBOLS for c in word):
        raise GrammarRejected("invalid")
    vec=[word.count(c) for c in SYMBOLS]
    matrix=[[grammar[a].count(b) for b in SYMBOLS] for a in SYMBOLS]
    def vmul(v,M):return [sum(v[i]*M[i][j] for i in range(3)) for j in range(3)]
    def mmul(A,B):return [[sum(A[i][k]*B[k][j] for k in range(3)) for j in range(3)] for i in range(3)]
    while depth:
        if depth&1:vec=vmul(vec,matrix)
        depth>>=1
        if depth:matrix=mmul(matrix,matrix)
    return tuple(vec)

def strict_symbolic_certificate(generated_rules,gold_rules):
    # ONLY after independent gold reference is available; source actor does not see gold.
    if generated_rules!=gold_rules:return "UNKNOWN_NOT_PROVEN"
    return "PROVED_ALL_START_WORDS_AND_ALL_FINITE_REWRITE_DEPTHS_BY_INDUCTION"
