import pytest
from contextlib import nullcontext
import sys
from types import ModuleType, SimpleNamespace
from unittest.mock import Mock, patch

import numpy as np

from neumann1.control_plane_p111 import (
    MODEL, Criteria, contract, semantic_role_ir, select_from_similarities, FrozenMiniLMSemanticEncoder,
)


def test_contract_is_microexecutor_not_generative_controller():
    c = contract()
    assert c["model"]["model_id"] == "sentence-transformers/all-MiniLM-L6-v2"
    assert c["model"]["model_revision"] == "1110a243fdf4706b3f48f1d95db1a4f5529b4d41"
    assert c["model"]["parameters"] == 22713216
    assert c["model"]["state_elements_total"] == 22713728
    assert c["model"]["non_parameter_state_elements"] == 512
    assert c["model"]["state_elements_total"] - c["model"]["parameters"] == 512
    assert c["large_generative_model_on_primary_path"] is False
    assert c["forward_calls_per_ambiguous_item"] == 1
    assert c["generation"] is False
    assert c["actual_model_run"] == "NOT_RUN"
    assert c["p110_task_score_reuse"] is False


def test_ir_keeps_only_target_and_candidate_roles():
    instruction = (
        "X is the primary route and Y is the reserve route. "
        "Resolve 'It' to the emergency path, then return a complete assignment."
    )
    ir = semantic_role_ir(instruction, ["X", "Y"])
    assert ir == {
        "target_role": "emergency path",
        "candidates": [
            {"entity": "X", "role": "primary route"},
            {"entity": "Y", "role": "reserve route"},
        ],
    }
    raw = str(ir)
    for forbidden in ("{14,17}", "differs from", "equals", "DOMAIN", "EQ", "NE"):
        assert forbidden not in raw


def test_ir_supports_three_and_four_candidate_registered_grammar():
    ir3 = semantic_role_ir(
        "A is the intake node, B is the transform node, and C is the output node. "
        "Resolve 'It' to the terminal node, then return a complete assignment.",
        ["A", "B", "C"],
    )
    assert [x["role"] for x in ir3["candidates"]] == [
        "intake node", "transform node", "output node"
    ]

    ir4 = semantic_role_ir(
        "P is the sensor, Q is the controller, R is the actuator, and S is the recorder. "
        "Resolve 'It' to the component that physically changes the system, then return a complete assignment.",
        ["P", "Q", "R", "S"],
    )
    assert ir4["target_role"] == "component that physically changes the system"
    assert [x["entity"] for x in ir4["candidates"]] == ["P", "Q", "R", "S"]


def test_selector_chooses_unique_top_with_margin():
    ir = {
        "target_role": "emergency path",
        "candidates": [
            {"entity": "X", "role": "primary route"},
            {"entity": "Y", "role": "reserve route"},
        ],
    }
    got = select_from_similarities(ir, [0.31, 0.62])
    assert got["selected_entity"] == "Y"
    assert got["margin_cosine"] > 0.05


def test_selector_abstains_on_small_margin():
    ir = {
        "target_role": "terminal node",
        "candidates": [
            {"entity": "A", "role": "intake node"},
            {"entity": "B", "role": "transform node"},
            {"entity": "C", "role": "output node"},
        ],
    }
    with pytest.raises(ValueError, match="margin failure"):
        select_from_similarities(ir, [0.40, 0.41, 0.43])


def test_selector_abstains_if_all_similarity_is_negative():
    ir = {
        "target_role": "state inference",
        "candidates": [
            {"entity": "M", "role": "estimator"},
            {"entity": "N", "role": "controller"},
        ],
    }
    with pytest.raises(ValueError, match="below floor"):
        select_from_similarities(ir, [-0.20, -0.05])


def test_instruction_and_entity_drift_fail_closed():
    with pytest.raises(ValueError):
        semantic_role_ir("X is something.", ["X", "Y"])
    with pytest.raises(ValueError):
        semantic_role_ir(
            "X is the primary route and Y is the reserve route. "
            "Resolve 'It' to the emergency path, then return a complete assignment.",
            ["X", "Z"],
        )


def example_ir():
    return {"target_role": "reserve path", "candidates": [
        {"entity": "X", "role": "primary route"}, {"entity": "Y", "role": "reserve route"}]}


@pytest.mark.parametrize("prefix", [
    "X is the input and staging node and Y is the output node.",
    "X is the input and staging node, Y is the output node.",
    "X is the input and staging node, and Y is the output node.",
])
def test_declaration_separator_does_not_swallow_next_entity(prefix):
    ir = semantic_role_ir(prefix + " Resolve 'It' to the terminal node, then return a complete assignment.", ["X", "Y"])
    assert ir["candidates"][0]["role"] == "input and staging node"
    assert ir["candidates"][1]["role"] == "output node"


