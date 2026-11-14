#!/usr/bin/env python3
"""POST-FIRST independent Z3 grade of previously frozen eight source-only CVC5 variants.

This step MUST be run only after candidate hash sealed at GitHub commit
6299428672d9b2c078c8050c41de8e9ebeba1e3d. No source gold affects
candidate generation, but choosing a working configuration after grading
IS retrospectively oracle-informed: never present as a deployment policy.
"""
import hashlib,json,pathlib,subprocess,sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from sgi_first_classical_original import top_level_forms,get_cmd,sha256
from sgi_postfirst_original_heldout_z3 import get_candidate,body_of_constraint,verify_z3

PREV_FIRST='44047cd18e17e517cf0029329589411b997f53427d8fa3e152b044183d8524f0'
UN_GRADED='32601fd1b243b4fec4d3a94df48ad3253320839a1b31e10756eda00ff9e803f9'
PREV=pathlib.Path('previous_first')
FIRST=pathlib.Path('eight_ungraded')
ORIGINAL=pathlib.Path('upstream/data/benchmarks/hard/PRE_76_10/PRE_76_10.sl')
DEST=pathlib.Path('postfirst_grade')

def grade_one(rawtext,defs,constraints,prior):
    record={'name':prior['name'],'index':prior['index'],
            'flags':prior['flags'],'first_stdout_sha256':prior['stdout_sha256'],
            'candidate_before_grade':'CANDIDATE_UNGRADED',
            'whole_goal_z3_verifier':'SMT SAT/UNSAT verdict, not proof kernel'}
    try:
        assert sha256(rawtext.encode())==prior['stdout_sha256']
        candidate=get_candidate(rawtext,'f')
        record['candidate_sha256']=sha256(candidate.encode())
        base='\n'.join(defs+[candidate])+'\n'
        source_expr='(and '+' '.join(body_of_constraint(x) for x in constraints[:-1])+')'
        future_expr=body_of_constraint(constraints[-1])
        record['source_goal']=verify_z3(base+'(assert (not '+source_expr+'))\n')
        record['withheld_goal']=verify_z3(base+'(assert (not '+future_expr+'))\n')
        a,b=record['source_goal'],record['withheld_goal']
        if a['result']=='unsat' and b['result']=='unsat':
            record['grade']='POSTFIRST_CLASSICAL_PASSES_PREVIOUSLY_OPENED_HELDOUT'
        elif a['result']=='unsat' and b['result']=='sat':
            record['grade']='POSTFIRST_CLASSICAL_HELDOUT_FALSIFIED'
        else:
            record['grade']='HOLD_Z3_OR_SOURCE_VALIDATION_FAILED'
    except Exception as e:
        record['grade']='HOLD_VERIFIER_EXCEPTION'
        record['error']=type(e).__name__+': '+str(e)[:120]
    return record

def main():
    a=(FIRST/'POSTFIRST_EIGHT_CONFIGS_CANDIDATES_BEFORE_GRADE.json').read_bytes()
    b=(PREV/'FIRST_CVC5_SOURCE_ONLY.json').read_bytes()
    assert sha256(a)==UN_GRADED,'ungraDED output changed'
    assert sha256(b)==PREV_FIRST,'historical first changed'
    current=json.loads(a);past=json.loads(b)
    assert len(current['results'])==8
    assert len(past['rows'])==12 and past['rows'][5]['path'].endswith('PRE_76_10.sl')
    raw=ORIGINAL.read_bytes()
    assert sha256(raw)==current['original_sha256']==past['rows'][5]['source_original_sha256']
    forms=top_level_forms(raw.decode('utf-8'))
    cs=[f[2] for f in forms if get_cmd(f[2])=='constraint']
    assert len(cs)==10
    defs=[f[2] for f in forms if get_cmd(f[2]) in ('define-fun','declare-fun','declare-sort','declare-const')]
    assert current['withheld_original_constraint_sha256']==sha256(cs[-1].encode())
    assert current['source_constraint_count']==9
    out=[]
    for arm in current['results']:
        name=FIRST/f"{arm['index']:02d}.stdout"
        text=name.read_bytes().decode('utf-8',errors='replace')
        row=grade_one(text,defs,cs,arm)
        out.append(row)
        print('CLASSICAL_GRADE',row['index'],row['name'],row['grade'],row.get('source_goal',{}).get('result'),row.get('withheld_goal',{}).get('result'),flush=True)
    counts={}
    for row in out:counts[row['grade']]=counts.get(row['grade'],0)+1
    dest={
      'study':'POST_FIRST retrospective classical-only eight-arm reproduction on previously opened SyGuS-SGI task; no oracle-selectable deployable policy',
      'candidate_first_sha256':UN_GRADED,'original_12task_first_sha256':PREV_FIRST,
      'upstream':'Barnard-PL-Labs/sygus-sgi-1',
      'upstream_commit':'e7ae840e5546e9243ff94afb1a29064fc050011c',
      'input_rights':'Nine original source-only input/output constraints. Withheld tenth constraint absent from all eight solver runs.',
      'graded_all_arms':True,'arms':out,'counts':counts,
      'ownweight_models_trained':0,'Q1_Q7':'OPEN','G1':'HOLD','G2':'NOT_RUN'}
    DEST.mkdir(exist_ok=True)
    p=DEST/'EIGHT_ARM_POSTFIRST_INDEPENDENT_Z3_GRADE.json'
    p.write_text(json.dumps(dest,indent=2,sort_keys=True))
    print('COUNTS',json.dumps(counts,sort_keys=True))
    print('GRADE_SHA256',sha256(p.read_bytes()))
if __name__=='__main__':main()
