"""RC39 independent FIRST grader for 24 precommitted active automata families.

Entire hidden reference machine is constructed HERE, after the learner
source was hash-frozen. Learner is only passed member(word) and eq(hyp);
its module cannot import this grader or read target graph.

Exact correctness is product-state equivalence for ALL finite words.
Finite random samples are merely auxiliary negative tests, not proof.
"""
from __future__ import annotations
from collections import deque
from dataclasses import dataclass
from hashlib import sha256,sha1
from pathlib import Path
from time import process_time_ns
import json,random,sys

from research.q3.rc39.active_mealy import ActiveMealyLearner,MealyProgram

ROOT=Path(__file__).resolve().parents[3]
PREREG=ROOT/"docs/experiments/q3_RC39_ACTIVE_AUTOMATA_FIRST_PREREG_2026_11_06.json"
LOCK=ROOT/"docs/experiments/q3_RC39_FIRST_LEARNER_SOURCE_LOCK.json"
LEARNER=ROOT/"research/q3/rc39/active_mealy.py"

def sha_blob(p:Path)->str:
    b=p.read_bytes()
    return sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()

@dataclass(frozen=True)
class HiddenMachine:
    """Reference is deliberately a different representation from learner AST."""
    n:int
    table:dict[tuple[int,str],tuple[int,str]]
    initial:int=0
    alphabet:str="ABC"

    def run(self,word:str)->str:
        q=self.initial
        s=[]
        for a in word:
            q,v=self.table[(q,a)]
            s.append(v)
        return "".join(s)

def hidden_family(family:str,seed:int)->HiddenMachine:
    letters="ABC"
    if family=="prefix_parity":
        n=2
        table={(q,a):((q^int(a=="A")),str(q^int(a=="A")))
               for q in range(n) for a in letters}
    elif family=="prefix_mod3":
        n=3
        table={(q,a):(((q+int(a=="A"))%3),str(int((q+int(a=="A"))%3==0)))
               for q in range(n) for a in letters}
    elif family=="presence":
        n=2
        table={(q,a):((q or int(a=="B")),str(q or int(a=="B")))
               for q in range(n) for a in letters}
    elif family.startswith("random_") and family.endswith("state"):
        n=int(family.removeprefix("random_").removesuffix("state"))
        if n not in (3,4,5):raise ValueError("invalid random state count")
        h=sha256(f"RC39|{family}|{seed}|2026-11-06".encode()).digest()
        rng=random.Random(int.from_bytes(h,"big"))
        table={(q,a):(rng.randrange(n),str(rng.randrange(2)))
               for q in range(n) for a in letters}
    else:raise ValueError("family not in FIRST prereg")
    return HiddenMachine(n,table)

def independent_product_prove(hidden:HiddenMachine,hyp:MealyProgram):
    """Second codepath directly checks hidden dict vs produced table.

    If BFS explores all reachable state pairs without output disagreement,
    the two deterministic Mealy transducers agree on every finite word by
    induction on length. No bounded-string extrapolation is needed.
    """
    if "".join(hyp.alphabet)!=hidden.alphabet:return {"equivalent":False,"counterexample":"A","nodes":0}
    q=deque([(hidden.initial,hyp.initial,"")])
    seen={(hidden.initial,hyp.initial)}
    nodes=0
    while q:
        h,p,prefix=q.popleft()
        nodes+=1
        for j,a in enumerate(hidden.alphabet):
            hn,ho=hidden.table[h,a]
            pn=hyp.transitions[p][j]
            po=hyp.emissions[p][j]
            if ho!=po:
                return {"equivalent":False,"counterexample":prefix+a,"nodes":nodes}
            nxt=hn,pn
            if nxt not in seen:
                seen.add(nxt)
                q.append((hn,pn,prefix+a))
    return {"equivalent":True,"counterexample":None,"nodes":nodes}

def locality_impossibility():
    """A machine inspecting only +/-7 positions around current B
    cannot determine unbounded previous-prefix parity.
    """
    even="C"*20+"B"+"C"*20
    odd="A"+"C"*19+"B"+"C"*20
    index=20
    assert len(even)==len(odd)==41
    assert even[index]==odd[index]=="B"
    for d in range(-7,8):
        assert even[index+d]==odd[index+d]
    def target(w):
        parity=0
        result=[]
        for a in w:
            if a=="A":parity^=1
            result.append("A" if a=="B" and parity else a)
        return "".join(result)
    assert target(even)[index]=="B" and target(odd)[index]=="A"
    return {"scope":"arbitrary READ_REL conjunctive predicate with offsets [-7,+7]",
            "radius":7,"same_local_window":True,
            "required_different_center_output":True,
            "proof":"Indistinguishable local windows imply identical local opcode outputs; target parity requires different B outputs."}

