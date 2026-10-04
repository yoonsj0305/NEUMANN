"""P1.6 semantic hypothesis -> finite surface normalization -> unchanged compiler.

Normalization uses generated text alone. It cannot repair meaning or consult the
original query. A narrowed candidate is only a hypothesis; the original verifier
checks the complete original single-witness obligation.
"""
from time import perf_counter_ns
import re

from neumann1.control_plane_v1 import canonical, digest, finite, snapshot
from neumann1.control_plane_p1_contract import MODEL
from neumann1.control_plane_p13 import admissibility, execute_selected
from neumann1.control_plane_p14 import _clean_generation, _routing_from_proposal
from neumann1.control_plane_p15 import (
    Budget, number, _name, _integer, parse_sketch as strict_parse_sketch,
    compile_sketch, validate_receipt, SketchProposalFailure, contract as parent_contract,
)
from neumann1.general_runtime_v106 import sha as core_digest

SCHEMA = "neumann.control-plane-p1.6.v1"
SYMBOLS = {"<":"LT", "<=":"LE", "=":"EQ", "==":"EQ", "!=":"NE", "≤":"LE", "≠":"NE"}
RELATIONS = ("LT","LE","EQ","NE")
RESERVED = {"DOMAIN","CSP","ARITHMETIC","ABSTAIN","END","START","ADD","SUB","MUL","DIV",*RELATIONS}
NAME = r"[A-Za-z][A-Za-z0-9_]{0,31}"
INTEGER = r"[+-]?[0-9]+"
FENCE = chr(96)*3
NORMALIZER_RULES = {
    "domain":"DOMAIN name integers; name integers; DOMAIN/name {comma-separated integers}",
    "relation":"prefix or infix LT/LE/EQ/NE (case-insensitive operator only); < <= = == != ≤ ≠",
    "wrapping":"known channel delimiters; optional text/csp/arithmetic/plain code fence",
    "preserved":"variable identity/case, literal values, operand order, relation order and candidate domain membership",
    "rejected":"reserved variable names, chained/unsupported operators, undeclared names, duplicate declarations, prose/comments, domain after relation",
    "semantic_additions":False,
}


def contract():
    c=parent_contract()
    c.update(schema=SCHEMA,wire="bounded semantic hypothesis; arithmetic P1.5 atoms; finite CSP surface alternatives",
             normalizer_rules=snapshot(NORMALIZER_RULES),
             normalizer_source_obligation_access=False,normalizer_semantic_repair=False,
             parent_canonical_compiler="UNCHANGED_P1.5",
             candidate_narrowing_allowed=True,
             candidate_scope="one complete assignment satisfying the original existential CSP obligation; no enumeration or uniqueness claim",
             original_solution_set_equivalence_required=False,
             candidate_subset_proved=False,original_verifier_required=True,
             p15_result_rescued=False)
    return c


def _variable(token):
    _name(token)
    if token.upper() in RESERVED: raise ValueError("reserved or ambiguous variable atom")
    return token


def _operator(token):
    if token.upper() in RELATIONS: return token.upper()
    return SYMBOLS.get(token)


def _operand(token):
    if re.fullmatch(INTEGER,token): _integer(token)
    else: _variable(token)
    return token


def _clean_surface(raw):
    if type(raw) is not str or len(raw.encode())>Budget().sketch_bytes:
        raise ValueError("bounded hypothesis text required")
    text=raw.strip()
    for marker in ("<|channel>final","<channel|>"):
        if marker in text: text=text.rsplit(marker,1)[-1].strip()
    for token in ("<turn|>","<eos>","<|end|>"): text=text.replace(token,"")
    lines=[line.strip() for line in text.splitlines() if line.strip()]
    if lines and lines[0].startswith(FENCE):
        if lines[0].lower() not in (FENCE,FENCE+"text",FENCE+"csp",FENCE+"arithmetic") or len(lines)<3 or lines[-1]!=FENCE:
            raise ValueError("unsupported hypothesis wrapper")
        lines=lines[1:-1]
    if any(FENCE in line for line in lines): raise ValueError("unbalanced hypothesis wrapper")
    if len(lines)>160: raise ValueError("hypothesis line cap")
    return lines


