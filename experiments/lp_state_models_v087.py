"""Runnable model-side state compression; no training is performed on import.

Budget-matched candidates, not reproductions of published trained baselines.
All predictions remain advisory to the shared original-LP certificate runtime.
"""
from __future__ import annotations

import torch
from torch import nn


class GraphStateModel(nn.Module):
    """Signed bipartite message passing with an optional paid 2m shortlist.

The full and compact versions have identical parameterization. The compact
path actually removes column states/edges before the last two graph updates;
it does not merely rename the supplied basis head. Top-k is advisory and can
discard a needed column. Neither hidden labels nor optimal bases enter forward.
"""

    def __init__(self, width=16, compact=False):
        super().__init__()
        self.width, self.compact = width, compact
        self.rows = nn.Sequential(nn.Linear(8, width), nn.ReLU())
        self.cols = nn.Sequential(nn.Linear(8, width), nn.ReLU())
        self.to_row = nn.ModuleList([nn.Sequential(nn.Linear(2 * width, width),
                                  nn.ReLU(), nn.Linear(width, width), nn.ReLU()) for _ in range(3)])
        self.to_col = nn.ModuleList([nn.Sequential(nn.Linear(2 * width, width),
                                  nn.ReLU(), nn.Linear(width, width), nn.ReLU()) for _ in range(3)])
        self.coarse = nn.Linear(width, 1)
        self.refine = nn.Linear(width, 1)
        self.primal = nn.Linear(width, 1)
        self.dual = nn.Linear(width, 1)

    def forward(self, matrix, row_features, col_features):
        m, n = matrix.shape
        rows, cols = self.rows(row_features), self.cols(col_features)
        row_degree = matrix.abs().sum(1).clamp_min(1e-6).unsqueeze(1)
        col_degree = matrix.abs().sum(0).clamp_min(1e-6).unsqueeze(1)
        rows = self.to_row[0](torch.cat((rows, matrix @ cols / row_degree), 1))
        cols = self.to_col[0](torch.cat((cols, matrix.T @ rows / col_degree), 1))
        coarse = self.coarse(cols).squeeze(1)
        if self.compact:
            selected = torch.argsort(coarse, descending=True, stable=True)[:min(n, 2 * m)]
            edges, states = matrix[:, selected], cols[selected]
        else:
            selected = torch.arange(n, device=matrix.device)
            edges, states = matrix, cols
        for layer in (1, 2):
            rd = edges.abs().sum(1).clamp_min(1e-6).unsqueeze(1)
            cd = edges.abs().sum(0).clamp_min(1e-6).unsqueeze(1)
            rows = self.to_row[layer](torch.cat((rows, edges @ states / rd), 1))
            states = self.to_col[layer](torch.cat((states, edges.T @ rows / cd), 1))
        scores = torch.full_like(coarse, -1e6)
        scores = scores.scatter(0, selected, self.refine(states).squeeze(1))
        x = torch.zeros_like(coarse).scatter(0, selected, self.primal(states).squeeze(1))
        return {'scores': scores, 'coarse': coarse, 'x': x,
                'y': self.dual(rows).squeeze(1), 'selected': selected,
                'state_columns': int(selected.numel()),
                'edge_multiply_terms': int(m * n * self.width * 2 +
                                           m * selected.numel() * self.width * 4)}


class PointwiseModel(nn.Module):
    """A cheap learned Direct candidate; shared analytic features are allowed."""

    def __init__(self, width=16):
        super().__init__()
        self.cols = nn.Sequential(nn.Linear(8, width), nn.ReLU(), nn.Linear(width, width), nn.ReLU())
        self.rows = nn.Sequential(nn.Linear(8, width), nn.ReLU())
        self.head = nn.Linear(width, 1)
        self.primal = nn.Linear(width, 1)
        self.dual = nn.Linear(width, 1)

    def forward(self, matrix, row_features, col_features):
        states, rows = self.cols(col_features), self.rows(row_features)
        scores = self.head(states).squeeze(1)
        return {'scores': scores, 'coarse': scores, 'x': self.primal(states).squeeze(1),
                'y': self.dual(rows).squeeze(1),
                'selected': torch.arange(matrix.shape[1], device=matrix.device),
                'state_columns': int(matrix.shape[1]), 'edge_multiply_terms': 0}


def roster(seed=87001):
    """Same allowed data/tools and parameter cap, not identical parameter counts.

The full16 network serves both executable Direct and no-compression roles.
The answer role may use its independently supervised x/y heads. The pointwise
model and a larger 128-wide graph model protect against a weak Direct choice.
The larger candidate is explicitly included, not a claimed paper reproduction.
"""
    result = {}
    for name, make in (
        ('compact16', lambda: GraphStateModel(16, True)),
        ('full16', lambda: GraphStateModel(16, False)),
        ('point16', lambda: PointwiseModel(16)),
        ('full128', lambda: GraphStateModel(128, False)),
    ):
        torch.manual_seed(seed)
        result[name] = make().eval()
    return result


def tensor_input(A, row_features, col_features):
    # Conversion belongs to each complete proposal path, not free setup.
    return tuple(torch.tensor(v, dtype=torch.float32) for v in (A, row_features, col_features))
