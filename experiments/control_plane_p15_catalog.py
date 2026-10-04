"""Eight authored opened-development obligations; references never enter the core."""
from neumann1.control_plane_v1 import snapshot


def catalog():
    rows, refs = [], []

    def add(query, family, private, witness, route):
        task_id = "p15d_%02d" % (len(rows)+1)
        instruction = ("Return the exact rational value required by the original query."
                       if family == "math_logic" else
                       "Return a complete assignment satisfying the original query.")
        rows.append({"task_id":task_id,"view":{"instruction":instruction,"public":{"query":query}}})
        refs.append({"task_id":task_id,"kind":"RAW_SEMANTIC","family":family,
                     "private":private,"witness":witness,"expected_route":route})

    for query, exact in (
        ("Starting from 30, divide by 5, subtract 2 from the quotient, then multiply by 9. Return the exact rational value.", "36"),
        ("Take 17, add 7, divide the result by 3, then subtract five halves. Return the exact rational value.", "11/2"),
        ("Begin with 19, subtract 7, add one quarter, then divide the result by 7. Return the exact rational value.", "7/4"),
        ("Multiply 6 by 4, divide the product by 8, then subtract three halves. Return the exact rational value.", "3/2"),
    ):
        add(query,"math_logic",{"exact":exact},exact,"ARITHMETIC")
    for query, domains, constraints, witness in (
        ("Choose M, N, O from {1,2,3,4}. M equals 3, N is less than M, and O equals N. Return a complete assignment.",
         {"M":[1,2,3,4],"N":[1,2,3,4],"O":[1,2,3,4]},
         [["eq","M",3],["lt","N","M"],["eq","O","N"]],{"M":3,"N":1,"O":1}),
        ("Choose I, J, K, L from {0,1,2}. I differs from K, J equals 2, K equals L, and I is less than J. Return a complete assignment.",
         {"I":[0,1,2],"J":[0,1,2],"K":[0,1,2],"L":[0,1,2]},
         [["ne","I","K"],["eq","J",2],["eq","K","L"],["lt","I","J"]],{"I":0,"J":2,"K":1,"L":1}),
        ("Assign S and T from {-2,-1,0,1}. S is at most T, T equals -1, and S differs from T. Return a complete assignment.",
         {"S":[-2,-1,0,1],"T":[-2,-1,0,1]},
         [["le","S","T"],["eq","T",-1],["ne","S","T"]],{"S":-2,"T":-1}),
        ("Assign P, Q, R from {0,1,2,3}. R equals 2, P differs from R, Q is at most R, and P equals Q. Return a complete assignment.",
         {"P":[0,1,2,3],"Q":[0,1,2,3],"R":[0,1,2,3]},
         [["eq","R",2],["ne","P","R"],["le","Q","R"],["eq","P","Q"]],{"P":0,"Q":0,"R":2}),
    ):
        add(query,"constraint_planning",{"domains":domains,"constraints":constraints},witness,"CSP")
    return snapshot(rows), snapshot(refs)
