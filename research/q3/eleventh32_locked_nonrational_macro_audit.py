"""First immutable eleventh32 author source exact derived EXP-LOG macro audit.

Ground claims in FIRST three-job CI artifacts only. SHA lock ORIGINAL source,
gold, neural predicted new macro before author grade, and independent full
analytic author grade. Distinguish graph compositional semantics from the
human-known POWER primitive, and source-only vs complete original proof.
"""
import argparse,collections,hashlib,json,pathlib
import sympy as sp
from erbench_original_eleventh import allowed_formula,calc,SYM
X=sp.Symbol('x')
LOCKS={
 'source':'8d9b2a510a905edd3800af734d06c8f63c8f59dbad1f526434dcce79b038e43c',
 'truth':'a6becf118284cfb10a84f520ccd0b055ce34af167dfb330b2a117557275b841e',
 'pred':'428c8a0f245d22577970bd26995f431088ccba6a4e9ef5b7065fbc89a3bf94fc',
 'grade':'0c05dce89897cf0046693f556f22b5b0bf1e74b27283c6daf9783df9dbe1be8c'}
def sha(path):return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()
def inspect(a):
    for k in LOCKS:
        got=sha(getattr(a,k));assert got==LOCKS[k],(k,'FIRST_RECEIPT_SHA_MUTATED',got)
    t=json.loads(pathlib.Path(a.truth).read_text())['private_true_equations']
    p=json.loads(pathlib.Path(a.pred).read_text());g=json.loads(pathlib.Path(a.grade).read_text())
    assert len(t)==32
    meta={r['id']:r for r in t}
    names={k:{r['id']:r for r in arr} for k,arr in g['cases'].items()}
    a_learned=names['D_learned_derived_power_top2']
    a_safe=names['C_safe_add_rational']
    a_full=names['A_full_same_actions']
    source={r['id']:r for r in json.loads(pathlib.Path(a.source).read_text())['source_numeric_without_equations']}
    derived=[];allrows=[];count=collections.Counter()
    for ident,row in a_learned.items():
        truth=meta[ident]
        exact=row['certified_named_macros']
        first_safe=a_safe[ident]['status']=='WHOLE_ORIGINAL_AUTHOR_PROVED'
        first_full=a_full[ident]['status']=='WHOLE_ORIGINAL_AUTHOR_PROVED'
        if exact:count['learned_exact']+=1
        good=[]
        for cand in exact:
            certs=cand.get('derived_EXPLOG_macros',[])
            if not certs:continue
            tree,var=allowed_formula(truth['original_expression'])
            fn=calc(tree,{var:X},SYM)
            expr=sp.sympify(cand['defined_operator_AST'],locals={'x':X})
            assert sp.simplify(fn-expr)==0,'PREVIOUS_PROOF_MISMATCH'
            for k in certs:
                b=sp.Integer(k['base']);sl=sp.Integer(k['slope'])
                assert b>1 and sl!=0
                lowered=sp.exp(sl*X*sp.log(b))
                canonical=sp.Pow(b,sl*X)
                assert sp.powdenest(lowered,force=True)==canonical
                assert k['positive_base_certified_compiled_graph']==str(canonical)
            nonrat=not sp.cancel(sp.together(fn)).is_rational_function(X)
            # Analytic proof outside every fixed-degree rational function:
            # a rational R(x)=P(x)/Q(x) grows at most polynomially as
            # x -> +infinity (outside finite poles). For these positive
            # exponential whole author functions the quotient by x**n
            # diverges for EVERY symbolic nonnegative integer n.
            symbolic_degree=sp.Symbol("n",integer=True,nonnegative=True)
            infinite_vs_any_power=sp.limit(fn/X**symbolic_degree,X,sp.oo)
            assert nonrat and infinite_vs_any_power==sp.oo,(
                "STRONG_NONRATIONAL_GROWTH_NOT_PROVED",truth["task_ID"],infinite_vs_any_power)
            good.append({'original_public_name':truth['collection']+':'+truth['task_ID'],
                'original_author_expression':truth['original_expression'],
                'source_generated_lambda':cand['named_lambda'],
                'induced_composite_exp_log_macros':certs,
                'strict_whole_original_symbolic_identity':True,
                'original_nonrational_function':nonrat,
                'old_safe_classical_original_SOLVED':first_safe,
                'all_same_rights_classical_original_SOLVED':first_full})
        if good:
            count['exact_derived_exp_log_cases']+=1
            if not first_safe:count['new_originals_beyond_safe']+=1
            derived.extend(good)
        allrows.append({'id':ident,'collection':truth['collection'],'task_ID':truth['task_ID'],
                        'learned_correct':bool(exact),'has_verified_derived_power':bool(good),
                        'same_source_only_numeric_ready':bool(source[ident].get('x')),
                        'safe_correct':first_safe,'full_correct':first_full})
    assert count['learned_exact']==9
    assert count['exact_derived_exp_log_cases']==2
    assert count['new_originals_beyond_safe']==2
    stats=p['training'];methods=p['methods']
    knowntrain=stats['source_reward_training_CPU_s']+stats['actual_neural_structural_MLP_CPU_s']
    result={'schema':'NEUMANN_Q3_FIRST_ELEVENTH_REAL_AUTHOR_NONRATIONAL_EXPLOG_COMPOSITION_CERTIFIED.v1',
        'immutable_ALL_FIRST_ORIGINAL_SOURCES_SHA':LOCKS,
        'exact_original_new_named_derived_exp_log_operators':derived,
        'all32_first_original_results':allrows,
        'counts':dict(count),
        'source_only_learner_train_and_eval_CPU_s':knowntrain+methods['D_learned_derived_power_top2']['inference_CPU_s'],
        'safe_old_nolearn_inference_CPU_s':methods['C_safe_add_rational']['inference_CPU_s'],
        'full_all_same_action_classical_inference_CPU_s':methods['A_full_same_actions']['inference_CPU_s'],
        'nonrational_induction_is_human_EXP_LOG_composition_with_source_inferred_base_k':True,
        'new_semantically_atomic_op_learned':'NO',
        'first_private_source_true_author_IS_public_development_benchmark':True,
        'learned_exclusive_vs_full_all_same_actions':0,
        'G1':'HOLD','Q3_global':'OPEN','Q4_allin_10x':'NOT_PROVED'}
    dest=pathlib.Path(a.out);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print('Q3_ELEVENTH_FIRST_NONRATIONAL_AUTHORED_OPERATOR_TWO_NATIVE_FULL_PROOFS',
       json.dumps({'derived':derived,'counts':dict(count),
                   'learned_CPU':result['source_only_learner_train_and_eval_CPU_s'],
                   'classical_ALL_CPU':result['full_all_same_action_classical_inference_CPU_s'],
                   'sha256':sha(dest)},sort_keys=True),flush=True)
if __name__=='__main__':
    parser=argparse.ArgumentParser()
    for k in LOCKS:parser.add_argument('--'+k,required=True)
    parser.add_argument('--out',required=True)
    inspect(parser.parse_args())
