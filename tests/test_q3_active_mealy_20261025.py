"""Research-only Q3 capability/regression, not a global Q3 discovery score."""
import pathlib,sys,itertools
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/"research"/"q3"/"active_mealy"))
from learned_active_inference import learn,execute,learned_equal

def oracle(m):
    def f(word):return execute(m,word)
    return f

def eq(m,alphabet):
    def f(candidate):
        todo=[(0,0,())];seen=set()
        while todo:
            a,b,p=todo.pop(0)
            if (a,b) in seen:continue
            seen.add((a,b))
            for x in alphabet:
                if candidate["output"][a][x]!=m["output"][b][x]:return p+(x,)
                todo.append((candidate["transition"][a][x],m["transition"][b][x],p+(x,)))
        return None
    return f

def test_late_reveal_without_eq_stays_provisional():
    m={"transition":[[(i+1)%7,0] for i in range(7)],
       "output":[[int(i==6),0] for i in range(7)]}
    p=learn(oracle(m))
    assert p["states"]==1 and "PROVISIONAL" in p["status"]
    assert execute(p,(0,)*7)!=execute(m,(0,)*7)
    q=learn(oracle(m),eq(m,(0,1)))
    assert q["states"]==7 and q["EQ_calls"]>=2
    assert eq(m,(0,1))(q) is None

def test_learned_equal_is_redundant_exact_observation_comparison():
    for k in range(1,6):
        for bits in itertools.product((0,1),repeat=k):
            x=tuple((v,) for v in bits)
            y=tuple((1-v,) for v in bits)
            assert learned_equal(x,x)
            assert not learned_equal(x,y)

def test_three_operand_sum_new_input_alphabet_and_variable_state_count():
    alphabet=tuple(range(8))
    s=[];o=[]
    for carry in range(3):
        ss=[];oo=[]
        for sym in alphabet:
            t=(sym&1)+((sym>>1)&1)+((sym>>2)&1)+carry
            ss.append(t//2);oo.append(t%2)
        s.append(ss);o.append(oo)
    m={"transition":s,"output":o}
    q=learn(oracle(m),eq(m,alphabet),alphabet=alphabet)
    assert q["states"]==3 and eq(m,alphabet)(q) is None
    for n in range(1,5):
        for a in range(1<<n):
            for b in range(1<<n):
                for c in range(1<<n):
                    w=tuple(((a>>i)&1)+2*((b>>i)&1)+4*((c>>i)&1)
                            for i in range(n+2))
                    z=execute(q,w)
                    assert sum(v<<i for i,v in enumerate(z))==a+b+c
