/* P44 read-only independent original-source audit.
 * Does NOT import P44 generator, P44 proposal runner or frozen P22 seed.
 * Alternate direct mathematical row/column gap definition is executed
 * against original 400 and compared to FIRST immutable SHA and exact rows.
 */
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';

const ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const P44_FIRST='8efe48796c15f8f322124afa6751dca1ea7816c93e038e4a38b90d08dcc3e639';
const P43_FIRST='8b5cb4927133930f6238adb17dbeba5a73d6955a368965b67318cc6aca78a398';
const P30_FIRST='0fb747b4fd7355649465b8ff3424c0170d6d178f47fd1ea64ca486c416672b79';
const SEED_BLOB='d82f09406b4b3ee4e9651c261013c8ce8aa850c7';
const sha=x=>createHash('sha256').update(x).digest('hex');
const blob=x=>createHash('sha1').update(Buffer.concat([Buffer.from('blob '+x.length+'\0'),x])).digest('hex');
const eq=(x,y)=>JSON.stringify(x)===JSON.stringify(y);
function valid(x){
 if(!Array.isArray(x)||x.length===0||x.length>30||!Array.isArray(x[0])||x[0].length===0||x[0].length>30)return false;
 const w=x[0].length;
 return x.every(r=>Array.isArray(r)&&r.length===w&&r.every(v=>Number.isInteger(v)&&v>=0&&v<=9));
}
function directOriginalFamily(input,axis,b,c){
 if(!valid(input)||b===c)return null;
 const out=input.map(r=>r.slice());
 const H=input.length,W=input[0].length;
 const lines=axis==='row'?H:W;
 const width=axis==='row'?W:H;
 for(let i=0;i<lines;i++){
  const markers=[];
  for(let j=0;j<width;j++){
   const x=axis==='row'?input[i][j]:input[j][i];
   if(x!==b)markers.push(j);
  }
  if(markers.length<2)continue;
  const lo=markers[0],hi=markers[markers.length-1];
  for(let j=lo+1;j<hi;j++){
   const pixel=axis==='row'?out[i][j]:out[j][i];
   if(pixel!==b)continue;
   if(axis==='row')out[i][j]=c;else out[j][i]=c;
  }
 }
 return out;
}

function alternatePropose(task){
 const matches=[];
 let trainCalls=0,testCalls=0;
 for(const axis of ['row','column']){
  for(let b=0;b<10;b++)for(let c=0;c<10;c++){
   if(b===c)continue;
   let fits=true,moves=false;
   for(const pair of task.train){
    trainCalls++;
    const pred=directOriginalFamily(pair.input,axis,b,c);
    if(!valid(pred)||!eq(pred,pair.output)){fits=false;break;}
    if(!eq(pred,pair.input))moves=true;
   }
   if(!fits||!moves)continue;
   const preds=[];
   for(const t of task.test){
    testCalls++;
    const out=directOriginalFamily(t.input,axis,b,c);
    if(!valid(out))throw Error('INDEPENDENT_DIRECT_GENERATOR_BAD_OUTPUT');
    preds.push(out);
   }
   matches.push({
    key:axis+'/background:'+b+'/fill:'+c,
    axis,b,c,preds
   });
  }
 }
 const outputKeys=new Set(matches.map(o=>JSON.stringify(o.preds)));
 const predicted=outputKeys.size===1?matches[0].preds:null;
 return {
  submitted:predicted!==null,
  output:predicted,
  ambiguous:outputKeys.size>1,
  candidates:matches.map(({key,axis,b,c})=>({key,axis,b,c})),
  trainCalls,testCalls
 };
}

