/** Export zero-gold P2.8 proof certificate for independent Python verification. */
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {propose} from './q3_p28_factorized_operator.mjs';
export function exportCertificate(task){
 const inputs=task.test.map(x=>x.input);
 const p=propose(task.train,inputs);
 if(p.prediction===null||p.trace.generated_AST===null)return null;
 return {schema:'neumann.q3.p28.proof-certificate.v1',
  ast:p.trace.generated_AST, train:task.train.map(x=>({input:x.input,output:x.output})),
  test_inputs:inputs,predicted_test:p.prediction};
}
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 if(!process.argv[2]){process.stderr.write('Expected task JSON path\n');process.exitCode=2;}
 else{try{const task=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
  const cert=exportCertificate(task);if(!cert){process.stderr.write('ABSTAIN: No unambiguous program\n');process.exitCode=3;}
  else process.stdout.write(JSON.stringify(cert,null,2)+'\n');
 }catch(e){process.stderr.write(String(e)+'\n');process.exitCode=1;}}
}
