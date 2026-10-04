"""P1.5 semantic atoms -> deterministic exact compiler -> original verifier.

Successful compilation certifies grammar/typing and accumulator order only.
It does not certify that learned atoms preserve the natural-language obligation.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from fractions import Fraction
import re
from time import perf_counter_ns

from neumann1.control_plane_v1 import canonical, digest, finite, snapshot
from neumann1.control_plane_p1_contract import MODEL
from neumann1.control_plane_p13 import admissibility, execute_selected
from neumann1.control_plane_p14 import _clean_generation, _routing_from_proposal
from neumann1.general_runtime_v106 import sha as core_digest

SCHEMA = "neumann.control-plane-p1.5.v1"
OPS = {"ADD":"+", "SUB":"-", "MUL":"*", "DIV":"/"}
RELATIONS = ("LT", "LE", "EQ", "NE")


@dataclass(frozen=True)
class Budget:
    semantic_model_calls: int = 1
    semantic_output_tokens: int = 192
    context_tokens: int = 4096
    semantic_wall_ms: float = 120000.0
    whole_item_wall_ms: float = 180000.0
    sketch_bytes: int = 8192
    arithmetic_operations: int = 15
    csp_variables: int = 9
    csp_relations: int = 128


def contract():
    return {"schema":SCHEMA,"model":dict(MODEL),"budget":asdict(Budget()),
            "wire":"ARITHMETIC START/ADD/SUB/MUL/DIV numeric atoms END; CSP DOMAIN/LT/LE/EQ/NE atoms END; ABSTAIN",
            "numeric_atoms":"bounded signed integer, rational n/d or decimal string; exact Fraction, no binary floats",
            "execution_ir_generated_by_model":False,"compiler_scope":"syntactic validity, exact literals and ordered accumulator composition; no natural-language equivalence proof",
            "original_verifier_required":True,"retry_after_failure":False,
            "parent_admissibility":"UNCHANGED_P1.3","mixed_fallback":"UNCHANGED_NOT_RERUN_IN_THIS_STUDY",
            "new_training":False,"frontier_calls":0,"sealed_data_opened":False,
            "p14_result_rescued":False,"development_only":True,"fresh_validation_registered":False,
            "p2_registration_admitted":False,"p2_admitted":False,"decision3_admitted":False,
            "global_questions_closed":[]}


def number(token):
    if type(token) is not str or len(token)>32 or not re.fullmatch(r"[+-]?(?:[0-9]+(?:\.[0-9]+)?|[0-9]+/[0-9]+)",token):
        raise ValueError("bounded exact numeric atom required")
    value=Fraction(token)
    if abs(value.numerator)>10**12 or value.denominator>10**12:
        raise ValueError("exact numeric atom exceeds P1.3 integer bounds")
    return value


def _name(value):
    if type(value) is not str or not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{0,31}",value):
        raise ValueError("bounded variable atom required")
    return value


def _integer(token):
    if not re.fullmatch(r"[+-]?[0-9]+",token): raise ValueError("CSP integer atom required")
    return int(number(token))


def parse_sketch(raw):
    if type(raw) is not str or len(raw.encode())>Budget().sketch_bytes: raise ValueError("bounded sketch required")
    text=_clean_generation(raw)
    lines=[line.split() for line in text.splitlines() if line.strip()]
    if lines==[["ABSTAIN"]]: return {"route":"ABSTAIN","atoms":[]}
    if len(lines)<3 or lines[0] not in (["ARITHMETIC"],["CSP"]) or lines[-1]!=["END"]:
        raise ValueError("exact sketch header and terminal END required")
    route=lines[0][0]; atoms=lines[1:-1]
    if route=="ARITHMETIC":
        if not 1<=len(atoms)<=Budget().arithmetic_operations+1 or len(atoms[0])!=2 or atoms[0][0]!="START":
            raise ValueError("one START followed by bounded ordered arithmetic atoms required")
        for i,atom in enumerate(atoms):
            if len(atom)!=2 or atom[0] not in (("START",) if i==0 else OPS): raise ValueError("invalid arithmetic atom")
            number(atom[1])
    else:
        if len(atoms)>Budget().csp_variables+Budget().csp_relations: raise ValueError("CSP sketch atom cap")
        for atom in atoms:
            if not atom or atom[0] not in (("DOMAIN",)+RELATIONS): raise ValueError("unsupported CSP atom")
            if atom[0]=="DOMAIN":
                if not 3<=len(atom)<=10: raise ValueError("DOMAIN name and 1..8 integers required")
                _name(atom[1])
                for token in atom[2:]: _integer(token)
            else:
                if len(atom)!=3: raise ValueError("relation requires exactly left and right atoms")
                _name(atom[1])
                if re.fullmatch(r"[+-]?[0-9]+",atom[2]): _integer(atom[2])
                else: _name(atom[2])
    return {"route":route,"atoms":snapshot(atoms)}


def compile_sketch(sketch):
    # Reparse the exact typed atom wire; arbitrary caller-supplied dictionaries
    # cannot bypass the same syntax gate used for generated text.
    if type(sketch) is not dict or set(sketch)!={"route","atoms"}: raise ValueError("exact typed sketch fields required")
    if sketch["route"]=="ABSTAIN":
        if sketch["atoms"]!=[]: raise ValueError("ABSTAIN cannot smuggle atoms")
        return {"route":"ABSTAIN"}
    wire=sketch["route"]+"\n"+"\n".join(" ".join(a) for a in sketch["atoms"])+"\nEND"
    checked=parse_sketch(wire)
    if checked!=sketch: raise ValueError("canonical typed atom mismatch")
    if sketch["route"]=="ARITHMETIC":
        def literal(token):
            n=number(token)
            return str(n.numerator) if n.denominator==1 else "(%d/%d)"%(n.numerator,n.denominator)
        expression=literal(sketch["atoms"][0][1])
        for op,token in sketch["atoms"][1:]: expression="("+expression+OPS[op]+literal(token)+")"
        public={"expression":expression,"bindings":{}}
    else:
        domains={}; constraints=[]; seen_relation=False
        for atom in sketch["atoms"]:
            if atom[0]=="DOMAIN":
                if seen_relation or atom[1] in domains: raise ValueError("unique domains must precede relations")
                domains[atom[1]]=[_integer(t) for t in atom[2:]]
            else:
                seen_relation=True
                right=_integer(atom[2]) if re.fullmatch(r"[+-]?[0-9]+",atom[2]) else atom[2]
                constraints.append([atom[0].lower(),atom[1],right])
        public={"domains":domains,"constraints":constraints}
    typed={"instruction":"Compiler type check only.","public":public}
    a=admissibility(typed)
    if a["admissible_routes"]!=[sketch["route"]] or a["interpretation_required"] is not False:
        raise ValueError("compiled atoms do not satisfy unchanged P1.3 contract")
    return {"route":sketch["route"],"public":snapshot(public),
            "certificate":{"sketch_sha256":digest(sketch),"public_sha256":digest(public),
                           "scope":contract()["compiler_scope"],"natural_language_equivalence_proved":False}}


def semantic_prompt(view):
    a=admissibility(view)
    if a["admissible_routes"]!=["DIRECT"] or a["interpretation_required"] is not True or set(view["public"])-{"query","background"}:
        raise ValueError("original raw stopped state required")
    return ("Identify a minimal semantic sketch of the original problem. Do not solve it. "
            "Do not write JSON, executable expressions, code, or explanations. Output only one sketch.\n"
            "For an exact sequential scalar calculation: first line ARITHMETIC; next START number; "
            "then one ADD number, SUB number, MUL number or DIV number per step, in the original order; last END. "
            "Numbers may be signed integers, exact fractions like 1/4, or exact decimals like 0.25. "
            "Every operation applies to the entire current accumulator.\n"
            "For finite integer constraints: first line CSP; declare every variable as DOMAIN name value value ...; "
            "then one LT left right, LE left right, EQ left right or NE left right per relation; last END. "
            "right is a declared variable or integer; declare domains before relations.\n"
            "If the full obligation cannot be expressed faithfully with these atoms, output ABSTAIN alone.\n"
            +canonical(view))


class SketchProposalFailure(RuntimeError):
    def __init__(self,message,receipt):
        super().__init__(message); self.receipt=snapshot(receipt)


def validate_receipt(receipt):
    if type(receipt.get("raw")) is not str or receipt.get("raw_sha256")!=digest(receipt["raw"]): raise ValueError("raw generation identity required")
    for k in ("input_tokens","output_tokens"):
        if type(receipt.get(k)) is not int or receipt[k]<0: raise ValueError("completed token accounting required")
    if receipt["input_tokens"]==0 or receipt["input_tokens"]>Budget().context_tokens or receipt["output_tokens"]>Budget().semantic_output_tokens:
        raise ValueError("semantic context/output budget drift")
    if max(finite(receipt.get("generation_ms"),True),finite(receipt.get("complete_ms"),True))>Budget().semantic_wall_ms:
        raise ValueError("semantic wall budget drift")
    if receipt.get("deadline_reached") is not False: raise ValueError("semantic generation deadline reached")
    if type(receipt.get("peak_accelerator_memory_bytes")) is not int or receipt["peak_accelerator_memory_bytes"]<=0:
        raise ValueError("semantic VRAM accounting required")
    identity=receipt.get("identity",{})
    if any(identity.get(k)!=v for k,v in MODEL.items()) or receipt.get("core_sha256")!=core_digest(identity) or receipt.get("identity_unchanged") is not True:
        raise ValueError("semantic core identity drift")
    return True


class FrozenSketchCompiler:
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
       "compile_ms":None,"routing_ms":None,"execution_ms":0.0,"verification_ms":0.0}
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
            sketch=parse_sketch(receipt["raw"]); r["sketch"]=sketch
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
