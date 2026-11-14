"""Independent old RC14 grammar capacity probe against sealed new RC16 source."""
import pathlib,sys,json
from itertools import product
here=pathlib.Path(__file__).resolve()
sys.path.insert(0,str(here.parents[2]/"rc14"))
# Keep the exact historical base grammar in this standalone probe.
def run_old(bits,code):
    alloc,op,x,y,emit,update=code
    r=0;result=[]
    for digit in bits:
        v=(r if alloc else 0,digit,0,1)
        a,b=v[x],v[y]
        tmp=(a+b,a^b,a|b,max(a,b),a-b,a*b)[op]
        bit=(tmp&1,(tmp>>1)&1,int(tmp!=0),1-(tmp&1))[emit]
        r=(tmp,tmp,tmp//2,tmp//3,tmp//4,tmp%2,0,max(tmp,0))[update] if alloc else 0
        if abs(r)>100000000:return None
        result.append(bit)
    return tuple(result)

def probe(dataset):
    examples=[]
    for key,target in dataset.items():
        n,x=map(int,key.split(":"))
        examples.append((tuple((x>>i)&1 for i in range(n)),tuple(target)))
    best=(-1,None);perfect=0;total=0
    for code in product(range(2),range(6),range(4),range(4),range(4),range(8)):
        s=0
        for bits,target in examples:
            pred=run_old(bits,code)
            if pred is None:s=-1;break
            s+=sum(a==b for a,b in zip(pred,target))
        if s>best[0]:best=(s,code)
        perfect+=(s==258);total+=1
    return {'programs':total,'best':best,'perfect':perfect}

if __name__=="__main__":
    # Sealed examples are in the full reproducible ZIP (not this slim branch).
    # This smoke uses an independently constructed same 62-source contract.
    samples={}
    for n in range(1,6):
        for x in range(1<<n):
            count=0;arr=[]
            for i in range(n):
                count+=(x>>i)&1;arr.append(int(count%3==0))
            samples[f"{n}:{x}"]=arr
    r=probe(samples)
    assert r['programs']==6144 and r['best'][0]==229 and r['perfect']==0
    print("RC14 bound PASS",r)
