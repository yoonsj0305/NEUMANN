"""Fail-closed *source rights* for NEUMANN program discovery tasks.

A finite set of authored input/output examples is NOT an oracle to an
unknown intended function at arbitrary new inputs. An invariant proof
counterexample is NOT a correct invariant label. No neural model may
silently fabricate missing source information.
"""
from dataclasses import dataclass
from enum import Enum

class SourceFeedback(str,Enum):
    ORIGINAL_EXAMPLE = 'original_example'
    FULL_SYMBOLIC_COUNTEREXAMPLE = 'full_symbolic_counterexample'
    INDUCTIVE_VC_COUNTEREXAMPLE = 'inductive_vc_counterexample'
    ARBITRARY_TARGET_OUTPUT = 'arbitrary_target_output'

class SourceKind(str,Enum):
    EXPLICIT_PBE = 'explicit_pbe'
    UNIVERSAL_SYMBOLIC = 'universal_symbolic'
    INVARIANT_VC = 'invariant_vc'

@dataclass(frozen=True)
class SourceRights:
    kind: SourceKind
    provided_ground_examples: int
    independent_target_oracle_explicitly_available: bool = False

    def permits(self,feedback:SourceFeedback) -> bool:
        if feedback is SourceFeedback.ARBITRARY_TARGET_OUTPUT:
            return self.independent_target_oracle_explicitly_available
        if feedback is SourceFeedback.ORIGINAL_EXAMPLE:
            return self.provided_ground_examples>0
        if feedback is SourceFeedback.FULL_SYMBOLIC_COUNTEREXAMPLE:
            return self.kind is SourceKind.UNIVERSAL_SYMBOLIC
        if feedback is SourceFeedback.INDUCTIVE_VC_COUNTEREXAMPLE:
            return self.kind is SourceKind.INVARIANT_VC
        return False

def author_rights(kind,authored_ground_examples=0):
    """Public original source has no arbitrary ideal-output oracle by default."""
    if authored_ground_examples<0:raise ValueError('INVALID_EXAMPLE_COUNT')
    return SourceRights(SourceKind(kind),authored_ground_examples,False)

def require_feedback(rights:SourceRights,requested:SourceFeedback):
    if not rights.permits(requested):
        raise PermissionError(
            'SOURCE_FEEDBACK_NOT_GROUNDED:' + str(requested.value) +
            '; no invented original output labels or original I(state) labels')
    return True

def original_frozen16_rights_summary():
    # Four distinct source groups (4 CLIA, 4 code2inv, 4 PBE BV, 4 PBE SLIA).
    # The declared feedback type is a source right, not model score.
    return {
        'CLIA_4':author_rights(SourceKind.UNIVERSAL_SYMBOLIC),
        'code2inv_4':author_rights(SourceKind.INVARIANT_VC),
        'PBE_BV_4':author_rights(SourceKind.EXPLICIT_PBE,1),
        'PBE_SLIA_4':author_rights(SourceKind.EXPLICIT_PBE,1),
    }

if __name__=='__main__':
    import json
    d={k:{'kind':v.kind.value,'arbitrary_target_oracle':v.permits(SourceFeedback.ARBITRARY_TARGET_OUTPUT)}
       for k,v in original_frozen16_rights_summary().items()}
    print(json.dumps(d,indent=2,sort_keys=True))
