"""Fresh P1.9 opened-development catalog; authored before model scores.

A: new feasibility-reducible ambiguity, zero-neural expected.
B: new multi-feasible semantic cues, never used in P1.8 model scoring.
"""
from neumann1.control_plane_p19_semantic import SEMANTIC_INSTRUCTIONS

SAT_INSTRUCTION = (
    "Resolve the single bounded pronoun by choosing the candidate interpretation "
    "that makes all stated constraints jointly satisfiable, then return a complete assignment."
)


def catalog():
    rows = [
        {
            "task_id": "p19d_a01",
            "stratum": "A_FEASIBILITY_REDUCIBLE",
            "view": {
                "instruction": SAT_INSTRUCTION,
                "public": {"query": "Choose X, Y from {2,5}. X equals 2, It equals 5. Return a complete assignment."},
            },
        },
        {
            "task_id": "p19d_a02",
            "stratum": "A_FEASIBILITY_REDUCIBLE",
            "view": {
                "instruction": SAT_INSTRUCTION,
                "public": {"query": "Choose A, B, C from {1,4,7}. A equals 1, C equals 7, It equals 4. Return a complete assignment."},
            },
        },
        {
            "task_id": "p19d_a03",
            "stratum": "A_FEASIBILITY_REDUCIBLE",
            "view": {
                "instruction": SAT_INSTRUCTION,
                "public": {"query": "Choose P, Q, R, S from {2,4,6,8}. P equals 2, Q equals 4, S equals 8, It equals 6. Return a complete assignment."},
            },
        },
        {
            "task_id": "p19d_a04",
            "stratum": "A_FEASIBILITY_REDUCIBLE",
            "view": {
                "instruction": SAT_INSTRUCTION,
                "public": {"query": "Choose M, N, O from {-6,-3,0}. M equals -6, N equals -3, It equals 0. Return a complete assignment."},
            },
        },
        {
            "task_id": "p19d_b01",
            "stratum": "B_MULTI_FEASIBLE_SEMANTIC",
            "view": {
                "instruction": SEMANTIC_INSTRUCTIONS[0],
                "public": {"query": "Choose X, Y from {11,14}. X differs from Y, It equals 14. Return a complete assignment."},
            },
        },
        {
            "task_id": "p19d_b02",
            "stratum": "B_MULTI_FEASIBLE_SEMANTIC",
            "view": {
                "instruction": SEMANTIC_INSTRUCTIONS[1],
                "public": {"query": "Choose A, B, C from {3,6,9}. A differs from B, A differs from C, B differs from C, It equals 6. Return a complete assignment."},
            },
        },
        {
            "task_id": "p19d_b03",
            "stratum": "B_MULTI_FEASIBLE_SEMANTIC",
            "view": {
                "instruction": SEMANTIC_INSTRUCTIONS[2],
                "public": {"query": "Choose P, Q, R, S from {10,20,30,40}. P differs from Q, P differs from R, P differs from S, Q differs from R, Q differs from S, R differs from S, It equals 30. Return a complete assignment."},
            },
        },
        {
            "task_id": "p19d_b04",
            "stratum": "B_MULTI_FEASIBLE_SEMANTIC",
            "view": {
                "instruction": SEMANTIC_INSTRUCTIONS[3],
                "public": {"query": "Choose M, N, O from {-5,0,5}. M differs from N, M differs from O, N differs from O, It equals 0. Return a complete assignment."},
            },
        },
    ]

    refs = [
        {
            "task_id": "p19d_a01", "family": "constraint_planning", "expected_candidate": 1,
            "private": {"domains": {"X":[2,5],"Y":[2,5]}, "constraints": [["eq","X",2],["eq","Y",5]]},
            "witness": {"X":2,"Y":5},
        },
        {
            "task_id": "p19d_a02", "family": "constraint_planning", "expected_candidate": 1,
            "private": {"domains": {"A":[1,4,7],"B":[1,4,7],"C":[1,4,7]}, "constraints": [["eq","A",1],["eq","C",7],["eq","B",4]]},
            "witness": {"A":1,"B":4,"C":7},
        },
        {
            "task_id": "p19d_a03", "family": "constraint_planning", "expected_candidate": 2,
            "private": {"domains": {"P":[2,4,6,8],"Q":[2,4,6,8],"R":[2,4,6,8],"S":[2,4,6,8]}, "constraints": [["eq","P",2],["eq","Q",4],["eq","S",8],["eq","R",6]]},
            "witness": {"P":2,"Q":4,"R":6,"S":8},
        },
        {
            "task_id": "p19d_a04", "family": "constraint_planning", "expected_candidate": 2,
            "private": {"domains": {"M":[-6,-3,0],"N":[-6,-3,0],"O":[-6,-3,0]}, "constraints": [["eq","M",-6],["eq","N",-3],["eq","O",0]]},
            "witness": {"M":-6,"N":-3,"O":0},
        },
        {
            "task_id": "p19d_b01", "family": "constraint_planning", "expected_candidate": 1,
            "semantic_grounding": "outbound carries traffic away from the system, so It denotes Y",
            "private": {"domains": {"X":[11,14],"Y":[11,14]}, "constraints": [["ne","X","Y"],["eq","Y",14]]},
            "witness": {"X":11,"Y":14},
        },
        {
            "task_id": "p19d_b02", "family": "constraint_planning", "expected_candidate": 1,
            "semantic_grounding": "center is the middle port, so It denotes B",
            "private": {"domains": {"A":[3,6,9],"B":[3,6,9],"C":[3,6,9]}, "constraints": [["ne","A","B"],["ne","A","C"],["ne","B","C"],["eq","B",6]]},
            "witness": {"A":3,"B":6,"C":9},
        },
        {
            "task_id": "p19d_b03", "family": "constraint_planning", "expected_candidate": 2,
            "semantic_grounding": "R is the third stage and immediately follows Q, the second stage, so It denotes R",
            "private": {"domains": {"P":[10,20,30,40],"Q":[10,20,30,40],"R":[10,20,30,40],"S":[10,20,30,40]}, "constraints": [["ne","P","Q"],["ne","P","R"],["ne","P","S"],["ne","Q","R"],["ne","Q","S"],["ne","R","S"],["eq","R",30]]},
            "witness": {"P":10,"Q":20,"R":30,"S":40},
        },
        {
            "task_id": "p19d_b04", "family": "constraint_planning", "expected_candidate": 1,
            "semantic_grounding": "standby is the takeover unit if the active unit fails, so It denotes N",
            "private": {"domains": {"M":[-5,0,5],"N":[-5,0,5],"O":[-5,0,5]}, "constraints": [["ne","M","N"],["ne","M","O"],["ne","N","O"],["eq","N",0]]},
            "witness": {"M":-5,"N":0,"O":5},
        },
    ]
    return rows, refs


def negative_controls():
    return (
        {
            "instruction": SEMANTIC_INSTRUCTIONS[0],
            "public": {"query": "Choose X, Y from {11,14}. It equals 14, It equals 11. Return a complete assignment."},
        },
        {
            "instruction": "Unregistered P1.9 semantic instruction.",
            "public": {"query": "Choose X, Y from {11,14}. X differs from Y, It equals 14. Return a complete assignment."},
        },
        {
            "instruction": SEMANTIC_INSTRUCTIONS[0],
            "public": {"query": "Choose X, Y, Z, W, V from {0,1}. It equals 1. Return a complete assignment."},
        },
        {
            "instruction": SEMANTIC_INSTRUCTIONS[1],
            "public": {"query": "Choose A, B, C from {3,6,9}. A differs from B, It differs from C. Return a complete assignment."},
        },
    )
