import test from "node:test";
import assert from "node:assert/strict";
import {exactGrid,assess,gitBlobSha} from "../experiments/q3_open_program_teacher_p22_verify.mjs";

const unitTask={
 train:[{input:[[1,0],[0,0]],output:[[0,1],[0,0]]}],
 test:[{input:[[0,1],[0,0]],output:[[0,0],[0,1]]}]
};
const shiftRight=g=>g.map(row=>[0,...row.slice(0,-1)]);
test("independent cell-wise equality checks dimensions and all palette cells",()=>{
 assert.ok(exactGrid([[0,2],[3,4]],[[0,2],[3,4]]));
 assert.equal(exactGrid([[0,2],[3,4]],[[0,2],[3,5]]),false);
 assert.equal(exactGrid([[0,2],[3,4]],[[0,2,0],[3,4,0]]),false);
});
test("original training and held-out test proposal both exact",()=>{
 const s=assess(shiftRight,unitTask);
 assert.equal(s.submitted,true);assert.equal(s.trainExact,true);
 assert.equal(s.testExact,true);assert.equal(s.falseAccept,false);
});
test("mutating held-out reference changes score, not executable program",()=>{
 const copy=structuredClone(unitTask);copy.test[0].output=[[8,8],[8,8]];
 const a=assess(shiftRight,unitTask),b=assess(shiftRight,copy);
 assert.equal(a.testExact,true);assert.equal(b.testExact,false);
 assert.equal(b.falseAccept,true);
});
test("mismatch on training pair cannot count as test success",()=>{
 const bad=()=>[[9,9],[9,9]];const s=assess(bad,unitTask);
 assert.equal(s.trainExact,false);assert.equal(s.testExact,false);
});
test("explicit abstention is not a wrong accepted candidate",()=>{
 const s=assess(null,unitTask);assert.equal(s.submitted,false);
 assert.equal(s.trainExact,false);assert.equal(s.falseAccept,false);
});
test("git blob SHA has deterministic content hash",()=>{
 const a=gitBlobSha(Buffer.from("abc")),b=gitBlobSha(Buffer.from("abd"));
 assert.match(a,/^[a-f0-9]{40}$/);assert.notEqual(a,b);
});
