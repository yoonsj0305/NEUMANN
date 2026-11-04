/* NEUMANN P1.3 first GPT-6 teacher proposal: four pure, task-specific executable
   rules derived from public TRAIN examples and TEST INPUTS ONLY.
   No task-id lookup in solvers, no test expected outputs embedded.
   This is an external frontier teacher, not learned NEUMANN or novel opcode proof.
*/
const copy=g=>g.map(row=>row.slice());
const valid=g=>Array.isArray(g)&&g.length>0&&g.length<=30&&Array.isArray(g[0])&&g[0].length>0&&g[0].length<=30&&g.every(r=>Array.isArray(r)&&r.length===g[0].length&&r.every(v=>Number.isInteger(v)&&v>=0&&v<=9));
const fail=()=>null;

function shiftDown(input){
 if(!valid(input))return fail();
 const w=input[0].length;
 return [Array(w).fill(0),...input.slice(0,-1).map(r=>r.slice())];
}
function intersectEmptyHalves(input){
 if(!valid(input))return fail();
 const h=input.length,w=input[0].length,n=Math.floor(h/2);
 if(h!==2*n+1||n<1||!input[n].every(v=>v===4))return fail();
 return Array.from({length:n},(_,r)=>Array.from({length:w},(_,c)=>input[r][c]===0&&input[n+1+r][c]===0?3:0));
}
function moveMarkedSudokuPatch(input){
 if(!valid(input)||input.length!==11||input[0].length!==11)return fail();
 for(let i=0;i<11;i++)if((i%4===3)&&!input[i].every(v=>v===5))return fail();
 for(let r=0;r<11;r++)for(let c=0;c<11;c++)if(c%4===3&&input[r][c]!==5)return fail();
 const marks=[];
 for(let r=0;r<11;r++)for(let c=0;c<11;c++)if(input[r][c]===4)marks.push([r,c]);
 if(marks.length!==1)return fail();
 const [r,c]=marks[0];if(r%4===3||c%4===3)return fail();
 const srcR=Math.floor(r/4)*4,srcC=Math.floor(c/4)*4;
 const dstR=(r%4)*4,dstC=(c%4)*4;
 if(dstR>8||dstC>8)return fail();
 const out=Array.from({length:11},(_,rr)=>Array.from({length:11},(_,cc)=>rr%4===3||cc%4===3?5:0));
 for(let dr=0;dr<3;dr++)for(let dc=0;dc<3;dc++)out[dstR+dr][dstC+dc]=input[srcR+dr][srcC+dc];
 return out;
}
function motifReplicator(input){
 if(!valid(input))return fail();
 const h=input.length,w=input[0].length,count=new Map();
 for(const row of input)for(const v of row)count.set(v,(count.get(v)||0)+1);
 const bg=[...count.entries()].sort((a,b)=>b[1]-a[1])[0][0];
 const dirs8=[[1,0],[-1,0],[0,1],[0,-1],[1,1],[1,-1],[-1,1],[-1,-1]];
 const seen=new Set(),key=(r,c)=>r+","+c,groups=[];
 for(let r=0;r<h;r++)for(let c=0;c<w;c++){
  if(input[r][c]===bg||seen.has(key(r,c)))continue;
  let stack=[[r,c]],pts=[];seen.add(key(r,c));
  while(stack.length){const [rr,cc]=stack.pop();pts.push([rr,cc]);for(const [dr,dc] of dirs8){const nr=rr+dr,nc=cc+dc;if(nr<0||nc<0||nr>=h||nc>=w||input[nr][nc]===bg||seen.has(key(nr,nc)))continue;seen.add(key(nr,nc));stack.push([nr,nc]);}}
  groups.push(pts);
 }
 const motifs=[];
 for(const pts of groups){
  let rs=pts.map(p=>p[0]),cs=pts.map(p=>p[1]),r0=Math.min(...rs),r1=Math.max(...rs),c0=Math.min(...cs),c1=Math.max(...cs);
  if(r1-r0!==2||c1-c0!==2)continue;
  let motif=Array.from({length:3},(_,r)=>Array.from({length:3},(_,c)=>input[r0+r][c0+c]));
  const colors=[...new Set(pts.map(([r,c])=>input[r][c]))];if(colors.length!==3)continue;
  const pointSet=new Set(pts.map(([r,c])=>key(r,c)));
  const exclusive=colors.filter(color=>{
    for(let r=0;r<h;r++)for(let c=0;c<w;c++)if(input[r][c]===color&&!pointSet.has(key(r,c)))return false;
    return true;
  });
  if(exclusive.length!==1)continue;
  const fill=exclusive[0],ends=colors.filter(c=>c!==fill).sort((a,b)=>a-b);
  const endpoints=ends.map(color=>pts.filter(([r,c])=>input[r][c]===color).map(([r,c])=>[r-r0,c-c0]));
  if(endpoints.some(x=>x.length!==1))continue;
  const pa=endpoints[0][0],pb=endpoints[1][0];
  if(![0,2].includes(pa[0])||![0,2].includes(pa[1])||pa[0]+pb[0]!==2||pa[1]+pb[1]!==2)continue;
  motifs.push({pointSet,motif,fill,ends,pa});
 }
 if(motifs.length!==1)return fail();
 const m=motifs[0],paint=copy(input);
 // Recover all other source-color square endpoints without looking at any output.
 function blocks(color){
  const visited=new Set(),out=[],dirs=[[1,0],[-1,0],[0,1],[0,-1]];
  for(let r=0;r<h;r++)for(let c=0;c<w;c++){
   if(input[r][c]!==color||m.pointSet.has(key(r,c))||visited.has(key(r,c)))continue;
   const stack=[[r,c]],p=[];visited.add(key(r,c));
   while(stack.length){const [rr,cc]=stack.pop();p.push([rr,cc]);for(const [dr,dc]of dirs){const nr=rr+dr,nc=cc+dc;if(nr<0||nc<0||nr>=h||nc>=w||input[nr][nc]!==color||m.pointSet.has(key(nr,nc))||visited.has(key(nr,nc)))continue;visited.add(key(nr,nc));stack.push([nr,nc]);}}
   const rs=p.map(q=>q[0]),cs=p.map(q=>q[1]),r0=Math.min(...rs),c0=Math.min(...cs),r1=Math.max(...rs),c1=Math.max(...cs),size=r1-r0+1;
   if(size!==c1-c0+1||p.length!==size*size)return null;
   out.push({r:r0,c:c0,k:size,id:out.length});
  }return out;
 }
 const A=blocks(m.ends[0]),B=blocks(m.ends[1]);if(!A||!B||A.length!==B.length||!A.length)return fail();
 const used=new Set();
 for(const a of A){
  const candidates=B.filter(b=>!used.has(b.id)&&b.k===a.k&&Math.abs(b.r-a.r)===2*a.k&&Math.abs(b.c-a.c)===2*a.k);
  if(candidates.length!==1)return fail();
  const b=candidates[0],k=a.k;used.add(b.id);
  const top=Math.min(a.r,b.r),left=Math.min(a.c,b.c);
  const qAR=a.r<b.r?0:2,qAC=a.c<b.c?0:2;
  const invertR=qAR!==m.pa[0],invertC=qAC!==m.pa[1];
  for(let rr=0;rr<3;rr++)for(let cc=0;cc<3;cc++)if(m.motif[rr][cc]===m.fill){
   const fr=invertR?2-rr:rr,fc=invertC?2-cc:cc;
   for(let dr=0;dr<k;dr++)for(let dc=0;dc<k;dc++){
    const R=top+fr*k+dr,C=left+fc*k+dc;
    if(R<0||C<0||R>=h||C>=w||paint[R][C]!==bg)return fail();
    paint[R][C]=m.fill;
   }
  }
 }
 return used.size===B.length?paint:fail();
}
const SOURCE={
 "6aa20dc0":motifReplicator,
 "25ff71a9":shiftDown,
 "6430c8c4":intersectEmptyHalves,
 "6d0160f0":moveMarkedSudokuPatch,
};
export {SOURCE,valid};
