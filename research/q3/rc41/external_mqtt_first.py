"""RC41: previously frozen L* and W-method on external MQTT Mealy models.

External public DOT data (mtappler/mut-learn) is retrieved at a pinned commit,
Git blob hash checked before parsing. The state graph only enters the model
through a source-output callback and after the learned program is frozen for
independent exact product verification. NOT a new neural algorithm.
"""
from __future__ import annotations

from collections import deque
from hashlib import sha1
from pathlib import Path
from time import process_time_ns
from urllib.request import urlopen, Request
import json
import re

from research.q3.rc39.active_mealy import ActiveMealyLearner, MealyProgram
from research.q3.rc39.membership_conformance import SourceMeter
from research.q3.rc39.wmethod_conformance import WMethodConformance

ROOT = Path(__file__).resolve().parents[3]
PRE = ROOT / "docs/experiments/q3_RC41_EXTERNAL_MQTT_FIRST_PREREG_2026_11_06.json"
EDGES = re.compile(r'\s*(s[0-9]+)\s*->\s*(s[0-9]+)\s*\[label="([^"]+) / ([^"]+)"\];\s*')
INITIAL = re.compile(r'\s*__start0\s*->\s*(s[0-9]+);\s*')


def git_blob(data: bytes) -> str:
    return sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def external_source(spec, commit):
    url = ("https://raw.githubusercontent.com/mtappler/mut-learn/"
           + commit + "/" + spec["path"])
    req = Request(url, headers={"User-Agent":"NEUMANN-reproducible-rc41"})
    with urlopen(req, timeout=25) as handle:
        data = handle.read(128_000)
    if git_blob(data) != spec["git_blob"]:
        raise ValueError("EXTERNAL_GIT_BLOB_SHA_MISMATCH")
    return data.decode("utf-8")


class PublishedMachine:
    def __init__(self, text, expected_states):
        edges=[]
        start=None
        for line in text.splitlines():
            m=EDGES.fullmatch(line)
            if m:
                edges.append(m.groups())
            elif "->" in line:
                m=INITIAL.fullmatch(line)
                if not m:
                    raise ValueError("UNRECOGNIZED_DOT_EDGE")
                if start is not None:
                    raise ValueError("MULTIPLE_INITIAL_STATES")
                start=m.group(1)
        if start is None or not edges:
            raise ValueError("EMPTY_OR_MISSING_INITIAL_DOT")
        states=sorted({s for s,_,_,_ in edges}|{t for _,t,_,_ in edges})
        inputs=sorted({a for _,_,a,_ in edges})
        outputs=sorted({o for _,_,_,o in edges})
        if (len(states)!=expected_states or start not in states
                or not 1<=len(inputs)<=8 or not 1<=len(outputs)<=8):
            raise ValueError("OUT_OF_FROZEN_SOURCE_SCOPE")
        si={s:i for i,s in enumerate(states)}
        ai={a:chr(65+i) for i,a in enumerate(inputs)}
        oi={o:str(i) for i,o in enumerate(outputs)}
        self.alphabet="".join(ai.values())
        self.output_alphabet="".join(oi.values())
        self.initial=si[start]
        self.states=len(states)
        self.transitions={}
        for s,t,a,o in edges:
            key=(si[s],ai[a])
            if key in self.transitions:
                raise ValueError("NONDETERMINISTIC_DOT_OR_DUPLICATE")
            self.transitions[key]=(si[t],oi[o])
        if len(self.transitions)!=len(states)*len(inputs):
            raise ValueError("INCOMPLETE_REFERENCE_MACHINE")
        self.raw_input_names=inputs
        self.raw_output_names=outputs
        self.edge_count=len(edges)

    def run(self, word):
        s=self.initial
        out=[]
        for a in word:
            s,o=self.transitions[(s,a)]
            out.append(o)
        return "".join(out)


def exact_independent_product(reference, compiled):
    # Different reference dictionary implementation vs learner state table.
    if "".join(compiled.alphabet)!=reference.alphabet:
        return False
    todo=deque([(reference.initial,compiled.initial)])
    visited=set(todo)
    while todo:
        a,b=todo.popleft()
        for index,letter in enumerate(reference.alphabet):
            nxt,emission=reference.transitions[a,letter]
            if emission!=compiled.emissions[b][index]:
                return False
            pair=(nxt,compiled.transitions[b][index])
            if pair not in visited:
                visited.add(pair)
                todo.append(pair)
    return True


