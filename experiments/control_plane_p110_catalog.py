"""Fresh P1.10 opened-development catalog, authored before any P1.10 Gemma score."""
from neumann1.control_plane_p110_semantic import SEMANTIC_INSTRUCTIONS

def catalog():
    rows=[
      {"task_id":"p110d_b01","stratum":"B_MULTI_FEASIBLE_MINIMAL_PAIRWISE","view":{"instruction":SEMANTIC_INSTRUCTIONS[0],"public":{"query":"Choose X, Y from {14,17}. X differs from Y, It equals 17. Return a complete assignment."}}},
      {"task_id":"p110d_b02","stratum":"B_MULTI_FEASIBLE_MINIMAL_PAIRWISE","view":{"instruction":SEMANTIC_INSTRUCTIONS[1],"public":{"query":"Choose A, B, C from {3,8,13}. A differs from B, A differs from C, B differs from C, It equals 13. Return a complete assignment."}}},
      {"task_id":"p110d_b03","stratum":"B_MULTI_FEASIBLE_MINIMAL_PAIRWISE","view":{"instruction":SEMANTIC_INSTRUCTIONS[2],"public":{"query":"Choose P, Q, R, S from {21,34,55,89}. P differs from Q, P differs from R, P differs from S, Q differs from R, Q differs from S, R differs from S, It equals 55. Return a complete assignment."}}},
      {"task_id":"p110d_b04","stratum":"B_MULTI_FEASIBLE_MINIMAL_PAIRWISE","view":{"instruction":SEMANTIC_INSTRUCTIONS[3],"public":{"query":"Choose M, N from {-9,-7}. M differs from N, It equals -7. Return a complete assignment."}}},
      {"task_id":"p110d_b05","stratum":"B_MULTI_FEASIBLE_MINIMAL_PAIRWISE","view":{"instruction":SEMANTIC_INSTRUCTIONS[4],"public":{"query":"Choose A, B, C from {16,32,64}. A differs from B, A differs from C, B differs from C, It equals 16. Return a complete assignment."}}},
      {"task_id":"p110d_b06","stratum":"B_MULTI_FEASIBLE_MINIMAL_PAIRWISE","view":{"instruction":SEMANTIC_INSTRUCTIONS[5],"public":{"query":"Choose P, Q, R, S from {-12,-9,-6,-3}. P differs from Q, P differs from R, P differs from S, Q differs from R, Q differs from S, R differs from S, It equals -3. Return a complete assignment."}}},
      {"task_id":"p110d_b07","stratum":"B_MULTI_FEASIBLE_MINIMAL_PAIRWISE","view":{"instruction":SEMANTIC_INSTRUCTIONS[6],"public":{"query":"Choose M, N, O from {25,50,75}. M differs from N, M differs from O, N differs from O, It equals 25. Return a complete assignment."}}},
      {"task_id":"p110d_b08","stratum":"B_MULTI_FEASIBLE_MINIMAL_PAIRWISE","view":{"instruction":SEMANTIC_INSTRUCTIONS[7],"public":{"query":"Choose X, Y from {101,202}. X differs from Y, It equals 202. Return a complete assignment."}}},
    ]
    refs=[
      {"task_id":"p110d_b01","family":"constraint_planning","expected_candidate":1,"semantic_grounding":"reserve route is the emergency path, so It denotes Y","private":{"domains":{"X":[14,17],"Y":[14,17]},"constraints":[["ne","X","Y"],["eq","Y",17]]},"witness":{"X":14,"Y":17}},
      {"task_id":"p110d_b02","family":"constraint_planning","expected_candidate":2,"semantic_grounding":"output node is the terminal node, so It denotes C","private":{"domains":{"A":[3,8,13],"B":[3,8,13],"C":[3,8,13]},"constraints":[["ne","A","B"],["ne","A","C"],["ne","B","C"],["eq","C",13]]},"witness":{"A":3,"B":8,"C":13}},
      {"task_id":"p110d_b03","family":"constraint_planning","expected_candidate":2,"semantic_grounding":"actuator physically changes the system, so It denotes R","private":{"domains":{"P":[21,34,55,89],"Q":[21,34,55,89],"R":[21,34,55,89],"S":[21,34,55,89]},"constraints":[["ne","P","Q"],["ne","P","R"],["ne","P","S"],["ne","Q","R"],["ne","Q","S"],["ne","R","S"],["eq","R",55]]},"witness":{"P":21,"Q":34,"R":55,"S":89}},
      {"task_id":"p110d_b04","family":"constraint_planning","expected_candidate":1,"semantic_grounding":"deputy is the succession role, so It denotes N","private":{"domains":{"M":[-9,-7],"N":[-9,-7]},"constraints":[["ne","M","N"],["eq","N",-7]]},"witness":{"M":-9,"N":-7}},
      {"task_id":"p110d_b05","family":"constraint_planning","expected_candidate":0,"semantic_grounding":"volatile cache is the fastest temporary tier, so It denotes A","private":{"domains":{"A":[16,32,64],"B":[16,32,64],"C":[16,32,64]},"constraints":[["ne","A","B"],["ne","A","C"],["ne","B","C"],["eq","A",16]]},"witness":{"A":16,"B":32,"C":64}},
      {"task_id":"p110d_b06","family":"constraint_planning","expected_candidate":3,"semantic_grounding":"docking is the rendezvous completion phase, so It denotes S","private":{"domains":{"P":[-12,-9,-6,-3],"Q":[-12,-9,-6,-3],"R":[-12,-9,-6,-3],"S":[-12,-9,-6,-3]},"constraints":[["ne","P","Q"],["ne","P","R"],["ne","P","S"],["ne","Q","R"],["ne","Q","S"],["ne","R","S"],["eq","S",-3]]},"witness":{"P":-12,"Q":-9,"R":-6,"S":-3}},
      {"task_id":"p110d_b07","family":"constraint_planning","expected_candidate":0,"semantic_grounding":"estimator is the state-inference component, so It denotes M","private":{"domains":{"M":[25,50,75],"N":[25,50,75],"O":[25,50,75]},"constraints":[["ne","M","N"],["ne","M","O"],["ne","N","O"],["eq","M",25]]},"witness":{"M":25,"N":50,"O":75}},
      {"task_id":"p110d_b08","family":"constraint_planning","expected_candidate":1,"semantic_grounding":"receive path is the inbound link, so It denotes Y","private":{"domains":{"X":[101,202],"Y":[101,202]},"constraints":[["ne","X","Y"],["eq","Y",202]]},"witness":{"X":101,"Y":202}},
    ]
    return rows,refs

def negative_controls():
    return (
      {"instruction":"Unregistered P1.10 cue.","public":{"query":"Choose X, Y from {14,17}. X differs from Y, It equals 17. Return a complete assignment."}},
      {"instruction":SEMANTIC_INSTRUCTIONS[0],"public":{"query":"Choose X, Y from {14,17}. It equals 17, It equals 14. Return a complete assignment."}},
      {"instruction":SEMANTIC_INSTRUCTIONS[1],"public":{"query":"Choose A, B, C, D, E from {1,2,3,4,5}. It equals 3. Return a complete assignment."}},
      {"instruction":SEMANTIC_INSTRUCTIONS[2],"public":{"query":"Choose P, Q, R from {21,34,55}. P differs from Q. Return a complete assignment."}},
    )
