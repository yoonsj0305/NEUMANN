/* RC45 GPT-6 CHAT authored, PUBLIC ARC TRAINING tasks. NOT NEUMANN own weights. First source-only code before looking at test gold. Source gated! */
function zero(h,w){return Array.from({length:h},()=>Array(w).fill(0))}

function shape(g){if(!Array.isArray(g)||!g.length||!Array.isArray(g[0])||!g[0].length||g.some(r=>r.length!==g[0].length))throw Error("shape");return [g.length,g[0].length]}

function op(id,g){
const [h,w]=shape(g);
if(id==="1bfc4729"){const p=[];for(let r=0;r<h;r++)for(let c=0;c<w;c++)if(g[r][c])p.push({r,c,v:g[r][c]});if(p.length!==2||p[0].r===p[1].r)throw Error("points");p.sort((a,b)=>a.r-b.r);const out=zero(h,w);for(let r=0;r<h;r++){const v=(Math.abs(r-p[0].r)<=Math.abs(r-p[1].r)?p[0]:p[1]).v;for(let c=0;c<w;c++)if(c===0||c===w-1||[0,p[0].r,p[1].r,h-1].includes(r))out[r][c]=v;}return out}
if(id==="1caeab9d"){const by=new Map();for(let r=0;r<h;r++)for(let c=0;c<w;c++){const v=g[r][c];if(v&&!by.has(v))by.set(v,[]);if(v)by.get(v).push([r,c])}if(!by.has(1))throw Error("anchor");const y=Math.min(...by.get(1).map(x=>x[0]));const out=zero(h,w);for(const [v,ps] of by){const shift=y-Math.min(...ps.map(x=>x[0]));for(const [r,c] of ps){if(r+shift<0||r+shift>=h||out[r+shift][c])throw Error("overlap");out[r+shift][c]=v}}return out}
if(id==="1cf80156"){const ps=[];for(let r=0;r<h;r++)for(let c=0;c<w;c++)if(g[r][c])ps.push([r,c]);if(!ps.length)throw Error("empty");const r0=Math.min(...ps.map(x=>x[0])),r1=Math.max(...ps.map(x=>x[0])),c0=Math.min(...ps.map(x=>x[1])),c1=Math.max(...ps.map(x=>x[1]));return g.slice(r0,r1+1).map(x=>x.slice(c0,c1+1))}
if(id==="1e0a9b12"){const out=zero(h,w);for(let c=0;c<w;c++){const vs=g.map(x=>x[c]).filter(Boolean);for(let i=0;i<vs.length;i++)out[h-vs.length+i][c]=vs[i]}return out}
if(id==="1fad071e"){let ct=0;for(let r=0;r<h-1;r++)for(let c=0;c<w-1;c++)if(g[r][c]===1&&g[r+1][c]===1&&g[r][c+1]===1&&g[r+1][c+1]===1)ct++;if(ct>5)throw Error("count");return [Array.from({length:5},(_,i)=>i<ct?1:0)]}
if(id==="2013d3e2"){const ps=[];for(let r=0;r<h;r++)for(let c=0;c<w;c++)if(g[r][c])ps.push([r,c]);if(!ps.length)throw Error("empty");const r=Math.min(...ps.map(x=>x[0])),c=Math.min(...ps.map(x=>x[1]));return g.slice(r,r+3).map(x=>x.slice(c,c+3))}
if(id==="2072aba6"){const out=zero(h*2,w*2);for(let r=0;r<h;r++)for(let c=0;c<w;c++){if(![0,5].includes(g[r][c]))throw Error("color");if(g[r][c]){out[2*r][2*c]=1;out[2*r][2*c+1]=2;out[2*r+1][2*c]=2;out[2*r+1][2*c+1]=1}}return out}
if(id==="23581191"){const pts=[];for(let r=0;r<h;r++)for(let c=0;c<w;c++)if(g[r][c])pts.push({r,c,v:g[r][c]});if(pts.length!==2||pts.map(x=>x.v).sort().join(",")!=="7,8")throw Error("points");const a=pts.find(x=>x.v===8),b=pts.find(x=>x.v===7),out=zero(h,w);for(let r=0;r<h;r++)for(let c=0;c<w;c++){const x=r===a.r||c===a.c,y=r===b.r||c===b.c;out[r][c]=x&&y?2:x?8:y?7:0}return out}
if(id==="25d8a9c8"){if(w!==3)throw Error("width");return g.map(row=>row.every(v=>v===row[0])?Array(w).fill(5):Array(w).fill(0))}
throw Error("ABSTAIN_UNSUPPORTED");
}
export {op};
