/**
 * Reused ARC-AGI-1 evaluation cohort, NOT a sealed/new generalization test.
 * Run: node experiments/q3_p28_reused_cohort_audit.mjs <ARC-AGI root>
 * Requires known pinned P2.7 cohort file, but no original test gold at proposal.
 */
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {propose,interpret} from './q3_p28_factorized_operator.mjs';
const eq=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
const ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const cohortFile=path.join(ROOT,'docs/experiments/q3_p27_COHORT_FROZEN.json');
function inputInScope(g) {
 return Array.isArray(g)&&g.length>0&&g.length**2<=30&&Array.isArray(g[0])&&g[0].length>0&&g[0].length**2<=30&&
 g.every(r=>Array.isArray(r)&&r.length===g[0].length&&r.every(c=>Number.isInteger(c)&&c>=0&&c<=9));
}
export function evaluateCohort(arcRoot, manifestPath=cohortFile){
 const manifest=JSON.parse(fs.readFileSync(manifestPath,'utf8'));
 if(!Array.isArray(manifest.ids)||manifest.ids.length!==32||new Set(manifest.ids).size!==32)throw Error('BAD_FROZEN_COHORT');
 const rows=[];
 for(const id of manifest.ids){
  const task=JSON.parse(fs.readFileSync(path.join(arcRoot,'data/evaluation',id),'utf8'));
  const testInputs=task.test.map(t=>t.input);
  const inScope=task.train.every(p=>inputInScope(p.input))&&testInputs.every(inputInScope);
  const proposed=propose(task.train,testInputs);
  const ast=proposed.trace.generated_AST;
  const replay=ast!==null&&task.train.every(p=>eq(interpret(ast,p.input),p.output))&&testInputs.every((x,i)=>eq(interpret(ast,x),proposed.prediction[i]));
  // gold accessed only AFTER the proposal and replay.
  const targets=task.test.map(t=>t.output);
  const submitted=proposed.prediction!==null&&replay;
  const correct=submitted&&eq(proposed.prediction,targets);
  rows.push({id,eligible:inScope,train_fit:proposed.trace.exact_train_programs>0,submitted,correct,
   wrong:submitted&&!correct, abstention:proposed.trace.abstention,
   enumerated:proposed.trace.enumerated,train_pair_evaluations:proposed.trace.train_pair_evaluations});
 }
 const count=f=>rows.filter(f).length;
 return {schema:'neumann.q3.p28.reused-public-arc-evaluation.v1',
  source:'fchollet/ARC-AGI@399030444e0ab0cc8b4e199870fb20b863846f34',
  cohort:'docs/experiments/q3_p27_COHORT_FROZEN.json',
  not_fresh_or_sealed:true, test_gold_accessed_after_proposal:true,
  result:{total:rows.length,out_of_scope:count(x=>!x.eligible),in_scope:count(x=>x.eligible),
   train_fit:count(x=>x.train_fit),submitted:count(x=>x.submitted),
   correct:count(x=>x.correct),wrong:count(x=>x.wrong)},rows,
  q3_global:'OPEN',q4_global:'OPEN',q7_global:'OPEN'};
}
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 if(!process.argv[2]){process.stderr.write('Usage: node experiments/q3_p28_reused_cohort_audit.mjs <ARC-AGI-root>\n');process.exitCode=2;}
 else{try{process.stdout.write(JSON.stringify(evaluateCohort(process.argv[2]),null,2)+'\n');}
 catch(e){process.stderr.write(String(e.stack||e)+'\n');process.exitCode=1;}}
}
