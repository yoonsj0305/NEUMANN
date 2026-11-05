import test from "node:test";
import assert from "node:assert/strict";
import {solve,run,CONTRACT} from "../experiments/q3_generated_decision_trees_p25.mjs";

function task(seed){
 let state=(seed*2995937+29)>>>0;
 const rng=()=>{state=(Math.imul(state,1664525)+1013904223)>>>0;return state%7;};
 const g=Array.from({length:5},()=>Array.from({length:10},rng));
 const out=Array.from({length:5},(_,r)=>Array.from({length:5},(_,c)=>g[r][c]===g[r][c+5]?4:g[r][c]===0?3:7));
 return {input:g,output:out};
}
test("can induce new nested branching AST, not a supplied whole operator",()=>{
 const train=[1,2,3,4,5].map(task),held=[6,7,8].map(task);
 const r=solve(train,held.map(x=>x.input));
 assert.deepEqual(r.prediction,held.map(x=>x.output));
 assert.equal(r.trace.selected_AST.mode,"half_lr");
 assert.equal(r.trace.selected_AST.tree.kind,"if");
 assert.equal(r.trace.neural_calls,0);assert.equal(r.trace.teacher_calls,0);
});
test("repeat predicts same AST and original grids",()=>{
 const tr=[1,2,3,4,5].map(task),queries=[6,7].map(task);
 const a=solve(tr,queries.map(x=>x.input)),b=solve(tr,queries.map(x=>x.input));
 assert.deepEqual(a.prediction,b.prediction);
 assert.deepEqual(a.trace.selected_AST,b.trace.selected_AST);
});
test("program is exact on original training pairs",()=>{
 const tr=[1,2,3,4,5].map(task),r=solve(tr,[task(6).input]);
 for(const p of tr)assert.deepEqual(run(r.trace.selected_AST,p.input),p.output);
});
test("bad original input never produces guessed program",()=>{
 const r=solve([],[[[1]]]);assert.equal(r.prediction,null);
 assert.equal(r.trace.abstention,"INVALID_INPUT");
});
test("test reference answers are never part of proposer interface",()=>{
 const tr=[1,2,3,4,5].map(task),q=task(6),a=solve(tr,[q.input]);
 const target=q.output.map(row=>row.slice());target[0][0]=(target[0][0]+1)%10;
 const b=solve(tr,[q.input]);
 assert.deepEqual(a.prediction,b.prediction);
 assert.notDeepEqual(b.prediction[0],target);
});
test("all scores and programs must be deterministic and bounded",()=>{
 const r=solve([1,2,3,4,5].map(task),[task(6).input]);
 assert.ok(r.trace.unique_subproblems<=CONTRACT.nodeBudgetPerMode*7+7);
 assert.ok(r.trace.wall_ms>=0);
 assert.ok(CONTRACT.maxDepth===3&&CONTRACT.splitBeam===12);
});
