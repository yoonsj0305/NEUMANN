"""RC21 regression guards: real learned-code runtime and CLASSICAL state grammar."""
import pathlib,sys,itertools
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/"research"/"q3"/"rc21"))
from learned_loop import SafeLearnedLoopLanguage,OWN_WEIGHT_SELECTED_CODE
from conditional_grammar import ConditionalStateGrammar

def test_neural_model_code_compiles_new_proof_gated_opcode():
    lang=SafeLearnedLoopLanguage()
    r=lang.register(OWN_WEIGHT_SELECTED_CODE,'0'*64)
    assert r=={"status":"SCOPED_CERTIFIED","token":"LEARNED_LOOP_6da4eabc0051"}
    assert lang.register((1,0,0,0,0),'0'*64)["status"]=="UNKNOWN_UNPROVED"
    for x in range(120):
        for b in range(2,20):
            rec=lang.execute(r["token"],x,b)
            assert rec["status"]=="EXACT" and (rec["q"],rec["r"])==divmod(x,b)
    digits=[0,2,3,7,2,8,3,2,10]
    receipt=lang.carry_normalize(r["token"],digits)
    total=sum(d<<i for i,d in enumerate(digits))
    assert receipt["low_bits"]==total&((1<<len(digits))-1)
    assert receipt["carry"]==total>>len(digits)
    assert lang.execute(r["token"],100,2,step_cap=1)["status"]=="UNKNOWN_STEP_CAP"

def test_classical_state_symbols_grow_without_maximum_state_capacity():
    for k in (3,5,7):
        def target(w):return int(sum(c=='1' for c in w)%k==0)
        def check(machine):
            for n in range(2*k+1):
                for tup in itertools.product('01',repeat=n):
                    w=''.join(tup);s=machine['initial']
                    for c in w:s=machine['transitions'][s][c]
                    if machine['output'][s]!=target(w):return w
            return None # this *bounded* check alone cannot prove unbounded equivalence
        r=ConditionalStateGrammar(target,check).synthesize()
        assert r['status']=='CONDITIONAL_EQ_CERTIFIED' and r['states']==k
        assert r['equivalence_queries']>0
