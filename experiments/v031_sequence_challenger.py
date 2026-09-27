from __future__ import annotations

from dataclasses import dataclass
import math
import re
import time
from typing import Iterable, Sequence

import torch
from torch import nn
from torch.utils.data import DataLoader, TensorDataset

from neumann1.direct_frontier import (
    PAIR_CLASS_COUNT,
    class_to_solution_pair,
    solution_pair_to_class,
)
from neumann1.paired_linear_dataset import (
    PairedLinearExample,
    make_near_negative,
)


_TOKEN_RE = re.compile(
    r"<=|>=|!=|[A-Za-z_][A-Za-z0-9_]*|"
    r"\d+(?:\.\d+)?|[+\-*/=;:,().]"
)
_TOKEN_CATEGORIES = (
    "PAD",
    "NUM",
    "VAR0",
    "VAR1",
    "VARX",
    "+",
    "-",
    "*",
    "/",
    "=",
    ";",
    "<=",
    ">=",
    "!=",
    "SOLVE",
    "EQUATION",
    "WORD",
    "PUNCT",
)
PAD_ID = 0
STRUCTURAL_LINEAR_CLASS = 0
STRUCTURAL_ABSTAIN_CLASS = PAIR_CLASS_COUNT
OUTPUT_CLASSES = PAIR_CLASS_COUNT + 1


@dataclass(frozen=True)
class SequenceExperimentConfig:
    max_tokens: int = 32
    numeric_scale: float = 32.0
    embedding_dim: int = 64
    d_model: int = 64
    heads: int = 4
    layers: int = 2
    feedforward_dim: int = 128
    output_classes: int = OUTPUT_CLASSES
    direct_training_examples: int = 8192
    structural_positive_examples: int = 4096
    structural_negative_examples: int = 4096
    epochs: int = 12
    batch_size: int = 256
    learning_rate: float = 2e-3
    weight_decay: float = 1e-4
    seed: int = 31
    cpu_threads: int = 2


@dataclass(frozen=True)
class EncodedSequence:
    token_ids: tuple[int, ...]
    numeric_values: tuple[float, ...]
    length: int


@dataclass(frozen=True)
class SequenceModelFootprint:
    parameter_count: int
    parameter_bytes: int
    architecture_weighted_sum_terms_proxy: int


@dataclass(frozen=True)
class SequencePairModels:
    config: SequenceExperimentConfig
    tokenizer: "SequenceTokenizer"
    direct_model: "TinySequenceTransformer"
    structural_model: "TinySequenceTransformer"
    direct_training_seconds: float
    structural_training_seconds: float


