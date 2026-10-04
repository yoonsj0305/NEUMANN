"""P1.7 P0: source references, complete bounded grammar, lazy coded selection.

This is a controlled-language mechanism, NOT a general semantic parser.
Unique grammar coverage is not a natural-language equivalence certificate.
No free generation, inferred numeric literal, hidden answer or retry is used.
"""
from __future__ import annotations

import re
from time import perf_counter_ns

from neumann1.control_plane_v1 import ROUTES, canonical, digest, finite, snapshot
from neumann1.control_plane_p1_contract import MODEL, validate_identity
from neumann1.control_plane_p13 import admissibility, execute_selected
from neumann1.control_plane_p14 import _routing_from_proposal
from neumann1.control_plane_p15 import Budget, number, compile_sketch
from neumann1.control_plane_p11 import CODES, CodePlan, CodedFailure, NextCodeBackend, audit_codes, plan_cost
from neumann1.control_plane_p12 import CODE_TOKEN_IDS, PERMUTATIONS, aggregate, Budget as ScoreBudget

SCHEMA = "neumann.control-plane-p1.7.p0.v1"
WORD_NUMBERS = {"one quarter":"1/4", "two thirds":"2/3", "one half":"1/2"}
LITERAL = r"(?:[+-]?(?:[0-9]+/[0-9]+|[0-9]+(?:\.[0-9]+)?)|one quarter|two thirds|one half)"
ENTITY = r"[A-Z][A-Z0-9_]{0,15}"
REL = {"equals":"EQ", "is less than":"LT", "is at most":"LE", "differs from":"NE"}
OP_WORDS = {"Start with":["START"],"Begin with":["START"],"Take":["START"],
            "Multiply":["START","MUL"],"add":["ADD"],"subtract":["SUB"],
            "divide":["DIV"],"multiply":["MUL"],"Choose":["DOMAIN"],"Assign":["DOMAIN"],
            **{word:[op] for word,op in REL.items()}}
INSTRUCTIONS = (
    "Return exact.", "Return a complete assignment.",
    "Return the exact rational value required by the original query.",
    "Return a complete assignment satisfying the original query.",
)
TAILS = ("Return the exact rational value.", "Return a complete assignment.")
MAX_CANDIDATES = 4
LEDGER_KEYS = ("input_rows", "score_rows", "scored_tokens", "evaluated_tokens", "padded_tokens", "forward_calls")


def contract():
    return {"schema":SCHEMA, "stage":"P0_SYNTHETIC_CONTRACT_ONLY", "model":dict(MODEL),
            "evidence":"query UTF-8 hash; Python Unicode codepoint half-open span; stable source-bound ID",
            "grammar":"bounded English sequential accumulator / shared-domain CSP; complete query consumption",
            "word_number_lexicon":dict(WORD_NUMBERS), "maximum_candidates":MAX_CANDIDATES,
            "ambiguity":"one It equals literal CSP clause; all declared-entity bindings enumerated or stop",
            "selection":"unique grammar candidate = zero neural; otherwise full-S4 fixed-code scoring with masks",
            "numeric_regeneration":False, "generated_calls":0, "retry":False,
            "cost_estimate_weight":0.0, "original_verifier_required":True,
            "compiler":"UNCHANGED_P1.5", "admissibility":"UNCHANGED_P1.3",
            "semantic_equivalence_proved":False, "p16_result_rescued":False,
            "actual_gemma_run":"NOT_RUN", "development_registration":"NOT_REGISTERED",
            "fresh_validation_registered":False, "p2_registration_admitted":False,
            "p2_admitted":False, "decision3_admitted":False, "global_questions_closed":[]}


def _raw_view(view):
    a = admissibility(view)
    if a["admissible_routes"] != ["DIRECT"] or not a["interpretation_required"]:
        raise ValueError("raw obligation required")
    if set(view["public"]) != {"query"} or view["instruction"] not in INSTRUCTIONS:
        raise ValueError("complete P0 instruction/query grammar only; background not discarded")
    return view["public"]["query"]


