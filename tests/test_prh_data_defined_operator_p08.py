"""Independence, semantics, and refusal tests for P0.8 first experiment."""
from copy import deepcopy
from itertools import product

import numpy as np
import pytest

from experiments.prh_data_defined_operator_p08 import (
    CONTRACT, Rule8, Reject, generate_task, induce, execute_1d, execute_2d,
    execute_typed, enumerative_direct, negative_controls, reference_1d, run,
)


def test_fixed_frozen_contract_and_no_global_claims():
    assert CONTRACT['base_seed'] == 20261103
    assert CONTRACT['task_count'] == 16
    assert CONTRACT['global_q1_to_q7'] == 'OPEN'
    assert CONTRACT['jepa_or_neural_training'] == 'NOT_RUN'


def test_independent_reference_equals_compiled_rule_on_exhaustive_short_inputs():
    # All 256 possible truth tables, all short binary arrays: no sampling.
    for byte in range(256):
        rule = Rule8(tuple((byte >> i) & 1 for i in range(8)))
        for n in (3, 4):
            for bits in product((0, 1), repeat=n):
                source = list(bits)
                assert reference_1d(source, byte) == execute_1d(rule, source)


def test_no_heldout_reference_access_in_inducer():
    rule_byte = 91
    task = generate_task(3, rule_byte)
    before = induce(task['train'])
    mutated = deepcopy(task)
    for example in mutated['test_1d'] + mutated['test_2d']:
        example['output'] = [[9999]]
    assert before['ast'] == induce(mutated['train'])['ast']
    assert before['rule_id'] == induce(mutated['train'])['rule_id']


def test_induction_requires_all_eight_contexts_and_unique_rule():
    task = generate_task(2, 203)
    ind = induce(task['train'])
    assert ind['rule_id'] == 203
    assert min(ind['coverage']) > 0
    assert ind['train_cells_observed'] == sum(CONTRACT['train_lengths'])
    scan = enumerative_direct(task['train'])
    assert scan['consistent_candidate_count'] == 1
    assert scan['unique_rule_id'] == 203


def test_true_binary_full_scene_matrix_transfer():
    task = generate_task(0, 148)
    program = induce(task['train'])['ast']
    assert all(execute_typed(program, t['input']) == t['output'] for t in task['test_1d'])
    assert all(execute_typed(program, t['input'], rowwise=True) == t['output'] for t in task['test_2d'])


def test_all_five_negative_controls_abstain():
    neg = negative_controls(generate_task(0, 187))
    assert neg['undercoverage'] == 'ABSTAIN_INCOMPLETE_CONTEXT'
    assert neg['contradictory_label'] == 'ABSTAIN_CONTRADICTORY_LOCAL_RULE'
    assert neg['wrong_output_shape'] == 'ABSTAIN_OUTPUT_SHAPE_OR_ALPHABET'
    assert neg['unsupported_alphabet'] == 'ABSTAIN_ALPHABET_OR_LENGTH'
    assert neg['nonlocal_dependence'] == 'ABSTAIN_CONTRADICTORY_LOCAL_RULE'


def test_illegal_ast_values_are_rejected():
    obj = Rule8(tuple([0,1]*4))
    x = [0,1,0,0,1,1]
    bad = obj.as_json()
    bad['table'][0] = 3
    with pytest.raises(Reject):
        execute_typed(bad, x)
    bad = obj.as_json()
    bad['op'] = '__eval__'
    with pytest.raises(Reject):
        execute_typed(bad, x)
    bad = obj.as_json()
    bad['boundary'] = 'zero-pad'
    with pytest.raises(Reject):
        execute_typed(bad, x)


def test_first_study_contract_does_not_silently_close_q3():
    out = run()
    assert out['global_Q1_to_Q7'] == 'OPEN'
    assert out['open_ended_opcode_invention'] == 'NOT_DEMONSTRATED'
    assert out['metrics']['unique_complete_tables'] == 16
    assert out['metrics']['induced_rule_ids_exact'] == 16
    assert out['metrics']['heldout_1d_exact'] == 48
    assert out['metrics']['heldout_2d_exact'] == 32
    assert out['metrics']['negative_rejections'] == 5
