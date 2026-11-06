"""RC42 cross-protocol portability: frozen RC39 Mealy learner vs legacy TLS DOT.

This strict source adapter only translates independently authored numeric-node
DOT with "input/output" labels to the existing source-only RC41 interface.
Learner/W implementation hashes are locked before this experiment.
"""
import json
import re
from hashlib import sha1
from pathlib import Path
from time import process_time_ns
from urllib.request import Request,urlopen

from research.q3.rc39.active_mealy import ActiveMealyLearner, MealyProgram
from research.q3.rc39.membership_conformance import SourceMeter
from research.q3.rc39.wmethod_conformance import WMethodConformance
from research.q3.rc41.external_mqtt_first import PublishedMachine, exact_independent_product

ROOT=Path(__file__).resolve().parents[3]
PRE=ROOT/"docs/experiments/q3_RC42_TLS_FIRST_PREREG_2026_11_06.json"
EDGE=re.compile(r'([0-9]+)\s*->\s*([0-9]+)\s*\[label="([^"]+)"\]')
STATE=re.compile(r'([0-9]+)')


def blob(data):
    return sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()


def strict_tls_adapter(text, required_states, inputs, outputs):
    lines=[l.strip() for l in text.splitlines() if l.strip()]
    if len(lines)<3 or lines[0]!="digraph {" or lines[-1]!="}":
        raise ValueError("UNSUPPORTED_TLS_DOT_CONTAINER")
    declarations=[]
    edges=[]
    for line in lines[1:-1]:
        m=STATE.fullmatch(line)
        if m:
            declarations.append(m.group(1))
            continue
        m=EDGE.fullmatch(line)
        if not m:
            raise ValueError("UNSUPPORTED_TLS_DOT_CONTENT")
        src,dst,label=m.groups()
        if "/" not in label:
            raise ValueError("NO_INPUT_OUTPUT_SEPARATOR")
        input_label,output_label=label.split("/",1)
        if not input_label or not output_label:
            raise ValueError("INVALID_TLS_IO")
        edges.append((src,dst,input_label,output_label))
    if (len(declarations)!=required_states or
        len(set(declarations))!=required_states or not edges):
        raise ValueError("TLS_DECLARED_STATE_COUNT_MISMATCH")
    used={src for src,_,_,_ in edges}|{dst for _,dst,_,_ in edges}
    if used!=set(declarations):
        raise ValueError("TLS_DECLARATIONS_EDGES_DISAGREE")
    found_inputs={a for _,_,a,_ in edges}
    found_outputs={o for _,_,_,o in edges}
    if (len(found_inputs)!=inputs or len(found_outputs)!=outputs or
        len(edges)!=required_states*inputs):
        raise ValueError("TLS_INPUT_OUTPUT_SCOPE_MISMATCH")
    encoded=['digraph g {']
    for src,dst,a,o in edges:
        encoded.append(f'  s{src} -> s{dst} [label="{a} / {o}"];')
    # Source convention: first standalone listed state is the initial state.
    encoded.append(f'__start0 -> s{declarations[0]};')
    encoded.append('}')
    return "\n".join(encoded)


def fetch_tls(spec, pre):
    url=("https://raw.githubusercontent.com/"+pre["external_repo"]+"/"
         +pre["external_commit"]+"/"+spec["path"])
    req=Request(url,headers={"User-Agent":"NEUMANN-RC42-frozen-TLS"})
    with urlopen(req,timeout=25) as response:
        data=response.read(128000)
    if blob(data)!=spec["git_blob"]:
        raise ValueError("PINNED_TLS_REFERENCE_SHA_DRIFT")
    return data.decode()


