"""Opened-data admission screen; reference equations never solve raw text."""

from __future__ import annotations

import ast
import hashlib
import json
import platform
import random
import re
from collections import Counter, defaultdict
from fractions import Fraction
from pathlib import Path
from statistics import median
from time import perf_counter_ns

SOURCE_REF = "78e727689e1c1bebfc4be39c446898e8e10b0518"
SOURCE_BLOB = "aad093525105c6331581d7082250b9c22578271e"
MAX_CHARS, MAX_NODES, MAX_DIGITS, MAX_BITS = 512, 127, 18, 4096
REPEATS, TIMING_SEED = 9, 7801
MIN_GAIN_FRACTION, MIN_REDUCTION, MIN_DIRECT_MS = 1 / 3, 0.20, 1.0
NUMBER = re.compile(r"(?:\d+(?:\.\d+)?|\.\d+)")
OPS = {ast.Add: "+", ast.Sub: "-", ast.Mult: "*", ast.Div: "/"}


class Unsupported(ValueError):
    pass


def bounded(value: Fraction) -> Fraction:
    if max(value.numerator.bit_length(), value.denominator.bit_length()) > MAX_BITS:
        raise Unsupported("rational arithmetic budget")
    return value


def literal(token: str) -> Fraction:
    if not NUMBER.fullmatch(token) or sum(c.isdigit() for c in token) > MAX_DIGITS:
        raise Unsupported("literal outside fixed grammar/budget")
    return bounded(Fraction(token))


