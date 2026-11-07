"""POST-FIRST finite-language impossibility and independent VM audit.
This is on already-opened PRE_10_100, not a new blind original test.
Proof is exact for the finite search grammar, NOT all Turing-computable programs.
"""
import hashlib,json,pathlib
import executable_conditional_graph_external_first as base

TASK="PRE_10_100"
GUARDS=(0,3)

def inspect():
    data=base.get_original(TASK)
    train,heldout=base.source_split(data)
    vocab=base.graph_library([x for x,y in train])
    items=[]
    for bit in GUARDS:
        groups=[[i for i,(x,y) in enumerate(train) if bool(x&(1<<bit))],
                [i for i,(x,y) in enumerate(train) if not (x&(1<<bit))]]
        fitting=[[p for p,s in vocab if all(s[i]==train[i][1] for i in grp)] for grp in groups]
        found=base.synthesize(train,allow_guard=True) if bit==3 else None
        items.append({"guard_bit":bit,"train_group_sizes":[len(g) for g in groups],
                      "full_vocabulary_expressions":len(vocab),
                      "fitting_branch_body_counts":[len(c) for c in fitting],
                      "both_branches_expressible":bool(fitting[0] and fitting[1]),
                      "chosen_global_synthesizer":found if found else None})
    # A deliberately invalid counterfactual mutates ONLY the learned guard.
    target=items[1]["chosen_global_synthesizer"]["ast"]
    if target is None or target[1]!=("bit",3):
        raise AssertionError("POSTFIRST_EXPECTED_GUARD_NOT_FOUND")
    wrong=["ite",["bit",0],target[2],target[3]]
    correct_scores=base.heldout_score(target,heldout)
    broken_scores=base.heldout_score(wrong,heldout)
    assert correct_scores["exact"] and not broken_scores["exact"]
    assert not items[0]["both_branches_expressible"] and items[1]["both_branches_expressible"]
    report={"schema":"neumann.q3.postfirst-finite-grammar-impossibility.v1",
            "status":"POSTFIRST_DEV_ONLY",
            "original_task":TASK,"upstream_commit":base.UPSTREAM,
            "train_n":len(train),"original_heldout_n":len(heldout),
            "guard_witness":items,"generated_correct_ast":target,
            "original_heldout_correct":correct_scores,
            "counterfactual_guard0_heldout":broken_scores,
            "interpretation":"Exhaustive only over bounded source graph vocabulary and 68 selected source I/O examples; no global semantic equivalence proof"}
    pathlib.Path("Q3_POSTFIRST_GUARD_IMPOSSIBILITY.json").write_text(json.dumps(report,indent=2))
    print(json.dumps({"train_n":len(train),"vocabulary":len(vocab),"guard0":items[0]["fitting_branch_body_counts"],
       "guard3":items[1]["fitting_branch_body_counts"],
       "correct_test_hits":correct_scores["hits"],
       "incorrect_guard_test_hits":broken_scores["hits"]},indent=2))

if __name__=="__main__":inspect()
