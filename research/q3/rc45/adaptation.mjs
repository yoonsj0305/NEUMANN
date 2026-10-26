/* RC45.2 GPT-6 chat proposed 8 new PUBLIC training operators, not NEUMANN own-weight. Source-only FIRST freeze. */
function z2(h,w){return Array.from({length:h},()=>Array(w).fill(0))}

function s2(g){if(!Array.isArray(g)||!g.length||!Array.isArray(g[0])||g.some(r=>r.length!==g[0].length))throw Error("shape");return [g.length,g[0].length]}

function op2(id,g){
const [h,w]=s2(g);
if(id==="25ff71a9")return [Array(w).fill(0),...g.slice(0,h-1).map(x=>[...x])];
if(id==="27a77e38"){const sep=g.findIndex(row=>row.every(v=>v===5));if(sep<1||sep>=h-1)throw Error("separator");const count=new Map();for(let r=0;r<sep;r++)for(const v of g[r])if(v&&v!==5)count.set(v,(count.get(v)||0)+1);const ranked=[...count].sort((a,b)=>b[1]-a[1]);if(!ranked.length||ranked.length>1&&ranked[0][1]===ranked[1][1])throw Error("tie");const out=g.map(r=>[...r]);out[h-1][Math.floor(w/2)]=ranked[0][0];return out}
if(id==="27f8ce4f"){if(h!==3||w!==3)throw Error("3x3");const counts=new Map();for(const row of g)for(const v of row)counts.set(v,(counts.get(v)||0)+1);const ranked=[...counts].sort((a,b)=>b[1]-a[1]);if(ranked.length>1&&ranked[0][1]===ranked[1][1])throw Error("tie");const color=ranked[0][0],out=z2(9,9);for(let r=0;r<3;r++)for(let c=0;c<3;c++)if(g[r][c]===color)for(let i=0;i<3;i++)for(let j=0;j<3;j++)out[3*r+i][3*c+j]=g[i][j];return out}
if(id==="28bf18c6"){const ps=[];for(let r=0;r<h;r++)for(let c=0;c<w;c++)if(g[r][c])ps.push([r,c]);if(!ps.length)throw Error("empty");const r0=Math.min(...ps.map(p=>p[0])),r1=Math.max(...ps.map(p=>p[0])),c0=Math.min(...ps.map(p=>p[1])),c1=Math.max(...ps.map(p=>p[1]));return g.slice(r0,r1+1).map(row=>{const ss=row.slice(c0,c1+1);return ss.concat(ss)})}
if(id==="29c11459"){if(w%2!==1)throw Error("odd width");const out=g.map(row=>[...row]);for(let r=0;r<h;r++){const vals=g[r].map((v,c)=>({v,c})).filter(x=>x.v!==0);if(!vals.length)continue;if(vals.length!==2||vals[0].c!==0||vals[1].c!==w-1)throw Error("endpoints");for(let c=0;c<w;c++)out[r][c]=c<(w-1)/2?vals[0].v:c>(w-1)/2?vals[1].v:5;}return out}
if(id==="2dc579da"){if(h!==w||h%2!==1||h<5)throw Error("odd square");const m=(h-1)/2,d=g[m][m];if(!g[m].every(v=>v===d)||!g.every(r=>r[m]===d))throw Error("divider");const cs=new Map();for(let r=0;r<h;r++)for(let c=0;c<w;c++)if(r!==m&&c!==m)cs.set(g[r][c],(cs.get(g[r][c])||0)+1);const ranked=[...cs].sort((a,b)=>b[1]-a[1]);if(ranked.length>1&&ranked[0][1]===ranked[1][1])throw Error("bg tie");const bg=ranked[0][0],choices=[];for(const [r0,c0] of [[0,0],[0,m+1],[m+1,0],[m+1,m+1]]){const q=g.slice(r0,r0+m).map(row=>row.slice(c0,c0+m));if(q.some(row=>row.some(v=>v!==bg)))choices.push(q)}if(choices.length!==1)throw Error("ambiguous quadrants");return choices[0]}
if(id==="2de01db2"){return g.map(row=>{const cs=new Map();for(const v of row)if(v)cs.set(v,(cs.get(v)||0)+1);if(!cs.size)throw Error("no dominant");const best=[...cs].sort((a,b)=>b[1]-a[1])[0][0];return row.map(v=>v===best?0:best)})}
if(id==="2dee498d"){for(let p=1;p<w;p++)if(w%p===0&&g.every(row=>{const base=row.slice(0,p),rev=[...base].reverse();for(let c=0;c<w;c+=p){const slice=row.slice(c,c+p);if(JSON.stringify(slice)!==JSON.stringify(base)&&JSON.stringify(slice)!==JSON.stringify(rev))return false}return true}))return g.map(row=>row.slice(0,p));throw Error("no common chunk")}
throw Error("ABSTAIN_NEW_OPERATOR");
}
export {op2};
