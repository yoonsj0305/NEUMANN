import test from 'node:test';
import assert from 'node:assert/strict';
import {propose as original} from '../experiments/q3_goal_conditioned_induction_p19.mjs';
import {propose,outputShape} from '../experiments/q3_shape_pruned_synthesis_p20.mjs';
const sample=(seed)=>Array.from({length:9},(_,r)=>Array.from({length:9},(_,c)=>(seed*17+r*11+c*31+r*c)%7<2?2:0));
const shiftDown=g=>[Array(g[0].length).fill(0),...g.slice(0,-1)];
const panels=(seed)=>{const g=Array.from({length:5},(_,r)=>Array.from({length:9},(_,c)=>(r*13+c*5+seed*17)%4===0?0:2));return [...g,Array(9).fill(4),...g.map((row,r)=>row.map((v,c)=>(v===0&&c%2===0)?0:2))];};
const overlap=g=>Array.from({length:5},(_,r)=>g[r].map((v,c)=>v===0&&g[r+6][c]===0?3:0));
function compare(train,testInputs){const old=original(train,testInputs),now=propose(train,testInputs);assert.deepEqual(now.prediction,old.prediction);assert.equal(now.trace.abstention,old.trace.abstention);assert.equal(now.trace.training_fit_count,old.trace.training_fit_count);return {old,new_:now};}
test('sound constant-shape inference for affine shifts',()=>{const g=sample(1);assert.deepEqual(outputShape(g,{type:'affine',crop:false,orientation:'rot90',dy:3,dx:-3,fill:'zero'}),[9,9]);});
test('strictly preserve zero-padded shift and fit count',()=>{const train=[1,2,3].map(s=>({input:sample(s),output:shiftDown(sample(s))}));const r=compare(train,[sample(4)]);assert.ok(r.new_.trace.actual_primitive_train_calls<=r.old.trace.train_sample_evaluations);});
test('strictly preserve separator-pair predicate and fitted program set',()=>{const train=[1,2,3].map(s=>({input:panels(s),output:overlap(panels(s))}));compare(train,[panels(4)]);});
test('shape-incompatible target must avoid all primitive calls while still abstaining',()=>{const train=[{input:sample(1),output:[[3]]}];const r=compare(train,[sample(2)]);assert.equal(r.new_.trace.actual_primitive_train_calls,0);assert.ok(r.new_.trace.shape_pruned_ast_count>1500);});
test('malformed input results in identical fail-closed behavior',()=>{compare([{input:[],output:[[1]]}],[sample(2)]);});
