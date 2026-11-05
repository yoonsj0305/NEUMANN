import test from "node:test";
import assert from "node:assert/strict";
import {generate,independentScore} from "../experiments/q3_exact_semantic_quotient_p16.mjs";

const OPS=["id","flipH","flipV","rot180","transpose"];
function interpreter(g,op){
  if(op==="id")return g.map(r=>r.slice());
  if(op==="flipH")return g.map(r=>r.slice().reverse());
  if(op==="flipV")return g.slice().reverse().map(r=>r.slice());
  if(op==="rot180")return g.slice().reverse().map(r=>r.slice().reverse());
  if(op==="transpose")return g[0].map((_,c)=>g.map(r=>r[c]));
  return null;
}
test("same TRAIN behavior but distinct TEST behavior cannot be merged",()=>{
  const x=[[1,2,1],[3,4,3]];
  const z=[[1,0,2],[3,4,5]];
  const report=independentScore({train:[{input:x,output:x}],test:[{input:z,output:z}]},OPS,interpreter);
  assert.equal(report.semantic_behavior_preserved,true);
  assert.equal(report.P.abstention,"AMBIGUOUS_TEST_PREDICTIONS");
  assert.equal(report.Q.abstention,"AMBIGUOUS_TEST_PREDICTIONS");
  assert.equal(report.P_original_exact,false);
  assert.equal(report.Q_original_exact,false);
});
test("independent generated original-score parity across 16 deterministic seeds",()=>{
  for(let seed=1;seed<=16;seed++){
    const g=Array.from({length:3},(_,r)=>Array.from({length:4},(_,c)=>(r*13+c*17+seed*11)%9));
    const out=interpreter(g,OPS[seed%OPS.length]);
    const r=independentScore({train:[{input:g,output:out}],test:[{input:g,output:out}]},OPS,interpreter);
    assert.equal(r.semantic_behavior_preserved,true,"seed "+seed);
    assert.equal(r.P_original_exact,r.Q_original_exact,"seed "+seed);
  }
});
test("unsupported inputs abstain with explicit reasons",()=>{
  const r=generate([],[[1]],OPS,interpreter,"quotient");
  assert.equal(r.prediction,null);
  assert.equal(r.trace.abstention,"INVALID_INPUT");
});
test("same semantic equivalence class supports all deterministic suffixes",()=>{
  const inputs=[[[1,2,3],[4,5,6]],[[1,0,1],[0,1,0]]];
  for(const x of inputs){
    const id=interpreter(x,"id"),hh=interpreter(interpreter(x,"flipH"),"flipH");
    assert.deepEqual(id,hh);
    for(const suffix of OPS)assert.deepEqual(interpreter(id,suffix),interpreter(hh,suffix));
  }
});
test("pruned search is not allowed to lose syntactic-prefix capability",()=>{
  const g=[[1,0,0],[0,0,1]],expected=interpreter(g,"flipH");
  const report=independentScore({train:[{input:g,output:expected}],test:[{input:g,output:expected}]},OPS,interpreter);
  assert.equal(report.semantic_behavior_preserved,true);
  assert.equal(report.P_original_exact,report.Q_original_exact);
  assert.ok(report.Q.operator_evaluations<=report.P.operator_evaluations);
});