function audit(originalRoot,p44File,p43File,p30File){
 const errors=[];
 const firstBytes=fs.readFileSync(p44File),p44sha=sha(firstBytes),first=JSON.parse(firstBytes);
 const base43=fs.readFileSync(p43File),b43sha=sha(base43),p43=JSON.parse(base43);
 const base30=fs.readFileSync(p30File),b30sha=sha(base30),p30=JSON.parse(base30);
 const p22Source=fs.readFileSync(path.join(ROOT,'experiments/q3_open_program_teacher_p22_FIRST_PROPOSAL.mjs'));
 const seedSha=blob(p22Source);
 if(p44sha!==P44_FIRST)errors.push('ORIGINAL_P44_FIRST_SHA_DRIFT');
 if(b43sha!==P43_FIRST)errors.push('ORIGINAL_P43_FIRST_SHA_DRIFT');
 if(b30sha!==P30_FIRST)errors.push('ORIGINAL_P30_FIRST_SHA_DRIFT');
 if(seedSha!==SEED_BLOB)errors.push('FROZEN_ORIGINAL_SEED_SHA_DRIFT');
 const dirname=path.join(originalRoot,'data/training');
 const names=fs.readdirSync(dirname).filter(x=>x.endsWith('.json')).sort();
 if(names.length!==400||first.rows?.length!==400||p43.rows?.length!==400||p30.rows?.length!==400)
  throw Error('INVALID_ORIGINAL_400_DENOMINATOR');
 let exact=0,submitted=0,wrong=0,extra=0,ambiguous=0,train=0,test=0;
 const sourceRows=[];
 const usedPrograms=new Set();
 for(let i=0;i<400;i++){
  const name=names[i],firstRow=first.rows[i],b43=p43.rows[i],b30=p30.rows[i];
  if(firstRow.id!==name||b43.id!==name||b30.id!==name){
   errors.push('ORIGINAL_TASK_ID_DRIFT_'+i);continue;
  }
  const task=JSON.parse(fs.readFileSync(path.join(dirname,name),'utf8'));
  const outcome=alternatePropose(task);
  // No original TEST gold enters alternatePropose; score only after
  // all candidates and semantic prediction are frozen.
  const correct=outcome.submitted&&eq(outcome.output,task.test.map(p=>p.output));
  const bad=outcome.submitted&&!correct;
  const already=b43.teacher_original_exact||b30.safe_exact;
  const newCorrect=correct&&!already;
  const expected={
   p30_correct:b30.safe_exact,p43_correct:b43.teacher_original_exact,
   prior_correct_oracle_set:already,
   p44_submitted:outcome.submitted,
   p44_correct:correct,p44_wrong:bad,
   p44_new_exact_over_both:newCorrect,p44_ambiguous:outcome.ambiguous,
   p44_train_semantic_fits:outcome.candidates.length,
   p44_candidate_programs:outcome.candidates,
   p44_prediction_sha256:outcome.submitted?sha(Buffer.from(JSON.stringify(outcome.output))):null,
   train_program_executions:outcome.trainCalls,
   test_input_program_executions:outcome.testCalls
  };
  for(const [k,v] of Object.entries(expected))
   if(!eq(firstRow[k],v))errors.push('ORIGINAL_ROW_MISMATCH_'+name+'_'+k);
  if(correct){
   sourceRows.push({original_id:name,
     matched_programs:outcome.candidates.map(p=>p.key),newCorrect});
   for(const candidate of outcome.candidates)usedPrograms.add(candidate.key);
  }
  exact+=Number(correct);submitted+=Number(outcome.submitted);
  wrong+=Number(bad);extra+=Number(newCorrect);
  ambiguous+=Number(outcome.ambiguous);
  train+=outcome.trainCalls;test+=outcome.testCalls;
 }
 const stats=first.stats;
 const expectations={
  original_tasks:400,teacher_seed_programs:1,
  group_orbit_distinct_candidate_programs:180,
  historical_p30_correct:54,historical_p43_correct:1,
  historical_oracle_union_correct:55,
  p44_submitted:submitted,p44_exact:exact,p44_wrong:wrong,
  p44_new_original_exact_vs_p30_and_p43:extra,
  p44_ambiguous:ambiguous,
  total_train_program_executions:train,
  total_test_input_program_executions:test,
  oracle_union_correct_upper_bound:55+extra
 };
 for(const [k,v] of Object.entries(expectations)){
  if(stats[k]!==v)errors.push('ORIGINAL_STAT_MISMATCH_'+k);
 }
 if(first.science_status!=='SCOPED_ONE_SEED_ORBIT_REUSE_FAIL')
  errors.push('FIRST_SCIENTIFIC_FAILURE_WAS_PROMOTED');
 if(first.Q3_NEUMANN_AUTONOMOUS_INVENTION!=='NOT_PROVEN'||
    first.Q6_CROSS_FORMALISM!=='NOT_PROVEN'||
    first.arc_evaluation_IDs_consumed!==0)
  errors.push('UNSUPPORTED_GLOBAL_SCIENCE_PROMOTION');
 return {
  schema:'neumann.q3.p44.original-first-independent-alternate-math-audit.v1',
  audit_pass:errors.length===0,error_count:errors.length,errors:errors.slice(0,20),
  pinned_original_first_sha256:p44sha,
  pinned_first_p43_sha256:b43sha,
  pinned_first_p30_sha256:b30sha,
  frozen_seed_git_blob:seedSha,
  independent_all_400_originals:400,
  alternate_independent_math_programs:180,
  source_first_program_loader_imported:false,
  independent_submitted:submitted,independent_exact:exact,
  independent_wrong:wrong,independent_extra_vs_frozen_55:extra,
  independently_scored_rows:sourceRows,
  distinct_success_variant_keys:[...usedPrograms].sort(),
  independent_train_program_calls:train,independent_test_program_calls:test,
  original_evaluation_ids_used:0,
  global_learned_new_semantics:'NOT_PROVEN'
 };
}

export {directOriginalFamily,alternatePropose,audit};
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 if(process.argv.length!==6){
  console.error('usage: node P44_AUDIT.mjs ARC_ROOT P44_FIRST P43_FIRST P30_FIRST');process.exitCode=2;
 }else try{
  const result=audit(...process.argv.slice(2));
  console.log(JSON.stringify(result,null,2));
  if(!result.audit_pass)process.exitCode=1;
 }catch(e){console.error(String(e.stack||e));process.exitCode=1;}
}
