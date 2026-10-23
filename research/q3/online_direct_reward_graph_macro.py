"""Direct online counterexample/reward learned graph-edits, NO classical teacher labels.

Previous PR542 trained a neural graph generator using all 486 exhaustive
classically FOUND winning target action-sequences. This new online model only
samples from its OWN evolving action policy, receives binary exact verifier
feedback on each sampled program and learns from ITS OWN rewarded rollouts.
The researcher does not show target macro syntax or teacher winning actions.

Allowed primitives/tree shape and source-to-target normalization remain fixed
HUMAN-provided; this is a scoped program self-discovery mechanism, not full
novel semantic primitive or a first-blind external family.
"""
import argparse,collections,hashlib,json,pathlib,time
import numpy as np
from sklearn.neural_network import MLPClassifier
from reward_learned_graph_edits_2adic_macro import (
    B,T,ACTIONS,BINARY,SIDES,TERMINALS,VOCAB,IDX,TEST,TRAIN,
    features,program,exact_oracle,exact_generic_identity,write,sha,original_grade)
OPTIONS=(BINARY,("LEFT","RIGHT"),BINARY,TERMINALS,TERMINALS,TERMINALS)
SEED=31415
ROLL_OUTS=1500

def reward_only_training(output):
    start=time.process_time()
    rng=np.random.default_rng(SEED)
    seen=collections.Counter()
    reward_events=[]
    rejected=0
    first_reward_step=None
    for episode in range(ROLL_OUTS):
        beta=TRAIN[episode%len(TRAIN)]
        actions=[]
        for i,choices in enumerate(OPTIONS):
            weights=np.asarray([0.2+seen[i,tuple(actions),action] for action in choices],float)
            if rng.random()<.25:weights=np.ones(len(choices),float)
            weights/=weights.sum()
            actions.append(str(rng.choice(choices,p=weights)))
        sym=program(actions)
        verified=bool(exact_oracle(sym,beta))
        if verified:
            if first_reward_step is None:first_reward_step=episode+1
            for i,action in enumerate(actions):
                seen[i,tuple(actions[:i]),action]+=1
            reward_events.append({"source_b":beta,"actions":actions,
              "macro_expr":str(sym),"episode":episode+1,
              "source_exact_identity":True})
        else:rejected+=1
    assert reward_events and first_reward_step is not None,"ONLINE_POLICY_NEVER_DISCOVERED_A_MACRO"
    # The autoregressive MLP is trained EXCLUSIVELY on the agent's OWN sampled
    # successful graph actions, not a classical teacher trace/data set.
    xx=[];yy=[]
    for event in reward_events:
        actions=event["actions"]
        for i,tok in enumerate(actions):
            xx.append(features(event["source_b"],i,actions[:i]))
            yy.append(tok)
    model=MLPClassifier(hidden_layer_sizes=(32,16),random_state=19,
              max_iter=1000,learning_rate_init=0.03,alpha=0.001)
    ttrain=time.process_time()
    model.fit(np.asarray(xx),np.asarray(yy))
    model_cpu=time.process_time()-ttrain
    def decode(beta):
        trace=[]
        for i in range(6):
            trace.append(str(model.predict([features(beta,i,trace)])[0]))
        return trace
    tests=[]
    for beta in TEST:
        actions=decode(beta)
        macro=program(actions)
        tests.append({"heldout_transition_b":beta,
             "autoregressive_graph_edit_actions":actions,
             "named_lambda_program":"lambda t,b: "+str(macro),
             "source_exact_transition_proof":bool(exact_oracle(macro,beta)),
             "all_symbolic_b_semiconjugacy_identity":bool(exact_generic_identity(macro))})
    cpu=time.process_time()-start
    reward_count=len(reward_events)
    history_sha=sha(json.dumps(reward_events,sort_keys=True).encode())
    out={"schema":"NEUMANN_Q3_ONLINE_OWN_REWARD_MACRO_GRAPH_CREATION.v1",
        "source_training_coefficients_not_given_macro_solution":list(TRAIN),
        "heldout_coefficients":list(TEST),
        "initial_policy_action_samples":"uniform 486-action typed grammar; adaptive conditional prefix-count policy with 25percent uniform exploration",
        "teacher_labels_or_verified_software_targets":"NONE",
        "only_model_own_rewarded_rollouts_used_to_train_neural_decoding":True,
        "source_math_feedback":"exact symbolic oracle g(2t+b t²)=g(t)² with required b,t dependence, nonconstant",
        "no_original_author_SMT_source_used_in_learning":True,
        "random_seed":SEED,"random_policy_proposals":ROLL_OUTS,
        "first_nontrivial_reward_episode":first_reward_step,
        "exact_positive_reward_count":reward_count,
        "exact_negative_reward_count":rejected,
        "online_positive_action_sequences_SHA256":history_sha,
        "distinct_discovered_program_graphs":len(set(tuple(e["actions"]) for e in reward_events)),
        "learned_model_training_CPU_s":model_cpu,
        "online_policy_verifier_and_train_total_CPU_s":cpu,
        "positive_rollout_examples":len(xx),
        "weights_SHA256":sha(json.dumps([x.tolist() for x in model.coefs_],sort_keys=True).encode()),
        "heldout_predicted_named_macro_and_source_proof":tests,
        "original_four_previously_OPENED_dev_only":True,
        "fully_new_atomic_semantic_primitive_invented":"NOT_PROVED",
        "classical_full_486_program_grammar_solver_exists":True,
        "neural_only_original_solution_expected":0,
        "G1_global":"HOLD","Q4_total_10x":"NOT_PROVED"}
    ident=write(output,out)
    print("Q3_ONLINE_DIRECT_REWARD_SELF_DISCOVERED_LAMBDA_BEFORE_ORIGINALS",
          json.dumps({"sha256":ident,
              "reward_only_rollouts":ROLL_OUTS,
              "positive_reward":reward_count,
              "first_positive_at":first_reward_step,
              "distinct_graphs":out["distinct_discovered_program_graphs"],
              "learned_model_CPU_s":model_cpu,
              "total_train_incl_reward_CPU_s":cpu,
              "heldout_exact":[x["source_exact_transition_proof"] for x in tests],
              "all_symbolic_b":[x["all_symbolic_b_semiconjugacy_identity"] for x in tests]},sort_keys=True),flush=True)
    assert all(z["source_exact_transition_proof"] and z["all_symbolic_b_semiconjugacy_identity"] for z in tests)
    return out
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--mode",choices=("train","original_grade"),required=True)
    p.add_argument("--out",required=True)
    p.add_argument("--pred")
    p.add_argument("--source-root")
    a=p.parse_args()
    if a.mode=="train":reward_only_training(a.out)
    else:original_grade(a.pred,a.out,a.source_root)
