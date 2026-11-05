import test from "node:test";
import assert from "node:assert/strict";
import {auditTask,MODES,SCHEMA} from "../experiments/q3_p25_representability_ceiling_p26.mjs";

const pair=(input,output)=>({input,output});
test("fixed source language and certificate version",()=>{
 assert.equal(SCHEMA,"neumann.q3.p26.p25-representability-ceiling.v1");
 assert.deepEqual(MODES,["same","half_lr","half_tb","shift_0_-1","shift_0_1","shift_-1_0","shift_1_0"]);
});
test("simple identity training is not falsely ruled out",()=>{
 const g=[[0,1],[1,0]];
 const a=auditTask({train:[pair(g,g)]});
 assert.equal(a.verdict,"NOT_PROVED");
 assert.equal(a.modes.length,5);
 assert.ok(a.modes.every(m=>m.collisions===0));
});
test("unsupported output shape has a rigorous impossibility certificate",()=>{
 const a=auditTask({train:[pair([[0,0,0],[0,0,0],[0,0,0]],[[2,2],[2,2]])]});
 assert.equal(a.verdict,"PROVED_SHAPE_IMPOSSIBLE");
 assert.deepEqual(a.modes,[]);
});
test("identical observations requiring different labels cannot be separated by any decision tree",()=>{
 const g=[[0,0],[0,0]],a=auditTask({train:[
  pair(g,[[0,0],[0,0]]),pair(g,[[1,0],[0,0]])]});
 assert.equal(a.verdict,"PROVED_FEATURE_COLLISION_ALL_SHAPE_MODES");
 assert.equal(a.modes.length,5);
 for(const m of a.modes){
  assert.ok(m.collisions>=1);
  assert.notEqual(m.first_witness.first_target,m.first_witness.second_target);
  assert.match(m.first_witness.signature_sha256,/^[0-9a-f]{64}$/);
 }
});
test("resource cap is not misrepresented as a mathematical impossibility",()=>{
 const g=Array.from({length:30},()=>Array(30).fill(0));
 const a=auditTask({train:[pair(g,g),pair(g,g)]});
 assert.equal(a.verdict,"NOT_PROVED");
 assert.ok(a.modes.length>=1);
 assert.ok(a.modes.every(m=>m.status==="ROW_CAP_OR_UNSUPPORTED"));
});
test("no public test gold is accepted or consulted",()=>{
 const g=[[0,1],[1,0]],train=[pair(g,g)];
 const x=auditTask({train,test:[{input:g,output:[[9,9],[9,9]]}]});
 const y=auditTask({train,test:[{input:g,output:[[0,0],[0,0]]}]});
 assert.deepEqual(x,y);
});
test("invalid training samples are rejected rather than assumed unsolvable",()=>{
 assert.throws(()=>auditTask({train:[]}),/INVALID_TRAIN/);
 assert.throws(()=>auditTask({train:[pair([[12]],[[0]])]}),/INVALID_TRAIN/);
});
