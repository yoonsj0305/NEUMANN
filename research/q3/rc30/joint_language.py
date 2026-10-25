"""RC30: extracted runnable two-opcode / learnt accumulator syntax.
The human gave a TWO-STATE FOREACH interpreter and four-row Boolean table
class. Actual learned PyTorch 9 scalar weights and frozen first predictions
are in independently reproduced conversation ZIP, not this compact file.
"""
import hashlib,re
FROZEN={
 "all_equal":{"compare":[1,0,0,1],"reduce":[0,0,0,1],"init":1},
 "any_equal":{"compare":[0,1,1,0],"reduce":[1,0,1,1],"init":0},
}
def name(table):
    if len(table)!=4 or any(type(b)!=int or b not in (0,1) for b in table):
        raise ValueError("bad Boolean table")
    return "OP_"+hashlib.sha256(bytes(table)).hexdigest()[:12]
def emit(code):
    a,b=name(code['compare']),name(code['reduce'])
    if code['init'] not in (0,1):raise ValueError("initial")
    return "\n".join((f"DEFINE {a} "+''.join(map(str,code['compare'])),
                      f"DEFINE {b} "+''.join(map(str,code['reduce'])),
                      f"INITIAL {code['init']}",f"EACH_PAIR {a} {b}",
                      "EMIT","END"))+"\n"
def parse(source):
    if type(source)!=str or len(source)>500:raise ValueError("size")
    lines=source.splitlines()
    if len(lines)!=6:raise ValueError("length")
    matches=[re.fullmatch(r"DEFINE (OP_[a-f0-9]{12}) ([01]{4})",line)
             for line in lines[:2]]
    if any(a is None for a in matches):raise ValueError("definitions")
    if not re.fullmatch("INITIAL [01]",lines[2]):raise ValueError("init")
    if lines[3]!=f"EACH_PAIR {matches[0][1]} {matches[1][1]}":
        raise ValueError("bindings")
    if lines[4:]!=["EMIT","END"]:raise ValueError("termination")
    tables=[[int(z) for z in a[2]] for a in matches]
    if any(name(table)!=entry[1] for table,entry in zip(tables,matches)):
        raise ValueError("sha identity mismatch")
    return {"compare":tables[0],"reduce":tables[1],"init":int(lines[2][-1])}
def run(code,x,y):
    if len(x)!=len(y):raise ValueError("width")
    s=code['init']
    for a,b in zip(x,y):
        if a not in (0,1) or b not in (0,1):raise ValueError("binary")
        s=code['reduce'][2*s+code['compare'][2*a+b]]
    return s
def prove(code,task):
    if task not in FROZEN:return "UNKNOWN_TASK"
    init_goal=1 if task=="all_equal" else 0
    initial=(code['init'],init_goal)
    work=[initial];seen={initial}
    while work:
        s,g=work.pop()
        if s!=g:return "FAIL"
        for a in (0,1):
            for b in (0,1):
                lhs=code['reduce'][2*s+code['compare'][2*a+b]]
                rhs=(g&int(a==b)) if task=="all_equal" else (g|int(a==b))
                pair=(lhs,rhs)
                if pair not in seen:seen.add(pair);work.append(pair)
    return "SCOPED_ALL_FINITE_LENGTHS"
def authorize(source,task):
    try:code=parse(source)
    except (ValueError,KeyError,TypeError):return "UNKNOWN_BAD_GRAMMAR"
    return "SCOPED_CERTIFIED" if prove(code,task)=="SCOPED_ALL_FINITE_LENGTHS" else "UNKNOWN_UNPROVED"
