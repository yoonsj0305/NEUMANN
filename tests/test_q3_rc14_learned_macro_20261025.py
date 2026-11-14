"""RC14 slim self-registering macro tests (full own PyTorch data in research ZIP)."""
import pathlib,random,sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/"research"/"q3"/"rc14"))
from registry import MacroRegistry,MODEL_SELECTED_CODE,exact_digit_normalization_proof_rule

def test_proof_gated_macro_and_rejected_ambiguous_candidate():
    reg=MacroRegistry()
    assert exact_digit_normalization_proof_rule(MODEL_SELECTED_CODE)
    assert reg.add_from_model("AUTO_RADIX2_NORMALIZE",MODEL_SELECTED_CODE,"sha-sealed").status=="SCOPED_CERTIFIED"
    assert reg.add_from_model("AUTO_WRONG",(1,1,1,0,0,2),"sha-sealed").status=="UNKNOWN_NO_ALL_LENGTH_PROOF"
    try:reg.invoke("AUTO_WRONG",[1,2,3])
    except ValueError:pass
    else:raise AssertionError("unverified macro should not execute")
    random_gen=random.Random(20261025)
    for n in (1,2,3,4,16,64,256,1024):
        for _ in range(12):
            digits=[random_gen.randrange(8) for i in range(n)]
            assert reg.invoke("AUTO_RADIX2_NORMALIZE",digits)==reg.reference_fallback(digits)

def test_three_factor_freeze_compatible_and_edge_conditions():
    reg=MacroRegistry()
    assert reg.add_from_model("AUTO_RADIX2_NORMALIZE",MODEL_SELECTED_CODE,"sha-sealed").status=="SCOPED_CERTIFIED"
    for n in (2,3,5,8):
        mask=(1<<n)-1
        for a in (0,1,3,7,mask):
            for b in (0,1,3,13,mask):
                for c in (0,1,3,mask):
                    a&=mask;b&=mask;c&=mask
                    digits=[sum(((a>>j)&1)*((b>>k)&1)*((c>>(i-j-k))&1)
                        for j in range(i+1) for k in range(i-j+1)) for i in range(n)]
                    bits,_=reg.invoke("AUTO_RADIX2_NORMALIZE",digits)
                    assert sum(v<<i for i,v in enumerate(bits))==(a*b*c)&mask
