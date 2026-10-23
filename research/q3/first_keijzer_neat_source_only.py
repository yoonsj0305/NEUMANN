"""First prospective independent original symbolic author programs from TWO DSO
benchmark named families, each untouched by NEUMANN Q3 studies so far.

Task names selected from PUBLISHED source metadata (one variable) WITHOUT
examining their true published author functions:
Keijzer 1,2,3,4,7,8,9 and Neat 1,2,3,4,6. Keijzer-6 omitted because
its author formula was opened by PR553. No Nguyen/Livermore test reuse.

Only runs in GitHub Actions SOURCE-generation job; TRUE functions exported
to separate grader-only artifact, never model/source job.
"""
import argparse,csv,hashlib,io,json,pathlib,urllib.request
import numpy as np
import sympy as sp
from livermore_original_source_eight import PUBLISHED_COMMIT,BLOB_SHA1,PATH,sha,save,author_formula
TARGETS=("Keijzer-1","Keijzer-2","Keijzer-3","Keijzer-4",
         "Keijzer-7","Keijzer-8","Keijzer-9",
         "Neat-1","Neat-2","Neat-3","Neat-4","Neat-6")
assert len(TARGETS)==12
X=sp.Symbol("x",real=True)
def prepare(src_out,gold_out):
    url=("https://raw.githubusercontent.com/dso-org/deep-symbolic-optimization/"
         +PUBLISHED_COMMIT+"/"+PATH)
    with urllib.request.urlopen(urllib.request.Request(url,
        headers={"User-Agent":"NEUMANN-Q3-FIRST-two-published-author-families/1"}),timeout=70) as f:
        raw=f.read()
    gitblob=hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
    assert gitblob==BLOB_SHA1
    records={r["name"]:r for r in csv.DictReader(io.StringIO(raw.decode("utf-8-sig")))
             if r["name"] in TARGETS}
    assert len(records)==12
    src=[];truth=[]
    for name in TARGETS:
        rec=records[name];assert rec["variables"]=="1"
        left,right,*_=json.loads(rec["train_spec"])["all"]["U"]
        lo,hi=float(left),float(right)
        assert np.isfinite([lo,hi]).all() and lo<hi
        expr=author_formula(rec["expression"])
        identity=sha(("Q3_DOUBLE_NEW_AUTHOR_20261023\x1f"+name).encode())[:24]
        rng=np.random.default_rng(int(identity[:12],16))
        x=rng.uniform(lo,hi,48)
        f=sp.lambdify(sp.Symbol("x",real=True),expr,"numpy")
        with np.errstate(all="ignore"):
            try:
                y=np.broadcast_to(np.asarray(f(x),dtype=float),x.shape)
                valid=np.all(np.isfinite(y)) and max(abs(y))<1e12
            except (ValueError,OverflowError,ZeroDivisionError,TypeError):
                valid=False;y=np.zeros_like(x)
        src.append({"id":identity,"collection":"DSO_"+name.split("-")[0],
                    "task_ID":name,
                    "x":x.tolist() if valid else [],
                    "y":y.tolist() if valid else [],
                    "observation_status":"VALID48" if valid else "UNKNOWN_INVALID_SOURCE",
                    "fixed_author_train_domain":[lo,hi]})
        truth.append({"id":identity,"collection":"DSO_"+name.split("-")[0],
             "task_ID":name,"original_expression":rec["expression"],
             "author_full_expression_sympy":str(expr),
             "source_domain_spec":rec["train_spec"]})
    src_sha=save(src_out,{"schema":"NEUMANN_Q3_FIRST_KEIJZER7_NEAT5_XY_ONLY.v1",
        "original_dataset_git_commit":PUBLISHED_COMMIT,
        "original_dataset_blob_sha1":BLOB_SHA1,
        "original_CSV_SHA256":sha(raw),
        "target_metadata_IDs_frozen_before_original_author_truth":list(TARGETS),
        "all_selected":12,"source_numeric_without_equations":src,
        "sampling_protocol":"48 fresh x-y noiseless uniform x inside published author train U range"})
    gold_sha=save(gold_out,{"schema":"NEUMANN_Q3_FIRST_KEIJZER7_NEAT5_GOLD_ONLY_GRADER.v1",
        "private_true_equations":truth})
    print("Q3_NEW_TWO_AUTHOR_FAMILIES_ORIGINAL12_PHYSICAL_SOURCE_TRUTH_SEPARATION",
       json.dumps({"source_SHA256":src_sha,"gold_SHA256":gold_sha,
                    "valid_numeric":sum(bool(r["x"]) for r in src),
                    "task_ids":list(TARGETS)},sort_keys=True),flush=True)
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--source",required=True);p.add_argument("--truth",required=True)
    a=p.parse_args();prepare(a.source,a.truth)