def extract_evidence(view):
    """Extract occurrences only. Repeated equal values retain distinct identities."""
    query = _raw_view(view); source = digest(view)
    tokens = []
    operators = "|".join(re.escape(s) for s in OP_WORDS)
    pattern = rf"(?<![A-Za-z0-9_./])(?P<literal>{LITERAL})(?![A-Za-z0-9_/]|\.[0-9])|\b(?P<operator>{operators})\b|\b(?P<entity>{ENTITY})\b"
    for m in re.finditer(pattern, query):
        kind = "literal" if m.group("literal") is not None else ("operator" if m.group("operator") is not None else "entity")
        surface = m.group(); normalized = WORD_NUMBERS.get(surface, surface) if kind == "literal" else (OP_WORDS[surface] if kind == "operator" else surface)
        if kind == "literal": number(normalized)
        span = [m.start(), m.end()]
        tokens.append({"id":digest([source, kind, span]), "kind":kind, "span":span,
                       "surface":surface, "value":normalized})
    if len(tokens) > 256: raise ValueError("evidence occurrence cap")
    return {"source_view_sha256":source, "query_sha256":digest(query), "tokens":tokens}


def _body(query):
    # Only prospectively registered request suffixes may be non-semantic.
    end = len(query.rstrip())
    for tail in TAILS:
        if query[:end].endswith(tail):
            end -= len(tail)
            break
    end = len(query[:end].rstrip())
    if end and query[end-1] == ".": end -= 1
    return query[:end], end


def _ref(evidence, start, end, kind):
    rows = [t for t in evidence["tokens"] if t["span"] == [start,end] and t["kind"] == kind]
    if len(rows) != 1: raise ValueError("exact source occurrence required")
    return rows[0]["id"]


def _arithmetic(query, evidence):
    body, end = _body(query)
    start = re.match(rf"(?:Start with|Begin with|Take)\s+(?P<n>{LITERAL})", body)
    atoms = []
    if start:
        atoms.append(["START", _ref(evidence,*start.span("n"),"literal")]); pos = start.end()
    else:
        start = re.match(rf"Multiply\s+(?P<a>{LITERAL})\s+by\s+(?P<b>{LITERAL})", body)
        if not start: return None
        atoms.extend([["START",_ref(evidence,*start.span("a"),"literal")],
                      ["MUL",_ref(evidence,*start.span("b"),"literal")]])
        pos = start.end()
    patterns = (
        ("ADD",rf"add\s+(?P<n>{LITERAL})(?:\s+to the quotient)?"),
        ("SUB",rf"subtract\s+(?P<n>{LITERAL})(?:\s+from the product)?"),
        ("DIV",rf"divide(?:\s+the result)?\s+by\s+(?P<n>{LITERAL})"),
        ("MUL",rf"multiply(?:\s+the result)?\s+by\s+(?P<n>{LITERAL})"),
    )
    while pos < len(body):
        separator = re.match(r"(?:\s*,\s*(?:then\s+)?|\s+then\s+|\s*;\s*(?:then\s+)?|\s*\n\s*(?:then\s+)?)",body[pos:])
        if not separator: raise ValueError("unconsumed arithmetic semantics")
        pos += separator.end(); found = False
        for op, pattern in patterns:
            m = re.match(pattern, body[pos:])
            if m:
                atoms.append([op,_ref(evidence,pos+m.start("n"),pos+m.end("n"),"literal")])
                pos += m.end(); found = True; break
        if not found: raise ValueError("unsupported arithmetic clause")
    if len(atoms) > Budget().arithmetic_operations+1: raise ValueError("arithmetic operation cap")
    return [{"route":"ARITHMETIC", "atoms":atoms, "covered_span":[0,end]}]


