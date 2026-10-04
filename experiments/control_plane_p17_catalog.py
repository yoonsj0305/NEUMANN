"""Frozen authored P1.7 opened-development catalog.

Public obligations and private original-checker references are authored before
any actual P1.7 Gemma score. Ambiguous items use an explicit public instruction:
choose the single pronoun binding that makes the stated constraints jointly
satisfiable. No hidden semantic label is supplied to the selector.
"""


AMBIGUOUS_INSTRUCTION = (
    "Resolve the single bounded pronoun by choosing the candidate interpretation "
    "that makes all stated constraints jointly satisfiable, then return a complete assignment."
)


def catalog():
    rows = [
        {"task_id":"p17d_01","view":{"instruction":"Return the exact rational value required by the original query.",
         "public":{"query":"Start with 52, divide by 4, add 5 to the quotient, then multiply by 3. Return the exact rational value."}}},
        {"task_id":"p17d_02","view":{"instruction":"Return the exact rational value required by the original query.",
         "public":{"query":"Take 31, subtract 7, divide the result by 6, then add one half. Return the exact rational value."}}},
        {"task_id":"p17d_03","view":{"instruction":"Return the exact rational value required by the original query.",
         "public":{"query":"Multiply 8 by 7, subtract 20 from the product, then divide by 9. Return the exact rational value."}}},
        {"task_id":"p17d_04","view":{"instruction":"Return the exact rational value required by the original query.",
         "public":{"query":"Begin with 41, add 7, divide the result by 8, then subtract one quarter. Return the exact rational value."}}},
        {"task_id":"p17d_05","view":{"instruction":"Return a complete assignment satisfying the original query.",
         "public":{"query":"Choose A, B, C from {0,1,2,3}. A equals 3, B is less than A, and C equals B. Return a complete assignment."}}},
        {"task_id":"p17d_06","view":{"instruction":"Return a complete assignment satisfying the original query.",
         "public":{"query":"Choose U, V, W from {-2,-1,0,1}. V equals 0, U is at most V, W differs from U, and W equals 1. Return a complete assignment."}}},
        {"task_id":"p17d_07","view":{"instruction":"Return a complete assignment satisfying the original query.",
         "public":{"query":"Assign H, J, K from {1,2,3}. H differs from J, J equals 2, and K equals H. Return a complete assignment."}}},
        {"task_id":"p17d_08","view":{"instruction":"Return a complete assignment satisfying the original query.",
         "public":{"query":"Assign D, E from {-4,-3,-2,-1}. D is less than E, E equals -1, and D differs from -3. Return a complete assignment."}}},
        {"task_id":"p17d_09","view":{"instruction":AMBIGUOUS_INSTRUCTION,
         "public":{"query":"Choose X, Y from {0,1}. X equals 0, It equals 1. Return a complete assignment."}}},
        {"task_id":"p17d_10","view":{"instruction":AMBIGUOUS_INSTRUCTION,
         "public":{"query":"Choose A, B, C from {0,1,2}. A equals 1, B equals 2, It equals 0. Return a complete assignment."}}},
        {"task_id":"p17d_11","view":{"instruction":AMBIGUOUS_INSTRUCTION,
         "public":{"query":"Choose P, Q, R, S from {0,1,2,3}. P equals 0, Q equals 1, R equals 2, It equals 3. Return a complete assignment."}}},
        {"task_id":"p17d_12","view":{"instruction":AMBIGUOUS_INSTRUCTION,
         "public":{"query":"Choose M, N, O from {-2,-1,0}. M equals -2, O equals 0, It equals -1. Return a complete assignment."}}},
    ]
    refs = [
        {"task_id":"p17d_01","kind":"RAW_SOURCE_BOUND","family":"math_logic","semantic_path":"UNIQUE",
         "private":{"exact":"54"},"witness":"54","expected_route":"ARITHMETIC"},
        {"task_id":"p17d_02","kind":"RAW_SOURCE_BOUND","family":"math_logic","semantic_path":"UNIQUE",
         "private":{"exact":"9/2"},"witness":"9/2","expected_route":"ARITHMETIC"},
        {"task_id":"p17d_03","kind":"RAW_SOURCE_BOUND","family":"math_logic","semantic_path":"UNIQUE",
         "private":{"exact":"4"},"witness":"4","expected_route":"ARITHMETIC"},
        {"task_id":"p17d_04","kind":"RAW_SOURCE_BOUND","family":"math_logic","semantic_path":"UNIQUE",
         "private":{"exact":"23/4"},"witness":"23/4","expected_route":"ARITHMETIC"},
        {"task_id":"p17d_05","kind":"RAW_SOURCE_BOUND","family":"constraint_planning","semantic_path":"UNIQUE",
         "private":{"domains":{"A":[0,1,2,3],"B":[0,1,2,3],"C":[0,1,2,3]},
         "constraints":[["eq","A",3],["lt","B","A"],["eq","C","B"]]},
         "witness":{"A":3,"B":0,"C":0},"expected_route":"CSP"},
        {"task_id":"p17d_06","kind":"RAW_SOURCE_BOUND","family":"constraint_planning","semantic_path":"UNIQUE",
         "private":{"domains":{"U":[-2,-1,0,1],"V":[-2,-1,0,1],"W":[-2,-1,0,1]},
         "constraints":[["eq","V",0],["le","U","V"],["ne","W","U"],["eq","W",1]]},
         "witness":{"U":-2,"V":0,"W":1},"expected_route":"CSP"},
        {"task_id":"p17d_07","kind":"RAW_SOURCE_BOUND","family":"constraint_planning","semantic_path":"UNIQUE",
         "private":{"domains":{"H":[1,2,3],"J":[1,2,3],"K":[1,2,3]},
         "constraints":[["ne","H","J"],["eq","J",2],["eq","K","H"]]},
         "witness":{"H":1,"J":2,"K":1},"expected_route":"CSP"},
        {"task_id":"p17d_08","kind":"RAW_SOURCE_BOUND","family":"constraint_planning","semantic_path":"UNIQUE",
         "private":{"domains":{"D":[-4,-3,-2,-1],"E":[-4,-3,-2,-1]},
         "constraints":[["lt","D","E"],["eq","E",-1],["ne","D",-3]]},
         "witness":{"D":-4,"E":-1},"expected_route":"CSP"},
        {"task_id":"p17d_09","kind":"RAW_SOURCE_BOUND","family":"constraint_planning","semantic_path":"AMBIGUOUS",
         "private":{"domains":{"X":[0,1],"Y":[0,1]},"constraints":[["eq","X",0],["eq","Y",1]]},
         "witness":{"X":0,"Y":1},"expected_route":"CSP","expected_candidate":1},
        {"task_id":"p17d_10","kind":"RAW_SOURCE_BOUND","family":"constraint_planning","semantic_path":"AMBIGUOUS",
         "private":{"domains":{"A":[0,1,2],"B":[0,1,2],"C":[0,1,2]},
         "constraints":[["eq","A",1],["eq","B",2],["eq","C",0]]},
         "witness":{"A":1,"B":2,"C":0},"expected_route":"CSP","expected_candidate":2},
        {"task_id":"p17d_11","kind":"RAW_SOURCE_BOUND","family":"constraint_planning","semantic_path":"AMBIGUOUS",
         "private":{"domains":{"P":[0,1,2,3],"Q":[0,1,2,3],"R":[0,1,2,3],"S":[0,1,2,3]},
         "constraints":[["eq","P",0],["eq","Q",1],["eq","R",2],["eq","S",3]]},
         "witness":{"P":0,"Q":1,"R":2,"S":3},"expected_route":"CSP","expected_candidate":3},
        {"task_id":"p17d_12","kind":"RAW_SOURCE_BOUND","family":"constraint_planning","semantic_path":"AMBIGUOUS",
         "private":{"domains":{"M":[-2,-1,0],"N":[-2,-1,0],"O":[-2,-1,0]},
         "constraints":[["eq","M",-2],["eq","O",0],["eq","N",-1]]},
         "witness":{"M":-2,"N":-1,"O":0},"expected_route":"CSP","expected_candidate":1},
    ]
    return rows, refs


def negative_controls():
    return (
        {"instruction":"Return exact.","public":{"query":"Start with 2 or 4, add 3. Return the exact rational value."}},
        {"instruction":"Return exact.","public":{"query":"Start with 2, divide by one fifth. Return the exact rational value."}},
        {"instruction":"Return a complete assignment.","public":{"query":"Choose X from {0,1}. X is greater than 0. Return a complete assignment."}},
        {"instruction":AMBIGUOUS_INSTRUCTION,"public":{"query":"Choose A, B, C, D, E from {0,1}. It equals 0. Return a complete assignment."}},
    )
