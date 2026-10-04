"""Opened P1.4 semantic-development catalog frozen before model scores.

Eight raw natural-language items require semantic compilation (four arithmetic,
four finite CSP). Four mixed typed items exercise the unchanged P1.3 masked
full-S4 fallback. Private references never enter controller/model inputs.
"""
from neumann1.control_plane_v1 import snapshot


def catalog():
    rows = []
    refs = []

    def add(view, kind, family, private, witness, expected_route):
        task_id = "p14d_%02d" % (len(rows) + 1)
        rows.append({"task_id": task_id, "view": view})
        refs.append({
            "task_id": task_id,
            "kind": kind,
            "family": family,
            "private": private,
            "witness": witness,
            "expected_route": expected_route,
        })

    raw_math = (
        ("Take 18, subtract 5, multiply the result by 3, then divide by 13. Return the exact rational value.", "3"),
        ("Divide 21 by 7, add 5 to the result, then multiply by 4. Return the exact rational value.", "32"),
        ("Subtract 2 from 11, divide that result by 3, then add one half. Return the exact rational value.", "7/2"),
        ("Multiply 8 by 5, subtract 6, then divide by 17. Return the exact rational value.", "2"),
    )
    for query, exact in raw_math:
        add(
            {"instruction": "Return the exact rational value required by the original query.",
             "public": {"query": query}},
            "RAW_SEMANTIC", "math_logic", {"exact": exact}, exact, "ARITHMETIC"
        )

    raw_csp = (
        (
            "Choose integer values A, B, C from {0,1,2} such that A is less than B and B is less than C. Return a complete assignment.",
            {"A": [0,1,2], "B": [0,1,2], "C": [0,1,2]},
            [["lt","A","B"],["lt","B","C"]],
            {"A":0,"B":1,"C":2},
        ),
        (
            "Choose X and Y from {1,2,3}. X must equal 1 and X must differ from Y. Return a complete assignment.",
            {"X":[1,2,3],"Y":[1,2,3]},
            [["eq","X",1],["ne","X","Y"]],
            {"X":1,"Y":2},
        ),
        (
            "Assign P, Q, R from {0,1,2,3}. P equals 0, P is less than Q, and Q is less than R. Return a complete assignment.",
            {"P":[0,1,2,3],"Q":[0,1,2,3],"R":[0,1,2,3]},
            [["eq","P",0],["lt","P","Q"],["lt","Q","R"]],
            {"P":0,"Q":1,"R":2},
        ),
        (
            "Assign A, B, C, D from {0,1}. A differs from B, B equals C, and C differs from D. Return a complete assignment.",
            {"A":[0,1],"B":[0,1],"C":[0,1],"D":[0,1]},
            [["ne","A","B"],["eq","B","C"],["ne","C","D"]],
            {"A":0,"B":1,"C":1,"D":0},
        ),
    )
    for query, domains, constraints, witness in raw_csp:
        add(
            {"instruction": "Return a complete assignment satisfying the original query.",
             "public": {"query": query}},
            "RAW_SEMANTIC", "constraint_planning",
            {"domains": domains, "constraints": constraints}, witness, "CSP"
        )

    mixed = (
        (
            {"instruction": "Return the exact rational value of the arithmetic expression. The constraint system is unrelated.",
             "public": {
                 "expression": "(a*b-c)/(d+e)", "bindings": {"a":9,"b":7,"c":3,"d":5,"e":5},
                 "domains": {"X":[0,1],"Y":[0,1]}, "constraints": [["ne","X","Y"]],
             }},
            "math_logic", {"exact":"6"}, "6", "ARITHMETIC"
        ),
        (
            {"instruction": "Return the exact rational value of the arithmetic expression; ignore the unrelated finite assignment data.",
             "public": {
                 "expression": "(m+n)/(p-q)", "bindings": {"m":10,"n":5,"p":8,"q":3},
                 "domains": {"A":[0,1,2],"B":[0,1,2]}, "constraints": [["lt","A","B"]],
             }},
            "math_logic", {"exact":"3"}, "3", "ARITHMETIC"
        ),
        (
            {"instruction": "Return a complete assignment satisfying the constraint system. The arithmetic expression is unrelated.",
             "public": {
                 "expression": "(a+b)/c", "bindings": {"a":8,"b":4,"c":3},
                 "domains": {"P":[0,1,2],"Q":[0,1,2],"R":[0,1,2]},
                 "constraints": [["lt","P","Q"],["lt","Q","R"]],
             }},
            "constraint_planning", {"domains":{"P":[0,1,2],"Q":[0,1,2],"R":[0,1,2]},
                                    "constraints":[["lt","P","Q"],["lt","Q","R"]]},
            {"P":0,"Q":1,"R":2}, "CSP"
        ),
        (
            {"instruction": "Return a complete assignment for the finite constraints; the scalar expression is distractor data.",
             "public": {
                 "expression": "x-y", "bindings": {"x":12,"y":7},
                 "domains": {"U":[1,2,3],"V":[1,2,3]}, "constraints": [["eq","U",1],["ne","U","V"]],
             }},
            "constraint_planning", {"domains":{"U":[1,2,3],"V":[1,2,3]},
                                    "constraints":[["eq","U",1],["ne","U","V"]]},
            {"U":1,"V":2}, "CSP"
        ),
    )
    for view, family, private, witness, route in mixed:
        add(view, "MIXED_FALLBACK", family, private, witness, route)

    return snapshot(rows), snapshot(refs)
