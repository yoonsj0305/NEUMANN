/* NEUMANN P2.3 | teacher-free typed rule induction. Original test gold not imported.
 * Bounded, deterministic, task-local SYMBOLIC synthesis, not across-task neural learning.
 * No task IDs, dataset fingerprints or task-specific complete executable solutions.
 */
export const CONTRACT = Object.freeze({schema:'neumann.q3.p23.typed-guard.v1', maxGrid:30,
  maxGuardTerms:2, source:'train+test.inputs-only', teacherCalls:0, neuralCalls:0});
const enc=(r,c)=>r+','+c;
const inGrid=g=>Array.isArray(g)&&g.length>0&&g.length<=30&&Array.isArray(g[0])&&g[0].length>0&&g[0].length<=30&&g.every(row=>Array.isArray(row)&&row.length===g[0].length&&row.every(v=>Number.isInteger(v)&&v>=0&&v<=9));
const eq=(a,b)=>inGrid(a)&&inGrid(b)&&a.length===b.length&&a.every((row,r)=>row.every((v,c)=>v===b[r][c]));
const clone=g=>g.map(row=>row.slice());
const directions=[[1,0],[-1,0],[0,1],[0,-1]];
function components(g,matcher){
  if(!inGrid(g))return [];
  const seen=new Set(),out=[],H=g.length,W=g[0].length;
  for(let r=0;r<H;r++)for(let c=0;c<W;c++){
    if(!matcher(g[r][c])||seen.has(enc(r,c)))continue;
    const queue=[[r,c]],pts=[];seen.add(enc(r,c));
    for(let i=0;i<queue.length;i++){const [y,x]=queue[i];pts.push([y,x]);
      for(const [dy,dx]of directions){const yy=y+dy,xx=x+dx;if(yy<0||xx<0||yy>=H||xx>=W||seen.has(enc(yy,xx))||!matcher(g[yy][xx]))continue;seen.add(enc(yy,xx));queue.push([yy,xx]);}}
    const rs=pts.map(p=>p[0]),cs=pts.map(p=>p[1]);const b=[Math.min(...rs),Math.min(...cs),Math.max(...rs),Math.max(...cs)];
    const colors=new Set(pts.map(([y,x])=>g[y][x]));out.push({pts,area:pts.length,box:b,colors:colors.size});
  }return out;
}
function bboxNZ(g){const cells=[];for(let y=0;y<g.length;y++)for(let x=0;x<g[0].length;x++)if(g[y][x]!==0)cells.push([y,x]);
 if(!cells.length)return null;return [Math.min(...cells.map(p=>p[0])),Math.min(...cells.map(p=>p[1])),Math.max(...cells.map(p=>p[0])),Math.max(...cells.map(p=>p[1]))];}
