"""Source-bound mathematical goal, order and termination certification.

A deliberately small first-order constructor fragment. It proves that the
source representation function flattens ordered CNil/Single/Concat trees,
instead of assuming this from its name. It does not certify OCaml overflow,
arbitrary effects, source attributes, or a lifted original hole skeleton.
"""
from dataclasses import dataclass
from copy import deepcopy
from itertools import product, permutations
import re

from neumann1.recursive_summary import SummaryError, identity, check_summary, program
from neumann1.typed_fold_projection import project, uncomment


class ProtocolError(SummaryError): pass


@dataclass(frozen=True)
class Symbol:
    kind: str
    word: tuple
    size: object = None


class ConstructorParser:
    def __init__(self, text, functions, variables):
        pattern = r"[A-Za-z_][A-Za-z_0-9]*|[(),]"
        tokens = re.findall(pattern, text)
        if re.sub(pattern, "", text).strip(): raise ProtocolError("Unsupported representation syntax")
        self.tokens, self.i, self.functions, self.variables = tokens, 0, functions, variables

    def take(self, expected=None):
        if self.i >= len(self.tokens): raise ProtocolError("Incomplete constructor expression")
        value = self.tokens[self.i]; self.i += 1
        if expected is not None and value != expected: raise ProtocolError("Constructor punctuation mismatch")
        return value

    def expression(self, depth=0):
        if depth > 32: raise ProtocolError("Constructor expression depth exceeded")
        token = self.take()
        if token == "(":
            value = self.expression(depth+1); self.take(")"); return value
        if token in {"Nil", "CNil"}: return (token,)
        if token in {"Cons", "Concat"}:
            self.take("("); a = self.expression(depth+1); self.take(",")
            b = self.expression(depth+1); self.take(")"); return (token, a, b)
        if token == "Single": return (token, self.expression(depth+1))
        if token in self.functions:
            args = tuple(self.expression(depth+1) for _ in range(self.functions[token]["arity"]))
            return ("call", token, args)
        if token in self.variables: return ("variable", token)
        raise ProtocolError("Unresolved constructor variable or call")

    def complete(self):
        result = self.expression()
        if self.i != len(self.tokens): raise ProtocolError("Unconsumed constructor syntax")
        return result


def declarations(clean):
    matches = list(re.finditer(r"^(?:let\s+rec|and)\s+(\w+)\s*([^=\n]*?)=\s*", clean, re.M))
    definitions = {}
    for i, match in enumerate(matches):
        name, parameters = match.groups()
        if name in definitions: raise ProtocolError("Repeated recursive declaration")
        params = parameters.split()
        if any(not p.isidentifier() for p in params): continue
        body = clean[match.end():matches[i+1].start() if i+1<len(matches) else len(clean)]
        end = re.search(r";;|\[@@|\bassert\s*\(",body)
        source_end=match.end()+(end.start() if end else len(body))
        body = body[:end.start() if end else len(body)].strip()
        definitions[name] = {"params":params,"body":body,"arity":len(params)+(body.startswith("function")),
                             "wrapper":not body.startswith("function"),"body_source_start":match.end(),"body_source_end":source_end}
    return definitions


def parse_representation(clean, name):
    all_defs = declarations(clean)
    if name not in all_defs: raise ProtocolError("Assertion representation declaration missing")
    # Reachability follows referenced declared identifiers, not file/name labels.
    required, pending = {}, [name]
    while pending:
        current = pending.pop()
        if current in required: continue
        if current not in all_defs: raise ProtocolError("Missing representation helper")
        definition = all_defs[current]
        if not 1 <= definition["arity"] <= 2: raise ProtocolError("Only unary/binary tree-to-list helpers supported")
        required[current] = definition
        identifiers = set(re.findall(r"\b\w+\b", definition["body"]))
        pending += sorted((identifiers & set(all_defs))-set(definition["params"])-set(required))
        if len(required)+len(pending) > 16: raise ProtocolError("Representation call graph budget exceeded")
    if len(required) > 8 or required[name]["arity"] != 1: raise ProtocolError("Bounded unary representation required")
    for current, definition in required.items():
        params = definition["params"]
        if len(params) != len(set(params)): raise ProtocolError("Unique representation parameters required")
        if definition["wrapper"]:
            expression = ConstructorParser(definition["body"], required, set(params)).complete()
            definition["clauses"] = [{"constructor":None,"names":[],"expression":expression}]
        else:
            chunks = definition["body"][len("function"):].strip().split("|")
            clauses = []
            for chunk in chunks:
                if not chunk.strip(): continue
                match = re.fullmatch(r"\s*(CNil|Single|Concat)\s*(.*?)\s*->\s*([\s\S]+)", chunk)
                if not match: raise ProtocolError("Representation requires exhaustive supported tree constructors")
                constructor, pattern, body = match.groups()
                names = re.findall(r"[A-Za-z_]\w*", pattern)
                residue = re.sub(r"[A-Za-z_]\w*|[(),\s]", "", pattern)
                expected = {"CNil":0,"Single":1,"Concat":2}[constructor]
                if residue or len(names)!=expected or len(set(names+params))!=len(names+params):
                    raise ProtocolError("Constructor pattern binding mismatch")
                expression = ConstructorParser(body, required, set(params+names)).complete()
                clauses.append({"constructor":constructor,"names":names,"expression":expression})
            if sorted(c["constructor"] for c in clauses) != ["CNil","Concat","Single"]:
                raise ProtocolError("Exactly one clause per tree constructor required")
            definition["clauses"] = clauses
    return required


