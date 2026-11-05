import test from 'node:test';
import assert from 'node:assert/strict';
import {propose,interpret,candidatePrograms,p27ShapeCeilingFor3x3To9x9} from '../experiments/q3_p28_factorized_operator.mjs';
const factored=(x)=>{
  const h=x.length,w=x[0].length;
  return Array.from({length:h*h},(_,r)=>Array.from({length:w*w},(_,c)=>
    x[Math.floor(r/h)][Math.floor(c/w)]===0?0:x[r%h][c%w]));
};
test('enumerates 81 learned truth tables',()=>assert.equal(candidatePrograms().length,81));
test('no learned rule if target is structurally wrong',()=>{
 const a=[[1,0],[0,1]],bad=[[9]];
 assert.equal(propose([{input:a,output:bad}],[a]).prediction,null);
});
test('inferred executable semantics transfer across colors',()=>{
 const train=[[[0,2],[2,0]],[[3,0],[3,3]],[[0,4],[4,4]]].map(input=>({input,output:factored(input)}));
 const query=[[9,0],[0,9]];
 const p=propose(train,[query]);
 assert.equal(p.trace.abstention,null);
 assert.deepEqual(p.prediction,[factored(query)]);
 assert.deepEqual(interpret(p.trace.generated_AST,query),factored(query));
});
test('fail closed for unsupported oversized output',()=>{
 const input=Array.from({length:6},()=>[2]);
 assert.equal(propose([{input,output:[[2]]}],[input]).trace.abstention,'INVALID_OR_OUT_OF_SCOPE_INPUT');
});
test('wrong heldout cannot be queried as gold',()=>{
 const a=[[1,0],[1,1]],t=propose([{input:a,output:factored(a)}],[a]);
 assert.ok(!('test_gold' in t.trace));
});
test('malformed grid and no examples must abstain',()=>{
 assert.equal(propose([],[ [[1]] ]).prediction,null);
 assert.equal(propose([{input:[[1,-1]],output:[[1]]}],[[[1]]]).prediction,null);
});
test('heldout input with unseen multi-color does not blindly guess',()=>{
 const a=[[0,2],[2,2]],b=[[0,3],[3,3]],query=[[1,2],[0,3]];
 const p=propose([{input:a,output:factored(a)},{input:b,output:factored(b)}],[query]);
 assert.equal(p.prediction,null);
 assert.equal(p.trace.abstention,'AMBIGUOUS_TRAIN_CONSISTENT_OPERATORS');
});
test('shape ceiling: P2.7 two operations cannot generate 9x9 from 3x3',()=>assert.equal(p27ShapeCeilingFor3x3To9x9(),true));
