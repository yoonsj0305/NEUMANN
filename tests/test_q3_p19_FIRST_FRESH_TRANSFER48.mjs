import test from "node:test";
import assert from "node:assert/strict";
import {assess} from "../experiments/q3_p19_FIRST_FRESH_TRANSFER48.mjs";
import {propose,execute,allASTs} from "../experiments/q3_goal_conditioned_induction_p19.mjs";
const shift=g=>[Array(g[0].length).fill(0),...g.slice(0,-1).map(r=>r.slice())];
const maps=[
 [[0,1,0,0,2],[0,0,0,2,0],[0,0,1,0,0],[2,0,0,0,0],[0,0,0,1,0]],
 [[1,0,0,0,0],[2,1,0,0,2],[0,0,2,0,1],[1,0,0,0,0],[0,0,1,2,0]],
 [[0,2,1,0,0],[0,0,2,0,0],[1,0,0,1,0],[0,1,0,0,2],[2,0,0,0,1]],
 [[2,0,0,0,1],[0,0,1,2,0],[0,2,0,0,0],[0,0,0,1,1],[0,1,0,0,0]]
];
test("P1.9 source program library enumerates more than 1500 executable programs",()=>{
 assert.ok([...allASTs()].length>1500);
});
test("first original scorer never allows TEST gold to change an inferred program",()=>{
 const train=maps.slice(0,3).map(input=>({input,output:shift(input)}));
 const good=assess({train,test:[{input:maps[3],output:shift(maps[3])}]},"toy-first");
 const bad=assess({train,test:[{input:maps[3],output:[[9]]}]},"toy-first");
 for(const key of ["P19_training_fit_count","P19_ambiguous","P19_submitted","P19_candidate_ASTs",
  "P19_train_replays","P19_test_replays","P19_representatives","P19_certificate"]){
   assert.deepEqual(good[key],bad[key],"GOLD_LEAK_"+key);
 }
 assert.equal(good.P19_submitted,true);
 assert.equal(good.P19_correct,true);
 assert.equal(bad.P19_correct,false);
 assert.equal(bad.P19_wrong,true);
});
test("original P1.9 synthesis exactly replays train and test through actual interpreter",()=>{
 const train=maps.slice(0,3).map(input=>({input,output:shift(input)}));
 const z=propose(train,[maps[3]]);
 assert.deepEqual(z.prediction,[shift(maps[3])]);
 const row=assess({train,test:[{input:maps[3],output:shift(maps[3])}]},"toy-replay");
 assert.ok(row.P19_certificate);
 assert.equal(row.P19_certificate.representative_ASTs.some(p=>
   train.every(q=>JSON.stringify(execute(q.input,p))===JSON.stringify(q.output))&&
   JSON.stringify(execute(maps[3],p))===JSON.stringify(shift(maps[3]))),true);
});