def wrapper_ranks(functions):
    ranks, active = {}, set()
    def rank(name):
        if name in ranks: return ranks[name]
        if name in active: raise ProtocolError("Cyclic nondecreasing representation wrappers")
        if not functions[name]["wrapper"]: ranks[name]=0; return 0
        active.add(name)
        expression = functions[name]["clauses"][0]["expression"]
        def calls(term):
            if term[0]=="call": return [term[1]]+[n for a in term[2] for n in calls(a)]
            return [n for a in term[1:] if isinstance(a, tuple) for n in calls(a)]
        destinations = calls(expression)
        value = 1+max([rank(n) for n in destinations]+[0])
        active.remove(name); ranks[name]=value; return value
    for name in functions: rank(name)
    return ranks


def clause_environment(definition, clause):
    import z3
    env = {p:Symbol("Tree",("tree:"+p,),z3.Int("size_"+p)) for p in definition["params"]}
    sizes = [v.size for v in env.values()]
    names, constructor = clause["names"], clause["constructor"]
    if constructor is None: return env, list(env.values()), [s>=1 for s in sizes]
    if constructor == "CNil": current = Symbol("Tree",(),z3.IntVal(1))
    elif constructor == "Single":
        env[names[0]] = Symbol("Head",("head:"+names[0],))
        current = Symbol("Tree",env[names[0]].word,z3.IntVal(1))
    else:
        for n in names: env[n]=Symbol("Tree",("tree:"+n,),z3.Int("size_"+n)); sizes.append(env[n].size)
        current = Symbol("Tree",env[names[0]].word+env[names[1]].word,1+env[names[0]].size+env[names[1]].size)
    return env, [env[p] for p in definition["params"]]+[current], [s>=1 for s in sizes]


def symbolic_expression(expression, env, orders, calls):
    import z3
    tag = expression[0]
    if tag == "variable": return env[expression[1]]
    if tag == "CNil": return Symbol("Tree",(),z3.IntVal(1))
    if tag == "Nil": return Symbol("List",())
    if tag == "Single":
        h = symbolic_expression(expression[1],env,orders,calls)
        if h.kind!="Head": raise ProtocolError("Single requires an unchanged head")
        return Symbol("Tree",h.word,z3.IntVal(1))
    if tag in {"Cons","Concat"}:
        a, b = [symbolic_expression(t,env,orders,calls) for t in expression[1:]]
        if tag == "Cons":
            if (a.kind,b.kind)!=("Head","List"): raise ProtocolError("Cons requires head and list")
            return Symbol("List",a.word+b.word)
        if (a.kind,b.kind)!=("Tree","Tree"): raise ProtocolError("Concat requires two trees")
        return Symbol("Tree",a.word+b.word,1+a.size+b.size)
    if tag == "call":
        name, terms = expression[1:]
        args = [symbolic_expression(t,env,orders,calls) for t in terms]
        if any(a.kind!="Tree" for a in args): raise ProtocolError("Representation calls require tree arguments")
        calls.append((name,args))
        return Symbol("List",tuple(atom for i in orders[name] for atom in args[i].word))
    raise ProtocolError("Unsupported constructor")