def _domain(line):
    prefix=re.match(r"DOMAIN\s+",line,re.IGNORECASE)
    explicit=prefix is not None
    body=line[prefix.end():].strip() if explicit else line
    match=re.fullmatch("("+NAME+r")\s+(.+)",body)
    if not match: return None
    variable,values=match.groups()
    if values.startswith("{") or values.endswith("}"):
        if not re.fullmatch(r"\{\s*"+INTEGER+r"\s*(?:,\s*"+INTEGER+r"\s*)*\}",values):
            raise ValueError("exact integer brace domain required")
        tokens=[x.strip() for x in values[1:-1].split(",")]
        rule="domain_braces"
    else:
        tokens=values.split()
        if not tokens or not all(re.fullmatch(INTEGER,x) for x in tokens):
            if explicit: raise ValueError("exact integer domain values required")
            return None
        rule="domain_space"
    _variable(variable)
    if not 1<=len(tokens)<=8: raise ValueError("bounded candidate domain required")
    for token in tokens: _integer(token)
    return ["DOMAIN",variable,*tokens],rule


def _relation(line):
    tokens=line.split()
    if len(tokens)==3 and _operator(tokens[0]):
        op,left,right=_operator(tokens[0]),tokens[1],tokens[2]; rule="relation_prefix"
    elif len(tokens)==3 and _operator(tokens[1]):
        left,op,right=tokens[0],_operator(tokens[1]),tokens[2]; rule="relation_infix"
    else:
        match=re.fullmatch("("+NAME+r")\s*(<=|==|!=|<|=|≤|≠)\s*("+INTEGER+"|"+NAME+")",line)
        if not match: raise ValueError("unsupported or ambiguous CSP surface")
        left,symbol,right=match.groups(); op=SYMBOLS[symbol]; rule="relation_symbol"
    _variable(left); _operand(right)
    return [op,left,right],rule


def normalize_hypothesis(raw):
    """Finite, single-parse surface conversion; no original input parameter."""
    lines=_clean_surface(raw)
    trace=[]
    if lines==["ABSTAIN"]:
        wire="ABSTAIN"
    elif lines and lines[0]=="ARITHMETIC":
        # Preserve the already successful arithmetic grammar exactly.
        wire="\n".join(lines); strict_parse_sketch(wire)
        trace=[{"rule":"arithmetic_identity","surface":"\n".join(lines),"atoms":None}]
    else:
        if len(lines)<3 or lines[0]!="CSP" or lines[-1]!="END":
            raise ValueError("exact hypothesis header and END required")
        atoms=[]; seen_relation=False
        for index,line in enumerate(lines[1:-1],start=2):
            result=_domain(line)
            if result is not None:
                if seen_relation: raise ValueError("candidate domains must precede relations")
                atom,rule=result
            else:
                atom,rule=_relation(line); seen_relation=True
            atoms.append(atom); trace.append({"line":index,"surface":line,"rule":rule,"atom":atom})
        wire="CSP\n"+"\n".join(" ".join(atom) for atom in atoms)+"\nEND"
    sketch=strict_parse_sketch(wire)
    return {"schema":"neumann.p16-normalization.v1","source_raw_sha256":digest(raw),
            "normalized_wire":wire,"normalized_sha256":digest(wire),"sketch":sketch,
            "trace":trace,"semantic_choices_added":False,"source_obligation_consulted":False,
            "candidate_subset_proved":False,"original_solution_set_equivalence_proved":False}


def parse_sketch(raw):
    return normalize_hypothesis(raw)["sketch"]


def semantic_prompt(view):
    a=admissibility(view)
    if a["admissible_routes"]!=["DIRECT"] or a["interpretation_required"] is not True or set(view["public"])-{"query","background"}:
        raise ValueError("original raw stopped state required")
    return ("Identify one compact semantic hypothesis for the original problem. "
            "Do not write JSON, executable expressions, code or explanations. Output only the hypothesis.\n"
            "For an exact sequential scalar calculation: ARITHMETIC, START number, then ADD/SUB/MUL/DIV number "
            "one per step in original order, then END. Each step applies to the whole accumulator. "
            "Use exact integers, rational fractions or decimals.\n"
            "For a finite CSP: first CSP, last END. Declare every assignment variable and a nonempty "
            "finite integer candidate domain, then relations. Domains may use DOMAIN X 0 1, X 0 1, "
            "or X {0,1}. Relations may use LT/LE/EQ/NE X Y, X LT/LE/EQ/NE Y, "
            "or X <, <=, =, ==, != Y. Keep operands in their stated order. "
            "You may narrow domains, including singleton values, to propose a complete candidate. "
            "No proof that all original solutions are preserved is requested; the original constraints "
            "still govern the final answer. Do not claim that a guessed candidate is verified.\n"
            "If unsupported or no useful hypothesis can be formed, output ABSTAIN alone.\n"+canonical(view))


