"""Fresh P1.11 opened-development catalog.

Authored and frozen before any P1.11 pretrained MiniLM score.
"""
from neumann1.control_plane_p111_semantic import SEMANTIC_INSTRUCTIONS


def catalog():
    rows = [
        {"task_id":"p111d_b01","stratum":"B_MULTI_FEASIBLE_SEMANTIC_MICROEXECUTOR","view":{"instruction":SEMANTIC_INSTRUCTIONS[0],"public":{"query":"Choose X, Y from {31,47}. X differs from Y, It equals 47. Return a complete assignment."}}},
        {"task_id":"p111d_b02","stratum":"B_MULTI_FEASIBLE_SEMANTIC_MICROEXECUTOR","view":{"instruction":SEMANTIC_INSTRUCTIONS[1],"public":{"query":"Choose A, B, C from {6,10,15}. A differs from B, A differs from C, B differs from C, It equals 10. Return a complete assignment."}}},
        {"task_id":"p111d_b03","stratum":"B_MULTI_FEASIBLE_SEMANTIC_MICROEXECUTOR","view":{"instruction":SEMANTIC_INSTRUCTIONS[2],"public":{"query":"Choose P, Q, R, S from {22,44,66,88}. P differs from Q, P differs from R, P differs from S, Q differs from R, Q differs from S, R differs from S, It equals 44. Return a complete assignment."}}},
        {"task_id":"p111d_b04","stratum":"B_MULTI_FEASIBLE_SEMANTIC_MICROEXECUTOR","view":{"instruction":SEMANTIC_INSTRUCTIONS[3],"public":{"query":"Choose M, N from {-14,-11}. M differs from N, It equals -14. Return a complete assignment."}}},
        {"task_id":"p111d_b05","stratum":"B_MULTI_FEASIBLE_SEMANTIC_MICROEXECUTOR","view":{"instruction":SEMANTIC_INSTRUCTIONS[4],"public":{"query":"Choose A, B, C from {17,29,43}. A differs from B, A differs from C, B differs from C, It equals 17. Return a complete assignment."}}},
        {"task_id":"p111d_b06","stratum":"B_MULTI_FEASIBLE_SEMANTIC_MICROEXECUTOR","view":{"instruction":SEMANTIC_INSTRUCTIONS[5],"public":{"query":"Choose P, Q, R, S from {5,12,19,26}. P differs from Q, P differs from R, P differs from S, Q differs from R, Q differs from S, R differs from S, It equals 26. Return a complete assignment."}}},
        {"task_id":"p111d_b07","stratum":"B_MULTI_FEASIBLE_SEMANTIC_MICROEXECUTOR","view":{"instruction":SEMANTIC_INSTRUCTIONS[6],"public":{"query":"Choose M, N, O from {120,240,360}. M differs from N, M differs from O, N differs from O, It equals 360. Return a complete assignment."}}},
        {"task_id":"p111d_b08","stratum":"B_MULTI_FEASIBLE_SEMANTIC_MICROEXECUTOR","view":{"instruction":SEMANTIC_INSTRUCTIONS[7],"public":{"query":"Choose X, Y from {303,606}. X differs from Y, It equals 303. Return a complete assignment."}}},
        {"task_id":"p111d_b09","stratum":"B_MULTI_FEASIBLE_SEMANTIC_MICROEXECUTOR","view":{"instruction":SEMANTIC_INSTRUCTIONS[8],"public":{"query":"Choose A, B, C from {-8,0,8}. A differs from B, A differs from C, B differs from C, It equals 0. Return a complete assignment."}}},
        {"task_id":"p111d_b10","stratum":"B_MULTI_FEASIBLE_SEMANTIC_MICROEXECUTOR","view":{"instruction":SEMANTIC_INSTRUCTIONS[9],"public":{"query":"Choose P, Q, R, S from {7,14,21,28}. P differs from Q, P differs from R, P differs from S, Q differs from R, Q differs from S, R differs from S, It equals 21. Return a complete assignment."}}},
        {"task_id":"p111d_b11","stratum":"B_MULTI_FEASIBLE_SEMANTIC_MICROEXECUTOR","view":{"instruction":SEMANTIC_INSTRUCTIONS[10],"public":{"query":"Choose M, N, O from {11,23,37}. M differs from N, M differs from O, N differs from O, It equals 37. Return a complete assignment."}}},
        {"task_id":"p111d_b12","stratum":"B_MULTI_FEASIBLE_SEMANTIC_MICROEXECUTOR","view":{"instruction":SEMANTIC_INSTRUCTIONS[11],"public":{"query":"Choose X, Y from {404,808}. X differs from Y, It equals 808. Return a complete assignment."}}},
    ]
    refs = [
        {"task_id":"p111d_b01","family":"constraint_planning","expected_candidate":1,"semantic_grounding":"warm standby is the failover copy, so It denotes Y","private":{"domains":{"X":[31,47],"Y":[31,47]},"constraints":[["ne","X","Y"],["eq","Y",47]]},"witness":{"X":31,"Y":47}},
        {"task_id":"p111d_b02","family":"constraint_planning","expected_candidate":1,"semantic_grounding":"syntax analyzer builds the parse tree, so It denotes B","private":{"domains":{"A":[6,10,15],"B":[6,10,15],"C":[6,10,15]},"constraints":[["ne","A","B"],["ne","A","C"],["ne","B","C"],["eq","B",10]]},"witness":{"A":6,"B":10,"C":15}},
        {"task_id":"p111d_b03","family":"constraint_planning","expected_candidate":1,"semantic_grounding":"condenser rejects heat to the surroundings, so It denotes Q","private":{"domains":{"P":[22,44,66,88],"Q":[22,44,66,88],"R":[22,44,66,88],"S":[22,44,66,88]},"constraints":[["ne","P","Q"],["ne","P","R"],["ne","P","S"],["ne","Q","R"],["ne","Q","S"],["ne","R","S"],["eq","Q",44]]},"witness":{"P":22,"Q":44,"R":66,"S":88}},
        {"task_id":"p111d_b04","family":"constraint_planning","expected_candidate":0,"semantic_grounding":"public verification key checks whether a signature is valid, so It denotes M","private":{"domains":{"M":[-14,-11],"N":[-14,-11]},"constraints":[["ne","M","N"],["eq","M",-14]]},"witness":{"M":-14,"N":-11}},
        {"task_id":"p111d_b05","family":"constraint_planning","expected_candidate":0,"semantic_grounding":"scheduler assigns jobs to executors, so It denotes A","private":{"domains":{"A":[17,29,43],"B":[17,29,43],"C":[17,29,43]},"constraints":[["ne","A","B"],["ne","A","C"],["ne","B","C"],["eq","A",17]]},"witness":{"A":17,"B":29,"C":43}},
        {"task_id":"p111d_b06","family":"constraint_planning","expected_candidate":3,"semantic_grounding":"fusion engine combines multiple measurements into one state estimate, so It denotes S","private":{"domains":{"P":[5,12,19,26],"Q":[5,12,19,26],"R":[5,12,19,26],"S":[5,12,19,26]},"constraints":[["ne","P","Q"],["ne","P","R"],["ne","P","S"],["ne","Q","R"],["ne","Q","S"],["ne","R","S"],["eq","S",26]]},"witness":{"P":5,"Q":12,"R":19,"S":26}},
        {"task_id":"p111d_b07","family":"constraint_planning","expected_candidate":2,"semantic_grounding":"battery stores electrical energy, so It denotes O","private":{"domains":{"M":[120,240,360],"N":[120,240,360],"O":[120,240,360]},"constraints":[["ne","M","N"],["ne","M","O"],["ne","N","O"],["eq","O",360]]},"witness":{"M":120,"N":240,"O":360}},
        {"task_id":"p111d_b08","family":"constraint_planning","expected_candidate":0,"semantic_grounding":"upstream channel carries requests from the client toward the service, so It denotes X","private":{"domains":{"X":[303,606],"Y":[303,606]},"constraints":[["ne","X","Y"],["eq","X",303]]},"witness":{"X":303,"Y":606}},
        {"task_id":"p111d_b09","family":"constraint_planning","expected_candidate":1,"semantic_grounding":"control valve meters fluid flow, so It denotes B","private":{"domains":{"A":[-8,0,8],"B":[-8,0,8],"C":[-8,0,8]},"constraints":[["ne","A","B"],["ne","A","C"],["ne","B","C"],["eq","B",0]]},"witness":{"A":-8,"B":0,"C":8}},
        {"task_id":"p111d_b10","family":"constraint_planning","expected_candidate":2,"semantic_grounding":"object code is relocatable machine instructions emitted before final linking, so It denotes R","private":{"domains":{"P":[7,14,21,28],"Q":[7,14,21,28],"R":[7,14,21,28],"S":[7,14,21,28]},"constraints":[["ne","P","Q"],["ne","P","R"],["ne","P","S"],["ne","Q","R"],["ne","Q","S"],["ne","R","S"],["eq","R",21]]},"witness":{"P":7,"Q":14,"R":21,"S":28}},
        {"task_id":"p111d_b11","family":"constraint_planning","expected_candidate":2,"semantic_grounding":"localization filter estimates robot pose from sensor evidence, so It denotes O","private":{"domains":{"M":[11,23,37],"N":[11,23,37],"O":[11,23,37]},"constraints":[["ne","M","N"],["ne","M","O"],["ne","N","O"],["eq","O",37]]},"witness":{"M":11,"N":23,"O":37}},
        {"task_id":"p111d_b12","family":"constraint_planning","expected_candidate":1,"semantic_grounding":"friction brake removes kinetic energy to stop the machine, so It denotes Y","private":{"domains":{"X":[404,808],"Y":[404,808]},"constraints":[["ne","X","Y"],["eq","Y",808]]},"witness":{"X":404,"Y":808}},
    ]
    return rows, refs


def negative_controls():
    return (
        {"instruction":"Unregistered P1.11 cue.","public":{"query":"Choose X, Y from {31,47}. X differs from Y, It equals 47. Return a complete assignment."}},
        {"instruction":SEMANTIC_INSTRUCTIONS[0],"public":{"query":"Choose X, Y from {31,47}. It equals 47, It equals 31. Return a complete assignment."}},
        {"instruction":SEMANTIC_INSTRUCTIONS[1],"public":{"query":"Choose A, B, C, D, E from {1,2,3,4,5}. It equals 3. Return a complete assignment."}},
        {"instruction":SEMANTIC_INSTRUCTIONS[2],"public":{"query":"Choose P, Q, R from {22,44,66}. P mirrors Q, It equals 44. Return a complete assignment."}},
    )
