"""Proof that an actual frozen external author original quartic needed a nested graph.

No original target used by the inference model. This postgrade mathematical
certificate uses first frozen eighth32 numeric-only proposals, private author
formula, independent native full grade with SHA assertions.

For all real a,b,c,d, f(x)=a*(b*x+c)^k+d has degree<=k when k in{1,2,3};
a nonzero degree-4 polynomial cannot be expressed with this single
unnested polynomial atom, but the model produced SQUARE∘SQUARE with exact
original identity. No claim of neural-only discovery against full grammar.
"""
import argparse,hashlib,json,pathlib,sympy as sp
from erbench_original_eighth import allowed_formula,calc,SYM
X=sp.Symbol('x')
LOCKS={
  "truth":"23c01a0ebaa93e4d8cf15abc15175e8bd11e9c738afd0683cfe6b986aece209f",
  "pred":"686bd782adf50caca46b6b41613cc9dc4e38dcf63d7c7f768d346ca75d4375eb",
  "grade":"14ea0bafd328a60e42f894180f58e107393d769b98cae77f02118b0616c6cacc"}
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def main(a):
    for k,v in LOCKS.items():
        got=sha(getattr(a,k))
        assert got==v, (k,'FIRST_AUTHOR_RECEIPT_MUTATED',got,v)
    gold=json.loads(pathlib.Path(a.truth).read_text())['private_true_equations']
    pred=json.loads(pathlib.Path(a.pred).read_text())
    grade=json.loads(pathlib.Path(a.grade).read_text())
    cand=[p for p in gold if p['collection']=='OEIS' and p['task_ID']=='oeis_3490']
    assert len(cand)==1
    target=cand[0];node,var=allowed_formula(target['original_expression'])
    true=sp.cancel(calc(node,{var:X},SYM))
    assert sp.Poly(true,X,domain=sp.QQ).degree()==4
    assert sp.cancel(true-(10*X+5)**4)==0
    ident=target['id']
    learned={p['id']:p for p in pred['methods']['learned_graph_edit_512']['predictions']}
    certified=[]
    for item in learned[ident]['generated_macros']:
        expr=sp.sympify(item['named_lambda'].removeprefix('lambda x: '),locals={'x':X})
        if sp.cancel(expr-true)==0:
            certified.append(item)
    assert certified
    candidates=[x for x in certified
       if x['action_graph_edits'][2]=='SQUARE' and x['action_graph_edits'][3]=='SQUARE']
    assert candidates,('MODEL_DID_NOT_GENERATE_SQUARE_OF_SQUARE',certified)
    method_result={}
    for method,rows in grade['cases'].items():
        exact=next(q for q in rows if q['id']==ident)
        method_result[method]=exact['status']=='FULL_ORIGINAL_AUTHOR_SYMBOLICALLY_IDENTICAL'
    assert method_result['learned_graph_edit_512']
    assert method_result['complete_3920_classical']
    assert not method_result['nolearn_random_512'] and not method_result['nolearn_simple_first_512']
    # The previous human primitive polynomial grammar contains only
    # x, x², x³ (and affine transforms), not quartic. Any single
    # polynomial base degree<=3 with output affine rescaling stays <=3.
    proof={
       'schema':'NEUMANN_Q3_EIGHTH32_FROZEN_FIRST_PUBLIC_QUARTIC_DEGREE_LOWER_BOUND.v1',
       'immutable_FIRST_ARTIFACT_sha256':LOCKS,
       'author_original':'OEIS:oeis_3490',
       'original_task_id':ident,
       'original_true_full_expression':str(true),
       'original_is_exact_degree_four_over_Q':True,
       'named_source_created_square_of_square_lambdas':[x['named_lambda'] for x in candidates],
       'all_real_affine_inputs_outputs_polynomial_atoms_degree_le3_impossible':True,
       'elementary_degree_proof':'deg(A*(B*x+C)^k+D)<=k<=3, for all real A,B,C,D; author polynomial degree=4',
       'exact_source_author_identity_proved':True,
       'first_512_learning_vs_controls_original_full_semantic_grade':method_result,
       'neural_only_beyond_complete_3920':False,
       'math_literature_novelty':'NONE_STANDARD_POLYNOMIAL_DEGREE',
       'fresh_external_author_original_task':'PUBLIC_FIRST_EIGHTH_BEFORE_AUTHOR_TRUTH',
       'G1':'HOLD','global_Q3':'OPEN','Q4_total_cost_10x':'NOT_PROVED'}
    path=pathlib.Path(a.out);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(proof,sort_keys=True,indent=2)+'\n')
    print('Q3_EIGHTH_FIRST_ORIGINAL_QUARTIC_NESTED_SQUARE_COMPOSITION_STRICT_PROOF',
          json.dumps({'task':ident,'true':str(true),
              'learned_nested_exact':proof['named_source_created_square_of_square_lambdas'],
              'classical':method_result,
              'proof_SHA256':sha(path)},sort_keys=True),flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser()
    for k in LOCKS:p.add_argument('--'+k,required=True)
    p.add_argument('--out',required=True)
    main(p.parse_args())
