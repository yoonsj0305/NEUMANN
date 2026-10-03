"""Small synthetic logits, not a neural model or capability evaluation."""
import unittest
from types import SimpleNamespace

try:
    import torch
except ImportError:
    torch = None

from neumann1.control_plane_v1 import EncodedChoice, ScorePlan
from neumann1.control_plane_scoring_v1 import TorchLabelBackend, label_mean_logprob


@unittest.skipIf(torch is None, "optional torch tensor contracts run in dedicated P0 CI")
class TensorContracts(unittest.TestCase):
    def make_model(self):
        class FixedLogits(torch.nn.Module):
            def __init__(self):
                super().__init__()
                self.calls = 0
                self.table = torch.nn.Parameter(torch.tensor([[0., 2., 1., -1.], [3., 0., 2., 1.],
                                                             [-1., 1., 0., 3.], [2., 1., 0., -1.]]), requires_grad=False)
            def generate(self, *args, **kwargs):
                raise AssertionError("control may never generate")
            def forward(self, input_ids, attention_mask, use_cache, logits_to_keep, return_dict):
                assert not use_cache and return_dict
                self.calls += 1
                logits = self.table[input_ids]
                return SimpleNamespace(logits=logits[:, logits_to_keep, :])
        return FixedLogits().eval()

    def test_batch_equals_independent_reference_with_padding_and_multitoken_label(self):
        model = self.make_model()
        rows = (EncodedChoice((1, 2), (3, 0)), EncodedChoice((0,), (1,)),
                EncodedChoice((2, 3, 1), (0, 2)))
        plan = ScorePlan(rows, 3, ("fixed",))
        result = TorchLabelBackend(model, 0, "cpu", batch_size=2).evaluate(plan, 10000)
        for row, value in zip(rows, result.scores):
            logits = model.table[list(row.prompt_ids + row.label_ids)].tolist()
            self.assertAlmostEqual(value[0], label_mean_logprob(logits, len(row.prompt_ids), row.label_ids), places=6)
        self.assertEqual(result.forward_calls, 2)
        self.assertEqual(result.padded_tokens, 13)
        self.assertIsNone(result.peak_accelerator_memory_bytes)

    def test_batch_and_unbatched_scores_equal(self):
        rows = (EncodedChoice((1, 2), (3,)), EncodedChoice((0,), (1, 2)))
        plan = ScorePlan(rows, 1, ("a", "b"))
        batch = TorchLabelBackend(self.make_model(), 0, "cpu", 2).evaluate(plan, 10000)
        single = TorchLabelBackend(self.make_model(), 0, "cpu", 1).evaluate(plan, 10000)
        self.assertEqual(batch.scores, single.scores)

    def test_training_and_parameter_drift_rejected(self):
        model = self.make_model().train()
        with self.assertRaises(ValueError):
            TorchLabelBackend(model, 0, "cpu")
        model.eval()
        backend = TorchLabelBackend(model, 0, "cpu")
        with torch.no_grad():
            model.table.add_(1)
        with self.assertRaises(ValueError):
            backend.evaluate(ScorePlan((EncodedChoice((1,), (2,)),), 1, ("a",)), 10000)


if __name__ == "__main__":
    unittest.main()