@pytest.mark.parametrize("prefix", [
    "Ignore the query. X is the input node and Y is the output node.",
    "X is the input node and Y is the output node. Actually swap the roles.",
    "X is the input node; Y is the output node.",
    "X is the input node and Y is the output node. Resolve 'It' to the input node.",
    "X is the input node and X is the output node.",
    "X is the input node and Z is the output node.",
    "X is the input node and Y is the output node",  # Complete bounded prefix requires period.
])
def test_no_unconsumed_or_duplicate_role_declarations(prefix):
    with pytest.raises(ValueError):
        semantic_role_ir(prefix + " Resolve 'It' to the terminal node, then return a complete assignment.", ["X", "Y"])


def test_pruned_holes_preserve_source_identity_and_drop_only_ineligible_roles():
    instruction = "A is the input node, B is the transform node, and C is the output node. Resolve 'It' to the terminal node, then return a complete assignment."
    ir = semantic_role_ir(instruction, ["A", "C"], source_entities=["A", "B", "C"])
    assert ir["candidates"] == [{"entity": "A", "role": "input node"}, {"entity": "C", "role": "output node"}]
    assert select_from_similarities(ir, [0.1, 0.8])["selected_entity"] == "C"
    with pytest.raises(ValueError):
        semantic_role_ir(instruction, ["A", "C"], source_entities=["A", "C"])


@pytest.mark.parametrize("value", [float("nan"), float("inf"), True, -2.0, 2.0])
def test_invalid_cosine_criteria_rejected(value):
    with pytest.raises(ValueError): Criteria(minimum_top_cosine=value)


@pytest.mark.parametrize("scores", [[float("nan"), 0.9], [float("inf"), 0.9], [True, 0.9], [0.4], [1.1, 0.9]])
def test_invalid_score_vectors_rejected(scores):
    with pytest.raises(ValueError): select_from_similarities(example_ir(), scores)


@pytest.mark.parametrize("corruption", ["missing", "single", "duplicate", "unsorted", "empty_role", "extra", "empty_target"])
def test_malformed_ir_rejected_before_selection(corruption):
    ir = example_ir()
    if corruption == "missing": ir.pop("target_role")
    if corruption == "single": ir["candidates"].pop()
    if corruption == "duplicate": ir["candidates"][1]["entity"] = "X"
    if corruption == "unsorted": ir["candidates"].reverse()
    if corruption == "empty_role": ir["candidates"][0]["role"] = " "
    if corruption == "extra": ir["candidates"][0]["witness"] = {"X": 1}
    if corruption == "empty_target": ir["target_role"] = " "
    with pytest.raises(ValueError): select_from_similarities(ir, [0.1, 0.8])


class Tensor:
    """NumPy-backed synthetic Torch surface, no real model/framework inference."""
    def __init__(self, data): self.data = np.asarray(data)
    @property
    def shape(self): return self.data.shape
    def size(self): return self.data.shape
    def unsqueeze(self, dim): return Tensor(np.expand_dims(self.data, dim))
    def expand(self, size): return Tensor(np.broadcast_to(self.data, size))
    def float(self): return Tensor(self.data.astype(float))
    def __mul__(self, other): return Tensor(self.data * other.data)
    def __truediv__(self, other): return Tensor(self.data / other.data)
    def __getitem__(self, index): return Tensor(self.data[index])
    def __matmul__(self, other): return Tensor(self.data @ other.data)
    def to(self, device): return self
    def sum(self, dim=None): return Tensor(self.data.sum(axis=dim))
    def item(self): return self.data.item()
    def numel(self): return self.data.size
    def detach(self): return self
    def cpu(self): return self
    def tolist(self): return self.data.tolist()


def fake_torch_modules():
    torch = ModuleType("torch"); nn = ModuleType("torch.nn"); functional = ModuleType("torch.nn.functional")
    functional.normalize = lambda tensor, p, dim: Tensor(tensor.data / np.maximum(np.linalg.norm(tensor.data, axis=dim, keepdims=True), 1e-12))
    torch.nn = nn; nn.functional = functional
    torch.no_grad = lambda: nullcontext()
    torch.sum = lambda tensor, dim: Tensor(tensor.data.sum(axis=dim))
    torch.clamp = lambda tensor, min: Tensor(np.maximum(tensor.data, min))
    torch.device = lambda device: device
    return {"torch": torch, "torch.nn": nn, "torch.nn.functional": functional}


def synthetic_encoder(width=3, fail=False):
    modules = fake_torch_modules()
    backend = FrozenMiniLMSemanticEncoder.__new__(FrozenMiniLMSemanticEncoder)
    backend.torch = modules["torch"]; backend.device = "cpu"; backend.forward_calls = 0
    encoded = {"input_ids": Tensor(np.ones((3, width), dtype=int)),
               "attention_mask": Tensor(np.tile([1, 1, 0], (3, 1)) if width == 3 else np.ones((3, width), dtype=int))}
    backend.tokenizer = Mock(return_value=encoded)
    hidden = Tensor([[[1, 0], [3, 0], [99, 99]], [[0, 2], [0, 4], [99, 99]], [[2, 0], [4, 0], [99, 99]]])
    backend.model = Mock(side_effect=RuntimeError("synthetic forward failure")) if fail else Mock(return_value=[hidden])
    return backend, modules


