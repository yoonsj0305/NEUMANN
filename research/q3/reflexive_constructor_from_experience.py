"""Q3: produce an EXECUTABLE CONSTRUCTOR PROGRAM from two verified examples.

The meta-kernel includes only:
 - generic typed AST evaluation (fold, empty_like, append, branch, member);
 - AST anti-unification (structure -> parameterized code);
 - search of small set-expression ASTs to induce a parameter binder.
The constructor IS an AST which takes I/O examples and RETURNS a new
executable program AST. It is not a manually registered target filter.

Previous verified CodeARC ASTs are SOURCE EXPERIENCE and do not include
MBPP task-specific answers. The two original source tasks have simple
symbol-removal implementations; thus this is a scope-limited mechanistic
proof, NOT unrestricted inventive intelligence or a novel theory.
"""
from __future__ import annotations
from hashlib import sha256
import json

def canonical(obj):
    return json.dumps(obj,sort_keys=True,separators=(",",":"),ensure_ascii=True)

def ident(obj):
    return sha256(canonical(obj).encode()).hexdigest()[:16]

def run_body(ast,arg, *, env=None):
    """Safe bounded interpreter. No eval, exec, arbitrary imports or I/O."""
    if env is None:env={}
    tag=ast[0]
    if tag=="arg":return arg[ast[1]]
    if tag=="acc":return env["acc"]
    if tag=="item":return env["item"]
    if tag=="constant":return ast[1]
    if tag=="empty_like":
        v=run_body(ast[1],arg,env=env)
        if type(v) not in (str,list,tuple):raise ValueError("UNSUPPORTED_SEQUENCE_TYPE")
        return type(v)()
    if tag=="member":
        token=run_body(ast[1],arg,env=env)
        options=run_body(ast[2],arg,env=env)
        return token in options
    if tag=="if":
        return run_body(ast[2] if run_body(ast[1],arg,env=env)
                        else ast[3],arg,env=env)
    if tag=="append":
        seq=run_body(ast[1],arg,env=env)
        item=run_body(ast[2],arg,env=env)
        if type(seq) is str and type(item) is str and len(item)==1:
            return seq+item
        if type(seq) is list:return seq+[item]
        if type(seq) is tuple:return seq+(item,)
        raise ValueError("INVALID_APPEND")
    if tag=="fold":
        xs=run_body(ast[1],arg,env=env)
        if type(xs) not in (str,list,tuple) or len(xs)>1024:
            raise ValueError("BOUNDED_SEQUENCE_REQUIRED")
        acc=run_body(ast[2],arg,env=env)
        for item in xs:
            acc=run_body(ast[3],arg,env={"acc":acc,"item":item})
            if type(acc) not in (str,list,tuple) or len(acc)>1024:
                raise ValueError("OUTPUT_CAP")
        return acc
    raise ValueError("UNKNOWN_AST_OPCODE")

def execute_safe(ast,args):
    try:return True,run_body(ast,args)
    except (ValueError,TypeError,IndexError,KeyError,RecursionError):
        return False,None

def compile_verified_source_filter(old):
    """One-time interface adapter from #712's previously VERIFIED AST into IR.

    This bridge is HUMAN-AUTHORED and does NOT invent the source family.
    Do not misrepresent its existence as a novel computational primitive.
    """
    if old.get("kind")!="DerivedSequenceFilter" or old.get("source_arg")!=0:
        raise ValueError("UNSUPPORTED_SOURCE_PROGRAM")
    removed=old.get("removed")
    if not isinstance(removed,list):raise ValueError("BAD_SOURCE_TYPE")
    return [
        "fold",["arg",0],["empty_like",["arg",0]],
        ["if",
            ["member",["item"],["constant",removed]],
            ["acc"],
            ["append",["acc"],["item"]]]
    ]

def antiunify(a,b,holes):
    if a==b:return a
    if (type(a) is list and type(b) is list and len(a)==len(b)
            and a and b and a[0]==b[0]):
        return [antiunify(x,y,holes) for x,y in zip(a,b)]
    pair=(canonical(a),canonical(b))
    if pair not in holes:holes[pair]=len(holes)
    return ["hole",holes[pair]]