class SequenceTokenizer:
    """Small categorical tokenizer with an explicit numeric scalar channel."""

    def __init__(
        self,
        *,
        max_tokens: int = 32,
        numeric_scale: float = 32.0,
    ):
        if max_tokens < 1:
            raise ValueError("max_tokens must be >= 1")
        if numeric_scale <= 0:
            raise ValueError("numeric_scale must be positive")
        self.max_tokens = int(max_tokens)
        self.numeric_scale = float(numeric_scale)
        self.category_to_id = {
            category: index
            for index, category in enumerate(_TOKEN_CATEGORIES)
        }

    @property
    def vocabulary_size(self) -> int:
        return len(_TOKEN_CATEGORIES)

    def encode(self, text: str) -> EncodedSequence:
        variables: dict[str, int] = {}
        ids: list[int] = []
        numeric_values: list[float] = []

        for token in _TOKEN_RE.findall(text):
            lower = token.lower()
            numeric_value = 0.0

            if re.fullmatch(r"\d+(?:\.\d+)?", token):
                category = "NUM"
                numeric_value = float(token) / self.numeric_scale
            elif lower == "solve":
                category = "SOLVE"
            elif lower == "equation":
                category = "EQUATION"
            elif re.fullmatch(r"[A-Za-z]", token):
                if lower not in variables:
                    variables[lower] = len(variables)
                ordinal = variables[lower]
                if ordinal == 0:
                    category = "VAR0"
                elif ordinal == 1:
                    category = "VAR1"
                else:
                    category = "VARX"
            elif token in {
                "+",
                "-",
                "*",
                "/",
                "=",
                ";",
                "<=",
                ">=",
                "!=",
            }:
                category = token
            elif re.fullmatch(
                r"[A-Za-z_][A-Za-z0-9_]*",
                token,
            ):
                category = "WORD"
            else:
                category = "PUNCT"

            ids.append(self.category_to_id[category])
            numeric_values.append(numeric_value)

        if len(ids) > self.max_tokens:
            raise ValueError(
                f"token length {len(ids)} exceeds max_tokens={self.max_tokens}"
            )

        length = len(ids)
        ids.extend([PAD_ID] * (self.max_tokens - length))
        numeric_values.extend(
            [0.0] * (self.max_tokens - length)
        )
        return EncodedSequence(
            token_ids=tuple(ids),
            numeric_values=tuple(numeric_values),
            length=length,
        )

    def encode_many(
        self,
        texts: Iterable[str],
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        encoded = [self.encode(text) for text in texts]
        token_ids = torch.tensor(
            [item.token_ids for item in encoded],
            dtype=torch.long,
        )
        numeric_values = torch.tensor(
            [item.numeric_values for item in encoded],
            dtype=torch.float32,
        ).unsqueeze(-1)
        lengths = torch.tensor(
            [item.length for item in encoded],
            dtype=torch.long,
        )
        return token_ids, numeric_values, lengths


class TinySequenceTransformer(nn.Module):
    """Two-layer token Transformer used only by the v0.0.31 experiment."""

    def __init__(
        self,
        tokenizer: SequenceTokenizer,
        config: SequenceExperimentConfig,
    ):
        super().__init__()
        if config.embedding_dim != config.d_model:
            raise ValueError(
                "embedding_dim must equal d_model in v0.0.31"
            )
        if config.d_model % config.heads != 0:
            raise ValueError("d_model must be divisible by heads")

        self.config = config
        self.token_embedding = nn.Embedding(
            tokenizer.vocabulary_size,
            config.d_model,
            padding_idx=PAD_ID,
        )
        self.numeric_projection = nn.Linear(
            1,
            config.d_model,
            bias=False,
        )
        self.position_embedding = nn.Embedding(
            config.max_tokens,
            config.d_model,
        )
        layer = nn.TransformerEncoderLayer(
            d_model=config.d_model,
            nhead=config.heads,
            dim_feedforward=config.feedforward_dim,
            dropout=0.0,
            activation="gelu",
            batch_first=True,
            norm_first=False,
        )
        self.encoder = nn.TransformerEncoder(
            layer,
            num_layers=config.layers,
            enable_nested_tensor=False,
        )
        self.head = nn.Linear(
            config.d_model,
            config.output_classes,
        )

    def forward(
        self,
        token_ids: torch.Tensor,
        numeric_values: torch.Tensor,
        lengths: torch.Tensor,
    ) -> torch.Tensor:
        positions = torch.arange(
            token_ids.shape[1],
            device=token_ids.device,
        ).unsqueeze(0)
        hidden = (
            self.token_embedding(token_ids)
            + self.numeric_projection(numeric_values)
            + self.position_embedding(positions)
        )
        padding_mask = token_ids.eq(PAD_ID)
        hidden = self.encoder(
            hidden,
            src_key_padding_mask=padding_mask,
        )

        live = (~padding_mask).to(hidden.dtype).unsqueeze(-1)
        pooled = (hidden * live).sum(dim=1) / live.sum(
            dim=1
        ).clamp_min(1.0)
        return self.head(pooled)


def configure_deterministic_cpu(
    config: SequenceExperimentConfig,
) -> None:
    torch.manual_seed(config.seed)
    torch.set_num_threads(config.cpu_threads)
    try:
        torch.set_num_interop_threads(1)
    except RuntimeError:
        pass
    torch.use_deterministic_algorithms(True)


def _training_tensors(
    tokenizer: SequenceTokenizer,
    texts: Sequence[str],
    labels: Sequence[int],
) -> TensorDataset:
    if len(texts) != len(labels):
        raise ValueError("texts and labels must have equal length")
    token_ids, numeric_values, lengths = tokenizer.encode_many(
        texts
    )
    targets = torch.tensor(labels, dtype=torch.long)
    return TensorDataset(
        token_ids,
        numeric_values,
        lengths,
        targets,
    )


def _fit_model(
    model: TinySequenceTransformer,
    dataset: TensorDataset,
    config: SequenceExperimentConfig,
) -> float:
    generator = torch.Generator().manual_seed(config.seed)
    loader = DataLoader(
        dataset,
        batch_size=config.batch_size,
        shuffle=True,
        generator=generator,
    )
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=config.learning_rate,
        weight_decay=config.weight_decay,
    )
    loss_fn = nn.CrossEntropyLoss()

    started = time.perf_counter()
    model.train()
    for _ in range(config.epochs):
        for (
            token_ids,
            numeric_values,
            lengths,
            targets,
        ) in loader:
            optimizer.zero_grad(set_to_none=True)
            logits = model(
                token_ids,
                numeric_values,
                lengths,
            )
            loss = loss_fn(logits, targets)
            loss.backward()
            nn.utils.clip_grad_norm_(
                model.parameters(),
                max_norm=1.0,
            )
            optimizer.step()

    return time.perf_counter() - started


