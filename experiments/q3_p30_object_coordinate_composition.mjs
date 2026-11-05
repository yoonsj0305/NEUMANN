/* NEUMANN P3.0: compose already-established object extraction with P2.9
 * example-induced coordinate programs.
 *
 * Important: all primitives are defined by humans, including crop operations.
 * Search and composition are automatic, but NOT autonomous opcode invention.
 * Preprocessor and typed coordinate program are independently executable.
 * Gold never enters proposal. Degraded mode: ABSTAIN.
 */
import * as P27 from './q3_compositional_schema_learning_p27.mjs';
import * as P29 from './q3_p29_induced_coordinate_programs.mjs';

export const CONTRACT=Object.freeze({
 schema:'neumann.q3.p30.object-coordinate-composition.v1',
 mode:'symbolic_candidate_composition_not_neural_learning',
 preprocessor_library:['cropNZ','cropBG','cropLargest'],
 original_p29_unmodified:true,
 neural_calls:0,teacher_calls:0,
 no_train_gold_for_scoring:false, // TRAIN examples contain labeled target grids by design.
 test_gold_exposed:false,
 first_task_scope:'public_train_development_only',
 fallback:'ABSTAIN'
});
const sig=x=>JSON.stringify(x);
const eq=(a,b)=>sig(a)===sig(b);
const grammar=[[],['cropNZ'],['cropBG'],['cropLargest']];
export function applyPipeline(ast,grid) {
 if(!ast||ast.kind!=='object-then-coordinate'||!Array.isArray(ast.preOps)||
    ast.preOps.length>1||ast.preOps.some(x=>!CONTRACT.preprocessor_library.includes(x)))
    return null;
 const pre=P27.executeGeometry(grid,ast.preOps);
 if(pre===null)return null;
 return P29.interpret(ast.coordinate,pre);
}
export function propose(train,testInputs) {
 const started=process.hrtime.bigint();
 const trace={schema:CONTRACT.schema,
  preprocessors_attempted:0,preprocess_ineligible:0,
  p29_calls:0,train_replay_checks:0,test_replay_checks:0,
  candidate_programs:0,distinct_predictions:0,
  selected_program:null,source_of_prediction:null,
  abstention:null,elapsed_ms:0};
 const done=(prediction,reason)=>{
  trace.abstention=reason;
  trace.elapsed_ms=Number(process.hrtime.bigint()-started)/1e6;
  return {prediction,trace};
 };
 if(!Array.isArray(train)||!train.length||!Array.isArray(testInputs)||!testInputs.length)
  return done(null,'INVALID_TASK');
 const candidates=[];
 for(const preOps of grammar){
  trace.preprocessors_attempted++;
  const pTr=[],pTest=[];
  let ok=true;
  for(const pair of train){
   const v=P27.executeGeometry(pair?.input,preOps);
   if(v===null){ok=false;break;}
   pTr.push({input:v,output:pair.output});
  }
  if(ok)for(const v of testInputs){
   const q=P27.executeGeometry(v,preOps);
   if(q===null){ok=false;break;}
   pTest.push(q);
  }
  if(!ok){trace.preprocess_ineligible++;continue;}
  trace.p29_calls++;
  const result=P29.synthesize(pTr,pTest);
  if(result.prediction===null||result.trace.ast===null)continue;
  const ast={kind:'object-then-coordinate',preOps:[...preOps],coordinate:result.trace.ast};
  trace.train_replay_checks+=train.length;
  if(!train.every(p=>eq(applyPipeline(ast,p.input),p.output)))
   throw Error('P30_SOURCE_INDEPENDENT_TRAIN_REPLAY_FAIL');
  trace.test_replay_checks+=testInputs.length;
  if(!testInputs.every((g,i)=>eq(applyPipeline(ast,g),result.prediction[i])))
   throw Error('P30_SOURCE_INDEPENDENT_TEST_REPLAY_FAIL');
  const item={prediction:result.prediction,ast,source:preOps.join('+')||'identity'};
  candidates.push(item);
  trace.candidate_programs++;
  // Original P29 is the identity-control priority. Preserves all P29 results.
  if(preOps.length===0){
   trace.selected_program=ast;
   trace.source_of_prediction='identity_P29_same_source';
   return done(result.prediction,null);
  }
 }
 if(!candidates.length)return done(null,'NO_TRAIN_CONSISTENT_COMPOSITION');
 const variants=new Map();
 for(const c of candidates){
  const key=sig(c.prediction);
  if(!variants.has(key))variants.set(key,c);
 }
 trace.distinct_predictions=variants.size;
 if(variants.size!==1)return done(null,'AMBIGUOUS_NEW_CROP_COMPOSITIONS');
 const chosen=variants.values().next().value;
 trace.selected_program=chosen.ast;
 trace.source_of_prediction=chosen.source;
 return done(chosen.prediction,null);
}
