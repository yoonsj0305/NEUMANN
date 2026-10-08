"""Parse a small explicit ML integer-fold subset; never execute upstream code.

Only the first Nil/Cons reference function is projected,not the whole OCaml
program,representation function,requires clauses or Synduce synthesis protocol.
Integers follow mathematical SMT semantics,not machine-int overflow.
"""
import re
from neumann1.recursive_summary import SummaryError, program, validate_problem


def uncomment(source):
    result=[]
    i,depth=0,0
    while i<len(source):
        if source[i:i+2]=="(*":depth+=1;i+=2
        elif source[i:i+2]=="*)":
            if depth==0:raise SummaryError("Unmatched ML comment")
            depth-=1;i+=2
        else:
            if depth==0:result.append(source[i])
            i+=1
    if depth:raise SummaryError("Unterminated ML comment")
    return "".join(result)


def reference_projection(source):
    source=uncomment(source)
    match=re.search(r"let\s+rec\s+(\w+)\s*=\s*function\s*\|\s*Nil\s*->\s*([\s\S]*?)\|\s*Cons\s*\(hd,\s*tl\)\s*->\s*([\s\S]*?)(?=\[@@|;;)",source)
    if not match:raise SummaryError("Unsupported ML fold declaration")
    name,empty_text,body=match.groups()
    if not re.fullmatch(r"\s*-?\d+\s*(?:,\s*-?\d+\s*)*",empty_text):
        raise SummaryError("Constant integer reference base required")
    empty=[int(t.strip()) for t in empty_text.split(",")]
    tokens=[]
    while body.strip():
        match=re.match(r"\s*(\d+|[A-Za-z_]\w*|[(),+\-=])",body)
        if not match:raise SummaryError("Unsupported ML reference syntax")
        tokens.append(match[1]);body=body[match.end():]
    cursor=0
    env={"hd":"head"}
    def peek():return tokens[cursor] if cursor<len(tokens) else None
    def take(expected=None):
        nonlocal cursor
        token=peek()
        if token is None or (expected is not None and token!=expected):
            raise SummaryError("Incomplete ML reference or unexpected token")
        cursor+=1
        return token
    def atom():
        token=take()
        if token.isdigit():return int(token)
        if token=="-":return ["sub",0,atom()]
        if token=="(":
            value=values();take(")");return value
        if token in {"max","min"}:
            return [token,atom(),atom()]
        if token==name:
            take("tl")
            refs=tuple(f"r{i}" for i in range(len(empty)))
            return refs[0] if len(refs)==1 else refs
        if token not in env:raise SummaryError("Unknown ML reference variable or call")
        return env[token]
    def expression():
        value=atom()
        while peek() in {"+","-"}:
            op=take()
            if isinstance(value,tuple):raise SummaryError("Tuple used as arithmetic")
            rhs=atom()
            if isinstance(rhs,tuple):raise SummaryError("Tuple used as arithmetic")
            value=["add" if op=="+" else "sub",value,rhs]
        return value
    def values():
        value=expression()
        if peek()!=",":return value
        items=[value]
        while peek()==",":take(",");items.append(expression())
        return tuple(items)
    while peek()=="let":
        take("let")
        parenthesized=peek()=="("
        if parenthesized:take("(")
        bindings=[take()]
        while peek()==",":take(",");bindings.append(take())
        if parenthesized:take(")")
        take("=")
        value=values();take("in")
        items=list(value) if isinstance(value,tuple) else [value]
        if len(items)!=len(bindings):raise SummaryError("Reference destructuring width mismatch")
        for key,item in zip(bindings,items):
            if not key.isidentifier() or key in env:raise SummaryError("Unsupported ML binding")
            env[key]=item
    value=values()
    if cursor!=len(tokens):raise SummaryError("Unconsumed ML reference syntax")
    outputs=list(value) if isinstance(value,tuple) else [value]
    public={"semantics":"integer_list_right_fold", "empty":empty,
            "step":program(["head"]+[f"r{i}" for i in range(len(empty))],outputs)}
    validate_problem(public)
    return public
