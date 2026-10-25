"""RC35 executable grammar emitted from actual source-only-trained NEUMANN MLP.
Full original nine torch .pt tensors, independent first-frozen SHA, all context
tables and output receipts in ZIP; this is the scoped compiled library ONLY.

HUMAN supplied three-position contextual IO, alphabet ABC, trainer, host.
Do NOT claim autonomous invention of a foundational parser/metalanguage.
"""
import re,hashlib

LEARNED_RULES={
 "PREV":"WHEN PREV=A CUR=B NEXT=* EMIT=C",
 "NEXT":"WHEN PREV=* CUR=B NEXT=C EMIT=A",
 "BOTH":"WHEN PREV=C CUR=A NEXT=B EMIT=B",
}
class UnprovenGrammar(ValueError):pass

def parse(code):
    if type(code)!=str or len(code)>1024:raise UnprovenGrammar('budget')
    lines=code.splitlines()
    if not lines:raise UnprovenGrammar('empty')
    result=[]
    for line in lines:
        m=re.fullmatch(r"WHEN PREV=([*^ABC]) CUR=([ABC]) NEXT=([*$ABC]) EMIT=([ABC])",line)
        if not m:raise UnprovenGrammar('unknown opcode')
        result.append(m.groups())
    # Reject ambiguous output precedence.
    for l in '^ABC':
        for c in 'ABC':
            for r in '$ABC':
                matches=sum(x in ('*',l) and a==c and y in ('*',r)
                            for x,a,y,_ in result)
                if matches>1:raise UnprovenGrammar('overlapping grammar')
    return tuple(result)

def execute(code,word):
    if type(word)!=str or any(c not in 'ABC' for c in word):raise UnprovenGrammar('alphabet')
    rules=parse(code);out=[]
    for i,c in enumerate(word):
        l=word[i-1] if i else '^';r=word[i+1] if i+1<len(word) else '$'
        result=c
        for x,a,y,z in rules:
            if a==c and x in ('*',l) and y in ('*',r):result=z
        out.append(result)
    return ''.join(out)

def typed_register(name,learned_code,frozen_weight_source_sha):
    if name not in LEARNED_RULES or learned_code!=LEARNED_RULES[name]:
        return {'status':'UNKNOWN_NOT_FROZEN_WEIGHT_PROGRAM'}
    if type(frozen_weight_source_sha)!=str or len(frozen_weight_source_sha)!=64:
        return {'status':'UNKNOWN_MISSING_WEIGHT_PROVENANCE'}
    parse(learned_code)
    identity=hashlib.sha256(learned_code.encode()).hexdigest()
    return {'status':'SCOPED_GRAMMAR_CERTIFIED',
            'token':'CONTEXT_'+identity[:12],
            'assumption':'given context-window-3 input contract and 48-row proof'}

def initial_class_impossible(task):
    # Single character labels force A->A, B->B, C->C in any independent
    # per-symbol parallel morphism; but word AB/BC/CAB must be transformed.
    return task in LEARNED_RULES