def parse_program(expression: str) -> tuple:
    if not isinstance(expression, str) or not expression or len(expression) > MAX_CHARS:
        raise Unsupported("expression length/type")
    expression = expression.strip()
    try:
        tree = ast.parse(expression, mode="eval")
    except (SyntaxError, ValueError, RecursionError) as exc:
        raise Unsupported("invalid expression") from exc
    if sum(1 for _ in ast.walk(tree)) > MAX_NODES:
        raise Unsupported("AST node budget")

    def build(node):
        if isinstance(node, ast.Constant) and type(node.value) in (int, float):
            token = ast.get_source_segment(expression, node)
            value = literal(token)
            return ("LIT", value.numerator, value.denominator)
        if isinstance(node, ast.BinOp) and type(node.op) in OPS:
            return (OPS[type(node.op)], build(node.left), build(node.right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in (ast.UAdd, ast.USub):
            return ("POS" if isinstance(node.op, ast.UAdd) else "NEG", build(node.operand))
        raise Unsupported("untrusted expression construct")

    return build(tree.body)


def execute(program: tuple, *, share: bool) -> tuple[Fraction, int]:
    memo, operation_count = {}, 0

    def visit(node):
        nonlocal operation_count
        if share and node in memo:
            return memo[node]
        op = node[0]
        if op == "LIT":
            value = Fraction(node[1], node[2])
        elif op in ("POS", "NEG"):
            a = visit(node[1]); value = a if op == "POS" else -a
            operation_count += 1
        else:
            a, b = visit(node[1]), visit(node[2])
            if op == "+": value = a + b
            elif op == "-": value = a - b
            elif op == "*": value = a * b
            elif op == "/":
                if not b: raise Unsupported("division by zero")
                value = a / b
            else: raise Unsupported("untrusted opcode")
            operation_count += 1
        value = bounded(value)
        if share: memo[node] = value
        return value

    answer = visit(program)
    return answer, operation_count


def independent_expression_value(expression: str) -> Fraction:
    """Separate token/precedence parser; does not consume AST/program output."""
    if not isinstance(expression, str) or not expression or len(expression) > MAX_CHARS:
        raise Unsupported("reference expression length/type")
    tokens = re.findall(r"\d+(?:\.\d+)?|\.\d+|[()+*/-]", expression)
    if "".join(tokens) != re.sub(r"\s", "", expression) or len(tokens) > MAX_NODES:
        raise Unsupported("reference token grammar/budget")
    index = 0

    def check(value):
        if value.numerator.bit_length() > MAX_BITS or value.denominator.bit_length() > MAX_BITS:
            raise Unsupported("reference arithmetic budget")
        return value

    def atom():
        nonlocal index
        if index >= len(tokens): raise Unsupported("missing reference operand")
        token = tokens[index]; index += 1
        if token in ("+", "-"):
            value = atom(); return check(value if token == "+" else -value)
        if token == "(":
            value = expression_at(0)
            if index >= len(tokens) or tokens[index] != ")":
                raise Unsupported("unclosed reference parentheses")
            index += 1; return value
        if token in ("*", "/", ")") or sum(c.isdigit() for c in token) > MAX_DIGITS:
            raise Unsupported("invalid reference literal")
        return check(Fraction(token))

    def expression_at(minimum):
        nonlocal index
        value = atom()
        precedence = {"+": 1, "-": 1, "*": 2, "/": 2}
        while index < len(tokens) and precedence.get(tokens[index], -1) >= minimum:
            op = tokens[index]; index += 1
            right = expression_at(precedence[op] + 1)
            if op == "+": value = value + right
            elif op == "-": value = value - right
            elif op == "*": value = value * right
            else:
                if right == 0: raise Unsupported("reference zero denominator")
                value = value / right
            value = check(value)
        return value

    answer = expression_at(0)
    if index != len(tokens): raise Unsupported("unused reference tokens")
    return answer


def observable_input(row: dict) -> str:
    """Only this projection may enter any future learned path."""
    if not all(isinstance(row.get(key), str) for key in ("Body", "Question")):
        raise Unsupported("observable text fields")
    return row["Body"] + " " + row["Question"]


def digest(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def observe(row: dict) -> dict:
    text = observable_input(row)
    answer = {"id": row["ID"], "observable_sha256": digest(text),
              "reference_sha256": digest(row["Equation"])}
    try:
        program = parse_program(row["Equation"])
        reference = independent_expression_value(row["Equation"])
        direct, dops = execute(program, share=False)
        shared, sops = execute(program, share=True)
        if direct != reference or shared != reference:
            raise RuntimeError("independent expression check disagreement")
        label = Fraction(str(row["Answer"]))
        if direct == label: status = "EXACT_MATCH"
        elif abs(direct - label) <= Fraction(1, 10**9): status = "ROUNDING_ONLY"
        else: status = "LABEL_DISAGREEMENT"
        values = [literal(m.group()) for m in NUMBER.finditer(text)]
        leaves = []
        def gather(node):
            if node[0] == "LIT": leaves.append(Fraction(node[1], node[2]))
            else:
                for child in node[1:]: gather(child)
        gather(program)
        answer.update(status=status, program_sha256=digest(program),
                      direct_ops=dops, shared_ops=sops,
                      operation_reduction=(dops-sops)/dops if dops else 0.0,
                      original_expression_verified=True,
                      exact_value=[direct.numerator, direct.denominator],
                      label_value=[label.numerator, label.denominator],
                      ungrounded_literal_values=sum(v not in values for v in leaves),
                      ambiguous_literal_values=sum(values.count(v)>1 for v in leaves))
    except (Unsupported, ZeroDivisionError, OverflowError, RecursionError) as exc:
        answer.update(status="UNSUPPORTED", reason=str(exc), original_expression_verified=False)
    return answer


def timed_path(expression: str, *, share: bool) -> float:
    start = perf_counter_ns()
    program = parse_program(expression)
    value, _ = execute(program, share=share)
    checked = independent_expression_value(expression)
    if value != checked: raise RuntimeError("timed path verification disagreement")
    return (perf_counter_ns()-start)/1e6


def admission(summary: dict) -> str:
    ok = (summary["exact_label_and_expression_rate"] == 1.0
          and summary["gain_incidence"] >= MIN_GAIN_FRACTION
          and summary["median_direct_ms"] >= MIN_DIRECT_MS)
    return "INVESTIGATE_NUMERIC_COMPRESSION_TARGET" if ok else "REJECT_SVAMP_NUMERIC_COMPRESSION_TARGET"


def run_audit(path: str | Path) -> dict:
    raw = Path(path).read_bytes()
    blob = hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
    if blob != SOURCE_BLOB: raise ValueError("source blob mismatch")
    source = json.loads(raw)
    if len(source) != 1000 or len({x["ID"] for x in source}) != len(source):
        raise ValueError("source row count/identity mismatch")
    observations = [observe(row) for row in source]
    valid = [i for i, row in enumerate(observations) if row["original_expression_verified"]]
    # One frozen local audit; repeats alternate method order and retain every sample.
    rng = random.Random(TIMING_SEED)
    for row in observations:
        row["direct_ms"] = []; row["shared_ms"] = []
    for repeat in range(REPEATS):
        order = list(valid); rng.shuffle(order)
        for index in order:
            methods = (("direct", False), ("shared", True))
            if (repeat+index)%2: methods = tuple(reversed(methods))
            for name, share in methods:
                observations[index][name+"_ms"].append(timed_path(source[index]["Equation"],share=share))
    bodies = defaultdict(list)
    for row, observation in zip(source, observations):
        if observation["status"] == "EXACT_MATCH":
            bodies[row["Body"]].append(observation)
    collisions = [{"body_sha256": digest(body), "ids": [r["id"] for r in rows],
                   "distinct_programs":len({r["program_sha256"] for r in rows})}
                  for body, rows in bodies.items()
                  if len({r["program_sha256"] for r in rows}) > 1]
    times = [median(observations[i]["direct_ms"]) for i in valid]
    summary = {
        "rows":len(source), "statuses":dict(Counter(r["status"] for r in observations)),
        "exact_label_and_expression_rate":sum(r["status"]=="EXACT_MATCH" for r in observations)/len(source),
        "operation_histogram":dict(sorted(Counter(observations[i]["direct_ops"] for i in valid).items())),
        "gain_rows":sum(observations[i]["operation_reduction"]>=MIN_REDUCTION for i in valid),
        "gain_incidence":sum(observations[i]["operation_reduction"]>=MIN_REDUCTION for i in valid)/len(source),
        "median_direct_ms":median(times) if times else None,
        "median_shared_ms":median(median(observations[i]["shared_ms"]) for i in valid) if valid else None,
        "body_collision_groups":len(collisions),
        "ungrounded_literal_rows":sum(observations[i]["ungrounded_literal_values"]>0 for i in valid),
        "ambiguous_literal_rows":sum(observations[i]["ambiguous_literal_values"]>0 for i in valid),
        "timed_paths":len(valid)*REPEATS*2,
        "learned_parameters":0,
        "raw_word_problem_solve_rate":None,
    }
    summary["decision"] = admission(summary) if times else "REJECT_UNSUPPORTED_SOURCE"
    return {"experiment":"v0.0.78 opened SVAMP numeric-program screen",
            "source":{"repository":"arkilpatel/SVAMP", "ref":SOURCE_REF,"blob":blob,
                      "sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw),"license":"MIT",
                      "exposure":"all rows opened development only"},
            "protocol":{"repeats":REPEATS,"timing_seed":TIMING_SEED,"min_gain_fraction":MIN_GAIN_FRACTION,
                        "min_operation_reduction":MIN_REDUCTION,"min_direct_ms":MIN_DIRECT_MS},
            "environment":{"python":platform.python_version(),"platform":platform.platform()},
            "summary":summary,"body_collisions":collisions,"rows":observations}
