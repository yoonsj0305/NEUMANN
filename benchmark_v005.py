from __future__ import annotations
import json

from neumann1 import (
    TwoStageOpenSetStructureFormer, training_examples, heldout_examples, final_test_examples,
    IRKind,
)


def evaluate():
    model=TwoStageOpenSetStructureFormer().fit(training_examples())
    validation_metrics=model.tune_threshold(heldout_examples())
    rows=[]
    for text, expected, bucket in final_test_examples():
        predicted, confidence=model.predict_kind(text)
        p_known=model.known_probability(text)
        rows.append({
            "text":text,
            "expected":expected.value,
            "bucket":bucket,
            "predicted":predicted.value,
            "correct":predicted==expected,
            "known_probability":p_known,
            "reported_confidence":confidence,
        })
    known=[r for r in rows if r["expected"]!="unknown"]
    unknown=[r for r in rows if r["expected"]=="unknown"]
    hard=[r for r in rows if r["bucket"]=="hard_negative"]
    summary={
        "validation_selected_threshold":model.threshold,
        "validation_known_coverage":validation_metrics.known_coverage,
        "validation_unknown_false_route_rate":validation_metrics.unknown_false_route_rate,
        "final_test_n":len(rows),
        "final_test_accuracy":sum(r["correct"] for r in rows)/len(rows),
        "final_known_auto_route_coverage":sum(r["predicted"]!="unknown" for r in known)/len(known),
        "final_known_routed_precision":sum(r["correct"] for r in known if r["predicted"]!="unknown") / max(1,sum(r["predicted"]!="unknown" for r in known)),
        "final_unknown_false_route_rate":sum(r["predicted"]!="unknown" for r in unknown)/len(unknown),
        "final_hard_negative_false_route_rate":sum(r["predicted"]!="unknown" for r in hard)/len(hard),
    }
    return {
        "notes":[
            "Threshold is selected on a separate validation set, then frozen for final_test_examples.",
            "Data are tiny and hand-authored; zero observed false routes is not a statistical guarantee.",
            "The model predicts structure kind only, not complete IR payloads.",
        ],
        "summary":summary,
        "rows":rows,
    }

if __name__=='__main__':
    r=evaluate()
    print(json.dumps(r,indent=2))
    with open('benchmark_v005_results.json','w',encoding='utf-8') as f:
        json.dump(r,f,indent=2)
