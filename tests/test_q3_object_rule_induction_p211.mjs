import test from 'node:test';
import assert from 'node:assert/strict';
import {segment,select,paint,move,valid,run,propose,scoreOriginal} from '../experiments/q3_object_rule_induction_p211.mjs';
const base=()=>Array.from({length:9},()=>Array(9).fill(0));
function scene(r=1,c=1,paintColor=1){const g=base();for(let i=0;i<3;i++)for(let j=0;j<3;j++)g[r+i][c+j]=paintColor;g[7][7]=2;return g;}
function repaint(g,newColor=4){return g.map(row=>row.map(x=>x===1?newColor:x));}

test('separates disconnected components and unique largest object',()=>{
 const g=scene();const a=segment(g,'color4');assert.equal(a.length,2);
 const large=select(g,'color4','largest');assert.equal(large.area,9);
 assert.equal(large.b.r0,1);assert.equal(large.b.c0,1);
});
test('ties are rejected rather than ranked by arbitrary iteration order',()=>{
 const g=base();g[0][0]=1;g[7][7]=2;
 assert.equal(select(g,'color4','largest'),null);
 assert.equal(select(g,'color8','smallest'),null);
});
test('paint rule replays a learned mask without IDs or exact input memorization',()=>{
 const p={partition:'color4',selector:'largest',action:'paint',mask:'object',colorMode:'constant',color:4};
 assert.deepEqual(run(scene(1,1),p),repaint(scene(1,1)));
 assert.deepEqual(run(scene(3,2),p),repaint(scene(3,2)));
});
test('moving an object rejects collisions and out-of-bounds output',()=>{
 const g=scene(1,1);const o=select(g,'color4','largest');
 const ok=move(g,o,1,0);assert.ok(valid(ok));
 assert.equal(ok[4][1],1);assert.equal(ok[1][1],0);
 assert.equal(move(g,o,-2,0),null);
 assert.equal(move(g,o,6,6),null);
});
test('training examples determine candidate consensus; conflicting unseen semantics abstain',()=>{
 const t=[{input:scene(1,1),output:repaint(scene(1,1))},{input:scene(4,1),output:repaint(scene(4,1))}];
 const q=propose(t,[scene(2,2)]);
 assert.ok(q.trace.candidate_programs>0);
 assert.ok(q.trace.train_fit_count>0);
 assert.ok(['AMBIGUOUS_TEST_OR_UNSUPPORTED',null].includes(q.trace.abstention));
 if(q.prediction!==null)assert.deepEqual(q.prediction[0],repaint(scene(2,2)));
});
test('scorer does not expose original test gold to any proposal arm',()=>{
 const g=scene(2,2),train=[{input:scene(1,1),output:repaint(scene(1,1))},{input:scene(4,1),output:repaint(scene(4,1))}];
 const task={train,test:[{input:g,output:repaint(g)}]};
 const noB=()=>({proposals:null,trace:{elapsed_ms:0,attempted:0}});
 const noQ=()=>({prediction:null,trace:{study_wall_ms:0,operator_evaluations:0}});
 const noP=()=>({prediction:null,trace:{wall_ms:0,candidate_ast_count:0}});
 const a=scoreOriginal(task,noB,noQ,noP);
 const mutation=JSON.parse(JSON.stringify(task));mutation.test[0].output[0][0]=9;
 const b=scoreOriginal(mutation,noB,noQ,noP);
 assert.equal(a.C_trace.candidate_programs,b.C_trace.candidate_programs);
 assert.equal(a.C_trace.train_fit_count,b.C_trace.train_fit_count);
 assert.equal(a.C_trace.abstention,b.C_trace.abstention);
 if(a.combined_exact)assert.equal(b.combined_exact,false);
});
test('invalid scenes fail closed',()=>{
 const r=propose([],[scene()]);assert.equal(r.prediction,null);assert.equal(r.trace.abstention,'INVALID_INPUT');
});

test('dimension-changing train targets fail closed without throwing',()=>{
 const input=scene(),output=[[1,2],[3,4]];
 const r=propose([{input,output}],[scene(2,2)]);
 assert.equal(r.prediction,null);assert.equal(r.trace.abstention,'NO_TRAIN_CONSISTENT_OBJECT_RULE');
});