def _csp(query, evidence):
    body, end = _body(query)
    head = re.match(rf"(?:Choose|Assign)\s+(?P<vars>{ENTITY}(?:(?:\s*,\s*|\s+and\s+){ENTITY})*)\s+from\s+\{{(?P<vals>[^{{}}]+)\}}\.\s*",body)
    if not head: return None
    entities = [(m.group(),_ref(evidence,head.start("vars")+m.start(),head.start("vars")+m.end(),"entity"))
                for m in re.finditer(ENTITY,head.group("vars"))]
    if not 1 <= len(entities) <= Budget().csp_variables or len({x[0] for x in entities}) != len(entities):
        raise ValueError("bounded distinct declared entities required")
    if not re.fullmatch(r"\s*[+-]?[0-9]+(?:\s*,\s*[+-]?[0-9]+){0,7}\s*",head.group("vals")):
        raise ValueError("bounded integer domain evidence required")
    values = [_ref(evidence,head.start("vals")+m.start(),head.start("vals")+m.end(),"literal")
              for m in re.finditer(r"[+-]?[0-9]+",head.group("vals"))]
    if len({next(t["value"] for t in evidence["tokens"] if t["id"] == v) for v in values}) != len(values):
        raise ValueError("duplicate domain values")
    atoms = [["DOMAIN",entity,*values] for _,entity in entities]
    pos = head.end(); ambiguous = None
    relations = "|".join(re.escape(s) for s in REL)
    while pos < len(body):
        m = re.match(rf"(?P<left>{ENTITY}|It)\s+(?P<rel>{relations})\s+(?P<right>{ENTITY}|{LITERAL})",body[pos:])
        if not m: raise ValueError("unsupported or unconsumed CSP clause")
        op = REL[m.group("rel")]
        rhs_kind = "entity" if re.fullmatch(ENTITY,m.group("right")) else "literal"
        right = _ref(evidence,pos+m.start("right"),pos+m.end("right"),rhs_kind)
        if m.group("left") == "It":
            if ambiguous is not None or op != "EQ": raise ValueError("one bounded pronoun EQ ambiguity only")
            ambiguous = len(atoms); atoms.append([op,None,right])
        else:
            left = _ref(evidence,pos+m.start("left"),pos+m.end("left"),"entity")
            atoms.append([op,left,right])
        pos += m.end()
        if pos < len(body):
            separator = re.match(r"(?:\s*,\s*(?:and\s+)?|\s+and\s+|\s*\.\s+|\s*;\s*|\s*\n\s*)",body[pos:])
            if not separator: raise ValueError("unconsumed CSP semantics")
            pos += separator.end()
    if len(atoms)-len(entities) > Budget().csp_relations: raise ValueError("relation cap")
    choices = [None] if ambiguous is None else [entity for _,entity in entities]
    if len(choices) > MAX_CANDIDATES: raise ValueError("ambiguity exceeds candidate cap; do not truncate")
    candidates = []
    for entity in choices:
        copied = snapshot(atoms)
        if ambiguous is not None: copied[ambiguous][1] = entity
        candidates.append({"route":"CSP", "atoms":copied, "covered_span":[0,end]})
    return candidates


def build_candidates(view):
    query = _raw_view(view); evidence = extract_evidence(view)
    candidates = _arithmetic(query,evidence)
    if candidates is None: candidates = _csp(query,evidence)
    if not candidates: raise ValueError("outside bounded P0 grammar; no guessed fallback candidate")
    for candidate in candidates:
        candidate["operator_evidence"] = [t["id"] for t in evidence["tokens"] if t["kind"] == "operator" and t["span"][1] <= candidate["covered_span"][1]]
    # Typed compiler validates every candidate before any scoring; it cannot
    # invent domains for undeclared names or turn ambiguous parses into unique.
    for candidate in candidates: _compile(evidence,candidate)
    return {"evidence":evidence,"candidates":candidates,"bundle_sha256":digest([evidence,candidates]),
            "scope":"COMPLETE_BOUNDED_GRAMMAR_ONLY_NOT_EQUIVALENCE_PROOF"}


