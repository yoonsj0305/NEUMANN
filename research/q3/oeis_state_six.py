"""Source/gold isolation for six PUBLIC OEIS authored integer sequences.

OEIS A000045 (Fibonacci), A000032 (Lucas), A000129 (Pell),
A001045 (Jacobsthal), A000073 (Tribonacci), A000078 (Tetranacci).
The model does not import this file and sees ONLY first16 integer values.
Independent grader receives exact author coefficients, initial conditions,
and withheld n16..120 (105 more values). This is custom noiseless evaluation,
not an official or secret OEIS contest.
"""
import argparse,hashlib,json,pathlib

ORIGINALS=(
 ('A000045','Fibonacci',(0,1),(1,1)),
 ('A000032','Lucas',(2,1),(1,1)),
 ('A000129','Pell',(0,1),(2,1)),
 ('A001045','Jacobsthal',(0,1),(1,2)),
 ('A000073','Tribonacci',(0,0,1),(1,1,1)),
 ('A000078','Tetranacci',(0,0,0,1),(1,1,1,1)),
)
def generate(initial,weights,total):
    r=len(initial);out=list(initial)
    for n in range(r,total):
        out.append(sum(weights[j]*out[n-j-1] for j in range(r)))
    return out

def save(path,value):
    p=pathlib.Path(path);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(value,sort_keys=True,indent=2)+'\n')
    return hashlib.sha256(p.read_bytes()).hexdigest()

def prepare(source_path,truth_path):
    source=[];gold=[]
    for oeis,title,initial,weights in ORIGINALS:
        entire=generate(initial,weights,121)
        ident=hashlib.sha256(('NEUMANN-REAL-PUBLISHED-OEIS-RECURRENCE\x1f'+oeis).encode()).hexdigest()[:24]
        source.append({'id':ident,'task_ID':oeis,'source_kind':'FIRST_16_EXACT_INTEGERS',
                       'n':list(range(16)),
                       'a':[str(v) for v in entire[:16]],
                       'author_equation_withheld':True})
        gold.append({'id':ident,'task_ID':oeis,'author_name':title,
                     'author_initial':[str(v) for v in initial],
                     'author_coefficients':[str(v) for v in weights],
                     'author_recurrence':'a(n)=sum_{j=1}^r c_j*a(n-j), n>=r',
                     'public_oeis_url':'https://oeis.org/'+oeis,
                     'exact_heldout_n16_120':[{'n':i,'a':str(entire[i])} for i in range(16,121)]})
    a=save(source_path,{'schema':'NEUMANN_Q3_OEIS6_FIRST_SOURCE_VALUES_ONLY.v1',
      'source_numeric_without_recurrence':source,'source_first16_only':True,
      'same_author_source_family':'OEIS published exact recurrences from six independently named sequences',
      'source_registry_not_imported_by_model':True})
    b=save(truth_path,{'schema':'NEUMANN_Q3_OEIS6_PRIVATE_ORIGINAL_PUBLISHED_RECURRENCE.v1',
      'private_true_author_recurrences':gold,'full_exact_future_16_120':105})
    print('Q3_SIX_REAL_AUTHOR_OEIS_SEQUENCES_SOURCE_TRUE_RECURRENCE_PHYSICALLY_SPLIT',
       json.dumps({'source_SHA256':a,'truth_SHA256':b,'originals':6,
                   'source_exact_integer_values_per_original':16,
                   'withheld_exact_future_per_original':105}),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--truth',required=True)
    args=p.parse_args();prepare(args.source,args.truth)
