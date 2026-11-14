"""RC31: real own-trained SOURCE opcode programs; symbolic composer is classical.
Original 16 PyTorch weights, frozen first predictions, full source code and
independent references in SHA-verified standalone ZIP. GLOBAL Q3 REMAINS OPEN.
"""
import hashlib,json
SOURCE={
0:((0,0),(0,2),(3,3)),1:((1,1),(0,0),(2,3),(4,4)),
2:((0,0),(1,2),(3,3)),3:((0,0),),4:((1,1),(0,2),(3,3)),
5:((1,1),),7:((0,1),),8:((0,1),(2,2)),
10:((1,1),(2,2)),12:((0,0),(2,2)),
13:((0,0),(1,2)),15:((0,0),(0,2))}
SOURCE12_SHA256='4d4dd8b585bc51cd22d37ddda8225c8a8328f392e943924dce0e7453885d0265'
# Exactly the frozen model-source-only classical composer ASTs.
NEW={
6:['CALL',7,['CALL',13,['ARG','a'],['ARG','b']],['CALL',13,['ARG','b'],['ARG','a']]],
9:['CALL',7,['CALL',7,['ARG','a'],['ARG','b']],['CALL',7,['CALL',3,['ARG','a'],['ARG','a']],['CALL',3,['ARG','b'],['ARG','a']]]],
11:['CALL',13,['ARG','b'],['ARG','a']],
14:['CALL',7,['CALL',3,['ARG','a'],['ARG','a']],['CALL',3,['ARG','b'],['ARG','a']]]}
def operand(mask,a,b):
    if type(a)!=int or type(b)!=int or a not in (0,1) or b not in (0,1):
        raise ValueError('binary only')
    if mask not in SOURCE:raise ValueError('opcode not registered')
    wires=[a,b]
    for left,right in SOURCE[mask]:
        if max(left,right)>=len(wires):raise ValueError('invalid learned body')
        wires.append(1-(wires[left]&wires[right]))
    return wires[-1]
def evaluate(ast,a,b):
    if type(ast) not in (tuple,list) or len(ast) not in (2,4):raise ValueError('syntax')
    if ast[0]=='ARG' and len(ast)==2 and ast[1] in ('a','b'):
        return a if ast[1]=='a' else b
    if ast[0]=='CALL' and len(ast)==4:
        return operand(ast[1],evaluate(ast[2],a,b),evaluate(ast[3],a,b))
    raise ValueError('unapproved grammar')
def token(ast):
    return 'AUTO_'+hashlib.sha256(json.dumps(ast,sort_keys=True,separators=(',',':')).encode()).hexdigest()[:12]
class VerifiedNewOpcode:
    def __init__(self):self.registered={}
    def register(self,ast,truthmask):
        if type(truthmask)!=int or not 0<=truthmask<16:return 'UNKNOWN_SPEC'
        try:got=sum(evaluate(ast,a,b)<<(2*a+b) for a in (0,1) for b in (0,1))
        except (ValueError,TypeError,KeyError,RecursionError):return 'UNKNOWN_GRAMMAR'
        if got!=truthmask:return 'UNKNOWN_WRONG_SEMANTICS'
        label=token(ast);self.registered[label]=ast;return label
    def apply(self,label,a,b):
        if label not in self.registered:raise ValueError('unverified instruction')
        if a not in (0,1) or b not in (0,1):raise ValueError('binary')
        return evaluate(self.registered[label],a,b)
def register_frozen():
    reg=VerifiedNewOpcode();names={}
    for target,ast in NEW.items():
        label=reg.register(ast,target)
        if not label.startswith('AUTO_'):raise AssertionError(label)
        names[target]=label
    return reg,names
