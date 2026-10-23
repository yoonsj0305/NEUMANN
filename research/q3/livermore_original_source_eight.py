"""Original independent Livermore 1D symbolic-regression author source.

Frozen external published source:
https://github.com/dso-org/deep-symbolic-optimization/blob/8348d5b08d1eef6170fdbfd222a492ded990ea12/dso/dso/task/regression/benchmarks.csv
Git blob exactly 229c99495c819dc65f9f7ac304fd8460d6b46d3a.
Livermore original author problems preselected only by NAMES and variable
count before any equation text was inspected by the learner.

This program runs ONLY in source creation CI job. Original analytical
formulas are kept in a separate PRIVATE grade-only artifact.
"""
import argparse,csv,hashlib,io,json,pathlib,urllib.request
import numpy as np
import sympy as sp

PUBLISHED_COMMIT="8348d5b08d1eef6170fdbfd222a492ded990ea12"
BLOB_SHA1="229c99495c819dc65f9f7ac304fd8460d6b46d3a"
PATH="dso/dso/task/regression/benchmarks.csv"
TARGETS=("Livermore-13","Livermore-15","Livermore-16","Livermore-18",
         "Livermore-19","Livermore-20","Livermore-21","Livermore-22")
X=sp.Symbol("x",real=True)

def sha(raw):return hashlib.sha256(raw).hexdigest()
def save(path,doc):
    p=pathlib.Path(path);p.parent.mkdir(parents=True,exist_ok=True)
    raw=(json.dumps(doc,sort_keys=True,indent=2,allow_nan=False)+"\n").encode()
    p.write_bytes(raw)
    return sha(raw)

def author_formula(raw):
    # Source author's public expressions, never learner gold labels.
    local={"x1":X,"pi":sp.pi,"E":sp.E,"pow":sp.Pow,
           "sin":sp.sin,"cos":sp.cos,"tan":sp.tan,
           "sinh":sp.sinh,"cosh":sp.cosh,
           "log":sp.log,"ln":sp.log,"sqrt":sp.sqrt,
           "exp":sp.exp,"abs":sp.Abs,"tanh":sp.tanh}
    expr=sp.sympify(raw,locals=local,evaluate=True)
    assert not expr.free_symbols or expr.free_symbols.issubset({X})
    return expr

def prepare(source_path,truth_path):
    url=("https://raw.githubusercontent.com/dso-org/deep-symbolic-optimization/"
         +PUBLISHED_COMMIT+"/"+PATH)
    with urllib.request.urlopen(urllib.request.Request(
        url,headers={"User-Agent":"NEUMANN-Q3-PROSPECTIVE_LIVERMORE_AUTHOR8/1"}),timeout=60) as u:
        raw=u.read()
    git_blob_hash=hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
    assert git_blob_hash==BLOB_SHA1,(git_blob_hash,"CHANGED_PUBLISHED_DSO_ORIGINAL")
    table=list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig"))))
    records={r["name"]:r for r in table if r["name"] in TARGETS}
    assert len(records)==len(TARGETS)==8
    numeric=[];original=[]
    for name in TARGETS:
        row=records[name]
        assert row["variables"]=="1",name
        # Domain from original published benchmark, not inferred from formula.
        domain=json.loads(row["train_spec"])["all"]["U"]
        left,right=float(domain[0]),float(domain[1])
        assert np.isfinite([left,right]).all() and left<right
        expr=author_formula(row["expression"])
        identity=sha(("LIVERMORE_EXTERNAL_DSO_PUBLISHED_1D\x1f"+name).encode())[:24]
        rng=np.random.default_rng(int(identity[:12],16))
        xx=rng.uniform(left,right,size=48)
        fn=sp.lambdify(X,expr,"numpy")
        with np.errstate(all="ignore"):
            try:
                yy=np.broadcast_to(np.asarray(fn(xx),float),xx.shape)
                ok=bool(np.all(np.isfinite(yy)) and np.max(abs(yy))<1e12)
            except (ValueError,TypeError,OverflowError,ZeroDivisionError):
                yy=np.empty_like(xx);ok=False
        # Invalid source remains one registered original and UNKNOWN.
        numeric.append({"id":identity,"collection":"LivermoreExternalDSO",
            "task_ID":name,"x":xx.tolist() if ok else [],
            "y":yy.tolist() if ok else [],
            "sampling":"48 uniform source points from author's published train_spec",
            "source_availability":"VALID_48_NUMERIC" if ok else "UNKNOWN_INVALID_ORIGINAL_SOURCE"})
        original.append({"id":identity,"collection":"LivermoreExternalDSO",
            "task_ID":name,"original_expression":row["expression"],
            "original_expression_sympy":str(expr),"original_var":"x1",
            "original_train_spec":row["train_spec"]})
    src={"schema":"NEUMANN_Q3_LIVERMORE_EIGHT_FIRST_ORIGINAL_SOURCE_ONLY.v1",
         "author_source_git_commit":PUBLISHED_COMMIT,
         "published_source_git_blob_sha1":BLOB_SHA1,
         "published_original_CSV_SHA256":sha(raw),
         "new_source_family":"DSO_ORIGINAL_LIVERMORE_13_15_16_18_19_20_21_22",
         "source_numeric_without_equations":numeric,
         "all_selected":8}
    true={"schema":"NEUMANN_Q3_LIVERMORE_EIGHT_PRIVATE_PUBLISHED_AUTHOR_TRUTH.v1",
          "author_source_commit":PUBLISHED_COMMIT,
          "private_true_equations":original}
    signed_source=save(source_path,src);signed_truth=save(truth_path,true)
    print("Q3_LIVERMORE_EXTERNAL_AUTHORED_EIGHT_SOURCE_TRUTH_PHYSICALLY_SEPARATED",
          json.dumps({"names":list(TARGETS),"source_sha256":signed_source,
                      "truth_sha256":signed_truth,"corpus_sha256":sha(raw),
                      "valid_sources":sum(bool(r["x"]) for r in numeric)},sort_keys=True),flush=True)
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--source",required=True)
    p.add_argument("--truth",required=True)
    a=p.parse_args();prepare(a.source,a.truth)
