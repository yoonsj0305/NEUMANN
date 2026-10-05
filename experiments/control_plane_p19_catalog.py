"""Fresh P1.9 opened-development catalog, authored before any P1.9 Gemma score."""
from neumann1.control_plane_p19_semantic import SEMANTIC_INSTRUCTIONS

def catalog():
    rows=[
      {"task_id":"p19d_b01","stratum":"B_MULTI_FEASIBLE_PROPOSITION","view":{"instruction":SEMANTIC_INSTRUCTIONS[0],"public":{"query":"Choose X, Y from {7,9}. X differs from Y, It equals 9. Return a complete assignment."}}},
      {"task_id":"p19d_b02","stratum":"B_MULTI_FEASIBLE_PROPOSITION","view":{"instruction":SEMANTIC_INSTRUCTIONS[1],"public":{"query":"Choose A, B, C from {2,4,6}. A differs from B, A differs from C, B differs from C, It equals 6. Return a complete assignment."}}},
      {"task_id":"p19d_b03","stratum":"B_MULTI_FEASIBLE_PROPOSITION","view":{"instruction":SEMANTIC_INSTRUCTIONS[2],"public":{"query":"Choose P, Q, R, S from {10,20,30,40}. P differs from Q, P differs from R, P differs from S, Q differs from R, Q differs from S, R differs from S, It equals 40. Return a complete assignment."}}},
      {"task_id":"p19d_b04","stratum":"B_MULTI_FEASIBLE_PROPOSITION","view":{"instruction":SEMANTIC_INSTRUCTIONS[3],"public":{"query":"Choose M, N from {-5,-4}. M differs from N, It equals -5. Return a complete assignment."}}},
      {"task_id":"p19d_b05","stratum":"B_MULTI_FEASIBLE_PROPOSITION","view":{"instruction":SEMANTIC_INSTRUCTIONS[4],"public":{"query":"Choose A, B, C from {11,22,33}. A differs from B, A differs from C, B differs from C, It equals 33. Return a complete assignment."}}},
      {"task_id":"p19d_b06","stratum":"B_MULTI_FEASIBLE_PROPOSITION","view":{"instruction":SEMANTIC_INSTRUCTIONS[5],"public":{"query":"Choose P, Q, R, S from {-8,-6,-4,-2}. P differs from Q, P differs from R, P differs from S, Q differs from R, Q differs from S, R differs from S, It equals -4. Return a complete assignment."}}},
      {"task_id":"p19d_b07","stratum":"B_MULTI_FEASIBLE_PROPOSITION","view":{"instruction":SEMANTIC_INSTRUCTIONS[6],"public":{"query":"Choose M, N, O from {4,5,6}. M differs from N, M differs from O, N differs from O, It equals 5. Return a complete assignment."}}},
      {"task_id":"p19d_b08","stratum":"B_MULTI_FEASIBLE_PROPOSITION","view":{"instruction":SEMANTIC_INSTRUCTIONS[7],"public":{"query":"Choose X, Y from {12,13}. X differs from Y, It equals 13. Return a complete assignment."}}},
    ]
    refs=[
      {"task_id":"p19d_b01","family":"constraint_planning","expected_candidate":1,"semantic_grounding":"contingency path is the fallback path, so It denotes Y","private":{"domains":{"X":[7,9],"Y":[7,9]},"constraints":[["ne","X","Y"],["eq","Y",9]]},"witness":{"X":7,"Y":9}},
      {"task_id":"p19d_b02","family":"constraint_planning","expected_candidate":0,"semantic_grounding":"receiving queue is the entry queue, so It denotes A","private":{"domains":{"A":[2,4,6],"B":[2,4,6],"C":[2,4,6]},"constraints":[["ne","A","B"],["ne","A","C"],["ne","B","C"],["eq","A",6]]},"witness":{"A":6,"B":2,"C":4}},
      {"task_id":"p19d_b03","family":"constraint_planning","expected_candidate":2,"semantic_grounding":"radio is the communications subsystem, so It denotes R","private":{"domains":{"P":[10,20,30,40],"Q":[10,20,30,40],"R":[10,20,30,40],"S":[10,20,30,40]},"constraints":[["ne","P","Q"],["ne","P","R"],["ne","P","S"],["ne","Q","R"],["ne","Q","S"],["ne","R","S"],["eq","R",40]]},"witness":{"P":10,"Q":20,"R":40,"S":30}},
      {"task_id":"p19d_b04","family":"constraint_planning","expected_candidate":0,"semantic_grounding":"coordinator is the managerial role, so It denotes M","private":{"domains":{"M":[-5,-4],"N":[-5,-4]},"constraints":[["ne","M","N"],["eq","M",-5]]},"witness":{"M":-5,"N":-4}},
      {"task_id":"p19d_b05","family":"constraint_planning","expected_candidate":2,"semantic_grounding":"archive tier is long-term storage, so It denotes C","private":{"domains":{"A":[11,22,33],"B":[11,22,33],"C":[11,22,33]},"constraints":[["ne","A","B"],["ne","A","C"],["ne","B","C"],["eq","C",33]]},"witness":{"A":11,"B":22,"C":33}},
      {"task_id":"p19d_b06","family":"constraint_planning","expected_candidate":3,"semantic_grounding":"touchdown is the landing phase, so It denotes S","private":{"domains":{"P":[-8,-6,-4,-2],"Q":[-8,-6,-4,-2],"R":[-8,-6,-4,-2],"S":[-8,-6,-4,-2]},"constraints":[["ne","P","Q"],["ne","P","R"],["ne","P","S"],["ne","Q","R"],["ne","Q","S"],["ne","R","S"],["eq","S",-4]]},"witness":{"P":-8,"Q":-6,"R":-2,"S":-4}},
      {"task_id":"p19d_b07","family":"constraint_planning","expected_candidate":1,"semantic_grounding":"predictor is the forecasting component, so It denotes N","private":{"domains":{"M":[4,5,6],"N":[4,5,6],"O":[4,5,6]},"constraints":[["ne","M","N"],["ne","M","O"],["ne","N","O"],["eq","N",5]]},"witness":{"M":4,"N":5,"O":6}},
      {"task_id":"p19d_b08","family":"constraint_planning","expected_candidate":0,"semantic_grounding":"uplink is the ground-to-space link, so It denotes X","private":{"domains":{"X":[12,13],"Y":[12,13]},"constraints":[["ne","X","Y"],["eq","X",13]]},"witness":{"X":13,"Y":12}},
    ]
    return rows,refs

def negative_controls():
    return (
      {"instruction":"Unregistered P1.9 cue.","public":{"query":"Choose X, Y from {7,9}. X differs from Y, It equals 9. Return a complete assignment."}},
      {"instruction":SEMANTIC_INSTRUCTIONS[0],"public":{"query":"Choose X, Y from {0,1}. It equals 1, It equals 0. Return a complete assignment."}},
      {"instruction":SEMANTIC_INSTRUCTIONS[1],"public":{"query":"Choose A, B, C, D, E from {0,1,2,3,4}. It equals 2. Return a complete assignment."}},
      {"instruction":SEMANTIC_INSTRUCTIONS[2],"public":{"query":"Choose P, Q, R from {0,1,2}. It differs from P. Return a complete assignment."}},
    )
