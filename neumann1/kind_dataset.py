from __future__ import annotations
from .types import IRKind
from .learned_representation import KindTrainingExample


def training_examples():
    raw = [
        ("Six satellites each support only certain communication slots. Give every satellite one distinct compatible slot.", IRKind.BIPARTITE_MATCHING),
        ("Allocate each nurse to one qualified shift so no shift receives more than one nurse.", IRKind.BIPARTITE_MATCHING),
        ("Pair applicants with acceptable projects, using each project at most once.", IRKind.BIPARTITE_MATCHING),
        ("Each robot can service a subset of stations. Can all robots receive different allowed stations?", IRKind.BIPARTITE_MATCHING),
        ("Match students to permitted laboratories with one student per laboratory.", IRKind.BIPARTITE_MATCHING),
        ("Choose a distinct compatible frequency channel for every transmitter.", IRKind.BIPARTITE_MATCHING),
        ("Every package has a set of eligible lockers; place all packages into different eligible lockers.", IRKind.BIPARTITE_MATCHING),
        ("Give every technician a different machine from the machines they are certified to operate.", IRKind.BIPARTITE_MATCHING),
        ("A road network has weighted links. Find the minimum travel cost from the depot to the hospital.", IRKind.SHORTEST_PATH),
        ("What is the least-delay route between node S and node T in this network?", IRKind.SHORTEST_PATH),
        ("Find a minimum-weight path through the graph from source to destination.", IRKind.SHORTEST_PATH),
        ("Which sequence of connected cities gives the smallest total driving time?", IRKind.SHORTEST_PATH),
        ("Packets can traverse weighted network links. Determine the minimum latency from A to Z.", IRKind.SHORTEST_PATH),
        ("Among all connected corridors, find the least total cost connection from entrance to exit.", IRKind.SHORTEST_PATH),
        ("Compute the cheapest route from warehouse W to store Q on the weighted map.", IRKind.SHORTEST_PATH),
        ("Find the minimum accumulated edge weight between two specified vertices.", IRKind.SHORTEST_PATH),
        ("Two unknown prices satisfy x+y=12 and 2x-y=3. Determine both unknowns.", IRKind.LINEAR_SYSTEM),
        ("Find the values of a and b that simultaneously satisfy 3a+2b=7 and a-b=1.", IRKind.LINEAR_SYSTEM),
        ("Determine two unknown currents from the simultaneous linear equations shown.", IRKind.LINEAR_SYSTEM),
        ("Solve the pair of first-degree equations for the two variables.", IRKind.LINEAR_SYSTEM),
        ("A matrix A and vector b are given. Find x such that Ax=b.", IRKind.LINEAR_SYSTEM),
        ("Recover the unknown coefficients that satisfy all listed linear equalities.", IRKind.LINEAR_SYSTEM),
        ("The totals give two independent linear constraints on x and y. Compute x and y.", IRKind.LINEAR_SYSTEM),
        ("Solve this nonsingular system of simultaneous linear equations.", IRKind.LINEAR_SYSTEM),
        ("Explain why the sky appears blue during the day.", IRKind.UNKNOWN),
        ("Summarize the main argument of this paragraph.", IRKind.UNKNOWN),
        ("Sort these numbers from smallest to largest.", IRKind.UNKNOWN),
        ("Estimate the area under this nonlinear curve using numerical integration.", IRKind.UNKNOWN),
        ("Schedule these jobs on machines to minimize makespan.", IRKind.UNKNOWN),
        ("Find a maximum flow through this capacitated network.", IRKind.UNKNOWN),
        ("Factor this polynomial into irreducible factors.", IRKind.UNKNOWN),
        ("Decide whether this Boolean formula is satisfiable.", IRKind.UNKNOWN),
        ("Describe the shortest paragraph in the report and assign it a label.", IRKind.UNKNOWN),
        ("A manager assigns jobs, then asks for the shortest written explanation of the policy.", IRKind.UNKNOWN),
        ("Explain the path by which an employee was assigned to a department; no optimization is requested.", IRKind.UNKNOWN),
        ("The word equation appears in this history question, but there are no numeric unknowns to solve.", IRKind.UNKNOWN),
    ]
    return [KindTrainingExample(t, k) for t, k in raw]


def heldout_examples():
    return [
        ("Each telescope can use only a few calibration ports. Select one allowed port per telescope without reusing any port.", IRKind.BIPARTITE_MATCHING, "known"),
        ("Every intern lists acceptable mentors, and each mentor may take at most one intern. Can everyone be accommodated?", IRKind.BIPARTITE_MATCHING, "known"),
        ("Connect every left-side device to a unique compatible right-side socket.", IRKind.BIPARTITE_MATCHING, "known"),
        ("Choose one distinct admissible classroom for each exam from its allowed set.", IRKind.BIPARTITE_MATCHING, "known"),
        ("Edges carry tolls. Determine the least total toll needed to get from origin O to destination D.", IRKind.SHORTEST_PATH, "known"),
        ("A mesh has weighted connections; what connected chain from u to v has minimum sum weight?", IRKind.SHORTEST_PATH, "known"),
        ("Which way through the transit graph minimizes accumulated travel time from station 1 to station 9?", IRKind.SHORTEST_PATH, "known"),
        ("Starting at node alpha, reach omega with minimum total edge cost.", IRKind.SHORTEST_PATH, "known"),
        ("Two quantities obey 4p+q=11 and p-2q=-1. Find p and q.", IRKind.LINEAR_SYSTEM, "known"),
        ("Determine the vector z satisfying Mz=c for the given nonsingular square matrix M.", IRKind.LINEAR_SYSTEM, "known"),
        ("There are two unknown concentrations and two independent first-degree balance relations. Recover both concentrations.", IRKind.LINEAR_SYSTEM, "known"),
        ("Find the unique values of r and s consistent with both stated linear equalities.", IRKind.LINEAR_SYSTEM, "known"),
        ("Write a concise explanation of why a rainbow separates colors.", IRKind.UNKNOWN, "unknown"),
        ("Compute a minimum spanning tree of this weighted network.", IRKind.UNKNOWN, "unknown"),
        ("Maximize profit subject to the listed linear inequalities.", IRKind.UNKNOWN, "unknown"),
        ("Find an Eulerian circuit if one exists.", IRKind.UNKNOWN, "unknown"),
        ("Assign each road a maintenance label and then describe the shortest label text; no route optimization is involved.", IRKind.UNKNOWN, "hard_negative"),
        ("The report gives an equation number and asks which employee was assigned to job 7; no equations must be solved.", IRKind.UNKNOWN, "hard_negative"),
        ("Explain the path of approval for a job assignment from manager to worker.", IRKind.UNKNOWN, "hard_negative"),
        ("A shortest-story contest pairs students with topics; determine nothing numerically, just summarize the rules.", IRKind.UNKNOWN, "hard_negative"),
    ]
