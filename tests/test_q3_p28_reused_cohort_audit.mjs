import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {evaluateCohort} from '../experiments/q3_p28_reused_cohort_audit.mjs';
const fractal=x=>{let h=x.length,w=x[0].length;return Array.from({length:h*h},(_,r)=>Array.from({length:w*w},(_,c)=>x[Math.floor(r/h)][Math.floor(c/w)]===0?0:x[r%h][c%w]));};
test('32-source audit separates in-scope, train-fit, and correct without test-gold proposal',()=>{
 const root=fs.mkdtempSync(path.join(os.tmpdir(),'p28-'));
 try {
  fs.mkdirSync(path.join(root,'data/evaluation'),{recursive:true});
  const ids=[];
  for(let i=0;i<32;i++){
   const id='case'+String(i).padStart(2,'0')+'.json';ids.push(id);
   const x=i<30?Array.from({length:6},()=>[1]):[[0,2],[2,0]];
   const task=i===31?{train:[{input:x,output:fractal(x)}],test:[{input:x,output:fractal(x)}]}:
    {train:[{input:x,output:[[9]]}],test:[{input:x,output:[[9]]}]};
   fs.writeFileSync(path.join(root,'data/evaluation',id),JSON.stringify(task));
  }
  const manifest=path.join(root,'frozen.json');
  fs.writeFileSync(manifest,JSON.stringify({ids}));
  const report=evaluateCohort(root,manifest);
  assert.equal(report.result.total,32);
  assert.equal(report.result.out_of_scope,30);
  assert.equal(report.result.in_scope,2);
  assert.equal(report.result.correct,1);
  assert.equal(report.result.wrong,0);
  assert.equal(report.test_gold_accessed_after_proposal,true);
 } finally {fs.rmSync(root,{recursive:true,force:true});}
});
test('cohort length and duplicates must fail closed',()=>{
 const root=fs.mkdtempSync(path.join(os.tmpdir(),'p28bad-'));
 try{const f=path.join(root,'manifest.json');fs.writeFileSync(f,JSON.stringify({ids:['same.json','same.json']}));
  assert.throws(()=>evaluateCohort(root,f),/BAD_FROZEN_COHORT/);
 }finally{fs.rmSync(root,{recursive:true,force:true});}
});