def _compile(evidence, candidate):
    rows = {t["id"]:t for t in evidence["tokens"]}
    atoms = []
    for atom in candidate["atoms"]:
        op = atom[0]; converted = [op]
        for i, ref in enumerate(atom[1:]):
            if ref not in rows: raise ValueError("unknown source reference")
            kind = rows[ref]["kind"]
            expected = "literal" if candidate["route"] == "ARITHMETIC" or (op == "DOMAIN" and i > 0) else "entity"
            if op != "DOMAIN" and candidate["route"] == "CSP" and i == 1: expected = kind
            if kind != expected: raise ValueError("source reference type mismatch")
            converted.append(rows[ref]["value"])
        atoms.append(converted)
    return compile_sketch({"route":candidate["route"],"atoms":atoms})


def compile_references(view, bundle, index):
    rebuilt = build_candidates(view)
    if bundle != rebuilt: raise ValueError("source, span, candidate or coverage drift")
    if type(index) is not int or not 0 <= index < len(bundle["candidates"]): raise ValueError("bounded candidate index required")
    proposal = _compile(bundle["evidence"],bundle["candidates"][index])
    proposal["certificate"].update(source_view_sha256=digest(view), bundle_sha256=bundle["bundle_sha256"],
                                   selected_candidate=index, numeric_regeneration=False,
                                   scope="Source-bound typed references; no natural-language equivalence proof")
    return proposal


def selector_prompt(view, bundle, permutation):
    if tuple(permutation) not in PERMUTATIONS or bundle != build_candidates(view): raise ValueError("fixed candidate legend required")
    # Integrity hashes are machine responsibility, not semantic evidence.
    # Compact aliases refer to exactly the same source-bound occurrences.
    aliases = {token["id"]:"e%d"%i for i,token in enumerate(bundle["evidence"]["tokens"])}
    evidence = [{"ref":aliases[t["id"]],"kind":t["kind"],"span":t["span"],
                 "surface":t["surface"],"value":t["value"]} for t in bundle["evidence"]["tokens"]]
    legend = []
    for i in range(4):
        if i < len(bundle["candidates"]):
            original = bundle["candidates"][i]
            candidate = {"route":original["route"],
                         "atoms":[[a[0],*[aliases[ref] for ref in a[1:]]] for a in original["atoms"]]}
        else: candidate = {"unavailable":True}
        legend.append({"code":CODES[permutation[i]],"interpretation":candidate})
    return ("Select the interpretation faithful to the original obligation. Return one code only. "
            "Unavailable slots cannot be chosen. References copy source evidence; never generate numbers.\n"
            +canonical({"original":view,"evidence":evidence,"legend":legend}))


def _choice(matrices, n):
    summaries = [aggregate(m) for m in matrices]
    def winner(row):
        ordered = sorted(range(n),key=lambda i:(-finite(row[i]),i))
        if row[ordered[0]]-row[ordered[1]] <= 0.5: raise ValueError("ambiguous candidate score margin")
        return ordered[0]
    choices = []
    for s in summaries:
        picked = winner([s["scores"][r] for r in ROUTES])
        if s["max_centered_loo_delta_nats"] > 0.5 or any(winner(row) != picked for row in s["loo_scores"]):
            raise ValueError("candidate permutation sensitivity")
        choices.append(picked)
    if len(set(choices)) != 1: raise ValueError("batch/order candidate disagreement")
    if max(abs(matrices[0][i][j]-m[i][j]) for m in matrices[1:] for i in range(24) for j in range(4)) > 0.05:
        raise ValueError("batch/order numerical drift")
    return choices[0]