def run():
    pre=json.loads(PRE.read_text())
    learner_path=ROOT/"research/q3/rc39/active_mealy.py"
    method_path=ROOT/"research/q3/rc39/wmethod_conformance.py"
    assert git_blob(learner_path.read_bytes())==pre["fixed_original_active_mealy_git_blob"]
    assert git_blob(method_path.read_bytes())==pre["fixed_wmethod_git_blob"]
    rows=[]
    begun=process_time_ns()
    for spec in pre["external_models"]:
        text=external_source(spec,pre["external_commit"])
        target=PublishedMachine(text,spec["max_reference_states"])
        # Only the callable membership(word)->observed output is provided to
        # the original frozen learner and W tester, NOT target.transitions.
        meter=SourceMeter(target.run,target.alphabet,target.output_alphabet,
                          query_cap=pre["budgets"]["max_unique_membership_per_case"])
        checker=WMethodConformance(
            meter,spec["max_reference_states"],
            verification_word_cap=pre["budgets"]["max_w_suite_words"])
        learner=ActiveMealyLearner(
            target.alphabet,target.output_alphabet,max_states=8,
            max_membership=pre["budgets"]["max_lstar_membership_per_case"],
            max_equivalence=pre["budgets"]["max_w_callbacks_per_case"])
        start=process_time_ns()
        output=learner.learn(meter.membership,checker.seek_counterexample)
        cpu=(process_time_ns()-start)/1e6
        frozen_ast=output.source
        program=MealyProgram.from_source(frozen_ast) if frozen_ast else None
        exact=(exact_independent_product(target,program) if program else False)
        certified=(output.status=="SCOPED_ALL_LENGTHS_PROVED"
                   and checker.completed_certificates>0)
        mutant_rejected=False
        if program:
            corrupted=json.loads(json.dumps(frozen_ast))
            q=corrupted["initial"]
            old=corrupted["emissions"][q][0]
            replacement=next((o for o in target.output_alphabet if o!=old),None)
            if replacement is None:
                raise ValueError("CANNOT_MUTATE_SINGLE_OUTPUT_ALPHABET")
            corrupted["emissions"][q][0]=replacement
            mutant_rejected=not exact_independent_product(
                target,MealyProgram.from_source(corrupted))
        rows.append({
            "source_case":spec["case"],
            "independent_external_model_url":("https://github.com/mtappler/mut-learn/blob/"
                 +pre["external_commit"]+"/"+spec["path"]),
            "source_git_blob":spec["git_blob"],"external_state_count":target.states,
            "external_input_count":len(target.raw_input_names),
            "external_output_count":len(target.raw_output_names),
            "external_transitions":target.edge_count,
            "learner_status":output.status,"compiled_ast":frozen_ast,
            "complete_source_only_w_certificate":certified,
            "after_freeze_independent_all_length":exact,
            "false_certificate":bool(certified and not exact),
            "negative_mutation_rejected":mutant_rejected,
            "unique_source_queries":meter.unique_queries,
            "unique_source_symbols":meter.unique_query_symbols,
            "conformance_words":checker.total_words_checked,
            "learner_internal_membership_calls":output.membership_calls,
            "w_callbacks":checker.callbacks,"process_cpu_ms":cpu
        })
    overall=(len(rows)==3 and len({r["source_git_blob"] for r in rows})==3
        and all(r["complete_source_only_w_certificate"]
                 and r["after_freeze_independent_all_length"]
                 and not r["false_certificate"]
                 and r["negative_mutation_rejected"] for r in rows))
    return {
        "schema":"neumann.q3.rc41.external-mqtt-first.v1",
        "science_status":"SCOPED_EXTERNAL_MQTT_FIRST_PASS" if overall else "SCOPED_EXTERNAL_MQTT_FIRST_FAIL",
        "cohort":"EXTERNALLY_AUTHORED_ALREADY_PUBLIC_AND_RESEARCHER_OPENED_MODEL_GROUP",
        "source_mealy_learner_frozen":pre["fixed_original_active_mealy_git_blob"],
        "w_method_frozen":pre["fixed_wmethod_git_blob"],
        "source_graph_passed_to_learner":False,
        "real_external_model_count":len(rows),
        "distinct_model_blobs":len({r["source_git_blob"] for r in rows}),
        "independent_all_length":sum(int(r["after_freeze_independent_all_length"]) for r in rows),
        "negative_mutations_rejected":sum(int(r["negative_mutation_rejected"]) for r in rows),
        "total_unique_source_queries":sum(r["unique_source_queries"] for r in rows),
        "total_unique_source_symbols":sum(r["unique_source_symbols"] for r in rows),
        "total_process_cpu_ms":(process_time_ns()-begun)/1e6,
        "Q3_neural_self_invention":"NOT_PROVEN",
        "Q4_strong_classical_end_to_end_advantage":"NOT_PROVEN",
        "Q6_cross_formalism_semantic_transfer":"NOT_PROVEN",
        "Q7_frontier":"NOT_PROVEN",
        "rows":rows
    }


if __name__=="__main__":
    result=run()
    print(json.dumps(result,indent=2,sort_keys=True))
    if result["science_status"]!="SCOPED_EXTERNAL_MQTT_FIRST_PASS":
        raise SystemExit(1)
