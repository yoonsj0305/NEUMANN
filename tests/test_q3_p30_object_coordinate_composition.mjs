import test from 'node:test';
import assert from 'node:assert/strict';
import * as P30 from '../experiments/q3_p30_object_coordinate_composition.mjs';
import * as P29 from '../experiments/q3_p29_induced_coordinate_programs.mjs';
const eq=(x,y)=>JSON.stringify(x)===JSON.stringify(y);
const pad=(obj,dh,dw,row,col,bg=0)=>{
 const H=obj.length+dh,W=obj[0].length+dw;
 const out=Array.from({length:H},()=>Array(W).fill(bg));
 for(let r=0;r<obj.length;r++)for(let c=0;c<obj[0].length;c++)out[row+r][col+c]=obj[r][c];
 return out;
};
const scale=(x,k)=>x.flatMap(row=>Array.from({length:k},()=>row.flatMap(v=>Array(k).fill(v))));
test('induce cropNZ then scale2, applied to unseen frame sizes and spatial placement',()=>{
 const a=[[1,2],[2,1]],b=[[1,2,1],[2,1,2]],c=[[1,2],[2,1],[1,2]];
 const train=[
  {input:pad(a,3,4,1,2),output:scale(a,2)},
  {input:pad(b,4,3,2,1),output:scale(b,2)}
 ];
 const target=pad(c,3,3,1,2);
 const a29=P29.synthesize(train,[target]);
 const res=P30.propose(train,[target]);
 assert.equal(a29.prediction,null,'P29 without object extraction must not secretly solve cropped task');
 assert.ok(eq(res.prediction,[scale(c,2)]),JSON.stringify(res.trace));
 assert.deepEqual(res.trace.selected_program.preOps,['cropNZ']);
 assert.ok(eq(P30.applyPipeline(res.trace.selected_program,target),scale(c,2)));
});
test('learn nonzero background cropBG without using oracle',()=>{
 const a=[[1,2],[2,1]],b=[[2,1],[1,2],[2,1]],c=[[1,2,1],[2,1,2]];
 const train=[
  {input:pad(a,4,4,1,2,9),output:a},
  {input:pad(b,4,5,2,3,9),output:b}
 ];
 const target=pad(c,5,4,2,2,9);
 const res=P30.propose(train,[target]);
 assert.ok(eq(res.prediction,[c]),JSON.stringify(res.trace));
 assert.deepEqual(res.trace.selected_program.preOps,['cropBG']);
});
test('identity P29 source wins whenever it already has an exact program',()=>{
 const a=[[1,2],[3,4]],b=[[2,3,4],[1,2,3]],c=[[3,4],[1,2],[2,3]];
 const train=[{input:a,output:scale(a,2)},{input:b,output:scale(b,2)}];
 const p29=P29.synthesize(train,[c]);
 const p30=P30.propose(train,[c]);
 assert.ok(eq(p29.prediction,[scale(c,2)]),JSON.stringify(p29.trace));
 assert.ok(eq(p30.prediction,p29.prediction));
 assert.equal(p30.trace.source_of_prediction,'identity_P29_same_source');
});
test('unfit or contradictory transforms abstain rather than propose a score',()=>{
 const a=[[1,2],[2,1]],target=pad(a,3,4,1,2);
 const r=P30.propose([{input:target,output:[[5]]}],[target]);
 assert.equal(r.prediction,null);
 assert.ok(r.trace.abstention);
});
test('candidate AST can be replayed without source task ID or hidden test gold',()=>{
 const a=[[1,2],[2,1]],b=[[1,2,1],[2,1,2]],c=[[1,2],[1,2],[2,1]];
 const tr=[{input:pad(a,4,3,2,1),output:scale(a,2)},
          {input:pad(b,3,5,1,2),output:scale(b,2)}];
 const g=pad(c,5,4,1,2);
 const r=P30.propose(tr,[g]);
 assert.ok(r.prediction!==null);
 assert.ok(eq(P30.applyPipeline(r.trace.selected_program,g),r.prediction[0]));
 assert.equal(P30.CONTRACT.neural_calls,0);
 assert.equal(P30.CONTRACT.teacher_calls,0);
});
