"""Paid early heads shared by compact and Direct; no hidden-target argument."""
from time import perf_counter_ns
import torch
from experiments.lp_state_models_v087 import GraphStateModel, PointwiseModel, tensor_input
from neumann1.lp_model_admission_v087 import features
from neumann1.lp_shortlist_v089 import solve_shortlist_checked


def early_indices(model, matrix, row_features, col_features):
    """The compact model's retained set needs only update zero and coarse head.

    Full graph Direct is allowed exactly the same coarse head. Pointwise Direct
    needs only its column scorer. Primal/dual heads are optional proposals, never
    acceptance authority, so this alternative omits them and pays shared rescue.
    """
    m, n = matrix.shape
    if isinstance(model, GraphStateModel):
        rows, cols = model.rows(row_features), model.cols(col_features)
        rd = matrix.abs().sum(1).clamp_min(1e-6).unsqueeze(1)
        cd = matrix.abs().sum(0).clamp_min(1e-6).unsqueeze(1)
        rows = model.to_row[0](torch.cat((rows, matrix @ cols / rd), 1))
        cols = model.to_col[0](torch.cat((cols, matrix.T @ rows / cd), 1))
        scores = model.coarse(cols).squeeze(1)
    elif isinstance(model, PointwiseModel):
        scores = model.head(model.cols(col_features)).squeeze(1)
    else:
        raise TypeError('unregistered frozen architecture')
    if not torch.isfinite(scores).all():
        return []  # advisory invalid proposal: paid full rescue
    return torch.argsort(scores, descending=True, stable=True)[:min(n, 2*m)].tolist()


def observe(raw, model):
    started = perf_counter_ns()
    D, rows, cols = features(**raw)
    tensors = tensor_input(D, rows, cols)
    with torch.inference_mode():
        indices = early_indices(model, *tensors)
    proposal_ms = (perf_counter_ns()-started)/1e6
    remaining = 5.-proposal_ms/1000.
    execution = solve_shortlist_checked(**raw, indices=indices, budget_s=remaining) if remaining > 0 else None
    total_ms = (perf_counter_ns()-started)/1e6
    return {'accepted': bool(execution and execution['accepted'] and total_ms <= 5000.),
            'total_ms': total_ms, 'proposal_ms': proposal_ms, 'execution': execution,
            'witness': execution['witness'] if execution else None, 'indices': indices,
            'answer': None}