def fit_sequence_pair(
    training_pool: Sequence[PairedLinearExample],
    *,
    config: SequenceExperimentConfig | None = None,
) -> SequencePairModels:
    config = config or SequenceExperimentConfig()
    required = max(
        config.direct_training_examples,
        config.structural_positive_examples,
    )
    if len(training_pool) < required:
        raise ValueError(
            "training pool is smaller than the pre-registered requirement"
        )
    if (
        config.structural_positive_examples
        != config.structural_negative_examples
    ):
        raise ValueError(
            "v0.0.31 requires equal structural positive/negative counts"
        )
    if (
        config.direct_training_examples
        != config.structural_positive_examples
        + config.structural_negative_examples
    ):
        raise ValueError(
            "Direct and Structural total training cardinality must match"
        )

    configure_deterministic_cpu(config)
    tokenizer = SequenceTokenizer(
        max_tokens=config.max_tokens,
        numeric_scale=config.numeric_scale,
    )

    direct_examples = list(
        training_pool[: config.direct_training_examples]
    )
    direct_texts = [example.text for example in direct_examples]
    direct_labels = [
        solution_pair_to_class(example.solution)
        for example in direct_examples
    ]

    structural_positive = list(
        training_pool[: config.structural_positive_examples]
    )
    structural_texts = [
        example.text for example in structural_positive
    ]
    structural_labels = [
        STRUCTURAL_LINEAR_CLASS
        for _ in structural_positive
    ]
    structural_texts.extend(
        make_near_negative(example, index)
        for index, example in enumerate(structural_positive)
    )
    structural_labels.extend(
        STRUCTURAL_ABSTAIN_CLASS
        for _ in structural_positive
    )

    direct_dataset = _training_tensors(
        tokenizer,
        direct_texts,
        direct_labels,
    )
    structural_dataset = _training_tensors(
        tokenizer,
        structural_texts,
        structural_labels,
    )

    torch.manual_seed(config.seed)
    direct_model = TinySequenceTransformer(
        tokenizer,
        config,
    )
    direct_seconds = _fit_model(
        direct_model,
        direct_dataset,
        config,
    )

    torch.manual_seed(config.seed)
    structural_model = TinySequenceTransformer(
        tokenizer,
        config,
    )
    structural_seconds = _fit_model(
        structural_model,
        structural_dataset,
        config,
    )

    return SequencePairModels(
        config=config,
        tokenizer=tokenizer,
        direct_model=direct_model,
        structural_model=structural_model,
        direct_training_seconds=direct_seconds,
        structural_training_seconds=structural_seconds,
    )


def model_footprint(
    model: TinySequenceTransformer,
    *,
    token_length: int,
) -> SequenceModelFootprint:
    if token_length < 1:
        raise ValueError("token_length must be >= 1")

    parameter_count = sum(
        parameter.numel()
        for parameter in model.parameters()
    )
    parameter_bytes = sum(
        parameter.numel() * parameter.element_size()
        for parameter in model.parameters()
    )

    config = model.config
    t = int(token_length)
    d = config.d_model
    ff = config.feedforward_dim

    numeric_projection_terms = t * d
    per_layer = (
        4 * t * d * d
        + 2 * t * t * d
        + 2 * t * d * ff
    )
    head_terms = d * config.output_classes
    proxy = (
        numeric_projection_terms
        + config.layers * per_layer
        + head_terms
    )

    return SequenceModelFootprint(
        parameter_count=int(parameter_count),
        parameter_bytes=int(parameter_bytes),
        architecture_weighted_sum_terms_proxy=int(proxy),
    )


def predict_classes(
    model: TinySequenceTransformer,
    tokenizer: SequenceTokenizer,
    texts: Sequence[str],
) -> tuple[list[int], float]:
    token_ids, numeric_values, lengths = tokenizer.encode_many(
        texts
    )
    model.eval()
    started = time.perf_counter()
    with torch.no_grad():
        logits = model(
            token_ids,
            numeric_values,
            lengths,
        )
        predicted = logits.argmax(dim=-1)
    wall_seconds = time.perf_counter() - started
    return [int(value) for value in predicted.tolist()], wall_seconds


def decode_direct_class(
    class_id: int,
) -> tuple[float, float] | None:
    if 0 <= int(class_id) < PAIR_CLASS_COUNT:
        return class_to_solution_pair(int(class_id))
    return None


def structural_accepts(class_id: int) -> bool:
    return int(class_id) == STRUCTURAL_LINEAR_CLASS
