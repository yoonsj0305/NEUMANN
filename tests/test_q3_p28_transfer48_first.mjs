import test from 'node:test';
import assert from 'node:assert/strict';
import {assess} from '../experiments/q3_p28_transfer48_first.mjs';
import {interpret,propose,candidatePrograms,p27ShapeCeilingFor3x3To9x9} from '../experiments/q3_p28_factorized_operator.mjs';

const x1=[[1,0],[0,2]],x2=[[3,0],[0,4]];
const ast={kind:"factorized-zero-conditional",selector:["inner","outer","inner","zero"]};
const first={train:[{input:x1,output:interpret(ast,x1)},{input:x2,output:interpret(ast,x2)}],
 test:[{input:x2,output:interpret(ast,x2)}]};
const k=o=>JSON.stringify(o);
test('frozen P28 grammar contains exactly 81 typed candidates; P27 3x3->9x9 shape unreachable',()=>{
 assert.equal(candidatePrograms().length,81);
 assert.equal(p27ShapeCeilingFor3x3To9x9(),true);
});
test('gold-blind P28 decisions remain identical after mutation of TEST gold',()=>{
 const right=assess(first,'opened-synthetic');
 const poisoned=assess({...first,test:[{input:x2,output:[[9,9,9]]}]},'opened-synthetic');
 for(const field of ["P28_ast","P28_train_fits","P28_abstained","P28_submitted","P28_enumerated",
                     "P28_pair_evaluations","P28_certificate","P27_attempts"]) {
   assert.equal(k(right[field]),k(poisoned[field]),'gold input into proposal: '+field);
 }
 assert.equal(right.P28_submitted,true);
 assert.equal(right.P28_correct,true);
 assert.equal(poisoned.P28_correct,false);
 assert.equal(poisoned.P28_wrong,true);
});
test('independent in-memory source replay cannot silently accept arbitrary gold',()=>{
 const r=assess(first,'opened-synthetic');
 const cert=r.P28_certificate;
 assert.ok(cert);
 assert.equal(cert.schema,'neumann.q3.p28.proof-certificate.v1');
 assert.equal(k(cert.predicted_test),k(first.test.map(t=>t.output)));
 for(const pair of cert.train)assert.equal(k(interpret(cert.ast,pair.input)),k(pair.output));
 for(let i=0;i<cert.test_inputs.length;i++)
   assert.equal(k(interpret(cert.ast,cert.test_inputs[i])),k(cert.predicted_test[i]));
});
test('original target ambiguity is safe-abstain and not claimed as a successful test',()=>{
 const firstX=[[1,2],[3,4]];
 const task={train:[{input:firstX,output:[[2]]}],test:[{input:firstX,output:[[2]]}]};
 const r=assess(task,'nonsquare-out-of-scope');
 assert.equal(r.P28_submitted,false);
 assert.equal(r.P28_correct,false);
 assert.equal(r.P28_ast,null);
});
