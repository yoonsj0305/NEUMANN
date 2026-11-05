import test from 'node:test';
import assert from 'node:assert/strict';
import {objects,synthesize,interpret,CONTRACT} from '../experiments/q3_p30_object_rewrite_language.mjs';

const eq=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
function ringScene(h,w,spec){
 const g=Array.from({length:h},()=>Array(w).fill(0));
 for(const [r,c,color] of spec)for(let dy=0;dy<3;dy++)for(let dx=0;dx<3;dx++)
  if(dy!==1||dx!==1)g[r+dy][c+dx]=color;
 return g;
}
function fillHoles(g,spec){
 const out=g.map(r=>r.slice());
 for(const [r,c]of spec)out[r+1][c+1]=9;
 return out;
}
test('higher-order learned operation fills holes in ALL objects, regardless of count, color or position',()=>{
 const specs1=[[0,0,3],[0,5,4]],specs2=[[1,0,6],[1,6,7],[4,3,8]],specsTest=[[0,0,4],[0,4,5],[4,0,8],[4,4,2]];
 const train=[
  {input:ringScene(7,9,specs1),output:fillHoles(ringScene(7,9,specs1),specs1)},
  {input:ringScene(9,11,specs2),output:fillHoles(ringScene(9,11,specs2),specs2)}
 ];
 const testInput=ringScene(9,9,specsTest);
 const result=synthesize(train,[testInput]);
 assert.equal(result.trace.status,'UNIQUE_PROOF_REPLAY',JSON.stringify(result.trace));
 const expected=fillHoles(testInput,specsTest);
 assert.ok(eq(result.prediction,[expected]));
 assert.ok(eq(interpret(result.trace.selected,testInput),expected));
 assert.equal(result.trace.selected.action,'holeFill');
});
test('semantic object segmentation is input-derived and reports connected shape attributes',()=>{
 const g=ringScene(7,9,[[0,0,3],[0,5,4]]);
 const objs=objects(g,{segment:'color4',bg:'zero'});
 assert.equal(objs.length,2);
 assert.deepEqual(objs.map(x=>x.area),[8,8]);
 assert.ok(objs.every(x=>x.bboxArea===9));
});
test('contradictory demonstrations must not produce a false confident program',()=>{
 const g=ringScene(4,4,[[0,0,2]]);
 const a=fillHoles(g,[[0,0,2]]);
 const b=g.map(r=>r.map(x=>x===0?1:x));
 const result=synthesize([{input:g,output:a},{input:g,output:b}],[g]);
 assert.equal(result.prediction,null);
 assert.equal(result.trace.status,'NO_TRAIN_CONSISTENT_OBJECT_PROGRAM');
});
test('wrong output geometry rejects object hypothesis and safely abstains',()=>{
 const g=ringScene(4,4,[[0,0,2]]);
 const result=synthesize([{input:g,output:[[9]]}],[g]);
 assert.equal(result.prediction,null);
 assert.equal(result.trace.status,'UNSUPPORTED_OR_BAD_SHAPE');
});
test('no labels passed through test-input interface and generated certificate does not memoize test outputs',()=>{
 assert.equal(CONTRACT.teacherCalls,0);
 assert.equal(CONTRACT.neuralCalls,0);
 const sp=[[0,0,3],[0,5,4]],g=ringScene(7,9,sp),out=fillHoles(g,sp);
 const t=[{input:g,output:out}];
 const x=synthesize(t,[g]);
 const y=synthesize(t,[g.map(r=>r.slice())]);
 assert.ok(eq(x.prediction,y.prediction));
 assert.ok(eq(x.trace.selected,y.trace.selected));
});
