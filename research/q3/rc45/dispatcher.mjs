/* Frozen SOURCE-only consensus dispatcher. No ARC task-id used for routing. */
import {op} from "./solver.mjs";
const OPS=["1bfc4729","1caeab9d","1cf80156","1e0a9b12","1fad071e","2013d3e2","2072aba6","23581191","25d8a9c8"];
export function dispatch(data){const valid=[];
for(const name of OPS){try{
if(!data.train.every(e=>JSON.stringify(op(name,e.input))===JSON.stringify(e.output)))continue;
const pred=data.test.map(e=>op(name,e.input));valid.push({name,pred});
}catch(e){}}
if(!valid.length)return {status:"UNKNOWN_NO_OPERATOR",compatible:[]};
const candidates=[...new Set(valid.map(v=>JSON.stringify(v.pred)))];
if(candidates.length!==1)return {status:"UNKNOWN_DISAGREE",compatible:valid.map(v=>v.name)};
return {status:"SOURCE_FIT_UNCERTIFIED",compatible:valid.map(v=>v.name),pred:valid[0].pred};}
