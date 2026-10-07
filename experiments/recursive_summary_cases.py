"""Known offline summary formulas; explicit O,not autonomous discovery."""
from neumann1.recursive_summary import program
from neumann1.recursive_symbolic_baseline import conjunction


def known_summary(problem,name):
    d=len(problem["empty"])
    z=[f"z{i}" for i in range(d)]
    def rename(t):
        if isinstance(t,str) and t.startswith("r") and t[1:].isdigit():return "z"+t[1:]
        return [rename(c) for c in t] if isinstance(t,list) else t
    if name=="sum":merge=[["add","l0","r0"]];invariant=True
    elif name=="mps":
        merge=[["max","l0",["add","l1","r0"]],["add","l1","r1"]]
        invariant=conjunction([["ge","z0",0],["ge","z0","z1"]])
    elif name=="mts":
        merge=[["max","r0",["add","l0","r1"]],["add","l1","r1"]]
        invariant=conjunction([["ge","z0",0],["ge","z0","z1"]])
    elif name=="mss":
        merge=[["add","l0","r0"],["max","r1",["add","l1","r0"]],
               ["max","l2",["add","l0","r2"]],
               ["max",["max","l3","r3"],["add","l1","r2"]]]
        invariant=conjunction([["ge","z1",0],["ge","z2",0],["ge","z2","z0"],["ge","z1","z0"],
                               ["ge","z3",0],["ge","z3","z1"],["ge","z3","z0"],["ge","z3","z2"]])
    else:raise ValueError("Unknown offline example")
    return {"empty":list(problem["empty"]),"step":program(["head"]+z,[rename(t) for t in problem["step"]["outputs"]]),
            "merge":program([f"l{i}" for i in range(d)]+[f"r{i}" for i in range(d)],merge),
            "decode":program(z,z),"invariant":program(z,[invariant])}


def lifted_prefix():
    problem={"semantics":"integer_list_right_fold","empty":[0],
             "step":program(["head","r0"],[["max",["add","head","r0"],0]])}
    proposal={"empty":[0,0],"step":program(["head","z0","z1"],[["max",["add","head","z0"],0],["add","head","z1"]]),
              "merge":program(["l0","l1","r0","r1"],[["max","l0",["add","l1","r0"]],["add","l1","r1"]]),
              "decode":program(["z0","z1"],["z0"]),
              "invariant":program(["z0","z1"],[["and",["ge","z0",0],["ge","z0","z1"]]])}
    return problem,proposal


def tree(values,shape):
    if not values:return ["nil"]
    if len(values)==1:return ["single",values[0]]
    cut=1 if shape=="right" else len(values)-1 if shape=="left" else len(values)//2
    return ["concat",tree(values[:cut],shape),tree(values[cut:],shape)]