def validate_selection(view, bundle, receipt):
    """Validate complete raw scoring and recompute decision; never trust a winner."""
    if bundle != build_candidates(view): raise ValueError("bundle drift")
    if not 2 <= len(bundle["candidates"]) <= 4: raise ValueError("selector only for ambiguous candidates")
    if receipt.get("status") != "COMPLETE" or receipt.get("bundle_sha256") != bundle["bundle_sha256"]:
        raise ValueError("partial or wrong candidate receipt")
    if receipt.get("prompt_sha256") != [digest(selector_prompt(view,bundle,p)) for p in PERMUTATIONS]:
        raise ValueError("scored prompt identity drift")
    if any(receipt.get("identity",{}).get(k) != v for k,v in MODEL.items()) or receipt.get("unchanged") is not True:
        raise ValueError("frozen core identity required")
    validate_identity(receipt["identity"])
    if type(receipt.get("generated_calls")) is not int or receipt["generated_calls"] != 0:
        raise ValueError("control generation forbidden")
    passes = receipt.get("passes",[])
    if len(passes) != 3: raise ValueError("complete batch/order passes required")
    totals = dict.fromkeys(LEDGER_KEYS,0)
    for p,(mode,size,order) in zip(passes,(("batch4",4,list(range(24))), ("unbatched1",1,list(range(24))),
                                          ("reverse_batch4",4,list(reversed(range(24)))))):
        if p.get("mode") != mode or p.get("batch_size") != size or p.get("order") != order or p.get("status") != "COMPLETE":
            raise ValueError("exact scoring execution mode required")
        if p.get("code_ids") != list(CODE_TOKEN_IDS): raise ValueError("original tokenizer codes required")
        plan = CodePlan(tuple(tuple(q) for q in p["prefixes"]),CODE_TOKEN_IDS)
        cost = plan_cost(plan,size)
        if len(plan.prefixes) != 24 or p.get("actual") != cost or p.get("planned") != cost:
            raise ValueError("complete prefix/cost coverage required")
        if type(p.get("peak_accelerator_memory_bytes")) is not int or p["peak_accelerator_memory_bytes"] <= 0:
            raise ValueError("accelerator memory receipt required")
        for k,v in cost.items(): totals[k] += v
    if totals != receipt.get("ledger") or any(v > getattr(ScoreBudget(),k) for k,v in totals.items()):
        raise ValueError("scoring ledger mismatch or cap")
    if passes[1]["prefixes"] != passes[0]["prefixes"] or passes[2]["prefixes"] != list(reversed(passes[0]["prefixes"])):
        raise ValueError("tokenized candidate prefix identity drift")
    if finite(receipt.get("complete_ms"),True) > ScoreBudget().task_wall_ms: raise ValueError("selector wall cap")
    return _choice([p["matrix"] for p in passes],len(bundle["candidates"]))