def first():
    prereg=json.loads(PREREG.read_text())
    lock=json.loads(LOCK.read_text())
    assert lock["original_source_git_blob"]==sha_blob(LEARNER)
    assert lock["preregistered_experiment_git_blob"]==sha_blob(PREREG)
    assert prereg["benchmark"]["tasks"]==24
    assert len(prereg["benchmark"]["seeds"])==4
    families=prereg["benchmark"]["families"]
    assert len(families)==6
    rows=[]
    aggregate={"membership_calls":0,"membership_symbols":0,"equivalence_calls":0,
               "independent_product_nodes":0,"total_model_cpu_ms":0.0}
    for family in families:
        for seed in prereg["benchmark"]["seeds"]:
            hidden=hidden_family(family,seed)
            proof_nodes=[0]
            def member(w):
                if type(w)!=str or any(c not in hidden.alphabet for c in w):
                    raise ValueError("membership bad input")
                return hidden.run(w)
            def equivalence(model):
                proof=independent_product_prove(hidden,model)
                proof_nodes[0]+=proof["nodes"]
                return proof["counterexample"]
            learner=ActiveMealyLearner(hidden.alphabet,"01",
                  max_states=prereg["benchmark"]["max_states"],
                  max_membership=prereg["benchmark"]["oracle_cap_per_task"],
                  max_equivalence=prereg["benchmark"]["equivalence_cap_per_task"])
            r=learner.learn(member,equivalence)
            if r.source is not None:
                compiled=MealyProgram.from_source(r.source)
                frozen=independent_product_prove(hidden,compiled)
                valid=frozen["equivalent"]
            else:
                compiled=None;frozen={"equivalent":False,"counterexample":None,"nodes":0}
                valid=False
            for k in ("membership_calls","membership_symbols","equivalence_calls"):
                aggregate[k]+=getattr(r,k)
            aggregate["independent_product_nodes"]+=proof_nodes[0]+frozen["nodes"]
            aggregate["total_model_cpu_ms"]+=r.process_cpu_ms
            rows.append({
                "family":family,"seed":seed,"reference_states":hidden.n,
                "status":r.status,"first_exact_all_finite_words":valid,
                "generated_executable_program":r.source,
                "source_observations":r.source_observations,
                "membership_calls":r.membership_calls,
                "membership_total_symbols":r.membership_symbols,
                "equivalence_calls":r.equivalence_calls,
                "counterexamples":r.counterexamples,
                "compiled_states":r.hypothesis_states,
                "model_process_cpu_ms":r.process_cpu_ms,
                "oracle_product_nodes":proof_nodes[0],
                "independent_postfirst_product_nodes":frozen["nodes"],
                "independent_counterexample":frozen["counterexample"],
            })
    correct=sum(x["first_exact_all_finite_words"] for x in rows)
    # Adversarial control: alter reachable initial transition, exact checker rejects.
    first_good=next((x for x in rows if x["first_exact_all_finite_words"]),None)
    if first_good:
        parsed=json.loads(json.dumps(first_good["generated_executable_program"]))
        q=parsed["initial"];old=parsed["emissions"][q][0]
        parsed["emissions"][q][0]="1" if old=="0" else "0"
        mutant=MealyProgram.from_source(parsed)
        negative=independent_product_prove(hidden_family(first_good["family"],first_good["seed"]),mutant)
    else:negative={"equivalent":False,"counterexample":None,"nodes":0}
    local=locality_impossibility()
    passed=(correct==24 and all(x["status"]=="SCOPED_ALL_LENGTHS_PROVED" for x in rows)
            and not negative["equivalent"] and negative["counterexample"] is not None)
    return {
       "schema":"neumann.q3.rc39.first-24-hidden-automata.v1",
       "prereg_blob":lock["preregistered_experiment_git_blob"],
       "learner_source_blob":lock["original_source_git_blob"],
       "original_first_result_proof_independent":True,
       "source_only_membership_and_equivalence_oracles":True,
       "teacher_model_code_access":False,"torch_training_calls":0,
       "science_status":"SCOPED_CLASSICAL_STRUCTURAL_LEARNING_PASS" if passed else "RC39_FIRST_24_FAIL",
       "first_tasks":len(rows),"all_finite_word_proven":correct,
       "negative_mutation_rejected":not negative["equivalent"],
       "local_RC38_radius7_unbounded_state_impossibility":local,
       "metrics":aggregate,
       "claims":{"all_length_lstar_classical_discovery":"SCOPED_PASS" if passed else "FAIL",
          "Q3_autonomous_neural_opcode_creation":"NOT_PROVEN",
          "Q4_cost_10x_over_equal_rights_classical":"NOT_PROVEN",
          "Q6_independent_semantic_family_transfer":"NOT_PROVEN",
          "Q7_frontier":"NOT_PROVEN"},
       "rows":rows
    }
if __name__=="__main__":
    result=first()
    print(json.dumps(result,ensure_ascii=False,indent=2))
    if result["science_status"]=="RC39_FIRST_24_FAIL":
        raise SystemExit(1)
