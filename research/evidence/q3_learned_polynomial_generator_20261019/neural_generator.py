"""Q3 CPU learned ten-term polynomial generator. POSTHOC development only.
The neural network generates a coefficient vector, not a template-class index.
No claim of inventing a primitive absent from the predeclared degree-2 vocabulary.
"""
from __future__ import annotations
import itertools, hashlib, json, time, warnings
import numpy as np
from sklearn.exceptions import ConvergenceWarning
from sklearn.neural_network import MLPRegressor

SEED=29
MONOMIALS=((),(0,),(1,),(2,),(0,0),(1,1),(2,2),(0,1),(0,2),(1,2))

def source_example(alpha,beta,roles):
    n,acc,cnt=roles
    a=np.zeros((3,3));b=np.zeros(3)
    a[acc,cnt]=alpha
    b[acc]=beta;b[cnt]=1
    features=np.r_[a.flatten(),b]
    coeff=np.zeros(10)
    coeff[0]=2*beta
    coeff[MONOMIALS.index((acc,))]=2
    coeff[MONOMIALS.index((cnt,cnt))]=-alpha
    coeff[MONOMIALS.index((cnt,))]=alpha-2*beta
    return features,coeff

def frozen_rows():
    train=[];test=[];omitted=[]
    for a,b in itertools.product(range(-5,6),repeat=2):
        for roles in itertools.permutations(range(3)):
            feat,coeff=source_example(a,b,roles)
            row=(feat,coeff,a,b,roles)
            if (a,b)==(1,0):omitted.append(row)
            elif (a*31+b*43+17)%11 in (0,1):test.append(row)
            else:train.append(row)
    assert (len(train),len(test),len(omitted))==(588,132,6)
    return train,test,omitted

def train_once():
    train,test,omitted=frozen_rows()
    X=np.array([x[0] for x in train]);Y=np.array([x[1] for x in train])
    Z=np.array([x[0] for x in test]);G=np.array([x[1] for x in test])
    t=time.perf_counter_ns()
    model=MLPRegressor(hidden_layer_sizes=(96,96),activation="tanh",
      solver="lbfgs",max_iter=850,random_state=SEED,alpha=1e-5)
    with warnings.catch_warnings(record=True) as ws:
        warnings.simplefilter("always",ConvergenceWarning)
        model.fit(X,Y)
    elapsed=(time.perf_counter_ns()-t)/1e6
    rounded=np.rint(model.predict(Z))
    successes=int(np.all(rounded==G,axis=1).sum())
    omitted_check={str(x[4]):bool(np.array_equal(
       np.rint(model.predict(x[0][None,:])[0]),x[1])) for x in omitted}
    all_weights=np.concatenate([x.ravel() for x in model.coefs_+model.intercepts_])
    report={
      "posthoc":True,"actual_cpu_trained_model":True,
      "model":"12-96-96-10 tanh source-conditioned polynomial coefficient generator",
      "learnable_parameters":len(all_weights),
      "weights_sha256":hashlib.sha256(all_weights.astype("float64").tobytes()).hexdigest(),
      "train_examples":len(train),"holdout_examples":len(test),
      "holdout_exact_coefficient_vector":successes,
      "all_a1_b0_roles_excluded_from_training":True,
      "omitted_a1_b0_source_permutation_results":omitted_check,
      "train_wall_ms":round(elapsed,3),
      "optimizer_convergence_warning":any(issubclass(w.category,ConvergenceWarning) for w in ws),
      "supervision":"Synthetic training examples carry complete ten-coefficient gold vectors",
      "predeclared_grammar":"all polynomial monomials degree <=2 in three Int state variables",
      "global_q3":"OPEN"}
    return model,report

def polynomial(coeff,vars,z3):
    terms=[]
    for c,monomial in zip(coeff,MONOMIALS):
        if int(c)==0:continue
        term=z3.IntVal(int(c))
        for k in monomial:term*=vars[k]
        terms.append(term)
    return z3.Sum(terms) if terms else z3.IntVal(0)