class FrozenEvidenceSelector:
    """Real frozen-core adapter; lazy caller construction, teacher forcing only.

    P0 tests inject synthetic adapters; no real Gemma result is claimed.
    All24 mappings / three execution modes are retained as a costly fallback,
    not presumed cheaper than Direct or a production optimal controller.
    """
    def __init__(self,core):
        from neumann1.control_plane_scoring_v1 import attach_frozen_gemma
        from experiments.control_plane_p1_first import forbid_generation
        self.core = core; self.identity = snapshot(core.identity)
        if any(self.identity.get(k) != v for k,v in MODEL.items()) or core.audit().get("unchanged") is not True:
            raise ValueError("original frozen core required")
        validate_identity(self.identity)
        self.counter = forbid_generation(core)
        self.encoder = attach_frozen_gemma(core).encode_prefix
        if tuple(audit_codes(core.processor.tokenizer)["token_ids"]) != CODE_TOKEN_IDS: raise ValueError("tokenizer code drift")
        self.backend = NextCodeBackend(core.model,core.processor.tokenizer.pad_token_id,core.device)

    def score(self,view,bundle,remaining_ms):
        began = perf_counter_ns(); elapsed = lambda:(perf_counter_ns()-began)/1e6
        receipt = {"status":"FAILED","bundle_sha256":bundle["bundle_sha256"],
                   "passes":[],"ledger":dict.fromkeys(LEDGER_KEYS,0)}
        try:
            prompts = [selector_prompt(view,bundle,p) for p in PERMUTATIONS]
            receipt["prompt_sha256"] = [digest(prompt) for prompt in prompts]
            prefixes = [tuple(self.encoder(prompt)) for prompt in prompts]
            for mode,size,order in (("batch4",4,list(range(24))), ("unbatched1",1,list(range(24))),
                                    ("reverse_batch4",4,list(reversed(range(24))))):
                plan = CodePlan(tuple(prefixes[i] for i in order),CODE_TOKEN_IDS)
                cost = plan_cost(plan,size)
                if any(receipt["ledger"][k]+v > getattr(ScoreBudget(),k) for k,v in cost.items()):
                    raise ValueError("selector pre-forward cost cap")
                p = {"mode":mode,"batch_size":size,"order":order,"prefixes":snapshot(plan.prefixes),
                     "code_ids":list(CODE_TOKEN_IDS),"planned":cost,"status":"STARTED"}
                receipt["passes"].append(p)
                left = min(finite(remaining_ms,True)-elapsed(),ScoreBudget().task_wall_ms-elapsed())
                if left <= 0: raise TimeoutError("selector preparation deadline")
                try: output = self.backend.evaluate(plan,size,left)
                except CodedFailure as exc:
                    p["known_partial_cost"] = snapshot(exc.known_cost)
                    for k,v in exc.known_cost.items(): receipt["ledger"][k] += v
                    raise
                for k,v in output["cost"].items(): receipt["ledger"][k] += v
                matrix = [None]*24
                for i,row in zip(order,output["scores"]): matrix[i] = snapshot(row)
                p.update(status="COMPLETE",actual=output["cost"],matrix=matrix,
                         peak_accelerator_memory_bytes=output["peak_accelerator_memory_bytes"])
            receipt["status"] = "COMPLETE"
        except Exception as exc: receipt["error"] = type(exc).__name__+": "+str(exc)
        receipt.update(identity=snapshot(self.core.identity), unchanged=self.core.identity == self.identity and self.core.audit().get("unchanged") is True,
                       generated_calls=self.counter["calls"],complete_ms=elapsed())
        return receipt


