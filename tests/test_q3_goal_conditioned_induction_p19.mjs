import test from 'node:test';
import assert from 'node:assert/strict';
import {propose,primitive,execute,allASTs} from '../experiments/q3_goal_conditioned_induction_p19.mjs';
function shift(g){return [Array(g[0].length).fill(0),...g.slice(0,-1).map(r=>r.slice())];}
function splitBothZero(g){const n=(g.length-1)/2;return Array.from({length:n},(_,r)=>g[r].map((a,c)=>a===0&&g[n+1+r][c]===0?3:0));}
const maps=[
 [[0,1,0,0,2],[0,0,0,2,0],[0,0,1,0,0],[2,0,0,0,0],[0,0,0,1,0]],
 [[1,0,0,0,0],[2,1,0,0,2],[0,0,2,0,1],[1,0,0,0,0],[0,0,1,2,0]],
 [[0,2,1,0,0],[0,0,2,0,0],[1,0,0,1,0],[0,1,0,0,2],[2,0,0,0,1]],
 [[2,0,0,0,1],[0,0,1,2,0],[0,2,0,0,0],[0,0,0,1,1],[0,1,0,0,0]],
];
function split(g){const n=3,w=9;return [...g.slice(0,n).map(r=>r.slice()),Array(w).fill(4),...g.slice(n).map(r=>r.slice())];}
function sample(i){const g=Array.from({length:6},(_,r)=>Array.from({length:9},(_,c)=>(i*31+r*13+c*7+r*c*3)%5===0?0:(i+r*2+c*3)%4===0?2:1));return split(g);}

test('generate executable translation without preprogrammed shift-down opcode',()=>{
 const train=maps.slice(0,3).map(input=>({input,output:shift(input)}));
 const got=propose(train,[maps[3]]);
 assert.deepEqual(got.prediction,[shift(maps[3])]);
 assert.equal(got.trace.model_forwards,0);
});
test('synthesize split-panel predicate and color mapping from training demonstrations',()=>{
 const samples=[0,1,2,3,4].map(sample),train=samples.slice(0,4).map(input=>({input,output:splitBothZero(input)}));
 const got=propose(train,[samples[4]]);
 assert.deepEqual(got.prediction,[splitBothZero(samples[4])]);
});
test('candidate must be consistent with every training sample',()=>{
 const input=maps[0],bad=maps[1].map(r=>r.map(()=>9));
 const z=propose([{input,output:shift(input)},{input,output:bad}],[maps[2]]);
 assert.equal(z.prediction,null);
 assert.equal(z.trace.abstention,'NO_TRAIN_CONSISTENT_AST');
});
test('illegal grid fails closed',()=>{
 const z=propose([{input:[],output:[[0]]}],[maps[3]]);
 assert.equal(z.prediction,null);
 assert.equal(z.trace.abstention,'INVALID_INPUT');
});
test('candidate enumeration is deterministic and contains no task labels',()=>{
 const a=[...allASTs()],b=[...allASTs()];assert.deepEqual(a,b);
 assert.ok(a.length>1500);
 assert.ok(a.every(x=>!('task_id' in x)));
});
