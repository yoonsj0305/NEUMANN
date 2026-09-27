from .types import Problem, Representation, IRKind, SolveResult, CostLedger, VerificationResult
from .engine import NeumannEngine
from .representation import ExplicitStructureFormer
from .solvers import BipartiteMatchingSolver, ShortestPathSolver, LinearSystemSolver
from .verifier import DeterministicVerifier
from .reference_semantics import ReferenceSemanticVerifier, SemanticContract

__all__ = [
    "Problem", "Representation", "IRKind", "SolveResult", "CostLedger", "VerificationResult",
    "NeumannEngine", "ExplicitStructureFormer", "BipartiteMatchingSolver",
    "ShortestPathSolver", "LinearSystemSolver", "DeterministicVerifier",
    "ReferenceSemanticVerifier", "SemanticContract",
]

from .learned_representation import LearnedKindStructureFormer, KeywordKindBaseline, KindTrainingExample
from .kind_dataset import training_examples, heldout_examples
__all__ += ["LearnedKindStructureFormer", "KeywordKindBaseline", "KindTrainingExample", "training_examples", "heldout_examples"]

from .open_set import TwoStageOpenSetStructureFormer, OpenSetMetrics
from .open_set_dataset import final_test_examples
__all__ += ["TwoStageOpenSetStructureFormer", "OpenSetMetrics", "final_test_examples"]

from .prototype_open_set import PrototypeOpenSetStructureFormer, PrototypeMetrics
from .open_set_v006_dataset import validation_v006, final_test_v006
__all__ += ["PrototypeOpenSetStructureFormer", "PrototypeMetrics", "validation_v006", "final_test_v006"]

from .matching_ir import ControlledMatchingStructureFormer, MatchingSemanticVerifier, MatchingSemanticContract
__all__ += ["ControlledMatchingStructureFormer", "MatchingSemanticVerifier", "MatchingSemanticContract"]

from .linear_ir import ControlledLinearSystemStructureFormer, LinearSemanticVerifier, LinearSemanticContract
from .composite import CompositeStructureFormer
__all__ += ["ControlledLinearSystemStructureFormer", "LinearSemanticVerifier", "LinearSemanticContract", "CompositeStructureFormer"]

from .learned_compiler_gate import LearnedProposalCompilerGate
from .compiler_gate_dataset import compiler_gate_training_examples, compiler_gate_validation_examples, compiler_gate_final_examples
__all__ += ["LearnedProposalCompilerGate", "compiler_gate_training_examples", "compiler_gate_validation_examples", "compiler_gate_final_examples"]

from .family_registry import FamilyAdapter, FamilyRegistry, FAMILY_CONTRACT_VERSION, builtin_family_registry
from .registry_engine import RegistryEngine
from .family_conformance import ConformanceResult, run_family_conformance
__all__ += ["FamilyAdapter", "FamilyRegistry", "FAMILY_CONTRACT_VERSION", "builtin_family_registry", "RegistryEngine", "ConformanceResult", "run_family_conformance"]

from .types import KindLike, kind_id, is_unknown_kind, display_kind
__all__ += ["KindLike", "kind_id", "is_unknown_kind", "display_kind"]

from .plugin_manifest import PluginManifest, PluginCatalog, ActivationPolicy, PluginActivator, PLUGIN_MANIFEST_VERSION
__all__ += ["PluginManifest", "PluginCatalog", "ActivationPolicy", "PluginActivator", "PLUGIN_MANIFEST_VERSION"]

from .plugin_discovery import DiscoveredManifest, DiscoveryIssue, DiscoveryReport, discover_installed_manifests, catalog_from_discovery
__all__ += ["DiscoveredManifest", "DiscoveryIssue", "DiscoveryReport", "discover_installed_manifests", "catalog_from_discovery"]

from .plugin_loading import resolve_python_entry_point, activate_python_plugin
__all__ += ["resolve_python_entry_point", "activate_python_plugin"]

from .plugin_authorization import (
    AuthorizationEvent, AuthorizationState, PluginAuthorizationLedger,
    PluginRuntimeBinding, ManagedPluginRegistry, AuthorizedPluginActivator,
)
__all__ += [
    "AuthorizationEvent", "AuthorizationState", "PluginAuthorizationLedger",
    "PluginRuntimeBinding", "ManagedPluginRegistry", "AuthorizedPluginActivator",
]

from .persistent_authorization import (
    PERSISTENT_LEDGER_VERSION, GENESIS_HASH, LedgerIntegrityError, LedgerCheckpoint,
    HashChainedAuthorizationLedger,
)
__all__ += [
    "PERSISTENT_LEDGER_VERSION", "GENESIS_HASH", "LedgerIntegrityError",
    "LedgerCheckpoint", "HashChainedAuthorizationLedger",
]

from .threat_model import (
    THREAT_MODEL_VERSION, Assurance, ThreatActor, Asset, TrustBoundary,
    ThreatScenario, default_threat_model, assurance_counts,
    unresolved_host_integrity_scenarios, next_control_priority,
    THREAT_MODEL_VERSION_V2, threat_model_v2, next_security_control_priority_v2,
)
__all__ += [
    "THREAT_MODEL_VERSION", "Assurance", "ThreatActor", "Asset", "TrustBoundary",
    "ThreatScenario", "default_threat_model", "assurance_counts",
    "unresolved_host_integrity_scenarios", "next_control_priority",
    "THREAT_MODEL_VERSION_V2", "threat_model_v2", "next_security_control_priority_v2",
]

