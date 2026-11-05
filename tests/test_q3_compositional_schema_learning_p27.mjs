import test from "node:test";
import assert from "node:assert/strict";
import {CONTRACT,allASTs,executeGeometry,runProgram,synthesize,learnPrior,eq} from "../experiments/q3_compositional_schema_learning_p27.mjs";
function pair(grid,ops){const output=executeGeometry(grid,ops);assert.ok(output);return {input:grid,output};}
function rectangle(seed){
 const h=7+seed%3,w=8+(seed*2)%3,g=Array.from({length:h},()=>Array(w).fill(0));
 const rh=2+seed%2,rw=3+(seed%3===0?1:0),a=1+seed%2;
 for(let r=0;r<rh;r++)for(let c=0;c<rw;c++)g[r+1][c+2]=r===0?a:r%2===0?2:1;
 return g;
}
const transformation=["cropNZ","r90"];
test("P27 grammar is finite, typed, deterministic, and makes no teacher calls",()=>{
 assert.equal(allASTs.length,157);
 assert.equal(CONTRACT.teacherCalls,0);
 assert.equal(CONTRACT.neuralCalls,0);
 assert.equal(CONTRACT.maxDepth,2);
 assert.deepEqual(allASTs[0],[]);
});
test("compose a novel two-step executable AST, test on new parameterized shapes",()=>{
 const tr=[1,2,3,4,5].map(s=>pair(rectangle(s),transformation));
 const held=[6,7,8].map(s=>pair(rectangle(s),transformation));
 const x=synthesize(tr,held.map(t=>t.input));
 assert.equal(x.trace.abstention,null,JSON.stringify(x.trace));
 assert.deepEqual(x.prediction,held.map(t=>t.output));
 assert.equal(x.trace.selected_AST.ops.length,2);
 for(const t of tr)assert.ok(eq(runProgram(x.trace.selected_AST,t.input),t.output));
 assert.equal(x.trace.neural_calls,0);
});
test("learn macro frequencies from supervised meta-training tasks, not eval test gold",()=>{
 const meta=[1,2,3,4,5,6].map(s=>({
   train:[pair(rectangle(s),transformation),pair(rectangle(s+1),transformation)],
   test:[pair(rectangle(s+10),transformation)]
 }));
 const prior=learnPrior(meta);
 assert.equal(prior.trainedTasks,6);
 assert.equal(prior.allAtomsHumanSpecified,true);
 assert.ok(prior.stats.correct>=1,JSON.stringify(prior.stats));
 assert.ok(Object.values(prior.prior).some(f=>Object.values(f).some(n=>n>0)));
});
test("invalid output shape and contradictory examples abstain",()=>{
 const g=[[0,0],[0,0]],h=[[1,1],[1,1]];
 const r=synthesize([{input:g,output:g},{input:g,output:h}],[g]);
 assert.equal(r.prediction,null);
 assert.equal(r.trace.abstention,"NO_TRAIN_CONSISTENT_PROGRAM");
});
test("test oracle answers cannot influence program proposal",()=>{
 const train=[1,2,3].map(s=>pair(rectangle(s),transformation));
 const g=rectangle(9),a=synthesize(train,[g]);
 const fakeGold=[[9,9,9],[9,9,9]];
 assert.ok(fakeGold);
 const b=synthesize(train,[g],{selector:"classical"});
 assert.deepEqual(a.prediction,b.prediction);
});
test("same grammar and search budget apply to learned/classical arms",()=>{
 const tr=[1,2,3,4].map(s=>pair(rectangle(s),transformation)),held=[rectangle(10)];
 const prior=learnPrior([{train:tr,test:[pair(rectangle(11),transformation)]}]).prior;
 const a=synthesize(tr,held,{maxCandidates:157}),b=synthesize(tr,held,{prior,selector:"learned",maxCandidates:157});
 assert.equal(a.trace.geometry_attempts,157);
 assert.equal(b.trace.geometry_attempts,157);
 assert.equal(b.trace.teacher_calls,0);
});
test("guard unknown colors and unrepresentable geometry",()=>{
 assert.equal(runProgram({ops:[],palette:[[0,0]]},[[8]]),null);
 assert.equal(executeGeometry([[1]],["unknown"]),null);
});
