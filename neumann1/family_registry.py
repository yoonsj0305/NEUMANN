from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable, Mapping

from .types import IRKind, KindLike, kind_id


FAMILY_CONTRACT_VERSION = "neumann.family.v1"


@dataclass(frozen=True)
class FamilyAdapter:
    """Runtime bundle for one representation family.

    Built-in families may use legacy IRKind values. Third-party families use
    open namespaced string kinds, for example "acme.min_cost_flow".
    """

    family_id: str
    ir_kind: KindLike
    compiler: object
    solver: object
    answer_verifier: object
    contract_version: str = FAMILY_CONTRACT_VERSION

    @property
    def canonical_kind_id(self) -> str:
        return kind_id(self.ir_kind)


class FamilyRegistry:
    def __init__(self, adapters: Iterable[FamilyAdapter] = ()):
        self._by_kind_id: dict[str, FamilyAdapter] = {}
        self._by_id: dict[str, FamilyAdapter] = {}
        for adapter in adapters:
            self.register(adapter)

    def register(self, adapter: FamilyAdapter) -> None:
        if adapter.contract_version != FAMILY_CONTRACT_VERSION:
            raise ValueError(
                f"unsupported family contract {adapter.contract_version!r}; "
                f"expected {FAMILY_CONTRACT_VERSION!r}"
            )

        canonical = adapter.canonical_kind_id
        if canonical == "core.unknown":
            raise ValueError("UNKNOWN cannot be registered as an executable family")
        if adapter.family_id in self._by_id:
            raise ValueError(f"duplicate family_id: {adapter.family_id}")
        if canonical in self._by_kind_id:
            raise ValueError(f"duplicate IR kind: {canonical}")

        if not callable(getattr(adapter.compiler, "form", None)):
            raise TypeError("family compiler must expose form(problem, ledger)")
        if not callable(getattr(adapter.solver, "supports", None)) or not callable(
            getattr(adapter.solver, "solve", None)
        ):
            raise TypeError("family solver must expose supports() and solve()")
        if not callable(getattr(adapter.answer_verifier, "verify", None)):
            raise TypeError("family answer verifier must expose verify()")

        self._by_id[adapter.family_id] = adapter
        self._by_kind_id[canonical] = adapter

    def get(self, kind: KindLike) -> FamilyAdapter | None:
        return self._by_kind_id.get(kind_id(kind))

    def get_by_id(self, family_id: str) -> FamilyAdapter | None:
        return self._by_id.get(family_id)

    def kinds(self) -> tuple[KindLike, ...]:
        return tuple(adapter.ir_kind for adapter in self._by_id.values())

    def kind_ids(self) -> tuple[str, ...]:
        return tuple(self._by_kind_id)

    def adapters(self) -> tuple[FamilyAdapter, ...]:
        return tuple(self._by_id.values())

    def compilers_by_kind(self) -> Mapping[KindLike, object]:
        return {adapter.ir_kind: adapter.compiler for adapter in self._by_id.values()}

    def solvers(self) -> tuple[object, ...]:
        return tuple(adapter.solver for adapter in self._by_id.values())


def builtin_family_registry() -> FamilyRegistry:
    from .matching_ir import ControlledMatchingStructureFormer
    from .linear_ir import ControlledLinearSystemStructureFormer
    from .solvers import BipartiteMatchingSolver, LinearSystemSolver
    from .verifier import DeterministicVerifier

    verifier = DeterministicVerifier()
    return FamilyRegistry(
        [
            FamilyAdapter(
                family_id="core.bipartite_matching",
                ir_kind=IRKind.BIPARTITE_MATCHING,
                compiler=ControlledMatchingStructureFormer(),
                solver=BipartiteMatchingSolver(),
                answer_verifier=verifier,
            ),
            FamilyAdapter(
                family_id="core.linear_system",
                ir_kind=IRKind.LINEAR_SYSTEM,
                compiler=ControlledLinearSystemStructureFormer(),
                solver=LinearSystemSolver(),
                answer_verifier=verifier,
            ),
        ]
    )