def prove_flatten(functions, root):
    import z3
    ranks = wrapper_ranks(functions)
    names = sorted(functions)
    choices = [list(permutations(range(functions[n]["arity"]))) for n in names]
    attempts = 0
    for candidate in product(*choices):
        attempts += 1
        if attempts > 256: raise ProtocolError("Bounded word specification search exceeded")
        orders = dict(zip(names,candidate)); records=[]; clause_records=[]; valid=True
        for name in names:
            for clause in functions[name]["clauses"]:
                env, args, assumptions = clause_environment(functions[name],clause)
                calls=[]
                actual = symbolic_expression(clause["expression"],env,orders,calls)
                expected = tuple(atom for i in orders[name] for atom in args[i].word)
                if actual.kind != "List" or actual.word != expected: valid=False; break
                clause_records.append({"function":name,"constructor":clause["constructor"],
                                       "word_actual":list(actual.word),"word_expected":list(expected)})
                for destination, values in calls:
                    total = sum(a.size for a in args); next_total=sum(a.size for a in values)
                    current_active, next_active = args[-1].size, values[-1].size
                    decreases = z3.Or(next_total<total,
                        z3.And(next_total==total,next_active<current_active),
                        z3.And(next_total==total,next_active==current_active,z3.BoolVal(ranks[destination]<ranks[name])))
                    solver=z3.Solver();solver.set(timeout=2000)
                    solver.add(*assumptions,z3.Not(decreases)); status=solver.check()
                    if status!=z3.unsat: valid=False; break
                    records.append({"function":name,"constructor":clause["constructor"],"callee":destination,
                                    "word_actual":list(actual.word),"word_expected":list(expected),
                                    "termination_status":str(status),"termination_smt2":solver.to_smt2()})
                if not valid: break
            if not valid: break
        if valid:
            return {"accepted":True,"specifications":{n:list(orders[n]) for n in names},"wrapper_ranks":ranks,
                    "proof_records":records,"clause_records":clause_records,"specification_candidates":attempts,
                    "theorem":"all finite ordered constructor trees: source representation returns their left-to-right word; total-node/active-node/wrapper-rank lexicographic descent"}
    raise ProtocolError("No universally ordered terminating representation specification")


def source_binding(source):
    if not isinstance(source,str) or len(source)>100000: raise ProtocolError("Bounded source required")
    clean=uncomment(source)
    if re.search(r'^\s*(?:open|include|module|external|exception)\b',clean,re.M):
        raise ProtocolError('Unsupported top-level binding or environment change')
    if re.search(r'^(?:let\s+rec|and)\s+(?:max|min|abs|not)\b',clean,re.M):
        raise ProtocolError('Standard scalar primitive shadowing unsupported')
    types=re.findall(r'^\s*type\s+\x27a\s+(\w+)\s*=\s*([\s\S]*?)(?=^\s*(?:type|let|assert)\b)',clean,re.M)
    matches_tree=[];matches_list=[]
    for name,body in types:
        normalized=re.sub(r'\s+',' ',body).strip().strip(';').strip()
        tree=r'(?:\| )?CNil \| Single of \x27a \| Concat of \x27a '+re.escape(name)+r' \* \x27a '+re.escape(name)
        linked=r'(?:\| )?Nil \| Cons of \x27a \* \x27a '+re.escape(name)
        if re.fullmatch(tree,normalized):matches_tree.append(name)
        if re.fullmatch(linked,normalized):matches_list.append(name)
    if len(matches_tree)!=1 or len(matches_list)!=1 or len(types)!=2 or len(re.findall(r'^\s*type\b',clean,re.M))!=2:
        raise ProtocolError('Exactly the supported polymorphic tree and linked-list ADTs required')
    for pattern in re.findall(r'\blet\s+(?:rec\s+)?(\([^=]*?\)|\w+(?:\s*,\s*\w+)*)\s*=',clean):
        if set(re.findall(r'\w+',pattern)) & {'max','min','abs','not'}:
            raise ProtocolError('Local standard scalar primitive shadowing unsupported')
    assertions=re.findall(r"\bassert\s*\(([^)]*)\)",clean)
    if len(assertions)!=1: raise ProtocolError("One explicit source synthesis assertion required")
    match=re.fullmatch(r"\s*(\w+)\s*=\s*(\w+)\s*@@\s*(\w+)\s*",assertions[0])
    if not match: raise ProtocolError("Supported target = representation @@ reference assertion required")
    target, representation, reference=match.groups()
    defs=declarations(clean)
    if reference not in defs:raise ProtocolError('Asserted source reference missing')
    source_ref=defs[reference]
    for occurrence in re.finditer(r'^\s*let(?!\s+rec\b)\s+',clean,re.M):
        if not source_ref['body_source_start']<=occurrence.start()<source_ref['body_source_end']:
            raise ProtocolError('Unsupported top-level nonrecursive binding')
    for pattern in re.findall(r'\blet\s+(\([^=]*?\)|\w+(?:\s*,\s*\w+)*)\s*=',source_ref['body']):
        if reference in re.findall(r'\w+',pattern):raise ProtocolError('Local recursive reference shadowing unsupported')
    projection=project(source)
    if projection["reference_function"]!=reference: raise ProtocolError("Projected helper is not the asserted source goal")
    functions=parse_representation(clean,representation)
    proof=prove_flatten(functions,representation)
    if target not in defs: raise ProtocolError("Source target missing")
    selected=defs[target]
    if selected["wrapper"]:
        if len(selected["params"])!=1: raise ProtocolError("Unsupported target wrapper")
        alias=re.fullmatch(r"(\w+)\s+(\w+)",selected["body"])
        if not alias or alias[2]!=selected["params"][0] or alias[1] not in defs: raise ProtocolError("Only unchanged unary target aliases supported")
        target_skeleton=alias[1];selected=defs[target_skeleton]
    else: target_skeleton=target
    if selected["params"]: raise ProtocolError("Parameterized target skeleton unsupported")
    body=re.sub(r"\s+"," ",selected["body"]).strip()
    skeleton=(r"function (?:\| )?CNil -> \[%synt (\w+)\] \| Single\s*\(?(\w+)\)? -> \[%synt (\w+)\] (\w+) "
              r"\| Concat\s*\(\s*(\w+)\s*,\s*(\w+)\s*\) -> \[%synt (\w+)\] "
              r"\("+re.escape(target_skeleton)+r" (\w+)\) \("+re.escape(target_skeleton)+r" (\w+)\)")
    m=re.fullmatch(skeleton,body)
    if not m: raise ProtocolError("Target is outside unchanged CNil/Single/ordered Concat hole skeleton")
    base,leaf,single,argument,left,right,merge,a,b=m.groups()
    if argument!=leaf or (a,b)!=(left,right): raise ProtocolError("Source target changes constructor arguments or order")
    if len({base,single,merge})!=3: raise ProtocolError("Distinct source synthesis holes required")
    return {"source_sha256":__import__('hashlib').sha256(source.encode()).hexdigest(),"projection":projection,
            "assertion":{"target":target,"representation":representation,"reference":reference},
            "reference_definition":deepcopy(source_ref),
            "target_skeleton":target_skeleton,"holes":{"empty":base,"singleton":single,"merge":merge},
            "representation_functions":functions,"flatten_proof":proof,
            "scope":"asserted pure source fragment with mathematical integers and explicitly encoded Boolean heads/goals; attributes, effects and OCaml overflow not certified"}


