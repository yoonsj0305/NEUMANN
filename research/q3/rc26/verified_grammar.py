"""RC26 frozen executable grammar extracted from actual OWN GRU hidden behavior.
Original 8 real PyTorch weights and all first-output bytes in research ZIP;
this lightweight GitHub module is NOT a neural-training replacement.
"""
import re,collections
FROZEN_GRAMMAR={
'mod3':"""AUTOMATON NEURAL_EXTRACTED_BINARY
START AUTO_STATE_fad748aa45
ON AUTO_STATE_fad748aa45 READ 0 => AUTO_STATE_fad748aa45 OUT 1
ON AUTO_STATE_fad748aa45 READ 1 => AUTO_STATE_ab395cb4c4 OUT 0
ON AUTO_STATE_ab395cb4c4 READ 0 => AUTO_STATE_ab395cb4c4 OUT 0
ON AUTO_STATE_ab395cb4c4 READ 1 => AUTO_STATE_923682bea6 OUT 0
ON AUTO_STATE_923682bea6 READ 0 => AUTO_STATE_923682bea6 OUT 0
ON AUTO_STATE_923682bea6 READ 1 => AUTO_STATE_fad748aa45 OUT 1
END
""",
'mod5':"""AUTOMATON NEURAL_EXTRACTED_BINARY
START AUTO_STATE_390401748a
ON AUTO_STATE_390401748a READ 0 => AUTO_STATE_390401748a OUT 1
ON AUTO_STATE_390401748a READ 1 => AUTO_STATE_a90d007c2f OUT 0
ON AUTO_STATE_a90d007c2f READ 0 => AUTO_STATE_a90d007c2f OUT 0
ON AUTO_STATE_a90d007c2f READ 1 => AUTO_STATE_94de9e90e2 OUT 0
ON AUTO_STATE_94de9e90e2 READ 0 => AUTO_STATE_94de9e90e2 OUT 0
ON AUTO_STATE_94de9e90e2 READ 1 => AUTO_STATE_2c24932e8e OUT 0
ON AUTO_STATE_2c24932e8e READ 0 => AUTO_STATE_2c24932e8e OUT 0
ON AUTO_STATE_2c24932e8e READ 1 => AUTO_STATE_90f21496b5 OUT 0
ON AUTO_STATE_90f21496b5 READ 0 => AUTO_STATE_90f21496b5 OUT 0
ON AUTO_STATE_90f21496b5 READ 1 => AUTO_STATE_390401748a OUT 1
END
"""}
EDGE=re.compile(r'ON (AUTO_STATE_[0-9a-f]{10}) READ ([01]) => (AUTO_STATE_[0-9a-f]{10}) OUT ([01])\Z')
def parse(text):
    lines=text.splitlines()
    if len(lines)<5 or lines[0]!='AUTOMATON NEURAL_EXTRACTED_BINARY' or lines[-1]!='END':
        raise ValueError('syntax')
    if not re.fullmatch(r'START AUTO_STATE_[0-9a-f]{10}',lines[1]):raise ValueError('start')
    start=lines[1][6:];table={}
    for line in lines[2:-1]:
        match=EDGE.fullmatch(line)
        if not match:raise ValueError('undeclared token')
        state,x,next_state,output=match.groups()
        if x in table.setdefault(state,{}):raise ValueError('duplicate')
        table[state][x]=(next_state,int(output))
    if start not in table or len(table)>32:raise ValueError('states')
    if any(set(x)!={'0','1'} for x in table.values()):raise ValueError('partial')
    if any(v[0] not in table for row in table.values() for v in row.values()):
        raise ValueError('unknown destination')
    return start,table

def run(compiled,word):
    start,table=compiled;out=[]
    for x in word:
        if type(x)!=int or x not in (0,1):raise ValueError('input')
        start,y=table[start][str(x)];out.append(y)
    return tuple(out)

def independent_product_proof(text,k):
    # Proof is about the extracted DISCRETE program, not original GRU!
    initial,transitions=parse(text)
    q=collections.deque([(initial,0)]);seen={(initial,0)}
    while q:
        p,r=q.popleft()
        for b in (0,1):
            target=(r+b)%k;dest,emit=transitions[p][str(b)]
            if emit!=int(target==0):return 'UNKNOWN_COUNTEREXAMPLE'
            pair=(dest,target)
            if pair not in seen:seen.add(pair);q.append(pair)
    if len(transitions)!=k or len(seen)!=k:return 'UNKNOWN_NONMINIMAL'
    return 'SCOPED_ALL_LENGTH_PASS'

def admission(task):
    if task not in ('mod3','mod5'):return 'UNKNOWN_NEW_FAMILY'
    code=FROZEN_GRAMMAR[task];k=int(task[3:])
    return independent_product_proof(code,k)

SCIENCE={'NEUMANN_own_weights_generate_latent_states':'SCOPED_PASS',
'compiler_authored_by':'CLASSICAL/HUMAN',
'GRU_all_length_certified':False,
'model_autonomously_invents_base_ISA':'OPEN',
'global_Q3':'OPEN','global_Q4':'OPEN','global_Q6':'OPEN','global_Q7':'OPEN'}
