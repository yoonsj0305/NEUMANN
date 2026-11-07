"""NEUMANN Q3: induce a NEW executable binary algebra from example constraints.

This is *not* an AST ranker, fixed pixel mask, hard-coded ARC color priority,
or prewritten object->filter->raster pipeline.

Algorithm, for each external original TRAIN problem:
  1. Infer a typed decomposition of each grid into congruent sub-grids,
     potentially separated by previously unknown uniform gutters.
  2. Discover an algebraic law from observed n-ary INPUT/OUTPUT relations:
     find identity, infer directed pairwise dominance constraints, reject
     cycles, take transitive closure, and compile an *executable partial*
     associative, commutative and idempotent binary join.
  3. If an unseen combination has no derivable order, ABSTAIN, not guess.
  4. Freeze the induced operator AST and test-input predictions BEFORE the
     official heldout answers are inspected.

The *learning* signal is actual original input/output constraint data,
not labels of a prewritten correct macro; no target color ordering is
encoded. The inference is a classical symbolic learner where that is cheaper.

Limit: join is one human-specified inductive bias, not arbitrary original
semantics or a learned policy that invents all possible new primitives.
An actual real-original success is SCOPED Q3 LAW-INVENTION, not automatically
a global autonomous frontier Q3 PASS or Q4/Q6.

Scientific first covers every official public TRAIN original (400) and
the exact *previously project-opened* P25 EVAL 32, not reserved unseen eval.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import NamedTuple

SOURCE="fchollet/ARC-AGI"
PIN="399030444e0ab0cc8b4e199870fb20b863846f34"
EVAL32=("2037f2c7","c87289bb","281123b4","0a1d4ef5","1c56ad9f",
 "c074846d","137f0df0","62ab2642","1a2e2828","f83cb3f6",
 "f3e62deb","68b67ca3","9ddd00f0","9772c176","b4a43f3b",
 "2685904e","96a8c0cd","7c8af763","0b17323b","0a2355a6",
 "0c9aba6e","81c0276b","31adaf00","6a11f6da","e7b06bea",
 "4b6b68e5","2a5f8217","93b4f4b3","a57f2f04","c1990cce",
 "4cd1b7b2","1e81d6f9")
SCHEMA="neumann.q3.induced-binary-algebra-from-external-originals.v1"


class CannotInfer(Exception):
    pass


def grid_ok(grid):
    return (isinstance(grid,list) and 1<=len(grid)<=30
            and isinstance(grid[0],list) and 1<=len(grid[0])<=30
            and all(isinstance(row,list) and len(row)==len(grid[0])
                    and all(type(v) is int and 0<=v<=9 for v in row)
                    for row in grid))


class Decomposition(NamedTuple):
    axis: str
    panel: int
    gutter: int
    count: int

    def to_data(self):
        return {"axis":self.axis,"panel":self.panel,
                "gutter":self.gutter,"count":self.count}


def subgrids(grid, decomp:Decomposition):
    """Generic executable partition program; no target color or target rule."""
    if not grid_ok(grid):return None
    h,w=len(grid),len(grid[0])
    p,g,m=decomp.panel,decomp.gutter,decomp.count
    if not (1<=p<=30 and g in (0,1) and 2<=m<=9):return None
    size=(w if decomp.axis=="columns" else h)
    other=(h if decomp.axis=="columns" else w)
    if p*m+(m-1)*g!=size:return None
    # Infer structural separators from raw input only, never from output.
    if g:
        colors=set()
        for k in range(1,m):
            i=k*p+(k-1)*g
            values={grid[y][i] for y in range(h)} if decomp.axis=="columns" \
                else set(grid[i])
            if len(values)!=1:return None
            colors.update(values)
        if len(colors)!=1:return None
    panels=[]
    for k in range(m):
        first=k*(p+g)
        if decomp.axis=="columns":
            panels.append([row[first:first+p] for row in grid])
        else:
            panels.append([row[:] for row in grid[first:first+p]])
    if any(not grid_ok(t) for t in panels):return None
    if len({(len(t),len(t[0])) for t in panels})!=1:return None
    return panels


def enumerate_decompositions(train):
    """Infer possible type-altering grid layouts without knowing any solution."""
    if not train:return
    shapes=[(len(row["input"]),len(row["input"][0]),
             len(row["output"]),len(row["output"][0])) for row in train]
    for axis in ("columns","rows"):
      for gutter in (0,1):
        counts=set()
        sizes=set()
        for h,w,oh,ow in shapes:
            if axis=="columns":
                if h!=oh:break
                p=ow;span=w
            else:
                if w!=ow:break
                p=oh;span=h
            if p<=0 or (span+gutter)%(p+gutter):break
            count=(span+gutter)//(p+gutter)
            if not 2<=count<=9:break
            counts.add(count)
            sizes.add(p)
        else:
            if len(counts)==1 and len(sizes)==1:
                d=Decomposition(axis,p,gutter,count)
                if all(subgrids(pair["input"],d) is not None for pair in train):
                    yield d


def closure_relations(colors, dominance):
    """Sound transitive closure. A cycle means no such partial-order law."""
    reach={a:set() for a in colors}
    for loser,winner in dominance:
        if loser==winner:continue
        if loser not in reach or winner not in reach:raise CannotInfer("BAD_ORDER")
        reach[loser].add(winner)
    for intermediate in colors:
        for a in colors:
            if intermediate in reach[a]:
                reach[a].update(reach[intermediate])
    if any(x in reach[x] for x in colors):
        raise CannotInfer("INCONSISTENT_DOMINANCE")
    return {a:tuple(sorted(v)) for a,v in reach.items()}


@dataclass(frozen=True)
class InventedJoin:
    identity: int
    edges:tuple
    colors:tuple

    def semantics(self):
        return closure_relations(self.colors,self.edges)

    def to_ast(self):
        """A new, runnable lambda, *learned* edge parameters are in the term."""
        return ["DefineOperator","learned_join",
          ["lambda",["a","b"],
            ["ChooseUniqueMaxUnder",
              ["Identity",self.identity],
              ["LearnedStrictOrder",[[a,b] for a,b in self.edges]],
              ["Vars","a","b"],
              ["Unknown","ABSTAIN"]
            ]],
          ["Laws","commutative","associative","idempotent",
           "identity"],
        ]

    def compile(self):
        # This is compiled closure, not a pick from a list of target programs.
        table=self.semantics()
        ident=self.identity
        def invented(a:int,b:int):
            if a==ident:return b
            if b==ident:return a
            if a==b:return a
            if a not in table or b not in table:
                return None
            if b in table[a]:return b
            if a in table[b]:return a
            return None  # Incomparable, fail-closed.
        return invented

    def all_laws_hold(self):
        op=self.compile()
        elems=set(self.colors)
        if self.identity not in elems:elems.add(self.identity)
        for a in elems:
            if op(a,self.identity)!=a or op(a,a)!=a:return False
            for b in elems:
                if op(a,b)!=op(b,a):return False
                for c in elems:
                    ab=op(a,b);bc=op(b,c)
                    x=op(ab,c) if ab is not None else None
                    y=op(a,bc) if bc is not None else None
                    if x!=y:
                        # Algebraic law only asserted on defined triples.
                        if x is not None or y is not None:return False
        return True


def train_invention(train,decomp,identity):
    """Invent color order exclusively from observed original TRAIN behavior."""
    pairs=set()
    used=set()
    overlap_cases=0
    meaningful_winners=0
    evidence=0
    for task in train:
        grid, expected=task["input"],task["output"]
        panels=subgrids(grid,decomp)
        if panels is None:return None
        h,w=len(expected),len(expected[0])
        if any(len(p)!=h or len(p[0])!=w for p in panels):
            return None
        for y in range(h):
          for x in range(w):
            values=[p[y][x] for p in panels]
            observed=expected[y][x]
            if observed not in values:
                return None
            members={v for v in values if v!=identity}
            used.update(members)
            if len(members)>=2:overlap_cases+=1
            if observed==identity:
                if members:return None
                continue
            if observed not in members:return None
            meaningful_winners+=1
            for v in members-{observed}:
                evidence+=1
                pairs.add((v,observed))
    if len(used)<3 or len(pairs)<2 or overlap_cases<2 or evidence<3:
        # An operator learned from only one trivial equality is not an invention.
        return None
    try:
        closure_relations(used|{identity},pairs)
    except CannotInfer:
        return None
    operator=InventedJoin(identity,tuple(sorted(pairs)),
                          tuple(sorted(used|{identity})))
    if not operator.all_laws_hold():
        return None
    # Replaying TRAIN is required to reject any overgeneralized law.
    if any(predict_single(operator,decomp,t["input"])!=t["output"] for t in train):
        return None
    return operator


def predict_single(law,decomp,grid):
    panels=subgrids(grid,decomp)
    if panels is None:return None
    out=[row[:] for row in panels[0]]
    join=law.compile()
    for part in panels[1:]:
        for y in range(len(out)):
            for x in range(len(out[0])):
                out[y][x]=join(out[y][x],part[y][x])
                if out[y][x] is None:return None
    return out


def infer_programs(train):
    if not train or not all(grid_ok(q["input"]) and grid_ok(q["output"])
                            for q in train):return []
    candidates=[]
    for d in enumerate_decompositions(train):
        colors={v for pair in train for v in (x for row in pair["input"] for x in row)}
        ranked=[v for v,n in Counter(v for pair in train
                   for row in pair["input"] for v in row).most_common()]
        for identity in ranked:
            program=train_invention(train,d,identity)
            if program is None:continue
            item={
                "decomposition":d.to_data(),
                "learned_binary_operator_AST":program.to_ast(),
                "learned_comparison_edges":len(program.edges),
                # Identity must be inferred from input frequency, not from
                # a source-dependent hand-authored target color.
                "identity_input_occurrences":sum(
                    row.count(identity) for task in train
                    for row in task["input"]),
                "inferred_type":"Grid -> List[Grid] -> Fold(LearnedJoin) -> Grid",
                "source_external_target_code_given_to_learner":False,
                "learned_law_semantics":True,
                "learned_order":program.edges,
                "_decomp":d,"_law":program,
            }
            candidates.append(item)
    # Unresolved source ambiguity remains as multiple programs and must
    # abstain on disagreeing TEST predictions; never inspect gold for choice.
    return candidates


def admit_program(train):
    programs=infer_programs(train)
    if not programs:return None
    # Identity is NOT chosen by minimizing the number of learned edges:
    # that wrongly favored arbitrary non-background colors, exactly a
    # structural underidentification counterexample caught before ORIGINAL.
    # Prefer the observed input modal color first (generic inductive bias),
    # then the shortest law among equally supported identities.
    programs.sort(key=lambda p:(
        -p["identity_input_occurrences"],p["learned_comparison_edges"],
        p["decomposition"]["gutter"],p["decomposition"]["axis"]))
    best=programs[0]
    # Freeze every equally good observed-data model, reject disagreeing
    # answers after test inputs without ever inspecting test gold.
    optimum=(best["identity_input_occurrences"],
             best["learned_comparison_edges"])
    equal=[p for p in programs
           if (p["identity_input_occurrences"],p["learned_comparison_edges"])
              == optimum]
    return {"models":equal,"selected_programs":len(equal),
            "candidate_programs":len(programs)}


def predict_frozen(admitted,test_grid):
    if admitted is None:return None
    predictions=[]
    for item in admitted["models"]:
        predicted=predict_single(item["_law"],item["_decomp"],test_grid)
        if predicted is None:return None
        predictions.append(predicted)
    if not predictions:return None
    key=json.dumps(predictions[0])
    if any(json.dumps(p)!=key for p in predictions[1:]):
        return None
    return predictions[0]


def serialize(admitted):
    if admitted is None:return None
    return {
      "number_consistent_models":admitted["candidate_programs"],
      "number_admitted_minimum_models":admitted["selected_programs"],
      "programs":[{k:v for k,v in model.items() if not k.startswith("_")}
                  for model in admitted["models"]],
    }


def study_one(task,identifier,cohort):
    raw_train=task["train"]
    admitted=admit_program(raw_train)
    frozen=serialize(admitted)
    fingerprint=hashlib.sha256(json.dumps(frozen,sort_keys=True).encode()).hexdigest()
    # All operator definitions are frozen BEFORE reading ANY test output.
    predictions=[predict_frozen(admitted,case["input"]) for case in task["test"]]
    result=[prediction==case["output"] for prediction,case
            in zip(predictions,task["test"])]
    submitted=all(p is not None for p in predictions)
    exact=submitted and all(result)
    # Strict learning necessity: abolish learned comparisons. Any nontrivial
    # overlap should become an ABSTAIN with a blank (=unlearned) law.
    blank_out=[]
    if admitted is not None and admitted["models"]:
        for entry in admitted["models"]:
            empty=InventedJoin(entry["_law"].identity,(),
                               entry["_law"].colors)
            blank_out.append([predict_single(empty,entry["_decomp"],q["input"])
                        for q in task["test"]])
    independent_of_edges=any(
        all(pred is not None and pred==q["output"]
            for pred,q in zip(case,task["test"]))
        for case in blank_out
    ) if blank_out else False
    return {
       "original_id":identifier,
       "cohort":cohort,
       "learned_ast_frozen_sha256":fingerprint,
       "model":frozen,
       "proposed":frozen is not None,
       "submitted":submitted,
       "original_TEST_exact":exact,
       "original_TEST_wrong_submission":submitted and not exact,
       "learning_is_necessary_on_this_original":exact and not independent_of_edges,
       "original_test_cases":len(task["test"]),
       "operator_new_strict_comparisons":(
           sum(p["learned_comparison_edges"] for p in frozen["programs"])
           if frozen else 0),
       "prediction_sha256":[hashlib.sha256(
            json.dumps(p,sort_keys=True).encode()).hexdigest() if p is not None
            else None for p in predictions],
    }


def run(arc_root:Path,out:Path):
    if out.exists():raise ValueError("NO_OVERWRITE_ORIGINAL_FIRST")
    out.mkdir(parents=True)
    rows=[]
    for group,folder,ids in (
        ("official_public_TRAIN_400","training",None),
        ("previously_opened_eval_P25_32","evaluation",EVAL32)
    ):
        datadir=arc_root/"data"/folder
        files=(sorted(datadir.glob("*.json")) if ids is None else
               [datadir/(x+".json") for x in ids])
        if ids is None and len(files)!=400:
            raise ValueError("EXPECTED_PINNED_400_PUBLIC_TRAIN")
        if ids is not None and len(files)!=32:
            raise ValueError("EXPECTED_PREVIOUS_32_EVAL")
        for file in files:
            task=json.loads(file.read_text())
            rec=study_one(task,file.stem,group)
            rows.append(rec)
            if rec["proposed"] or rec["original_TEST_exact"]:
                print(group,file.stem,"operator",rec["operator_new_strict_comparisons"],
                      "correct",rec["original_TEST_exact"],flush=True)
    groups={}
    for group in ("official_public_TRAIN_400","previously_opened_eval_P25_32"):
        subset=[r for r in rows if r["cohort"]==group]
        groups[group]={
          "original_tasks":len(subset),
          "new_operator_definitions":sum(r["proposed"] for r in subset),
          "test_submissions":sum(r["submitted"] for r in subset),
          "original_test_exact":sum(r["original_TEST_exact"] for r in subset),
          "original_test_wrong_submissions":sum(r["original_TEST_wrong_submission"] for r in subset),
          "learned_law_required_for_correctness":sum(r["learning_is_necessary_on_this_original"] for r in subset),
        }
    report={
      "schema":SCHEMA,"pin":PIN,
      "scientific_scope":"ORIGINAL_PUBLIC_TRAIN_PLUS_PREVIOUSLY_OPENED_EVAL_DEV",
      "prewritten_target_priority":False,
      "machine_induced_new_binary_operator_laws":True,
      "new_public_eval_reserved_ids_consumed":0,
      "Q3_GLOBAL":"OPEN","Q4":"OPEN","Q6":"OPEN",
      "groups":groups,"rows":rows,
    }
    (out/"FIRST.json").write_text(json.dumps(report,sort_keys=True,indent=2)+"\n")
    print("SCOPED_RESULTS",json.dumps({k:v for k,v in report.items() if k!="rows"},sort_keys=True))
    return report


if __name__=="__main__":
    arg=argparse.ArgumentParser()
    arg.add_argument("--arc-root",type=Path,required=True)
    arg.add_argument("--out",type=Path,required=True)
    a=arg.parse_args()
    run(a.arc_root,a.out)
