/* Fixed 17 operator SOURCE-only selector. No task identifiers used for choosing operators. */
import {op} from "./solver.mjs";
import {op2} from "./adaptation.mjs";
const OPS1=["1bfc4729","1caeab9d","1cf80156","1e0a9b12","1fad071e","2013d3e2","2072aba6","23581191","25d8a9c8"], OPS2=["25ff71a9","27a77e38","27f8ce4f","28bf18c6","29c11459","2dc579da","2de01db2","2dee498d"];
export function dispatch17(d){const matches=[];
for(const id of OPS1.concat(OPS2)){try{const fun=OPS1.includes(id)?op:op2;
if(!d.train.every(ex=>JSON.stringify(fun(id,ex.input))===JSON.stringify(ex.output)))continue;
const pred=d.test.map(ex=>fun(id,ex.input));matches.push({id,pred});
}catch(e){}}
if(!matches.length)return {status:"UNKNOWN_NO_SOURCE_FIT",compatible:[]};
const distinct=[...new Set(matches.map(v=>JSON.stringify(v.pred)))];
if(distinct.length!==1)return {status:"UNKNOWN_AMBIGUOUS",compatible:matches.map(v=>v.id)};
return {status:"SOURCE_FIT_ONLY",compatible:matches.map(v=>v.id),pred:matches[0].pred};}