class FrozenHypothesisCompiler:
    def __init__(self,core):
        self.core=core; self.identity=snapshot(core.identity)
        if any(self.identity.get(k)!=v for k,v in MODEL.items()) or core.audit().get("unchanged") is not True:
            raise ValueError("exact frozen core required")

    def propose(self,view,remaining_ms):
        prompt=semantic_prompt(view); left=finite(remaining_ms,True)
        if left<=0: raise TimeoutError("no semantic generation time")
        began=perf_counter_ns()
        generated=self.core.generate([{"role":"user","content":prompt}],Budget().semantic_output_tokens,False,min(left,Budget().semantic_wall_ms))
        receipt={k:generated.get(k) for k in ("raw","input_tokens","output_tokens","generation_ms","deadline_reached","peak_accelerator_memory_bytes","core_sha256")}
        receipt.update(raw_sha256=digest(receipt["raw"]) if type(receipt["raw"]) is str else None,
                       complete_ms=(perf_counter_ns()-began)/1e6,identity=snapshot(self.core.identity),
                       identity_unchanged=self.core.identity==self.identity and self.core.audit().get("unchanged") is True)
        try: validate_receipt(receipt)
        except Exception as exc: raise SketchProposalFailure(type(exc).__name__+": "+str(exc),receipt) from exc
        return receipt


def interpret_and_execute(view,compiler,executor,original_verifier):
    began=perf_counter_ns(); elapsed=lambda:(perf_counter_ns()-began)/1e6
    r={"schema":SCHEMA,"status":"FAILED","accepted":False,"executed":False,"selected_route":None,
       "sketch":None,"proposal":None,"original_view_sha256":digest(view),"model_calls":0,
       "input_tokens":None,"output_tokens":None,"tool_calls":0,"verifier_calls":0,
       "accounting_complete":False,"semantic_budget_valid":False,"error":None,
       "normalization":None,"normalization_ms":None,"compile_ms":None,"routing_ms":None,"execution_ms":0.0,"verification_ms":0.0}
    try:
        semantic_prompt(view)
        left=lambda:Budget().whole_item_wall_ms-elapsed()
        r["model_calls"]=1
        receipt=compiler.propose(snapshot(view),left())
        r["semantic_receipt"]=snapshot(receipt)
        r["input_tokens"]=receipt.get("input_tokens"); r["output_tokens"]=receipt.get("output_tokens")
        validate_receipt(receipt)
        # A charged, completed generation remains charged even if atoms or
        # strict canonical compilation fail. Candidate validity is separate.
        r["accounting_complete"]=True; r["semantic_budget_valid"]=True
        start=perf_counter_ns()
        try:
            normalized=normalize_hypothesis(receipt["raw"]); r["normalization"]=normalized
        finally: r["normalization_ms"]=(perf_counter_ns()-start)/1e6
        start=perf_counter_ns()
        try:
            sketch=normalized["sketch"]; r["sketch"]=sketch
            proposal=compile_sketch(sketch); r["proposal"]=proposal
        finally: r["compile_ms"]=(perf_counter_ns()-start)/1e6
        if proposal["route"]=="ABSTAIN": r["status"]="ABSTAINED"
        else:
            start=perf_counter_ns(); typed,routed=_routing_from_proposal(view,proposal)
            r["routing_ms"]=(perf_counter_ns()-start)/1e6
            r["selected_route"]=routed["selected_route"]; r["typed_view_sha256"]=digest(typed)
            if left()<=0: raise TimeoutError("semantic item deadline before execution")
            def execute(route,project):
                r["tool_calls"]+=1; start=perf_counter_ns()
                try: return executor(route,project)
                finally: r["execution_ms"]+=(perf_counter_ns()-start)/1e6
            def verify(_typed,answer):
                r["verifier_calls"]+=1; start=perf_counter_ns()
                try: return original_verifier(snapshot(view),answer)
                finally: r["verification_ms"]+=(perf_counter_ns()-start)/1e6
            execution=execute_selected(typed,routed,execute,verify); r["execution"]=snapshot(execution)
            r["executed"]=execution["executed"]; r["accepted"]=execution["accepted"]
            r["status"]="ACCEPTED" if r["accepted"] else ("EXECUTION_FAILED" if execution.get("error") else "REJECTED_BY_ORIGINAL_VERIFIER")
        if left()<=0:
            r["accepted"]=False; r["status"]="FAILED"; r["semantic_budget_valid"]=False
            raise TimeoutError("complete semantic item deadline exceeded")
    except SketchProposalFailure as exc:
        r["semantic_receipt"]=snapshot(exc.receipt)
        r["input_tokens"]=exc.receipt.get("input_tokens"); r["output_tokens"]=exc.receipt.get("output_tokens")
        r["error"]=type(exc).__name__+": "+str(exc)
    except Exception as exc:
        r["error"]=type(exc).__name__+": "+str(exc)
    r["complete_ms"]=elapsed()
    return r
