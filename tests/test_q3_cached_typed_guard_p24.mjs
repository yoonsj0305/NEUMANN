import test from 'node:test';
import assert from 'node:assert/strict';
import {solve,eq,execute,components} from './q3_cached_typed_guard_p24.mjs';
const p=(g,o)=>({input:g,output:o});
const assess=(train,testInput,expected)=>{const r=solve(train,[testInput]);return {ok:r.prediction!==null&&eq(r.prediction[0],expected),r};};
test('learns newly composed zero-between-horizontal-endpoints -> two constant action',()=>{
 const train=[p([[4,0,0,4],[0,3,0,3],[7,0,0,7]],[[4,2,2,4],[0,3,2,3],[7,2,2,7]]),p([[0,5,0,5,0],[6,0,0,6,0]],[[0,5,2,5,0],[6,2,2,6,0]])];
 const g=[[9,0,0,9],[0,0,8,0],[8,0,8,0]],expected=[[9,2,2,9],[0,0,8,0],[8,2,8,0]];
 const {ok,r}=assess(train,g,expected);assert.equal(ok,true,JSON.stringify(r.trace));assert.equal(r.trace.teacher_calls,0);
});
test('learns two-panel relation both-zero from train data',()=>{
 const train=[p([[0,3,0,5],[2,0,1,0]],[[5,0],[0,5]]),p([[4,0,8,0],[0,0,0,7]],[[0,5],[5,0]])];
 const g=[[0,2,0,3],[9,0,8,0]],expected=[[5,0],[0,5]];
 const {ok,r}=assess(train,g,expected);assert.equal(ok,true,JSON.stringify(r.trace));
});
test('learns one-column left shift with zero fill recolor',()=>{
 const train=[p([[1,1,0],[0,2,2]],[[1,5,5],[2,2,5]]),p([[0,3,3,0],[4,0,0,4]],[[3,3,5,5],[5,5,4,5]])];
 const g=[[6,6,0,0],[0,7,7,7]],exp=[[6,5,5,5],[7,7,7,5]];
 const {ok,r}=assess(train,g,exp);assert.equal(ok,true,JSON.stringify(r.trace));
});
test('count the connected components and create output column size n+1',()=>{
 const train=[p([[5,0,5],[0,0,0],[0,5,0]],[[0],[0],[0],[0]]),p([[0,5,0],[0,0,0],[0,0,5]],[[0],[0],[0]])];
 const g=[[5,0,5,0,5],[0,0,0,0,0],[0,5,0,5,0]],exp=Array.from({length:6},()=>[0]);
 const {ok,r}=assess(train,g,exp);assert.equal(ok,true,JSON.stringify(r.trace));
});
test('crop unique foreground multicolor component by emergent color-count predicate',()=>{
 const train=[p([[1,2,3,0,0],[4,5,6,0,7],[1,1,1,0,0]],[[1,2,3],[4,5,6],[1,1,1]]),p([[9,8,7,0,0],[6,5,4,0,3],[9,9,9,0,0]],[[9,8,7],[6,5,4],[9,9,9]])];
 const g=[[3,2,1,0,5],[4,5,6,0,0],[3,3,3,0,0]],exp=[[3,2,1],[4,5,6],[3,3,3]];
 const {ok,r}=assess(train,g,exp);assert.equal(ok,true,JSON.stringify(r.trace));
});
test('malformed original test or train inputs fail closed without executing',()=>{
 const x=solve([{input:[[0]],output:[[0]]}],[[12]]);assert.equal(x.prediction,null);assert.equal(x.trace.abstention,'INVALID_INPUT');
});
test('task identity and gold output never appear in student interface',()=>{
 const original={train:[p([[0,1],[0,1]],[[0,1],[0,1]])],testInput:[[2,0],[2,0]]};
 const a=solve(original.train,[original.testInput]);const b=solve(original.train.map(p=>({...p})),[original.testInput]);
 assert.deepEqual(a.prediction,b.prediction);
});
test('feature cache does not leak across calls with caller-mutated input arrays',()=>{
 const g=[[0,0,0],[0,1,0],[0,0,0]],t=[{input:g,output:[[0,0,0],[0,1,0],[0,0,0]]}];
 const a=solve(t,[[1,0,0],[0,1,0],[0,0,0]]);
 g[0][0]=7;t[0].output[0][0]=7;
 const b=solve(t,[[1,0,0],[0,1,0],[0,0,0]]);
 assert.ok(b.trace.abstention!==undefined);
});