def certify_source_summary(source, proposal):
    binding=source_binding(source)
    public=binding["projection"]["public"]
    cert=check_summary(public,proposal)
    if not cert["accepted"]: return {"accepted":False,"status":"SUMMARY_NOT_CERTIFIED","binding":binding,"certificate":cert}
    width=len(public["empty"]); latent=len(proposal["empty"])
    outputs=proposal["decode"]["outputs"]; names=proposal["decode"]["inputs"]
    # An invertible state permutation lets the same original holes store the
    # original output width. Added state requires an explicit changed engine.
    indices=[names.index(t) if isinstance(t,str) and t in names else None for t in outputs]
    same_skeleton=latent==width and sorted(i for i in indices if i is not None)==list(range(width))
    return {"accepted":True,"status":"SOURCE_BOUND_MATHEMATICAL_GOAL_CERTIFIED","binding":binding,"certificate":cert,
            "proposal_sha256":identity(proposal),"original_hole_skeleton_implementable":same_skeleton,
            "requires_added_or_changed_internal_state":not same_skeleton,
            "machine_OCaml_execution_certified":False,"official_benchmark_score":False,"fresh_eligible":0,"learning_performed":False}


class SourceBoundDagEngine:
    """The decoded source goal on DAGs, subject to the stated fragment scope."""
    def __init__(self, source, proposal):
        from neumann1.recursive_dag import CertifiedDagSummary
        self._certificate=certify_source_summary(source,proposal)
        if not self._certificate['accepted']:raise ProtocolError('Source goal was not certified')
        self._binding=identity(self._certificate)
        self._engine=CertifiedDagSummary(self._certificate['binding']['projection']['public'],proposal)

    @property
    def certificate(self):return deepcopy(self._certificate)

    def run(self,dag,**budgets):
        if identity(self._certificate)!=self._binding:raise ProtocolError('Source fragment binding changed')
        result=self._engine.run_dag(dag,**budgets)
        result['source_sha256']=self._certificate['binding']['source_sha256']
        result['source_assertion']=deepcopy(self._certificate['binding']['assertion'])
        result['source_scope']=self._certificate['binding']['scope']
        result['original_hole_skeleton_implementable']=self._certificate['original_hole_skeleton_implementable']
        return result
