"""RC27 exact audits to defend against upgrading scoped status to global."""
import pathlib,sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/"research"/"q3"/"rc27"))
from proof_boundary import FrozenEvidence,admit,runtime_choice,FROZEN_LONG_HORIZON

def test_long_horizon_receipts_neural_errors_repaired():
    v=FROZEN_LONG_HORIZON
    assert len(v)==8
    accepted=[x for x in v.values() if x['cert']]
    assert len(accepted)==7
    assert sum(x['neural'] for x in accepted)==125253
    assert sum(x['symbolic'] for x in accepted)==0
    assert sum(x['neural'] for x in v.values())==175982
    assert 7*262144==1835008

def test_fail_closed_evidence_and_proposer_provenance():
    ok=FrozenEvidence(502,"trained_gru","SCOPED_COMPILED",
        "PROVED_EQUIVALENT_FINITE_PROGRAM","PROVED_MINIMAL",190,0)
    assert admit(ok)=="SCOPED_CERTIFIED"
    bad=FrozenEvidence(504,"trained_gru","SCOPED_COMPILED",
        "FAIL_COUNTEREXAMPLE","FAIL_NONMINIMAL",50729,50729)
    assert admit(bad)=="UNKNOWN_NO_ALL_LENGTH_PROOF"
    teacher=FrozenEvidence(502,"classical_teacher","SCOPED_COMPILED",
        "PROVED_EQUIVALENT_FINITE_PROGRAM","PROVED_MINIMAL",0,0)
    assert admit(teacher)=="UNKNOWN_NOT_OWN_WEIGHT_SOURCE"
    assert runtime_choice(0.032,0.01)=="CLASSICAL_EXACT_FIRST"

def test_finite_observations_do_not_prove_neural_oracle_itself():
    # Both observers agree on all words the extractor tested (<=12), but
    # disagree later. Any validator making a universal neural claim from
    # ONLY those probes would be unsound.
    def oracle(word,mod,flip=False):
        v=int(word.count("1")%mod==0)
        return 1-v if flip and len(word)>=20 else v
    for k in (3,5):
        for n in range(0,13):
            for word in ("0"*n,"1"*n,("01"*7)[:n]):
                assert oracle(word,k)==oracle(word,k,True)
        assert oracle("1"*20,k)!=oracle("1"*20,k,True)
