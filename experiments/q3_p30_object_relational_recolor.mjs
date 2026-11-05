/* NEUMANN P3.0 | Object-relational label-rule induction (opened mechanism).
 * A source-object graph is generated from each input (four/five plausible
 * connectivity partitions). Instead of selecting a single object as P2.1
 * did, learn a relational predicate and TWO independent object actions.
 * Exact TRAIN full-grid replay + agreement of tied minimum-cost programs.
 *
 * Entire candidate language is still human-specified. This is NOT a new
 * universal opcode discovered autonomously or a cross-family Q3 proof.
 */
import {background,segment,PARTITIONS,valid as validGrid} from "./q3_object_rule_induction_p211.mjs";
export const CONTRACT=Object.freeze({
 schema:"neumann.q3.p30.object-relational-rule-induction.v1",
 maxObjects:24,maxTrain:12,maxTests:5,maxCandidates:25000,
 maxGrid:30,source:"PUBLIC TRAIN pairs only; TEST INPUTS without TEST OUTPUTS",
 teacherCalls:0,neuralCalls:0,newTraining:false,
 hypothesis:"for every detected object: branch on relational predicate then paint or preserve",
 policy:"only independently replayed minimum-cost unambiguous predictions; otherwise ABSTAIN"
});
const eq=(x,y)=>JSON.stringify(x)===JSON.stringify(y);
const cp=g=>g.map(row=>row.slice());
function rank(items,obj,field,kind) {
 const nums=items.map(x=>field(x));
 const n=field(obj);
 const extremum=kind==="min"?Math.min(...nums):Math.max(...nums);
 return n===extremum&&nums.filter(x=>x===extremum).length===1;
}
function features(g,objects,obj){
 const b=obj.b,cols=obj.colors,area=obj.area;
 const flags={
   uniqueLargest:rank(objects,obj,x=>x.area,"max"),
   uniqueSmallest:rank(objects,obj,x=>x.area,"min"),
   uniqueTopmost:rank(objects,obj,x=>x.b.r0,"min"),
   uniqueBottommost:rank(objects,obj,x=>x.b.r1,"max"),
   uniqueLeftmost:rank(objects,obj,x=>x.b.c0,"min"),
   uniqueRightmost:rank(objects,obj,x=>x.b.c1,"max"),
   uniqueWidest:rank(objects,obj,x=>x.width,"max"),
   uniqueTallest:rank(objects,obj,x=>x.height,"max"),
   singleton:area===1,
   areaGt3:area>3,
   widthGtHeight:obj.width>obj.height,
   heightGtWidth:obj.height>obj.width,
   squareBBox:obj.width===obj.height,
   touchesGridEdge:b.r0===0||b.c0===0||b.r1===g.length-1||b.c1===g[0].length-1,
   singleColor:cols.length===1,
   multipleObjects:objects.length>1,
   countAtLeast3:objects.length>=3
 };
 // Color is treated as a value of a source feature, not a task-specific key.
 for(let c=0;c<=9;c++)flags["srcColor"+c]=cols.length===1&&cols[0]===c;
 return flags;
}
const PREDICATES=[
 "uniqueLargest","uniqueSmallest","uniqueTopmost","uniqueBottommost",
 "uniqueLeftmost","uniqueRightmost","uniqueWidest","uniqueTallest",
 "singleton","areaGt3","widthGtHeight","heightGtWidth","squareBBox",
 "touchesGridEdge","singleColor","multipleObjects","countAtLeast3",
 ...Array.from({length:10},(_,i)=>"srcColor"+i)
];
function parse(g,partition) {
 if(!validGrid(g))return null;
 const bg=background(g);
 if(bg===null)return null;
 const objects=segment(g,partition);
 if(!objects.length||objects.length>CONTRACT.maxObjects)return null;
 const seen=new Set();
 for(const obj of objects)for(const [r,c]of obj.pts){
   const id=r+","+c;
   if(seen.has(id)||g[r][c]===bg)return null;
   seen.add(id);
 }
 return {g,partition,objects,items:objects.map(obj=>({obj,flags:features(g,objects,obj)})),seen,bg};
}
function actionsFor(p,output) {
 if(!validGrid(output)||p.g.length!==output.length||p.g[0].length!==output[0].length)return null;
 for(let r=0;r<p.g.length;r++)for(let c=0;c<p.g[0].length;c++)
   if(!p.seen.has(r+","+c)&&p.g[r][c]!==output[r][c])return null;
 return p.items.map(({obj,flags})=>{
   const cells=obj.pts,allowed=new Set();
   if(cells.every(([r,c])=>p.g[r][c]===output[r][c]))allowed.add("copy");
   const vals=new Set(cells.map(([r,c])=>output[r][c]));
   if(vals.size===1)allowed.add("paint:"+vals.values().next().value);
   return {flags,allowed};
 });
}
function executeOnParsed(parsed,ast) {
 if(parsed===null)return null;
 const out=cp(parsed.g);
 for(const {obj,flags}of parsed.items){
   const action=flags[ast.predicate]?ast.when:ast.otherwise;
   if(action==="copy")continue;
   if(!/^paint:[0-9]$/.test(action))return null;
   const value=Number(action.slice(-1));
   for(const [r,c]of obj.pts)out[r][c]=value;
 }
 return out;
}
export function execute(ast,input){
 if(!ast||ast.kind!=="object-relational-paint"||!PARTITIONS.includes(ast.partition)||
    !PREDICATES.includes(ast.predicate)||typeof ast.when!=="string"||typeof ast.otherwise!=="string")return null;
 const parsed=parse(input,ast.partition);
 return executeOnParsed(parsed,ast);
}
export function synthesize(train,testInputs) {
 const start=process.hrtime.bigint();
 const trace={schema:CONTRACT.schema,partitions:0,trainObjects:0,
   consideredPredicates:0,candidatePrograms:0,trainConsistent:0,
   executable:0,minCost:null,tiedPrograms:0,distinctTestPredictions:0,
   ast:null,reason:null,wallMs:0};
 const finish=(prediction,reason)=>{
   trace.reason=reason;
   trace.wallMs=Number(process.hrtime.bigint()-start)/1e6;
   return {prediction,trace};
 };
 if(!Array.isArray(train)||!train.length||train.length>CONTRACT.maxTrain||
   !train.every(x=>x&&validGrid(x.input)&&validGrid(x.output))||
   !Array.isArray(testInputs)||!testInputs.length||testInputs.length>CONTRACT.maxTests||
   !testInputs.every(validGrid))return finish(null,"INVALID_INPUT");
 let best=Infinity,candidates=new Map(),ties=0;
 const admit=(ast,cost,pred)=>{
   if(cost<best){best=cost;candidates=new Map();ties=0;}
   if(cost!==best)return;
   const key=JSON.stringify(pred);
   if(!candidates.has(key))candidates.set(key,{ast,pred});
   ties++;
 };
 for(const partition of PARTITIONS){
   const samples=[],pts=[];
   let eligible=true;
   for(const example of train) {
     const parsed=parse(example.input,partition);
     const actions=parsed&&actionsFor(parsed,example.output);
     if(!actions){eligible=false;break;}
     samples.push(...actions);pts.push(parsed);
   }
   if(!eligible||!samples.length)continue;
   const ptests=testInputs.map(x=>parse(x,partition));
   if(ptests.some(x=>x===null))continue;
   trace.partitions++;
   trace.trainObjects+=samples.length;
   const colors=new Set();
   for(const sample of samples)for(const a of sample.allowed)if(a.startsWith("paint:"))colors.add(a);
   const acts=["copy",...[...colors].sort()];
   for(const predicate of PREDICATES) {
     const yes=samples.filter(x=>x.flags[predicate]),no=samples.filter(x=>!x.flags[predicate]);
     if(!yes.length||!no.length)continue; // Every branch must be witnessed in TRAIN.
     trace.consideredPredicates++;
     for(const when of acts)for(const otherwise of acts){
       trace.candidatePrograms++;
       if(trace.candidatePrograms>CONTRACT.maxCandidates)return finish(null,"PROGRAM_BUDGET");
       if(!yes.every(x=>x.allowed.has(when))||!no.every(x=>x.allowed.has(otherwise)))continue;
       const ast={kind:"object-relational-paint",partition,predicate,when,otherwise};
       if(!train.every(x=>eq(execute(ast,x.input),x.output)))continue;
       trace.trainConsistent++;
       const cost=3+(predicate.startsWith("srcColor")?2:0)+
         (when.startsWith("paint:")?1:0)+(otherwise.startsWith("paint:")?1:0)+
         (when===otherwise?1:0);
       if(cost>best)continue;
       const pred=ptests.map(p=>executeOnParsed(p,ast));
       if(pred.some(x=>x===null))continue;
       trace.executable++;
       if(!testInputs.every((x,i)=>eq(execute(ast,x),pred[i])))throw Error("EXECUTABLE_TEST_REPLAY_DRIFT");
       admit(ast,cost,pred);
     }
   }
 }
 trace.minCost=Number.isFinite(best)?best:null;
 trace.tiedPrograms=ties;trace.distinctTestPredictions=candidates.size;
 if(!candidates.size)return finish(null,"NO_TRAIN_FITTING_OBJECT_RELATION");
 if(candidates.size>1)return finish(null,"AMBIGUOUS_MIN_COST_OBJECT_RELATION");
 const only=candidates.values().next().value;
 trace.ast=only.ast;
 return finish(only.pred,null);
}