def run():
    pre=json.loads(PRE.read_text())
    if blob((ROOT/"research/q3/rc39/active_mealy.py").read_bytes())!=pre["frozen_original_lstar_git_blob"]:
        raise ValueError("ORIGINAL_LEARNER_CHANGED")
    if blob((ROOT/"research/q3/rc39/wmethod_conformance.py").read_bytes())!=pre["frozen_classical_wmethod_git_blob"]:
        raise ValueError("CLASSICAL_VERIFIER_CHANGED")
    rows=[]
    t0=process_time_ns()
    for spec in pre["external_models"]:
        source=fetch_tls(spec,pre)
        normalized=strict_tls_adapter(source,spec["reference_bound"],
                        spec["inputs"],spec["outputs"])
        target=PublishedMachine(normalized,spec["reference_bound"])
        source_meter=SourceMeter(target.run,target.alphabet,target.output_alphabet,
                                query_cap=pre["budgets"]["max_unique_membership_per_case"])
        w=WMethodConformance(source_meter,spec["reference_bound"],
                             verification_word_cap=pre["budgets"]["max_w_test_words_per_case"])
        learner=ActiveMealyLearner(target.alphabet,target.output_alphabet,max_states=8,
                 max_membership=pre["budgets"]["max_lstar_membership_per_case"],
                 max_equivalence=pre["budgets"]["max_w_calls"])
        started=process_time_ns()
        result=learner.learn(source_meter.membership,w.seek_counterexample)
        cpu_ms=(process_time_ns()-started)/1e6
        frozen_ast=result.source
        model=MealyProgram.from_source(frozen_ast) if frozen_ast else None
        exact=exact_independent_product(target,model) if model else False
        certified=(result.status=="SCOPED_ALL_LENGTHS_PROVED" and w.completed_certificates>0)
        mutated_rejected=False
        if frozen_ast:
            altered=json.loads(json.dumps(frozen_ast))
            state=altered["initial"]
            old=altered["emissions"][state][0]
            alternative=next((symbol for symbol in target.output_alphabet if symbol!=old),None)
            if alternative is None:
                raise ValueError("SINGLE_OUTPUT_NO_MUTATION")
            altered["emissions"][state][0]=alternative
            mutated_rejected=not exact_independent_product(
                target,MealyProgram.from_source(altered))
        rows.append({
          "case":spec["case"],"external_git_blob":spec["git_blob"],
          "source_url":"https://github.com/"+pre["external_repo"]+"/blob/"
                     +pre["external_commit"]+"/"+spec["path"],
          "reference_state_bound":spec["reference_bound"],
          "input_symbols":spec["inputs"],"output_symbols":spec["outputs"],
          "transition_count":target.edge_count,
          "learner_status":result.status,
          "compiled_ast":frozen_ast,
          "complete_source_only_w_certificate":certified,
          "independent_after_freeze_all_lengths":exact,
          "false_certificate":bool(certified and not exact),
          "wrong_mutant_rejected":mutated_rejected,
          "distinct_source_queries":source_meter.unique_queries,
          "source_query_symbols":source_meter.unique_query_symbols,
          "w_callbacks":w.callbacks,
          "w_conformance_word_checks":w.total_words_checked,
          "learner_process_cpu_ms":cpu_ms
        })
    success=(len(rows)==2 and len({r["external_git_blob"] for r in rows})==2
             and all(r["complete_source_only_w_certificate"]
                     and r["independent_after_freeze_all_lengths"]
                     and not r["false_certificate"]
                     and r["wrong_mutant_rejected"] for r in rows))
    return {
      "schema":"neumann.q3.rc42.cross-protocol-external-tls-first.v1",
      "science_status":"SCOPED_EXTERNAL_TLS_CROSS_PROTOCOL_PASS" if success else "RC42_EXTERNAL_TLS_FIRST_FAIL",
      "frozen_learner_and_wmethod":True,
      "external_protocol":"TLS_legacy_models",
      "external_corpus":"damascenodiego/DynamicLstarM",
      "external_github_commit":pre["external_commit"],
      "original_external_cases":len(rows),
      "independent_all_length_proven":sum(r["independent_after_freeze_all_lengths"] for r in rows),
      "wrong_mutants_rejected":sum(r["wrong_mutant_rejected"] for r in rows),
      "source_membership_queries_total":sum(r["distinct_source_queries"] for r in rows),
      "total_process_cpu_ms":(process_time_ns()-t0)/1e6,
      "Q3_neural_autonomous_discovery":"NOT_PROVEN",
      "Q4_strongest_classical_advantage":"NOT_PROVEN",
      "Q6_cross_formalism_semantic_transfer":"NOT_PROVEN",
      "Q7_frontier":"NOT_PROVEN",
      "rows":rows
    }


if __name__=="__main__":
    first=run()
    print(json.dumps(first,indent=2,sort_keys=True))
    if first["science_status"]!="SCOPED_EXTERNAL_TLS_CROSS_PROTOCOL_PASS":
        raise SystemExit(1)
