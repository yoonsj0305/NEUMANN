"""Independent-author Q3 DFA originals: SHA-frozen FIRST predictions.

External author: eendor/formal-languages at commit
9f43910c2d2facfcc3c8e1510dcfae7003caf638.
Files: examples/dfa_even_zeros.json and examples/dfa_div3.json.

The proposer has ONLY a line-oriented SOURCE membership-oracle subprocess,
never the external author's state labels or transition table. A separate
score invocation reads the exact pinned original JSON AFTER SHA freeze.
This is external-author scoped mathematical transfer, NOT unrelated
mathematical Q6 or arbitrary primitive/meta-language invention.
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


AUTHOR_SHA="9f43910c2d2facfcc3c8e1510dcfae7003caf638"
AUTHOR="eendor/formal-languages"
FILES=("dfa_even_zeros.json","dfa_div3.json")


def evaluate_original(dfa,word):
    state=dfa["start"]
    for symbol in word:
        state=dfa["transitions"][state][symbol]
    return int(state in dfa["accepting"])


def subprocess_oracle(args):
    # Only this separate SOURCE oracle process loads external author JSON.
    dfa=json.loads(Path(args.spec).read_text())
    for line in sys.stdin:
        word=json.loads(line)
        outcome=evaluate_original(dfa,word)
        sys.stdout.write(str(outcome)+"\n")
        sys.stdout.flush()


class OraclePipe:
    def __init__(self,spec):
        self.proc=subprocess.Popen(
            [sys.executable,str(Path(__file__).resolve()),
             "oracle","--spec",str(spec)],
            stdin=subprocess.PIPE,stdout=subprocess.PIPE,
            text=True,bufsize=1)
        self.queries=0

    def __call__(self,word):
        if self.proc.poll() is not None:
            raise ValueError("external SOURCE oracle unavailable")
        self.proc.stdin.write(json.dumps(word)+"\n")
        self.proc.stdin.flush()
        response=self.proc.stdout.readline()
        if not response or response.strip() not in ("0","1"):
            raise ValueError("invalid SOURCE binary label")
        self.queries+=1
        return int(response)

    def close(self):
        if self.proc.poll() is None:
            self.proc.stdin.close()
            self.proc.wait(timeout=10)


def targets():
    rng=random.Random(7312445)
    rows=[]
    for fname in FILES:
        for i in range(2048):
            size=rng.randrange(16,240)
            word="".join(rng.choice("01") for _ in range(size))
            rows.append((fname,word))
    return tuple(rows)


def propose(data_dir,out):
    rows=[]
    details={}
    engine=NeumannEngine(None,[],None)
    target_rows=targets()
    for fname in FILES:
        service=OraclePipe(data_dir/fname)
        try:
            # All verifier inputs longer than 2*N-1 source-probe horizon.
            check_words=("0110110111","1110110010","1001110101",
                         "01100110110")
            checks=tuple((w,service(w)) for w in check_words)
            invented=engine.invent_unknown_state_operator(
                service,max_states=4,alphabet=("0","1"),
                independent_source_checks=checks)
            if invented.status!="SOURCE_CERTIFIED_CONDITIONAL_DFA":
                raise ValueError(fname+" source discovery failed: "+invented.status)
            # No original raw DFA specs or output labels are opened here.
            for task_name,word in target_rows:
                if task_name==fname:
                    rows.append({
                        "task":fname,"word":word,
                        "prediction":invented.apply(word)})
            details[fname]={
                "invented_ast":repr(invented.program.ast),
                "inferred_states":invented.program.state_count,
                "source_queries":service.queries,
                "identification_source_queries":invented.queried_source_words,
                "independent_source_checks":len(checks),
                "max_states_assumption":4,
                "source_oracle_only":True}
        finally:
            service.close()
    package={
        "schema":"NEUMANN.Q3.UNKNOWN-STATE.EXTERNAL-AUTHOR.FIRST.v1",
        "external_author":AUTHOR,
        "external_commit":AUTHOR_SHA,
        "external_files":FILES,
        "proposer_read_raw_original_json":False,
        "source_oracle_service_isolated":True,
        "target_gold_used_in_learning":False,
        "human_provided_DFA_class_and_state_bound":True,
        "original_independent_author":True,
        "unrestricted_Q3_Q6_pass":False,
        "programs":details,"rows":rows}
    out.write_text(json.dumps(package,sort_keys=True,separators=(",",":"))+"\n")
    print("FIRST_EXTERNAL_FROZEN_SHA",
          hashlib.sha256(out.read_bytes()).hexdigest())
    print("SOURCE_DISCOVERY",json.dumps(details,sort_keys=True))


def score(data_dir,frozen,expected_sha,out):
    actual=hashlib.sha256(frozen.read_bytes()).hexdigest()
    if actual!=expected_sha:
        raise ValueError("external proposal modified after SHA freeze")
    package=json.loads(frozen.read_text())
    if (package["target_gold_used_in_learning"] or
            package["external_commit"]!=AUTHOR_SHA or
            tuple(package["external_files"])!=FILES):
        raise ValueError("provenance/freeze mismatch")
    external={name:json.loads((data_dir/name).read_text()) for name in FILES}
    results={}
    failures=[]
    for idx,entry in enumerate(package["rows"]):
        name=entry["task"]
        expected=evaluate_original(external[name],entry["word"])
        right=expected==entry["prediction"]
        counters=results.setdefault(name,{"total":0,"exact":0})
        counters["total"]+=1
        counters["exact"]+=int(right)
        if not right:failures.append({"row":idx,"task":name})
    report={
        "source_sha256":actual,
        "independent_author_original":AUTHOR,
        "pinned_commit":AUTHOR_SHA,
        "exact_by_external_task":results,
        "exact":sum(x["exact"] for x in results.values()),
        "total":sum(x["total"] for x in results.values()),
        "all_correct":not failures,
        "global_Q3_Q6_pass":False,
        "limits":"same regular-language semantics, bounded source DFA prior"}
    out.write_text(json.dumps({"report":report,"failures":failures},indent=2)+"\n")
    print("INDEPENDENT_AUTHOR_SCORE",json.dumps(report,sort_keys=True))
    if failures:
        raise AssertionError("source-first external task scored incorrectly")


if __name__=="__main__":
    ap=argparse.ArgumentParser()
    commands=ap.add_subparsers(dest="command",required=True)
    oracle=commands.add_parser("oracle")
    oracle.add_argument("--spec",type=Path,required=True)
    propose_p=commands.add_parser("propose")
    propose_p.add_argument("--data-dir",type=Path,required=True)
    propose_p.add_argument("--output",type=Path,required=True)
    scorer=commands.add_parser("score")
    scorer.add_argument("--data-dir",type=Path,required=True)
    scorer.add_argument("--predictions",type=Path,required=True)
    scorer.add_argument("--expected-sha",required=True)
    scorer.add_argument("--output",type=Path,required=True)
    args=ap.parse_args()
    if args.command=="oracle":subprocess_oracle(args)
    elif args.command=="propose":propose(args.data_dir,args.output)
    else:score(args.data_dir,args.predictions,args.expected_sha,args.output)
