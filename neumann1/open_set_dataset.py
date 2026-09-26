from __future__ import annotations
from .types import IRKind


def final_test_examples():
    return [
        ("Every sensor can connect to certain gateways. Give each sensor a different compatible gateway.", IRKind.BIPARTITE_MATCHING, "known"),
        ("Each manuscript has acceptable reviewers, and a reviewer may take only one manuscript. Is a complete allocation possible?", IRKind.BIPARTITE_MATCHING, "known"),
        ("Select one distinct legal docking bay for every spacecraft from its allowed bays.", IRKind.BIPARTITE_MATCHING, "known"),
        ("Can every candidate receive a unique acceptable role from the roles on their list?", IRKind.BIPARTITE_MATCHING, "known"),
        ("Links have energy costs. Reach terminal T from source S with minimum accumulated energy.", IRKind.SHORTEST_PATH, "known"),
        ("Among connected waypoints, find a chain from base to target whose weights sum to the least value.", IRKind.SHORTEST_PATH, "known"),
        ("Determine the minimum-cost traversal from vertex a to vertex h in the weighted network.", IRKind.SHORTEST_PATH, "known"),
        ("Travel times label the arcs; find the least-time connection between the two requested nodes.", IRKind.SHORTEST_PATH, "known"),
        ("The unknowns u and v obey 2u+3v=13 and 5u-v=7. Determine u and v.", IRKind.LINEAR_SYSTEM, "known"),
        ("Find y in the matrix equation By=d for a nonsingular B.", IRKind.LINEAR_SYSTEM, "known"),
        ("Two unknown flow rates satisfy two independent linear balance equations. Recover both.", IRKind.LINEAR_SYSTEM, "known"),
        ("Compute the unique pair m,n consistent with the two affine equalities.", IRKind.LINEAR_SYSTEM, "known"),
        ("Find a maximum matching in this general graph, which is not specified as bipartite.", IRKind.UNKNOWN, "unknown"),
        ("Compute all-pairs shortest paths for this graph.", IRKind.UNKNOWN, "unknown"),
        ("Solve this quadratic equation for x.", IRKind.UNKNOWN, "unknown"),
        ("Find the minimum-cost flow satisfying capacities and supplies.", IRKind.UNKNOWN, "unknown"),
        ("Assign a title to every paragraph and choose the shortest title wording.", IRKind.UNKNOWN, "hard_negative"),
        ("Explain the route by which an invoice was assigned an account number.", IRKind.UNKNOWN, "hard_negative"),
        ("This equation label appears beside a historical timeline; summarize the passage.", IRKind.UNKNOWN, "hard_negative"),
        ("Pair each student with a discussion topic, then write the shortest summary of the activity.", IRKind.UNKNOWN, "hard_negative"),
    ]