function modeOutput(mode,g){
  if(!inGrid(g))return null;
  const H=g.length,W=g[0].length;
  if(mode==='same')return {H,W};
  if(mode==='half_lr'&&W%2===0)return {H,W:W/2};
  if(mode==='half_tb'&&H%2===0)return {H:H/2,W};
  if(mode.startsWith('shift_'))return {H,W};
  return null;
}
function source(mode,g,r,c){
  const H=g.length,W=g[0].length;
  if(mode==='same')return {a:g[r][c],b:0,r,c,H,W,g};
  if(mode==='half_lr')return {a:g[r][c],b:g[r][c+W/2],r,c,H,W:W/2,g};
  if(mode==='half_tb')return {a:g[r][c],b:g[r+H/2][c],r,c,H:H/2,W,g};
  const parts=mode.split('_'),dy=+parts[1],dx=+parts[2];const sy=r-dy,sx=c-dx;
  return {a:sy>=0&&sx>=0&&sy<H&&sx<W?g[sy][sx]:0,b:g[r][c],r,c,H,W,g};
}
function primitiveFacts(c){
  const {g,r,col,H,W,a,b}= {g:c.g,r:c.r,col:c.c,H:c.H,W:c.W,a:c.a,b:c.b};
  const row=g[r]||[],colValues=g.map(row=>row[c.c]).filter(v=>v!==undefined);
  const left=row.slice(0,c.c).some(v=>v!==0),right=row.slice(c.c+1).some(v=>v!==0);
  const above=colValues.slice(0,c.r).some(v=>v!==0),below=colValues.slice(c.r+1).some(v=>v!==0);
  const count4=directions.reduce((s,[dy,dx])=>s+(g[c.r+dy]?.[c.c+dx]!==undefined&&g[c.r+dy][c.c+dx]!==0?1:0),0);
  const border=c.r===0||c.c===0||c.r===H-1||c.c===W-1;
  const box=bboxNZ(g),inside=box!==null&&c.r>=box[0]&&c.r<=box[2]&&c.c>=box[1]&&c.c<=box[3];
  const facts={
    'aZero':a===0,'aNonzero':a!==0,'bZero':b===0,'bNonzero':b!==0,
    'bothZero':a===0&&b===0,'bothNonzero':a!==0&&b!==0,'eitherZero':a===0||b===0,
    'aEqualsB':a===b,'aDiffersB':a!==b,'xorNonzero':(a===0)!==(b===0),
    'rowBetween':left&&right,'rowZeroBetween':g[c.r][c.c]===0&&left&&right,
    'colBetween':above&&below,'colZeroBetween':g[c.r][c.c]===0&&above&&below,
    'rowHasNZ':left||right||g[c.r][c.c]!==0,'colHasNZ':above||below||g[c.r][c.c]!==0,
    'border':border,'notBorder':!border,'top':c.r===0,'bottom':c.r===H-1,
    'left':c.c===0,'right':c.c===W-1,'insideNZBox':inside,'outsideNZBox':!inside,
    'adj4AtLeast2':count4>=2,'adj4AtLeast1':count4>=1,'adj4None':count4===0,
    'rowEven':c.r%2===0,'colEven':c.c%2===0,
  };
  return facts;
}
function factSet(train,mode,inputs=null){
  const all=inputs===null?train.map(x=>x.input):inputs;
  const cases=[];
  for(let k=0;k<all.length;k++){
    const g=all[k],sh=modeOutput(mode,g);if(!sh)return null;
    if(inputs===null&&(train[k].output.length!==sh.H||train[k].output[0].length!==sh.W))return null;
    for(let r=0;r<sh.H;r++)for(let c=0;c<sh.W;c++){
      const ctx=source(mode,g,r,c);const facts=primitiveFacts(ctx);
      cases.push({ctx,facts,target:inputs===null?train[k].output[r][c]:null});
    }
  }
  return cases;
}
const reprValue=(action,ctx)=>action==='a'?ctx.a:action==='b'?ctx.b:Number(action.slice(1));
function programCell(plan,ctx,facts){
  const evalCond=term=>term[0]==='!'?!facts[term.slice(1)]:!!facts[term];
  let on=false;
  if(plan.guard.kind==='always')on=true;
  else if(plan.guard.kind==='literal')on=evalCond(plan.guard.terms[0]);
  else if(plan.guard.kind==='and')on=plan.guard.terms.every(evalCond);
  else if(plan.guard.kind==='or')on=plan.guard.terms.some(evalCond);
  return reprValue(on?plan.alt:plan.base,ctx);
}
function execute(plan,g){
  const sh=modeOutput(plan.mode,g);if(!sh)return null;const out=[];
  for(let r=0;r<sh.H;r++){const row=[];for(let c=0;c<sh.W;c++){const ctx=source(plan.mode,g,r,c);const v=programCell(plan,ctx,primitiveFacts(ctx));if(!Number.isInteger(v)||v<0||v>9)return null;row.push(v);}out.push(row);}return out;
}
const trimModes=['same','half_lr','half_tb','shift_0_-1','shift_0_1','shift_-1_0','shift_1_0'];
function bitmap(features,terms){let bits=0n;for(let i=0;i<features.length;i++){const [name,not]=terms;let v=!!features[i][name];if(not)v=!v;if(v)bits|=1n<<BigInt(i);}return bits;}
function synthesizeConditionals(train,testInputs,trace){
  const candidates=[],palette=[...new Set(train.flatMap(p=>p.output.flat()))].sort((a,b)=>a-b);
  for(const mode of trimModes){const samples=factSet(train,mode);if(!samples)continue;
    const fkeys=Object.keys(samples[0].facts);let full=(1n<<BigInt(samples.length))-1n;
    const features=[];for(const name of fkeys){const pos=bitmap(samples.map(x=>x.facts),[name,false]);if(pos!==0n&&pos!==full)features.push({name,mask:pos,cost:1.0+(name.includes('Even')?1.0:0)});}
    const actions=['a',...(mode==='half_lr'||mode==='half_tb'?['b']:[]),...palette.map(v=>'c'+v)];
    const seenActionPairs=new Set();
    for(const base of actions)for(const alt of actions){if(base===alt)continue;
      const pair=base+'|'+alt;if(seenActionPairs.has(pair))continue;seenActionPairs.add(pair);
      let must1=0n,must0=0n,valid=true,discriminating=false;
      for(let i=0;i<samples.length;i++){
        const el=samples[i],p=reprValue(base,el.ctx),q=reprValue(alt,el.ctx),y=el.target;
        const isP=p===y,isQ=q===y;
        if(!isP&&!isQ){valid=false;break;}
        if(isP&&!isQ)must0|=1n<<BigInt(i);
        else if(!isP&&isQ){must1|=1n<<BigInt(i);discriminating=true;}
      }
      if(!valid)continue;
      trace.action_pair_feasible++;
      const actionCost=(base==='a'?0.15:base==='b'?0.5:0.8)+(alt.startsWith('c')?0.8:0.4);
      const modeCost=mode==='same'?0:mode.startsWith('half')?1.5:1.1;
      function add(mask,guard,guardCost){trace.guard_attempts++;
        if((mask&must1)!==must1||(mask&must0)!==0n)return;
        // Every fitted candidate is exactly replayed, independently of bitset shortcuts.
        const plan={kind:'conditional',mode,base,alt,guard,score:modeCost+actionCost+guardCost};
        trace.program_candidates_exact_replay++;
        if(train.every(p=>eq(execute(plan,p.input),p.output)))candidates.push(plan);
      }
      if(must0===0n){add(full,{kind:'always',terms:[]},0.2);}
      if(!discriminating)continue;
      for(let a=0;a<features.length;a++){
        const x=features[a];add(x.mask,{kind:'literal',terms:[x.name]},x.cost);
        add(full^x.mask,{kind:'literal',terms:['!'+x.name]},x.cost+.25);
      }
      // Generate new AND/OR expressions instead of choosing a prewritten whole operator.
      for(let a=0;a<features.length;a++)for(let b=a+1;b<features.length;b++){
        const x=features[a],y=features[b];const cost=x.cost+y.cost;
        add(x.mask&y.mask,{kind:'and',terms:[x.name,y.name]},cost+0.35);
        add(x.mask|y.mask,{kind:'or',terms:[x.name,y.name]},cost+0.45);
        // Negated conjunction also safely compiled by the same AST interpreter.
        add(x.mask&(full^y.mask),{kind:'and',terms:[x.name,'!'+y.name]},cost+.6);
        add((full^x.mask)&y.mask,{kind:'and',terms:['!'+x.name,y.name]},cost+.6);
      }
    }
  }
  return candidates;
}
function cropPlans(train){const plans=[];
  const metrics=['area','colors','height','width'];
  for(const metric of metrics){const values=new Set();for(const p of train){for(const obj of components(p.input,v=>v!==0)){
    const [r0,c0,r1,c1]=obj.box;values.add(metric==='height'?r1-r0+1:metric==='width'?c1-c0+1:obj[metric]);}}
    for(const v of values){const plan={kind:'crop',metric,value:v,score:3.5+(metric==='colors'?0:1)};
      if(train.every(p=>eq(executeExtra(plan,p.input),p.output)))plans.push(plan);
    }
  }
  return plans;
}
function executeExtra(plan,g){if(!inGrid(g))return null;
  if(plan.kind==='crop'){
    const found=components(g,v=>v!==0).filter(obj=>{const [r0,c0,r1,c1]=obj.box;const k=plan.metric==='height'?r1-r0+1:plan.metric==='width'?c1-c0+1:obj[plan.metric];return k===plan.value;});
    if(found.length!==1)return null;
    const [r0,c0,r1,c1]=found[0].box;return g.slice(r0,r1+1).map(row=>row.slice(c0,c1+1));
  }
  if(plan.kind==='count'){
    const count=components(g,v=>v===plan.inputColor).length+plan.offset;
    if(count<1||count>30)return null;
    return plan.axis==='column'?Array.from({length:count},()=>[plan.outputColor]):[Array(count).fill(plan.outputColor)];
  }
  return null;
}
function countPlans(train){const plans=[];
 const allInputColors=[...new Set(train.flatMap(p=>p.input.flat()))];
 for(const sourceColor of allInputColors)for(let offset=-2;offset<=2;offset++)for(const axis of ['column','row']){
  const colors=[...new Set(train.flatMap(p=>p.output.flat()))];
  for(const outputColor of colors){const p={kind:'count',inputColor:sourceColor,offset,axis,outputColor,score:2.8+Math.abs(offset)*.5};
   if(train.every(ex=>eq(executeExtra(p,ex.input),ex.output)))plans.push(p);
  }
 }
 return plans;
}
function solve(train,testInputs){
 const started=Date.now(),trace={schema:CONTRACT.schema,original_train_examples:train?.length||0,action_pair_feasible:0,
  guard_attempts:0,program_candidates_exact_replay:0,exact_fit_programs:0,min_score_ties:0,original_test_program_evals:0,
  selected_AST:null,abstention:null,wall_ms:null,neural_forward_calls:0,teacher_calls:0};
 if(!Array.isArray(train)||train.length===0||!train.every(p=>inGrid(p.input)&&inGrid(p.output))||!Array.isArray(testInputs)||testInputs.length===0||!testInputs.every(inGrid)){
  trace.abstention='INVALID_INPUT';trace.wall_ms=Date.now()-started;return {prediction:null,trace};
 }
 const all=synthesizeConditionals(train,testInputs,trace).concat(cropPlans(train),countPlans(train));
 trace.exact_fit_programs=all.length;
 if(!all.length){trace.abstention='NO_TRAIN_CONSISTENT_PROGRAM';trace.wall_ms=Date.now()-started;return {prediction:null,trace};}
 all.sort((a,b)=>a.score-b.score||JSON.stringify(a).localeCompare(JSON.stringify(b)));
 // A single parsimonious score level; never consult gold to select among hypotheses.
 const best=all[0].score,ties=all.filter(p=>Math.abs(p.score-best)<1e-9);trace.min_score_ties=ties.length;
 const preds=new Map();let unsupported=false;
 for(const ast of ties){const grids=[];for(const input of testInputs){trace.original_test_program_evals++;const out=ast.kind==='conditional'?execute(ast,input):executeExtra(ast,input);if(!inGrid(out)){unsupported=true;break;}grids.push(out);}
  if(grids.length!==testInputs.length)continue;preds.set(JSON.stringify(grids),{grids,ast});
 }
 let prediction=null;
 if(unsupported)trace.abstention='UNSUPPORTED_TEST_EXECUTION';
 else if(preds.size===0)trace.abstention='NO_VALID_TEST_PROGRAM';
 else if(preds.size>1)trace.abstention='AMBIGUOUS_MINIMUM_DESCRIPTION_LENGTH';
 else {const item=preds.values().next().value;prediction=item.grids;trace.selected_AST=item.ast;}
 trace.wall_ms=Date.now()-started;return {prediction,trace};
}
export {inGrid,eq,components,modeOutput,source,primitiveFacts,execute,executeExtra,solve};
