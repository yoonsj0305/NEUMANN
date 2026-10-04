"""Authored opened CPU interface checks, frozen before the first route run.

The type determines the specialist deliberately. This is a contract diagnostic,
not independent semantic routing evidence or an external capability benchmark.
"""
from neumann1.control_plane_v1 import snapshot


def catalog():
    rows = []; references = []
    def add(public, expected_status, eligible, selected=None, family=None, private=None, witness=None):
        task_id = "p13v_%02d" % (len(rows)+1)
        rows.append({"task_id": task_id, "view": {"instruction": "Satisfy the original public problem obligations.", "public": public}})
        references.append({"task_id": task_id, "status": expected_status, "admissible_routes": eligible,
                           "selected_route": selected, "family": family, "private": private, "witness": witness})
    for expression,bindings,exact in (
        ("(a-b*c)/(d+e*f)", {"a":31,"b":4,"c":6,"d":3,"e":2,"f":5}, "7/13"),
        ("(a/(b-c)+d)*(e+f)", {"a":12,"b":5,"c":1,"d":2,"e":3,"f":4}, "35"),
        ("-(a-b)/(c+d/e)", {"a":8,"b":3,"c":2,"d":6,"e":3}, "-5/4"),
        ("(a+b)/(c-d/(e+f))", {"a":7,"b":2,"c":5,"d":4,"e":1,"f":3}, "9/4")):
        add({"expression":expression,"bindings":bindings,"background":"Irrelevant planning and coding words."},
            "SELECTED", ["ARITHMETIC"], "ARITHMETIC", "math_logic", {"exact":exact}, exact)
    coding = (
        ("Return the inclusive running maxima of items, a list of integers. Empty input returns [].",
         "def solve(items):\n    return [max(items[:i+1]) for i in range(len(items))]\n",
         [([],[]),([3,1,4,2],[3,3,4,4]),([-5,-7,-2],[-5,-5,-2]),([0],[0]),([2,2,1],[2,2,2])]),
        ("Rotate the integer list items one place to the left. Empty input returns [].",
         "def solve(items):\n    return items[1:]+items[:1]\n",
         [([],[]),([1],[1]),([4,5,6],[5,6,4]),([-2,0],[0,-2]),([3,3],[3,3])]),
        ("Return the smallest nonnegative integer absent from items, a list of integers.",
         "def solve(items):\n    n=0\n    while n in items:\n        n+=1\n    return n\n",
         [([],0),([0,1,3],2),([-1,-2],0),([1,2],0),([2,0,1,0],3)]),
        ("Return the absolute difference of each consecutive pair in items, in order. Length below two returns [].",
         "def solve(items):\n    return [abs(items[i+1]-items[i]) for i in range(len(items)-1)]\n",
         [([],[]),([4],[]),([1,5,2],[4,3]),([-3,-7,0],[4,7]),([2,2],[0])]))
    for requirement,source,cases in coding:
        tests = [{"input":i,"output":o} for i,o in cases]
        add({"requirement":requirement,"examples":[tests[1]],"background":"Irrelevant arithmetic words."},
            "SELECTED", ["PYTHON"], "PYTHON", "coding", {"tests":tests}, source)
    planning = (
        ({"a":[0,1,2,3,4],"b":[0,1,2,3,4],"c":[0,1,2,3,4],"d":[0,1,2,3,4],"e":[0,1,2,3,4]},
         [["lt","a","b"],["lt","b","c"],["lt","c","d"],["lt","d","e"],["ne","a","d"]],
         {"a":0,"b":1,"c":2,"d":3,"e":4}),
        ({"v%d"%i:[0,1,2] for i in range(6)},
         [["ne","v%d"%i,"v%d"%((i+1)%6)] for i in range(6)]+[["ne","v0","v2"]],
         {"v%d"%i:i%3 for i in range(6)}),
        ({"h":[0,1,2,3],"a":[0,1,2,3],"b":[0,1,2,3],"c":[0,1,2,3],"d":[0,1,2,3]},
         [["eq","h",2]]+[["lt",n,"h"] for n in ("a","b","c","d")],
         {"h":2,"a":0,"b":1,"c":0,"d":1}),
        ({"a":[0,1],"b":[0,1],"c":[0,1],"d":[0,1],"e":[0,1]},
         [["ne",a,b] for a in ("a","b") for b in ("c","d","e")],
         {"a":0,"b":0,"c":1,"d":1,"e":1}))
    for domains,constraints,witness in planning:
        add({"domains":domains,"constraints":constraints,"background":"ARITHMETIC is just irrelevant text."},
            "SELECTED", ["CSP"], "CSP", "constraint_planning", {}, witness)
    invalid = (
        {"expression":"x+1"},
        {"expression":"x**2","bindings":{"x":3}},
        {"expression":"x+1","bindings":{"x":True}},
        {"domains":{"a":[0,1]},"constraints":[["ne","a","missing"]]},
        {"domains":{"a":[0,1]},"constraints":[["unknown","a",0]]},
        {"domains":{"a":[0,1,1]},"constraints":[]},
        {"requirement":"Return a list.","examples":[{"input":[],"output":[],"hidden_answer":[]} ]},
        {"requirement":" ","examples":[{"input":[],"output":[]}]})
    for public in invalid: add(public,"REJECTED",[])
    add({"expression":"a/b","bindings":{"a":8,"b":2},"domains":{"p":[0,1],"q":[0,1]},
         "constraints":[["ne","p","q"]]}, "NEEDS_SEMANTIC_FALLBACK", ["ARITHMETIC","CSP"])
    add({"requirement":"Return the number of list elements.","examples":[{"input":[1,2],"output":2}],
         "domains":{"u":[1,2],"v":[1,2]},"constraints":[["le","u","v"]]},
        "NEEDS_SEMANTIC_FALLBACK", ["CSP","PYTHON"])
    add({"query":"How many distinct integer triples satisfy the conditions described in prose?"},
        "NEEDS_SEMANTIC_INTERPRETATION", ["DIRECT"])
    add({"query":"Write a program satisfying an incomplete natural-language specification."},
        "NEEDS_SEMANTIC_INTERPRETATION", ["DIRECT"])
    return snapshot(rows), snapshot(references)
