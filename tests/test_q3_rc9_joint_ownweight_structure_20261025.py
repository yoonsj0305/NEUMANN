"""Independent low-polynomial grader and science scope controls for RC9.1."""
import pathlib,sys,itertools
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/"research"/"q3"/"joint_structure_rc9"))
from learned_operator import product,rule_proven,local_rule,GATE_G,GATE_H

def independent_gf2(n,a,b):
    s=0
    for i in range(n):
        if (a>>i)&1:s^=b<<i
    return s&((1<<n)-1)

def test_local_8_rule_all_length_proof_and_mutants():
    assert rule_proven()
    for which in ("g","h"):
        for i in range(4):
            g=list(GATE_G);h=list(GATE_H)
            if which=="g":g[i]^=1
            else:h[i]^=1
            assert any(local_rule(c,a,b,g,h)!=(c^(a&b))
                       for c,a,b in itertools.product((0,1),repeat=3))

def test_all_unseen_four_to_eight_bit_pairs():
    count=0
    for n in range(4,9):
        for a in range(1<<n):
            for b in range(1<<n):
                assert product(n,a,b)==independent_gf2(n,a,b)
                count+=1
    assert count==87296

def test_robust_fail_closed_validation():
    for n,a,b in [(0,0,0),(2,-1,0),(2,0,9)]:
        try:product(n,a,b)
        except ValueError:pass
        else:raise AssertionError("failed to reject invalid input")
    try:product(3,1,2,route=("j","j"))
    except ValueError:pass
    else:raise AssertionError("route not proved cannot be admitted")

def test_learned_wiring_reused_with_human_integer_carry():
    count=0
    for n in range(1,8):
        for a in range(1<<n):
            for b in range(1<<n):
                carry=0;out=0
                for i in range(n):
                    carry_in=carry
                    for j in range(i+1):
                        carry_in+=GATE_G[((a>>(i-j))&1)+2*((b>>j)&1)]
                    out|=(carry_in&1)<<i;carry=carry_in>>1
                assert out==((a*b)&((1<<n)-1))
                count+=1
    assert count==21844
