"""Q3 Boolean meta-constructor synthetic exhaustive class FIRST replay.

Every constructor has unseen arity 5/6/7 original truth tables. No formula,
operator name or target output enters the learner. A one-bit fold recurrence
is supplied as an inductive grammar and is NOT autonomously invented.
"""
from __future__ import annotations
import json
from itertools import product
from pathlib import Path
from neumann1.boolean_meta_inventor import invent_boolean_fold,InsufficientEvidence


def evaluate(table,a,b):
    return table[2*a+b]


def main():
    methods=source=heldout=correct=0
    gates=[]
    for base_mask in range(16):
        base=tuple((base_mask>>i)&1 for i in range(4))
        if len(set(base))<2:
            continue
        for extension_mask in range(16):
            step=tuple((extension_mask>>i)&1 for i in range(4))
            def true_program(bits):
                value=evaluate(base,*bits[:2])
                for bit in bits[2:]:
                    value=evaluate(step,value,bit)
                return value
            invented=invent_boolean_fold(true_program)
            assert invented.base_table==base
            assert invented.extension_table==step
            methods+=1;source+=invented.source_observations
            gates.append(invented.base_gate_count+invented.extension_gate_count)
            for n in (5,6,7):
                for bits in product((0,1),repeat=n):
                    heldout+=1
                    correct+=invented.apply(bits)==true_program(bits)
    assert (methods,source,heldout,correct)==(224,6272,50176,50176)
    reference=lambda bits:sum(bits)%2
    def false_friend(bits):
        return reference(bits) ^ int(len(bits)==5 and bits==(1,1,1,1,1))
    witness=invent_boolean_fold(false_friend)
    counterexample=witness.apply((1,1,1,1,1))!=false_friend((1,1,1,1,1))
    assert counterexample
    report={'schema':'NEUMANN.Q3.boolean-meta-fold.synthetic-exhaustive-FIRST.v1',
            'method_families':methods,
            'source_observations':source,
            'heldout_arity_5_6_7':heldout,
            'heldout_exact':correct,
            'nand_gates_total_min':min(gates),
            'nand_gates_total_max':max(gates),
            'unseen_length_5_single_exception_missed':counterexample,
            'scope':'all 14 nonconstant binary bases by all 16 binary transitions',
            'critical_prior':'human supplied one-bit fold recurrence and NAND universal gate',
            'not_established':['self-created arbitrary meta language',
                               'independent-author domain transfer',
                               '10x full compute or frontier equivalence',
                               'arbitrary source functions generalize to all lengths']}
    path=Path(__file__).with_name('q3_boolean_meta_fold_first_results.json')
    path.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
    return report

if __name__=='__main__':
    main()