from .plugin_isolation import (
    PLUGIN_RPC_VERSION, MAX_REQUEST_BYTES, MAX_RESPONSE_BYTES,
    PluginProcessError, PluginProcessTimeout, PluginProtocolError,
    SubprocessPluginDispatcher, OutOfProcessCompiler, OutOfProcessSolver,
    OutOfProcessVerifier, build_out_of_process_adapter,
)
__all__ += [
    "PLUGIN_RPC_VERSION", "MAX_REQUEST_BYTES", "MAX_RESPONSE_BYTES",
    "PluginProcessError", "PluginProcessTimeout", "PluginProtocolError",
    "SubprocessPluginDispatcher", "OutOfProcessCompiler", "OutOfProcessSolver",
    "OutOfProcessVerifier", "build_out_of_process_adapter",
]

from .runtime_cost import RuntimeCostAssessment, assess_dispatch_timings
__all__ += ["RuntimeCostAssessment", "assess_dispatch_timings"]

from .persistent_plugin_isolation import (
    PERSISTENT_PLUGIN_RPC_VERSION, WorkerStatePolicy, WorkerRecycleEvent,
    PersistentSubprocessPluginDispatcher, build_persistent_out_of_process_adapter,
)
__all__ += [
    "PERSISTENT_PLUGIN_RPC_VERSION", "WorkerStatePolicy", "WorkerRecycleEvent",
    "PersistentSubprocessPluginDispatcher", "build_persistent_out_of_process_adapter",
]

from .worker_lifecycle import (
    WorkerStateClass, LifecycleMode, LifecycleDecision,
    parse_worker_state_class, persistent_lifecycle_decision, fresh_lifecycle_decision,
    require_persistent_compatible, require_fresh_compatible,
)
__all__ += [
    "WorkerStateClass", "LifecycleMode", "LifecycleDecision",
    "parse_worker_state_class", "persistent_lifecycle_decision", "fresh_lifecycle_decision",
    "require_persistent_compatible", "require_fresh_compatible",
]

from .lifecycle_attestation import (
    LIFECYCLE_ATTESTATION_VERSION, MIN_ATTESTATION_CASES, MIN_WARM_REPETITIONS,
    AttestationStatus, LifecycleConformanceCase, LifecycleAttestation,
    LifecycleAttestationRegistry, conformance_corpus_digest,
    run_lifecycle_conformance_attestation,
)
__all__ += [
    "LIFECYCLE_ATTESTATION_VERSION", "MIN_ATTESTATION_CASES", "MIN_WARM_REPETITIONS",
    "AttestationStatus", "LifecycleConformanceCase", "LifecycleAttestation",
    "LifecycleAttestationRegistry", "conformance_corpus_digest",
    "run_lifecycle_conformance_attestation",
]


from .persistent_attestation import (
    PERSISTENT_ATTESTATION_LEDGER_VERSION, ATTESTATION_GENESIS_HASH,
    AttestationLedgerIntegrityError, AttestationLedgerCheckpoint,
    AttestationLedgerEvent, AttestationEvidenceState, HashChainedAttestationLedger,
)
__all__ += [
    "PERSISTENT_ATTESTATION_LEDGER_VERSION", "ATTESTATION_GENESIS_HASH",
    "AttestationLedgerIntegrityError", "AttestationLedgerCheckpoint",
    "AttestationLedgerEvent", "AttestationEvidenceState", "HashChainedAttestationLedger",
]


from .structural_efficiency import (
    ExecutionCostSnapshot, StructuralEfficiencyObservation,
    canonical_representation_bytes, measure_repeated_structural_reuse,
)
__all__ += [
    "ExecutionCostSnapshot", "StructuralEfficiencyObservation",
    "canonical_representation_bytes", "measure_repeated_structural_reuse",
]

from .model_side_cost import (
    TwoStageModelFootprint, ProposalCostObservation,
    RepeatedProposalReuseObservation, inspect_two_stage_model,
    measure_two_stage_proposal, measure_repeated_proposal_reuse,
)
__all__ += [
    "TwoStageModelFootprint", "ProposalCostObservation",
    "RepeatedProposalReuseObservation", "inspect_two_stage_model",
    "measure_two_stage_proposal", "measure_repeated_proposal_reuse",
]

from .neural_open_set import TinyNeuralOpenSetStructureFormer, NeuralOpenSetMetrics
from .neural_model_cost import (
    TinyNeuralModelFootprint, NeuralProposalCostObservation,
    RepeatedNeuralProposalReuseObservation, inspect_tiny_neural_model,
    measure_tiny_neural_proposal, measure_repeated_neural_proposal_reuse,
)
__all__ += [
    "TinyNeuralOpenSetStructureFormer", "NeuralOpenSetMetrics",
    "TinyNeuralModelFootprint", "NeuralProposalCostObservation",
    "RepeatedNeuralProposalReuseObservation", "inspect_tiny_neural_model",
    "measure_tiny_neural_proposal", "measure_repeated_neural_proposal_reuse",
]
