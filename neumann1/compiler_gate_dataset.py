from __future__ import annotations

from .types import IRKind
from .learned_representation import KindTrainingExample


def compiler_gate_training_examples():
    raw = [
        ("S1 can use A or C; S2 can use B or D", IRKind.BIPARTITE_MATCHING),
        ("R1 can connect to X or Y; R2 can connect to Y or Z", IRKind.BIPARTITE_MATCHING),
        ("P1 may be assigned to J1 or J3; P2 may be assigned to J2 or J4", IRKind.BIPARTITE_MATCHING),
        ("Allowed for U1: K1, K2; Allowed for U2: K2, K3", IRKind.BIPARTITE_MATCHING),
        ("D1 can take C1 and C3; D2 can take C2 or C4", IRKind.BIPARTITE_MATCHING),
        ("A1 can be assigned to B1 or B2; A2 can be assigned to B2 or B3", IRKind.BIPARTITE_MATCHING),
        ("T1 can use F1, F2; T2 can use F2, F3", IRKind.BIPARTITE_MATCHING),
        ("Allowed for M1: N1 and N3; Allowed for M2: N2 or N4", IRKind.BIPARTITE_MATCHING),
        ("Q1 may be assigned to W1, W2; Q2 may be assigned to W2, W3", IRKind.BIPARTITE_MATCHING),
        ("C1 can connect to H1 or H2; C2 can connect to H2 or H3", IRKind.BIPARTITE_MATCHING),
        ("x + y = 5; x - y = 1", IRKind.LINEAR_SYSTEM),
        ("2*a + 3*b = 9; a - b = 1", IRKind.LINEAR_SYSTEM),
        ("Solve: p + q = 10; 2*p - q = 4", IRKind.LINEAR_SYSTEM),
        ("3*u - v = 7; u + 2*v = 8", IRKind.LINEAR_SYSTEM),
        ("m + 4*n = 14; 2*m - n = 1", IRKind.LINEAR_SYSTEM),
        ("5*r + s = 11; r - 3*s = -1", IRKind.LINEAR_SYSTEM),
        ("Equation: c + d = 8; 4*c - d = 7", IRKind.LINEAR_SYSTEM),
        ("7*h - 2*k = 12; h + k = 5", IRKind.LINEAR_SYSTEM),
        ("v + 2*w = 13; 3*v - w = 4", IRKind.LINEAR_SYSTEM),
        ("Solve: z + t = 6; z - 4*t = -9", IRKind.LINEAR_SYSTEM),
        ("Find the shortest path from A to B.", IRKind.UNKNOWN),
        ("Compute a minimum spanning tree of this graph.", IRKind.UNKNOWN),
        ("Maximize profit subject to linear constraints.", IRKind.UNKNOWN),
        ("Find a maximum flow through the network.", IRKind.UNKNOWN),
        ("x*x + y = 4; x - y = 1", IRKind.UNKNOWN),
        ("x + y <= 5; x - y = 1", IRKind.UNKNOWN),
        ("S1 can use A or C with cost 5; S2 can use B or C", IRKind.UNKNOWN),
        ("S1 can use A or C; S2 can use B with capacity 2", IRKind.UNKNOWN),
        ("Explain why the sky is blue.", IRKind.UNKNOWN),
        ("Sort these numbers in ascending order.", IRKind.UNKNOWN),
        ("Assign every worker to a job while minimizing total cost.", IRKind.UNKNOWN),
        ("Solve a nonlinear system with quadratic terms.", IRKind.UNKNOWN),
    ]
    return [KindTrainingExample(text, kind) for text, kind in raw]


def compiler_gate_validation_examples():
    return [
        ("K1 can use R1 or R2; K2 can use R2 or R3", IRKind.BIPARTITE_MATCHING, "known"),
        ("Allowed for V1: P1, P3; Allowed for V2: P2 and P4", IRKind.BIPARTITE_MATCHING, "known"),
        ("a + b = 7; a - 2*b = 1", IRKind.LINEAR_SYSTEM, "known"),
        ("4*x + y = 12; x - y = 0", IRKind.LINEAR_SYSTEM, "known"),
        ("Compute a shortest route in a weighted graph.", IRKind.UNKNOWN, "unknown"),
        ("Find a minimum-cost flow.", IRKind.UNKNOWN, "unknown"),
        ("x*x + y = 3; x - y = 1", IRKind.UNKNOWN, "near_unknown"),
        ("A1 can use B1 or B2 with cost 3; A2 can use B2", IRKind.UNKNOWN, "near_unknown"),
    ]


def compiler_gate_final_examples():
    return [
        ("L1 can use X1 or X2; L2 can use X2 or X3", IRKind.BIPARTITE_MATCHING, "known"),
        ("Allowed for G1: H1 and H3; Allowed for G2: H2 or H4", IRKind.BIPARTITE_MATCHING, "known"),
        ("N1 may be assigned to P1, P2; N2 may be assigned to P2, P3", IRKind.BIPARTITE_MATCHING, "known"),
        ("R1 can connect to S1 or S2; R2 can connect to S2 or S4", IRKind.BIPARTITE_MATCHING, "known"),
        ("a + c = 9; a - c = 3", IRKind.LINEAR_SYSTEM, "known"),
        ("2*p + q = 8; p - q = 1", IRKind.LINEAR_SYSTEM, "known"),
        ("Solve: u + 3*v = 11; 2*u - v = 4", IRKind.LINEAR_SYSTEM, "known"),
        ("5*m - n = 14; m + n = 4", IRKind.LINEAR_SYSTEM, "known"),
        ("Find an Eulerian circuit in this graph.", IRKind.UNKNOWN, "far_unknown"),
        ("Compute the shortest path from source to target.", IRKind.UNKNOWN, "far_unknown"),
        ("Maximize x+y subject to inequalities.", IRKind.UNKNOWN, "near_unknown"),
        ("x*x + y = 10; x - y = 2", IRKind.UNKNOWN, "near_unknown"),
        ("x + y <= 8; x - y = 2", IRKind.UNKNOWN, "near_unknown"),
        ("S1 can use A or B with cost 4; S2 can use B or C", IRKind.UNKNOWN, "near_unknown"),
        ("S1 can use A or B; S2 can use B with capacity 2", IRKind.UNKNOWN, "near_unknown"),
        ("Assign each worker to one job minimizing total cost.", IRKind.UNKNOWN, "near_unknown"),
        ("Explain the path by which a document was assigned an ID.", IRKind.UNKNOWN, "hard_negative"),
        ("The equation number is 7; summarize the paragraph.", IRKind.UNKNOWN, "hard_negative"),
    ]
