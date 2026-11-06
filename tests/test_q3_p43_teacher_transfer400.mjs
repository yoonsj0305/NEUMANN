import test from 'node:test';
import assert from 'node:assert/strict';
import {propose,exactGrid} from '../experiments/q3_p43_teacher_transfer400_first.mjs';

const one=x=>[[x]];
const task=[{input:one(1),output:one(2)}];

test('correct train fit picks independent test prediction from function, not source ID',()=>{
 const funcs=[['candidateX',g=>one(g[0][0]+1)],['candidateY',g=>one(g[0][0]+3)]];
 const r=propose(task,[one(3)],funcs);
 assert.equal(r.fitting_program_count,1);
 assert.deepEqual(r.program_ids,['candidateX']);
 assert.deepEqual(r.prediction,[one(4)]);
 assert.equal(r.ambiguous,false);
});

test('training mismatch can never be accepted despite a plausible test output',()=>{
 const funcs=[['bad',g=>one(g[0][0]===1?7:4)]];
 const r=propose(task,[one(3)],funcs);
 assert.equal(r.abstained,true);
 assert.equal(r.prediction,null);
});

test('two training-consistent programs disagree on test => fail closed',()=>{
 const funcs=[
  ['left',g=>one(g[0][0]===1?2:4)],
  ['right',g=>one(g[0][0]===1?2:5)]
 ];
 const r=propose(task,[one(3)],funcs);
 assert.equal(r.fitting_program_count,2);
 assert.equal(r.ambiguous,true);
 assert.equal(r.prediction,null);
});

test('two distinct training-consistent programs with unanimous tests may be accepted',()=>{
 const funcs=[
  ['left',g=>one(g[0][0]+1)],
  ['right',g=>one(g[0][0]===1?2:g[0][0]+1)]
 ];
 const r=propose(task,[one(3)],funcs);
 assert.equal(r.fitting_program_count,2);
 assert.deepEqual(r.prediction,[one(4)]);
 assert.equal(r.ambiguous,false);
});

test('exception, bad output and malformed output all abstain',()=>{
 const funcs=[['error',()=>{throw Error('fake');}],['bad-grid',()=>[[]]],['null',()=>null]];
 const r=propose(task,[one(3)],funcs);
 assert.equal(r.abstained,true);
 assert.equal(r.prediction,null);
});

test('cell-accurate original output equality and size mismatch',()=>{
 assert.equal(exactGrid([[1,2],[3,4]],[[1,2],[3,4]]),true);
 assert.equal(exactGrid([[1,2]],[[1,2],[3,4]]),false);
 assert.equal(exactGrid([[1,2]],[[2,1]]),false);
 assert.equal(exactGrid(null,[[1]]),false);
});