def fill(template,values):
    if type(template) is list:
        if len(template)==2 and template[0]=="hole":
            return values[template[1]]
        return [fill(x,values) for x in template]
    return template

def atoms_of(x):
    if type(x) is str:return list(x)
    if type(x) in (list,tuple):
        if all(type(e) in (int,bool,float,str) for e in x):
            return list(x)
    raise ValueError("UNSUPPORTED_TOKEN_CONTAINER")

def meta_eval(ast,examples):
    """Reusable programs for synthesizing candidate program PARAMETERS."""
    tag=ast[0]
    if tag=="tokens":
        k=ast[1];index=ast[2]
        bucket=[]
        for args,y in examples:
            source=args[index] if k=="input" else y
            bucket.extend(atoms_of(source))
        return sorted(set(bucket),key=lambda v:repr(v))
    if tag=="minus":
        a=meta_eval(ast[1],examples);b=meta_eval(ast[2],examples)
        return [x for x in a if x not in b]
    if tag=="intersect":
        a=meta_eval(ast[1],examples);b=meta_eval(ast[2],examples)
        return [x for x in a if x in b]
    if tag=="union":
        a=meta_eval(ast[1],examples);b=meta_eval(ast[2],examples)
        return sorted(set(a+b),key=lambda x:repr(x))
    if tag=="literal":
        return ast[1]
    raise ValueError("UNKNOWN_META_OPCODE")

def candidate_binders():
    input_tokens=["tokens","input",0]
    output_tokens=["tokens","output",0]
    # Search candidates are GENERIC set algebra over observations,
    # not domain-specific 'characters-to-delete' named functions.
    atoms=[input_tokens,output_tokens,["literal",[]]]
    candidates=list(atoms)
    for a in atoms[:2]:
        for b in atoms[:2]:
            for op in ("minus","intersect","union"):
                candidates.append([op,a,b])
    return sorted(candidates,key=lambda x:(len(canonical(x)),canonical(x)))

def fit_sources(experiences):
    """Infer a NEW program-generating function, not a target answer."""
    if len(experiences)<2:raise ValueError("NEED_TWO_SEPARATE_SOURCES")
    program_asts=[compile_verified_source_filter(e["verified_program"])
                  for e in experiences]
    holes={}
    template=antiunify(program_asts[0],program_asts[1],holes)
    if len(holes)!=1:raise ValueError("NO_UNIQUE_PROGRAM_GENERALIZATION")
    hole_num=next(iter(holes.values()))
    if hole_num!=0:raise ValueError("BAD_HOLE")
    solution=None;audits=[]
    for meta in candidate_binders():
        applies=[]
        for experience in experiences:
            examples=experience["train_io"]
            try:
                value=meta_eval(meta,examples)
                candidate=fill(template,[["constant",value]])
                ok=all(execute_safe(candidate,args)==(True,y)
                       for args,y in examples)
            except (TypeError,ValueError):
                ok=False
            applies.append(ok)
        audits.append({"binder":meta,"source_consistency":applies})
        if all(applies) and solution is None:
            solution=meta
    if solution is None:raise ValueError("NO_GENERALIZED_BINDER")
    learned={
        "kind":"DefineRepresentationConstructor",
        "symbol":"invented_constructor_"+ident([template,solution]),
        "constructor_program":{
            "type":"MapObservedIOToExecutableAST",
            "parameter_binder":solution,
            "template":template,
            "hole_count":1},
        "source_programs":[e["id"] for e in experiences],
        "source_train_examples":[len(e["train_io"]) for e in experiences],
        "relative_new_constructor":True,
        "human_supplied_generic_kernel":True,
    }
    return learned,audits

def construct(learned,examples):
    if learned.get("kind")!="DefineRepresentationConstructor":
        return None
    try:
        binder=learned["constructor_program"]["parameter_binder"]
        subst=meta_eval(binder,examples)
        ast=fill(learned["constructor_program"]["template"],
                 [["constant",subst]])
        if not all(execute_safe(ast,args)==(True,y)
                   for args,y in examples):
            return None
        return ast
    except (TypeError,ValueError,IndexError,KeyError,RecursionError):
        return None
