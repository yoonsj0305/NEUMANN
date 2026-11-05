import {solve as P23} from './q3_typed_guard_ast_p23.mjs';
import {solve as P24} from './q3_cached_typed_guard_p24.mjs';
let state=20261105;const rand=()=>((state=(Math.imul(state,1664525)+1013904223)>>>0)/4294967296);
function grid(h,w){return Array.from({length:h},()=>Array.from({length:w},()=>rand()<.67?0:1+Math.floor(rand()*5)));}
function target(g,kind){const H=g.length,W=g[0].length;
 if(kind===0)return g.map(row=>row.slice());
 if(kind===1)return g.map(row=>row.map(v=>v===0?4:v));
 if(kind===2)return g.map(row=>row.map((v,i)=>i?row[i-1]||2:2));
 if(kind===3&&W%2===0)return g.map(row=>row.slice(0,W/2).map((v,i)=>v===row[i+W/2]?4:0));
 if(kind===4&&W%2===0)return g.map(row=>row.slice(0,W/2).map((v,i)=>v===0&&row[i+W/2]===0?3:0));
 if(kind===5){const h=H,w=W;return Array.from({length:h},()=>Array(w).fill(8));}
 return Array.from({length:Math.max(1,H-1)},()=>Array(Math.max(1,W-1)).fill(0));
}
const errors=[];let aNs=0,bNs=0,pass=0,first={};
for(let i=0;i<56;i++){
 const h=i%7===0?15:5+i%6,w=i%5===0?16:6+i%7,kind=i%7;
 const train=Array.from({length:2},()=>{const g=grid(h,w);return {input:g,output:target(g,kind)};});
 const test=grid(h,w),a0=process.hrtime.bigint(),a=P23(train,[test]),a1=process.hrtime.bigint(),b=P24(train,[test]),b1=process.hrtime.bigint();
 aNs+=Number(a1-a0);bNs+=Number(b1-a1);
 const x={prediction:a.prediction,abstention:a.trace.abstention,fit:a.trace.exact_fit_programs,AST:a.trace.selected_AST};
 const y={prediction:b.prediction,abstention:b.trace.abstention,fit:b.trace.exact_fit_programs,AST:b.trace.selected_AST};
 if(JSON.stringify(x)!==JSON.stringify(y)){errors.push({i,kind,a:x,b:y});}
 else pass++;
}
console.log(JSON.stringify({tested:56,pass,failed:errors.length,P23_ms:aNs/1e6,P24_ms:bNs/1e6,ratio:aNs/bNs,errors:errors.slice(0,2)}));
if(errors.length)process.exit(1);
