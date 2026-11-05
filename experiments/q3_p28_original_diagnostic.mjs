/**
 * Re-run P2.8 on the frozen diagnostic original task file supplied by user.
 * CLI: node experiments/q3_p28_original_diagnostic.mjs <ARC-AGI/data/training/007bbfb7.json>
 * TEST gold is touched only after the prediction has been generated.
 * Upstream public file is not downloaded and not embedded in this repo.
 */
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import {propose,p27ShapeCeilingFor3x3To9x9,interpret} from './q3_p28_factorized_operator.mjs';
const eq=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
function fail(s) { throw new Error('P28_SOURCE_CONTRACT_FAIL:'+s); }
export function evaluateOriginal(filePath) {
  const name=path.basename(filePath);
  if(name!=='007bbfb7.json')fail('WRONG_ORIGINAL_TASK_ID');
  const bytes=fs.readFileSync(filePath);
  const data=JSON.parse(bytes.toString('utf8'));
  if(!Array.isArray(data.train)||!Array.isArray(data.test))fail('INVALID_ORIGINAL_TASK');
  const testInputs=data.test.map(pair=>pair.input); // no gold read
  const result=propose(data.train,testInputs);
  let replayOk=result.prediction!==null&&result.trace.generated_AST!==null&&
      data.train.every(p=>eq(interpret(result.trace.generated_AST,p.input),p.output))&&
      testInputs.every((x,i)=>eq(interpret(result.trace.generated_AST,x),result.prediction[i]));
  // The only original TEST target reads follow the frozen prediction above.
  const testGold=data.test.map(pair=>pair.output);
  const exact=replayOk&&eq(result.prediction,testGold);
  return {
    schema:'neumann.q3.p28.selected-original-diagnostic.v1',
    scope:'SELECTED_AFTER_TRAIN_EXAMINATION_NOT_FRESH_UNSEEN',
    source:'fchollet/ARC-AGI@399030444e0ab0cc8b4e199870fb20b863846f34',
    source_file:'data/training/007bbfb7.json',
    source_blob_sha256:createHash('sha256').update(bytes).digest('hex'),
    train_pairs:data.train.length,
    test_pairs:data.test.length,
    exact_test_pass:exact,
    old_p27_shape_ceiling:p27ShapeCeilingFor3x3To9x9(),
    independent_exact_replay:replayOk,
    trace:result.trace,
    original_gold_accessed_after_proposal:true,
    q3_global:'OPEN',q4_global:'OPEN',q7_frontier:'OPEN'
  };
}
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url)) {
  if(!process.argv[2]){process.stderr.write('Expected original public ARC JSON filepath\n');process.exitCode=2;}
  else{try{process.stdout.write(JSON.stringify(evaluateOriginal(process.argv[2]),null,2)+'\n');}
  catch(e){process.stderr.write(String(e)+'\n');process.exitCode=1;}}
}