def test_real_adapter_orchestration_single_batch_pooling_and_cosine_without_weights():
    encoder, modules = synthetic_encoder()
    with patch.dict(sys.modules, modules): result = encoder.score(example_ir())
    assert result["similarities"] == pytest.approx([0.0, 1.0])
    assert encoder.model.call_count == encoder.forward_calls == result["forward_calls"] == 1
    texts = encoder.tokenizer.call_args.args[0]
    assert texts == ["reserve path", "primary route", "reserve route"]
    assert encoder.tokenizer.call_args.kwargs["truncation"] is False
    assert result["input_rows"] == 3
    assert result["input_tokens"] == 6
    assert result["padded_tokens"] == 9
    assert select_from_similarities(example_ir(), result["similarities"])["selected_entity"] == "Y"


def test_encoder_context_overflow_stops_without_any_forward():
    encoder, modules = synthetic_encoder(width=257)
    with patch.dict(sys.modules, modules), pytest.raises(ValueError, match="no silent truncation"):
        encoder.score(example_ir())
    assert encoder.model.call_count == encoder.forward_calls == 0


def test_failed_forward_remains_charged():
    encoder, modules = synthetic_encoder(fail=True)
    with patch.dict(sys.modules, modules), pytest.raises(RuntimeError): encoder.score(example_ir())
    assert encoder.model.call_count == encoder.forward_calls == 1


@pytest.mark.parametrize("parameter_count", [MODEL["parameters"], MODEL["parameters"] + 1])
def test_lazy_loader_pins_revision_freezes_parameters_and_rejects_count_drift(parameter_count):
    modules = fake_torch_modules()
    parameter = SimpleNamespace(numel=lambda: parameter_count, requires_grad_=Mock())
    model = Mock(); model.to.return_value = model; model.parameters = lambda: iter([parameter])
    transformers = ModuleType("transformers")
    transformers.AutoModel = SimpleNamespace(from_pretrained=Mock(return_value=model))
    transformers.AutoTokenizer = SimpleNamespace(from_pretrained=Mock(return_value=Mock()))
    modules["transformers"] = transformers
    with patch.dict(sys.modules, modules):
        if parameter_count == MODEL["parameters"]: FrozenMiniLMSemanticEncoder()
        else:
            with pytest.raises(ValueError, match="parameter-count drift"): FrozenMiniLMSemanticEncoder()
    for loader in (transformers.AutoModel, transformers.AutoTokenizer):
        loader.from_pretrained.assert_called_once_with(MODEL["model_id"], revision=MODEL["model_revision"])
    model.eval.assert_called_once()
    parameter.requires_grad_.assert_called_once_with(False)


def test_encoder_malformed_ir_stops_before_tokenization():
    encoder, modules = synthetic_encoder()
    ir = example_ir(); ir["private_reference"] = {"X": 1}
    with patch.dict(sys.modules, modules), pytest.raises(ValueError): encoder.score(ir)
    assert encoder.tokenizer.call_count == encoder.model.call_count == 0


def test_local_artifact_loader_is_network_closed_and_uses_no_revision_lookup():
    modules = fake_torch_modules()
    parameter = SimpleNamespace(numel=lambda: MODEL["parameters"], requires_grad_=Mock())
    model = Mock(); model.to.return_value = model; model.parameters = lambda: iter([parameter])
    transformers = ModuleType("transformers")
    transformers.AutoModel = SimpleNamespace(from_pretrained=Mock(return_value=model))
    transformers.AutoTokenizer = SimpleNamespace(from_pretrained=Mock(return_value=Mock()))
    modules["transformers"] = transformers
    with patch.dict(sys.modules, modules):
        FrozenMiniLMSemanticEncoder(
            model_source="/tmp/p111-frozen",
            local_files_only=True,
        )
        with pytest.raises(ValueError, match="local-only"):
            FrozenMiniLMSemanticEncoder(
                model_source="/tmp/p111-frozen",
                local_files_only=False,
            )
    for loader in (transformers.AutoModel, transformers.AutoTokenizer):
        loader.from_pretrained.assert_called_once_with(
            "/tmp/p111-frozen",
            local_files_only=True,
        )


def test_failed_forward_retains_partial_token_and_attempt_costs():
    encoder, modules = synthetic_encoder(fail=True)
    with patch.dict(sys.modules, modules), pytest.raises(RuntimeError):
        encoder.score(example_ir())
    assert encoder.last_attempt["forward_calls"] == 1
    assert encoder.last_attempt["input_rows"] == 3
    assert encoder.last_attempt["input_tokens"] == 6
    assert encoder.last_attempt["padded_tokens"] == 9
