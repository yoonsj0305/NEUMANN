"""Fresh P1.9 opened-development catalog, authored before any P1.9 Gemma score."""
from neumann1.control_plane_p19_semantic import SEMANTIC_INSTRUCTIONS

def catalog():
    rows=[
      {"task_id":"p19d_b01","stratum":"B_MULTI_FEASIBLE_PROPOSITION","view":{"instruction":SEMANTIC_INSTRUCTIONS[0],"public":{"query":"Choose X, Y from {0,1}. X differs from Y, It equals 1. Return a complete assignment."}}},
      {"task_id":"p19d_b02","stratum":"B_MULTI_FEASIBLE_PROPOSITION","view":{"instruction":SEMANTIC_INSTRUCTIONS[1],"public":{"query":"Choose A, B, C from {0,1,2}. A differs from B, A differs from C, B differs from C, It equals 2. Return a complete assignment."}}},
      {"task_id":"p19d_b03","stratum":"B_MULTI_FEASIBLE_PROPOSITION","view":{"instruction":SEMANTIC_INSTRUCTIONS[2],"public":{"query":"Choose P, Q, R, S from {0,1,2,3}. P differs from Q, P differs from R, P differs from S, Q differs from R, Q differs from S, R differs from S, It equals 3. Return a complete assignment."}}},
      {"task_id":"p19d_b04","stratum":"B_MULTI_FEASIBLE_PROPOSITION","view":{"instruction":SEMANTIC_INSTRUCTIONS[3],"public":{"query":"Choose M, N from {-1,0}. M differs from N, It equals -1. Return a complete assignment."}}},
      {"task_id":"p19d_b05","stratum":"B_MULTI_FEASIBLE_PROPOSITION","view":{"instruction":SEMANTIC_INSTRUCTIONS[4],"public":{"query":"Choose A, B, C from {10,20,30}. A differs from B, A differs from C, B differs from C, It equals 30. Return a complete assignment."}}},
      {"task_id":"p19d_b06","stratum":"B_MULTI_FEASIBLE_PROPOSITION","view":{"instruction":SEMANTIC_INSTRUCTIONS[5],"public":{"query":"Choose P, Q, R, S from {-3,-2,-1,0}. P differs from Q, P differs from R, P differs from S, Q differs from R, Q differs from S, R differs from S, It equals -1. Return a complete assignment."}}},
      {"task_id":"p19d_b07","stratum":"B_MULTI_FEASIBLE_PROPOSITION","view":{"instruction":SEMANTIC_INSTRUCTIONS[6],"public":{"query":"Choose M, N, O from {1,2,3}. M differs from N, M differs from O, N differs from O, It equals 2. Return a complete assignment."}}},
      {"task_id":"p19d_b08","stratum":"B_MULTI_FEASIBLE_PROPOSITION","view":{"instruction":SEMANTIC_INSTRUCTIONS[7],"public":{"query":"Choose X, Y from {5,6}. X differs from Y, It equals 6. Return a complete assignment."}}},
    ]
    refs=[
      {"task_id":"p19d_b01","family":"constraint_planning","expected_candidate":1,"semantic_grounding":"contingency path is the fallback path, so It denotes Y","private":{"domains":{"X":[0,1],"Y":[0,1]},"constraints":[["ne","X","Y"],["eq","Y",1]]},"witness":{"X":0,"Y":1}},
      {"task_id":"p19d_b02","family":"constraint_planning","expected_candidate":0,"semantic_grounding":"receiving queue is the entry queue, so It denotes A","private":{"domains":{"A":[0,1,2],"B":[0,1,2],"C":[0,1,2]},"constraints":[["ne","A","B"],["ne","A","C"],["ne","B","C"],["eq","A",2]]},"witness":{"A":2,"B":0,"C":1}},
      {"task_id":"p19d_b03","family":"constraint_planning","expected_candidate":2,"semantic_grounding":"radio is the communications subsystem, so It denotes R","private":{"domains":{"P":[0,1,2,3],"Q":[0,1,2,3],"R":[0,1,2,3],"S":[0,1,2,3]},"constraints":[["ne","P","Q"],["ne","P","R"],["ne","P","S"],["ne","Q","R"],["ne","Q","S"],["ne","R","S"],["eq","R",3]]},"witness":{"P":0,"Q":1,"R":3,"S":2}},
      {"task_id":"p19d_b04","family":"constraint_planning","expected_candidate":0,"semantic_grounding":"coordinator is the managerial role, so It denotes M","private":{"domains":{"M":[-1,0],"N":[-1,0]},"constraints":[["ne","M","N"],["eq","M",-1]]},"witness":{"M":-1,"N":0}},
      {"task_id":"p19d_b05","family":"constraint_planning","expected_candidate":2,"semantic_grounding":"archive tier is long-term storage, so It denotes C","private":{"domains":{"A":[10,20,30],"B":[10,20,30],"C":[10,20,30]},"constraints":[["ne","A","B"],["ne","A","C"],["ne","B","C"],["eq","C",30]]},"witness":{"A":10,"B":20,"C":30}},
      {"task_id":"p19d_b06","family":"constraint_planning","expected_candidate":3,"semantic_grounding":"touchdown is the landing phase, so It denotes S","private":{"domains":{"P":[-3,-2,-1,0],"Q":[-3,-2,-1,0],"R":[-3,-2,-1,0],"S":[-3,-2,-1,0]},"constraints":[["ne","P","Q"],["ne","P","R"],["ne","P","S"],["ne","Q","R"],["ne","Q","S"],["ne","R","S"],["eq","S",-1]]},"witness":{"P":-3,"Q":-2,"R":0,"S":-1}},
      {"task_id":"p19d_b07","family":"constraint_planning","expected_candidate":1,"semantic_grounding":"predictor is the forecasting component, so It denotes N","private":{"domains":{"M":[1,2,3],"N":[1,2,3],"O":[1,2,3]},"constraints":[["ne","M","N"],["ne","M","O"],["ne","N","O"],["eq","N",2]]},"witness":{"M":1,"N":2,"O":3}},
      {"task_id":"p19d_b08","family":"constraint_planning","expected_candidate":0,"semantic_grounding":"uplink is the ground-to-space link, so It denotes X","private":{"domains":{"X":[5,6],"Y":[5,6]},"constraints":[["ne","X","Y"],["eq","X",6]]},"witness":{"X":6,"Y":5}},
    ]
    return rows,refs

def negative_controls():
    return (
      {"instruction":"Unregistered P1.9 cue.","public":{"query":"Choose X, Y from {0,1}. X differs from Y, It equals 1. Return a complete assignment."}},
      {"instruction":SEMANTIC_INSTRUCTIONS[0],"public":{"query":"Choose X, Y from {0,1}. It equals 1, It equals 0. Return a complete assignment."}},
      {"instruction":SEMANTIC_INSTRUCTIONS[1],"public":{"query":"Choose A, B, C, D, E from {0,1,2,3,4}. It equals 2. Return a complete assignment."}},
      {"instruction":SEMANTIC_INSTRUCTIONS[2],"public":{"query":"Choose P, Q, R from {0,1,2}. P differs from Q. Return a complete assignment."}},
    )
