"""Q3 FIRST external-original generalization across nonregular language semantics.

External source authorship fixed at eendor/formal-languages:
9f43910c2d2facfcc3c8e1510dcfae7003caf638.
Original independent author CFG and PDA rules are hidden in a separate SOURCE
membership-oracle process. The proposer only sees membership(WORD)->0/1.

No source CFG productions, PDA stack operations or test gold are supplied to
the learned program. Targets are frozen and SHA hashed before score() opens
the original external author model. Both originals are still formal languages:
this is scoped representation-class transfer, NOT unrestricted Q6.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import random
import subprocess
import sys
from pathlib import Path

from neumann1 import NeumannEngine

AUTHOR="eendor/formal-languages"
SHA="9f43910c2d2facfcc3c8e1510dcfae7003caf638"
EXTERNAL=(
    ("cfg_anbn.json",("a","b")),
    ("pda_balanced.json",("(",")")),
)


def load_author_object(author_root,spec):
    sys.path.insert(0,str((author_root/"src").resolve()))
    from automata import io
    return io.load(spec)


def oracle_worker(args):
    machine=load_author_object(args.author_root,args.spec)
    for line in sys.stdin:
        word=json.loads(line)
        result=int(machine.accepts(word))
        sys.stdout.write(str(result)+"\n")
        sys.stdout.flush()


class IsolatedOracle:
    def __init__(self,author_root,spec):
        self.proc=subprocess.Popen([
            sys.executable,str(Path(__file__).resolve()),
            "oracle","--author-root",str(author_root),
            "--spec",str(spec)],
            stdin=subprocess.PIPE,stdout=subprocess.PIPE,
            text=True,bufsize=1)
        self.calls=0
    def __call__(self,word):
        if self.proc.poll() is not None:
            raise RuntimeError("independent SOURCE service unavailable")
        self.proc.stdin.write(json.dumps(word)+"\n")
        self.proc.stdin.flush()
        raw=self.proc.stdout.readline()
        if raw.strip() not in ("0","1"):
            raise RuntimeError("independent SOURCE oracle invalid reply")
        self.calls+=1
        return int(raw)
    def close(self):
        if self.proc.poll() is None:
            self.proc.stdin.close()
            self.proc.wait(timeout=20)


def frozen_target_words(alphabet,seed):
    a,b=alphabet
    rng=random.Random(seed)
    candidates=set()
    for n in range(9,45):
        candidates.update((
            a*n+b*n,b*n+a*n,
            (a+b)*n,(b+a)*n,
            a*n+b*n+a*n+b*n))
    while len(candidates)<1024:
        n=rng.randrange(18,89)
        candidates.add("".join(rng.choice(alphabet) for _ in range(n)))
    return tuple(sorted(candidates,key=lambda w:(len(w),w)))[:1024]


def propose(author_root,out):
    engine=NeumannEngine(None,[],None)
    programs={}
    predictions=[]
    for i,(filename,alphabet) in enumerate(EXTERNAL):
        source=IsolatedOracle(
            author_root,author_root/"examples"/filename)
        try:
            found=engine.invent_representation_class_adaptive(
                source,alphabet=alphabet,max_dfa_states=4,
                max_source_length=8)
            if found.program is None:
                raise ValueError(
                    filename+" source invention ABSTAINED: "+found.status+
                    " DFA="+found.finite_state_status+
                    " counter="+found.counter_status)
            if found.representation_class!="unbounded_counter":
                raise ValueError(
                    "source class diagnostic did not falsify DFA: "+
                    found.representation_class)
            programs[filename]={
                "new_representation_class":found.representation_class,
                "source_oracle_calls":source.calls,
                "finite_state_attempt":found.finite_state_status,
                "counter_attempt":found.counter_status,
                "source_generated_ast":repr(found.program.ast),
                "source_train_examples":found.program.source_examples,
                "independent_source_verifiers":found.program.source_verifiers,
                "source_candidates_checked":found.program.candidates_checked}
            for word in frozen_target_words(alphabet,909211+i):
                predictions.append({
                    "task":filename,"word":word,
                    "prediction":found.apply(word)})
        finally:
            source.close()
    body={
        "schema":"NEUMANN.Q3.UNBOUNDED-STATE.EXTERNAL-ORIGINAL-FIRST.v1",
        "author":AUTHOR,"author_revision":SHA,
        "author_originals":tuple(x[0] for x in EXTERNAL),
        "source_worker_isolated":True,
        "target_gold_read_by_proposer":False,
        "hidden_CFG_PDA_rules_passed_to_learner":False,
        "source_length_max":14,
        "target_length_min":18,
        "global_Q3_Q6_pass":False,
        "programs":programs,"rows":predictions}
    out.write_text(json.dumps(body,sort_keys=True,separators=(",",":"))+"\n")
    print("Q3_UNBOUNDED_FIRST_SHA",hashlib.sha256(out.read_bytes()).hexdigest())
    print("SOURCE_INVENTED_PROGRAMS",json.dumps(programs,sort_keys=True))


def score(author_root,frozen,expected_sha,out):
    sha=hashlib.sha256(frozen.read_bytes()).hexdigest()
    if sha!=expected_sha:
        raise ValueError("original first frozen SHA changed")
    proposed=json.loads(frozen.read_text())
    if proposed["author_revision"]!=SHA or proposed["target_gold_read_by_proposer"]:
        raise ValueError("source/original provenance failure")
    models={
        name:load_author_object(author_root,author_root/"examples"/name)
        for name,_ in EXTERNAL}
    result={}
    failures=[]
    for i,row in enumerate(proposed["rows"]):
        y=int(models[row["task"]].accepts(row["word"]))
        equal=int(row["prediction"]==y)
        entry=result.setdefault(row["task"],{"n":0,"exact":0,
                                              "positive":0,"negative":0})
        entry["n"]+=1
        entry["exact"]+=equal
        entry["positive"]+=y
        entry["negative"]+=1-y
        if not equal:failures.append({"index":i,"task":row["task"]})
    summary={
        "author":AUTHOR,"revision":SHA,"sha256":sha,
        "original_exact":result,
        "total":sum(v["n"] for v in result.values()),
        "correct":sum(v["exact"] for v in result.values()),
        "all_correct":not failures,
        "independent_author_original":True,
        "nonregular_mathematical_semantics":True,
        "human_supplied_counter_metalanguage":True,
        "global_Q3_Q6_pass":False}
    out.write_text(json.dumps(
        {"summary":summary,"failures":failures},indent=2)+"\n")
    print("Q3_EXTERNAL_NONREGULAR_SCORE",json.dumps(summary,sort_keys=True))
    if failures:
        raise AssertionError("source-frozen external originals not all correct")


if __name__=="__main__":
    p=argparse.ArgumentParser()
    commands=p.add_subparsers(dest="command",required=True)
    oracle=commands.add_parser("oracle")
    oracle.add_argument("--author-root",type=Path,required=True)
    oracle.add_argument("--spec",type=Path,required=True)
    propose_p=commands.add_parser("propose")
    propose_p.add_argument("--author-root",type=Path,required=True)
    propose_p.add_argument("--output",type=Path,required=True)
    score_p=commands.add_parser("score")
    score_p.add_argument("--author-root",type=Path,required=True)
    score_p.add_argument("--predictions",type=Path,required=True)
    score_p.add_argument("--sha",required=True)
    score_p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    if args.command=="oracle":oracle_worker(args)
    elif args.command=="propose":propose(args.author_root,args.output)
    else:score(args.author_root,args.predictions,args.sha,args.output)