def interpret_and_execute(view,executor,original_verifier,selector_factory=None):
    began = perf_counter_ns(); elapsed = lambda:(perf_counter_ns()-began)/1e6
    result = {"schema":SCHEMA,"status":"FAILED","accepted":False,"executed":False,
              "original_view_sha256":digest(view),"selected_route":None,"model_calls":0,
              "neural_forward_calls":0,"generated_calls":0,"evaluated_tokens":0,"padded_tokens":0,
              "tool_calls":0,"verifier_calls":0,"accounting_complete":True,"error":None,
              "extraction_ms":0.0,"selection_ms":0.0,"compile_ms":0.0,"routing_ms":0.0,
              "execution_ms":0.0,"verification_ms":0.0,"proposal":None}
    try:
        start = perf_counter_ns()
        try: bundle = build_candidates(view); result["bundle"] = snapshot(bundle)
        finally: result["extraction_ms"] = (perf_counter_ns()-start)/1e6
        if len(bundle["candidates"]) == 1:
            chosen = 0; result["selection"] = "UNIQUE_COMPLETE_BOUNDED_GRAMMAR"
        elif selector_factory is None:
            result["status"] = "NEEDS_BOUNDED_SEMANTIC_SELECTION"
            result["complete_ms"] = elapsed(); return result
        else:
            start = perf_counter_ns(); result["model_calls"] = 1
            result.update(accounting_complete=False,neural_forward_calls=None,generated_calls=None,
                          evaluated_tokens=None,padded_tokens=None)
            try:
                selector = selector_factory()
                left = Budget().whole_item_wall_ms-elapsed()
                if left <= 0: raise TimeoutError("lazy selector startup deadline")
                receipt = selector.score(snapshot(view),snapshot(bundle),left)
                result["selector_receipt"] = snapshot(receipt)
                # Completed or partial work remains charged even if a semantic,
                # identity, permutation or deadline gate subsequently rejects it.
                ledger = receipt.get("ledger",{})
                for target,key in (("neural_forward_calls","forward_calls"),("evaluated_tokens","evaluated_tokens"),("padded_tokens","padded_tokens")):
                    if type(ledger.get(key)) is int and ledger[key] >= 0: result[target] = ledger[key]
                if type(receipt.get("generated_calls")) is int: result["generated_calls"] = receipt["generated_calls"]
                chosen = validate_selection(view,bundle,receipt)
                result.update(accounting_complete=True,neural_forward_calls=receipt["ledger"]["forward_calls"],
                              generated_calls=0,evaluated_tokens=receipt["ledger"]["evaluated_tokens"],
                              padded_tokens=receipt["ledger"]["padded_tokens"],selection="MASKED_FULL_S4_CANDIDATE")
            finally: result["selection_ms"] = (perf_counter_ns()-start)/1e6
        result["selected_candidate"] = chosen
        start = perf_counter_ns()
        try: proposal = compile_references(view,bundle,chosen); result["proposal"] = snapshot(proposal)
        finally: result["compile_ms"] = (perf_counter_ns()-start)/1e6
        start = perf_counter_ns(); typed,routed = _routing_from_proposal(view,proposal)
        result["routing_ms"] = (perf_counter_ns()-start)/1e6
        result["selected_route"] = routed["selected_route"]
        if elapsed() >= Budget().whole_item_wall_ms: raise TimeoutError("item deadline before executor")
        def execute(route,project):
            result["tool_calls"] += 1; start = perf_counter_ns()
            try: return executor(route,project)
            finally: result["execution_ms"] += (perf_counter_ns()-start)/1e6
        def verify(_typed,answer):
            result["verifier_calls"] += 1; start = perf_counter_ns()
            try: return original_verifier(snapshot(view),answer)
            finally: result["verification_ms"] += (perf_counter_ns()-start)/1e6
        execution = execute_selected(typed,routed,execute,verify); result["execution"] = snapshot(execution)
        result.update(accepted=execution["accepted"],executed=execution["executed"],
                      status="ACCEPTED" if execution["accepted"] else ("EXECUTION_FAILED" if execution.get("error") else "REJECTED_BY_ORIGINAL_VERIFIER"))
        if elapsed() >= Budget().whole_item_wall_ms:
            result.update(accepted=False,status="FAILED"); raise TimeoutError("complete item deadline")
    except Exception as exc: result["error"] = type(exc).__name__+": "+str(exc)
    result["complete_ms"] = elapsed()
    return result


def replay_semantics(view,record,original_verifier):
    """Model-free decision/answer check. Timings require separate raw accounting.

    Returns semantic consistency, not archive integrity or economic evidence.
    It neither invokes a selector nor runs an executor or changes the verdict.
    """
    if record.get("status") not in ("ACCEPTED","REJECTED_BY_ORIGINAL_VERIFIER") or record.get("accounting_complete") is not True:
        raise ValueError("semantic-only replay requires a complete gated execution record")
    if record.get("original_view_sha256") != digest(view): raise ValueError("original view drift")
    bundle = build_candidates(view)
    if record.get("bundle") != bundle: raise ValueError("archived evidence/candidates drift")
    chosen = 0 if len(bundle["candidates"]) == 1 else validate_selection(view,bundle,record["selector_receipt"])
    if record.get("selected_candidate") != chosen or record.get("proposal") != compile_references(view,bundle,chosen):
        raise ValueError("cached choice or compiler result drift")
    if record.get("selected_route") != record["proposal"]["route"]: raise ValueError("route drift")
    execution = record.get("execution",{})
    accepted = original_verifier(snapshot(view),snapshot(execution.get("answer"))) if execution.get("executed") and "answer" in execution else False
    if type(accepted) is not bool or accepted != record.get("accepted") or accepted != execution.get("accepted"):
        raise ValueError("original verifier result drift")
    return {"semantic_consistency":True,"accepted":accepted,"archive_integrity_checked":False,
            "cost_replayed":False,"historical_result_rescued":False}
