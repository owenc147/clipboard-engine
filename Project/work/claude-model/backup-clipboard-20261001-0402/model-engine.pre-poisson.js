// Claude title model engine for Binocular. Pure functions; no DOM. Works in the app and in Node tests.
(function(root){
const SKILL=['QB','RB','WR','TE'];
const SLOT={QB:['QB'],RB:['RB'],WR:['WR'],TE:['TE'],K:['K'],DEF:['DEF'],FLEX:['RB','WR','TE'],WRRB_FLEX:['RB','WR'],REC_FLEX:['WR','TE'],SUPER_FLEX:['QB','RB','WR','TE']};
// Weekly CV and blend weights backtested on the 2024 and 2025 seasons (1,630 player-snapshots, rest-of-season PPG).
const CV={QB:.45,RB:.62,WR:.69,TE:.70,K:.45,DEF:.70},HZ={QB:.03,RB:.04,WR:.038,TE:.04,K:0,DEF:0}/* weekly injury hazard, 2024-25 absence runs */;
// Weekly trade-value chart (Sep 30, 2026; 0-99, 1QB). Blended 30% with FantasyCalc in 1QB leagues.
const CHART={"Jahmyr Gibbs":99,"Bijan Robinson":97,"Jaxon Smith-Njigba":96,"Ja'Marr Chase":94,"Kenneth Walker":93,"Amon-Ra St. Brown":92,"Christian McCaffrey":91,"Jonathan Taylor":90,"Justin Jefferson":89,"CeeDee Lamb":88,"James Cook":76,"Chris Olave":74,"Ashton Jeanty":72,"Puka Nacua":70,"Derrick Henry":69,"Chase Brown":65,"Drake London":63,"Jeremiyah Love":60,"Josh Allen":59,"Brock Bowers":55,"DeVonta Smith":51,"Saquon Barkley":50,"Trey McBride":49,"Nico Collins":47,"George Pickens":46,"Kyren Williams":44,"Malik Nabers":39,"Garrett Wilson":37,"Zay Flowers":36,"Christian Watson":34,"Lamar Jackson":33,"Tetairoa McMillan":31,"D'Andre Swift":30,"Parker Washington":30,"Omarion Hampton":29,"Tee Higgins":27,"Cam Skattebo":26,"Ladd McConkey":25,"Javonte Williams":25,"Breece Hall":23,"Davante Adams":22,"Rashee Rice":22,"Jaylen Waddle":21,"DJ Moore":19,"Bucky Irving":19,"Dalton Kincaid":17,"Emeka Egbuka":16,"Matthew Golden":15,"Mike Evans":15,"Bhayshul Tuten":15,"A.J. Brown":14,"Joe Burrow":13,"David Montgomery":13,"Michael Wilson":12,"Chuba Hubbard":12,"Brock Purdy":9,"Luther Burden":8,"Josh Downs":7,"Jalen Hurts":7,"Tyler Warren":6};
const BLEND={QB:[.7,.2,.1],RB:[.95,.05,0],WR:[.95,.05,0],TE:[.95,.05,0]},BIAS={QB:.92,RB:1,WR:1,TE:1}; // 2024+2025 backtests (1,630 snapshots)
const K_MARKET=0.08;
const CVY={pass_yd:.28,rush_yd:.55,rec_yd:.6};
function Phi(z){const t=1/(1+.2316419*Math.abs(z)),d=.3989423*Math.exp(-z*z/2),q=d*t*(.3193815+t*(-.3565638+t*(1.781478+t*(-1.821256+t*1.330274))));return z>0?1-q:q}
function pOver(m,th,k){if(m<=0)return 0;const s=Math.sqrt(Math.log(1+(CVY[k]||.5)**2)),mu=Math.log(m)-s*s/2;return 1-Phi((Math.log(th)-mu)/s)}
function rng(seed){let s=seed>>>0||1;return()=>{s^=s<<13;s^=s>>>17;s^=s<<5;return (s>>>0)/4294967296}}

// Build a league model: expected weekly values (history-blended) per player.
function prepare(data,lid,market){
 const L=data.leagues[lid],cur=data.week,W=[];for(let w=cur;w<=17;w++)W.push(w);
 const ptd=L.ptd||4,pos=p=>(data.players[p]||[])[1]||'?',name=p=>(data.players[p]||[p])[0],st=p=>(data.players[p]||[])[3]||'';
 // League scoring from raw stat columns (data.keys): completions, yards-per-point, INT value, 6-pt TDs and yardage
 // bonuses (expected bonus for projections via a lognormal yardage model; exact bonus for actual games). Legacy data falls back to PPR + pass-TD adjustment.
 const KI={};(data.keys||[]).forEach((k,i)=>KI[k]=i+1);const SC=L.score,BON=L.bonus||{},NEW=!!(data.keys&&SC);
 const gpOf=r=>NEW?r[r.length-1]:r[1];
 const fp=(v,p,mean,d=1)=>{if(!v)return 0;const ps=pos(p);if(ps==='K'||ps==='DEF')return v[0]/d;let t=0;for(const k in SC){const i=KI[k];if(i)t+=SC[k]*(v[i]||0)/d}
  for(const st in BON){const y=(v[KI[st]]||0)/d;if(y<=0)continue;for(const [th,b] of BON[st])t+=b*(mean?pOver(y,th,st):(y>=th?1:0))}return t===0&&v[0]>0?v[0]/d:t}; // no stat columns: fall back to PPR
 const pts=(x,p)=>NEW?fp(x,p,true):(x?x[0]+(ptd-4)*x[1]:0);
 const val={},F={},raw={};
 const all=new Set();Object.values(L.teams).forEach(t=>t.players.forEach(p=>all.add(p)));(L.fa||[]).forEach(p=>all.add(p));
 for(const p of all){
  const pr=(data.proj[p]||[]).map(x=>pts(x,p));raw[p]=pr;const nz=pr.filter(v=>v>0);const pa=nz.length?nz.reduce((a,b)=>a+b)/nz.length:0;let f=1;
  if(pa>0&&SKILL.includes(pos(p))){let hs=0,hw=0;const h=data.hist[p]||{};[data.season-3,data.season-2,data.season-1].forEach((y,i)=>{const s=h[y];if(s&&gpOf(s)>0){const g=gpOf(s),pp=NEW?fp(s,p,true,g):(s[0]+(ptd-4)*s[2])/s[1];hs+=(i+1)*pp*Math.min(g,17)/17;hw+=i+1}});
   const hh=hw?hs/hw:pa;const wk=data.s26[p]||[];const c=wk.length?wk.reduce((a,x)=>a+(NEW?fp(x,p,false):x[0]+(ptd-4)*x[1]),0)/wk.length:pa;const bw=BLEND[pos(p)];f=Math.min(1.3,Math.max(.6,(bw[0]*pa+bw[1]*hh+bw[2]*c)/pa))*(BIAS[pos(p)]||1)}
  F[p]=f;const s=st(p);val[p]=pr.map((v,i)=>{if(['IR','PUP','Sus','NA'].includes(s)&&i<3)return 0;if(s==='Out'&&i===0)return 0;return v*f});
 }
 const slots=L.slots.map(s=>SLOT[s]).filter(Boolean).sort((a,b)=>a.length-b.length);
 // market value 0-100 (FantasyCalc normalized, blended with chart in 1QB leagues)
 const mk=(market&&market.players)||{};const mx=Math.max(1,...Object.values(mk).map(x=>x.value||0));
 const MV=p=>{const fv=(mk[p]?.value||0)/mx*100;const c=CHART[name(p)];return (L.qbs===1&&c!=null)?.7*fv+.3*c:fv};
 return {lid,L,data,W,nReg:L.last-cur+1,pos,name,st,val,F,raw,slots,MV};
}
function lineupWeek(M,pl,wi,ok){const c=pl.filter(p=>!ok||ok(p)).map(p=>[p,M.pos(p),M.val[p]?M.val[p][wi]:0]).sort((a,b)=>b[2]-a[2]);const used=new Uint8Array(c.length),out=[];let t=0;
 for(const s of M.slots){for(let i=0;i<c.length;i++){if(!used[i]&&s.includes(c[i][1])){used[i]=1;t+=c[i][2];out.push(c[i][0]);break}}}return {t,out}}
function rosLineup(M,pl){let t=0;for(let i=0;i<M.nReg;i++)t+=lineupWeek(M,pl,i).t;return t/M.nReg}

// Acceptance: history part (accepted trade sides) + market part.
function pTrain(M,R,G,dO){const pv=M.L.pv||{},Lw=a=>a.map(p=>pv[p]||0).sort((x,y)=>y-x).reduce((t,v,i)=>t+(i?.4:1)*v,0);
 const dl=Lw(R)-Lw(G),cons=G.length>R.length?1:G.length<R.length?-1:0,acc=M.data.accepted.filter(a=>a.cons===cons);
 const sv=x=>acc.length?acc.filter(a=>a.dl<=x).length/acc.length:.5;let p=Math.min(.9,Math.max(.02,.64*sv(dl)/(sv(0)||.5)));
 let o=p/(1-p);if(dO>=1)o*=2;else if(dO<-.5)o*=.5;p=Math.min(.9,o/(1+o));return {p,dl}}
function marketDiff(M,R,G){const s=a=>a.map(M.MV).sort((x,y)=>y-x).reduce((t,v,i)=>t+(i?.4:1)*v,0);return s(R)-s(G)}
function accept(M,R,G,dO,k){const cl=x=>Math.min(.97,Math.max(.03,x)),lg=x=>Math.log(x/(1-x));const t=pTrain(M,R,G,dO),dm=marketDiff(M,R,G);
 return {p:1/(1+Math.exp(-(lg(cl(t.p))+(k??K_MARKET)*dm))),dl:t.dl,dm}}
function fitK(models,labels){let best={k:K_MARKET,ll:-Infinity,n:0};const rows=labels.filter(l=>models[l.lid]&&l.r.length&&l.g.length);if(rows.length<3)return {...best,n:rows.length};const maxK=rows.length<15?.12:.3,minK=rows.length<15?.04:0;
 for(let k=minK;k<=maxK+1e-9;k+=.005){let ll=0;for(const l of rows){const p=accept(models[l.lid],l.r,l.g,0,k).p;ll+=l.y?Math.log(p):Math.log(1-p)}if(ll>best.ll)best={k:+k.toFixed(3),ll,n:rows.length}}
 return best}

// Player-level Monte Carlo with common random numbers across scenarios.
function engine(M){const ids=[...new Set(Object.values(M.L.teams).flatMap(t=>t.players))];const ix={};ids.forEach((p,i)=>ix[p]=i);
 const nfl={};let nt=0;const pl=ids.map(p=>{const ps=M.pos(p),st=M.st(p),age=(M.data.players[p]||[])[4]||26,h=M.data.hist[p]||{};let gp=0,y=0;for(const yr of [M.data.season-3,M.data.season-2,M.data.season-1]){if(h[yr]){const r=h[yr];gp+=Math.min(M.data.keys?r[r.length-1]:r[1],17);y++}}
  const av=y?gp/(17*y):.9;let hz=HZ[ps]||0;hz*=Math.min(2,Math.max(.6,(1-av)/.12));if(ps==='RB'&&age>=28)hz*=1.3;else if(age>=31)hz*=1.2;
  // Total weekly spread is calibrated to the backtested CV, so the season-talent and shared NFL-team parts are carved out of it (not stacked on top).
  // K and DEF use an additive normal so scores can be zero or negative (DEF floor -10, K floor -2).
  const cv=CV[ps]||.6,sT=Math.sqrt(Math.log(1+cv*cv)),norm=['K','DEF'].includes(ps),sTeam=norm?0:.15,sTal=norm?0:(y?.12:.18),team=(M.data.players[p]||[])[2];if(team&&nfl[team]==null)nfl[team]=nt++;
  return {p,pos:ps,mean:M.val[p]||[],hz,miss:st==='Questionable'?.25:st==='Doubtful'?.75:st==='Out'?1:0,sI:Math.sqrt(Math.max(.01,sT*sT-sTeam*sTeam-sTal*sTal)),sTeam,sTal,norm,cv,floor:ps==='DEF'?-10:-2,nfl:team?nfl[team]:null}});
 return {ids,ix,pl,nt}}
function simulate(M,E,scenarios,N,acc,seed){
 const NW=M.W.length,rids=Object.keys(M.L.teams),me=M.L.me,PT=M.L.playoff_teams,last=M.L.last,cur=M.data.week,R=acc.rand||(acc.rand=rng(seed||12345));
 let spare=null;const g=()=>{if(spare!==null){const s=spare;spare=null;return s}let u=0;while(!u)u=R();const v=R(),r=Math.sqrt(-2*Math.log(u));spare=r*Math.sin(6.283185307*v);return r*Math.cos(6.283185307*v)};
 const pl=E.pl,np=pl.length;
 if(!acc.S){acc.S=scenarios.map(sc=>{const Rs={};for(const r of rids)Rs[r]=M.L.teams[r].players.map(p=>E.ix[p]);for(const [pid,to] of sc.moves||[]){const i=E.ix[pid];for(const r of rids){const j=Rs[r].indexOf(i);if(j>=0)Rs[r].splice(j,1)}Rs[to].push(i)}return {R:Rs}});
  const greedy=(roster,w,ok)=>{const c=roster.filter(ok).sort((a,b)=>(pl[b].mean[w]||0)-(pl[a].mean[w]||0));const used=new Uint8Array(c.length),out=[];for(const s of M.slots){for(let q=0;q<c.length;q++){if(!used[q]&&s.includes(pl[c[q]].pos)){used[q]=1;out.push(c[q]);break}}}return out};
  acc.greedy=greedy;for(const s of acc.S){s.DL={};for(const r of rids){s.DL[r]=[];for(let w=0;w<NW;w++)s.DL[r].push(greedy(s.R[r],w,i=>!(w===0&&pl[i].miss>=1)))}}
  acc.res=scenarios.map(s=>({name:s.name,po:0,s1:0,title:0,fin:0,wins:0,n:0,titles:{},wk:new Array(NW).fill(0)}));
  acc.tal=new Float64Array(np);acc.iS=new Int16Array(np);acc.iE=new Int16Array(np);acc.m0=new Uint8Array(np);acc.st=new Int32Array(np);acc.dr=new Float64Array(np*NW);acc.dst=new Int32Array(np*NW);acc.tf=new Float64Array(64*NW);acc.tst=new Int32Array(64*NW);acc.stamp=0}
 const {tal,iS,iE,m0,st,dr,dst,tf,tst,greedy}=acc;
 const init=i=>{if(st[i]===acc.stamp)return;st[i]=acc.stamp;const p=pl[i];tal[i]=Math.exp(p.sTal*g()-p.sTal*p.sTal/2);m0[i]=R()<p.miss?1:0;
  if(p.hz>0){const w0=Math.floor(Math.log(R()||1e-9)/Math.log(1-p.hz));if(w0<NW){iS[i]=w0;iE[i]=R()<.18?99:w0+1+Math.floor(-Math.log(R()||1e-9)*2.6)}else{iS[i]=99;iE[i]=99}}else{iS[i]=99;iE[i]=99}};
 const avail=(i,w)=>{init(i);if(w===0&&m0[i])return false;return !(w>=iS[i]&&w<iE[i])};
 const draw=(i,w)=>{const x=i*NW+w;if(dst[x]===acc.stamp)return dr[x];dst[x]=acc.stamp;const p=pl[i];let f=1;if(p.sTeam>0&&p.nfl!=null){const y=p.nfl*NW+w;if(tst[y]!==acc.stamp){tst[y]=acc.stamp;tf[y]=Math.exp(.15*g()-.01125)}f=tf[y]}if(p.norm){const m=p.mean[w]||0;return dr[x]=m?Math.max(p.floor,m+p.cv*m*g()):0}return dr[x]=(p.mean[w]||0)*tal[i]*f*Math.exp(p.sI*g()-p.sI*p.sI/2)};
 const score=(s,r,w)=>{let Lu=s.DL[r][w];if(!Lu)return 0;for(const i of Lu){if(!avail(i,w)){Lu=greedy(s.R[r],w,j=>avail(j,w));break}}let t=0;for(const i of Lu)t+=draw(i,w);return t};
 for(let n=0;n<N;n++){acc.stamp++;
  acc.S.forEach((s,si)=>{const Wn={},PF={};for(const r of rids){Wn[r]=M.L.teams[r].w;PF[r]=M.L.teams[r].pf}
   for(let wk=cur;wk<=last;wk++){for(const [a,b] of M.L.sched[wk]||[]){const sa=score(s,a,wk-cur),sb=score(s,b,wk-cur);PF[a]+=sa;PF[b]+=sb;const wn=sa>=sb?a:b;Wn[wn]++;if(wn===me)acc.res[si].wk[wk-cur]++}}
   const o=[...rids].sort((x,y)=>Wn[y]-Wn[x]||PF[y]-PF[x]),seeds=o.slice(0,PT),m=(a,b,wk)=>wk>17||wk<cur?a:(score(s,a,wk-cur)>=score(s,b,wk-cur)?a:b),p0=last+1;let champ,fin;
   if(PT<=2){champ=m(seeds[0],seeds[1]||seeds[0],p0);fin=seeds.slice(0,2)}
   else if(PT===4){let x=m(seeds[0],seeds[3],p0),y=m(seeds[1],seeds[2],p0);champ=m(x,y,p0+1);fin=[x,y]}
   else if(PT===6){const a=m(seeds[2],seeds[5],p0),b=m(seeds[3],seeds[4],p0);const x=m(seeds[0],b,p0+1),y=m(seeds[1],a,p0+1);champ=m(x,y,p0+2);fin=[x,y]}
   else if(PT===8){const a=m(seeds[0],seeds[7],p0),b=m(seeds[3],seeds[4],p0),c=m(seeds[1],seeds[6],p0),d=m(seeds[2],seeds[5],p0);const x=m(a,b,p0+1),y=m(c,d,p0+1);champ=m(x,y,p0+2);fin=[x,y]}
   else{const a=m(seeds[1],seeds[6]||seeds[1],p0),b=m(seeds[2],seeds[5]||seeds[2],p0),c=m(seeds[3],seeds[4]||seeds[3],p0);const x=m(seeds[0],c,p0+1),y=m(a,b,p0+1);champ=m(x,y,p0+2);fin=[x,y]}
   const Rr=acc.res[si];Rr.n++;Rr.wins+=Wn[me]-M.L.teams[me].w;if(seeds.includes(me))Rr.po++;if(o[0]===me)Rr.s1++;if(champ===me)Rr.title++;if(fin.includes(me))Rr.fin++;Rr.titles[champ]=(Rr.titles[champ]||0)+1})}
 return acc}

// Trade scan from team X's perspective.
function combos(a,n){return n===1?a.map(x=>[x]):n===2?a.flatMap((x,i)=>a.slice(i+1).map(y=>[x,y])):a.flatMap((x,i)=>a.slice(i+1).flatMap((y,j)=>a.slice(i+j+2).map(z=>[x,y,z])))}
function scan(M,x,opt={}){const ros={};for(const p in M.val)ros[p]=M.val[p].slice(0,M.nReg).reduce((a,b)=>a+b,0);
 const sl=M.slots.filter(s=>!(s.length===1&&['K','DEF'].includes(s[0])));
 const LR=pl=>{const c=pl.map(p=>[M.pos(p),ros[p]||0]).sort((a,b)=>b[1]-a[1]);const u=new Uint8Array(c.length);let t=0;for(const s of sl){for(let i=0;i<c.length;i++){if(!u[i]&&s.includes(c[i][0])){u[i]=1;t+=c[i][1];break}}}return t/M.nReg};
 const X=M.L.teams[x],bx=LR(X.players),mine=X.players.filter(p=>SKILL.includes(M.pos(p))).sort((a,b)=>ros[b]-ros[a]).slice(0,opt.depth||12),res=[];
 for(const r in M.L.teams){if(r===x)continue;const T=M.L.teams[r],bo=LR(T.players),th=T.players.filter(p=>SKILL.includes(M.pos(p))).sort((a,b)=>ros[b]-ros[a]).slice(0,(opt.depth||12)-1);
  for(let a=1;a<=3;a++)for(let b=1;b<=3;b++)for(const gv of combos(mine,a))for(const t of combos(th,b)){const dx=LR(X.players.filter(p=>!gv.includes(p)).concat(t))-bx;if(dx<(opt.min||.5))continue;
   const dO=LR(T.players.filter(p=>!t.includes(p)).concat(gv))-bo;if(dO<-.5)continue;const ac=accept(M,gv,t,dO,opt.k);if(ac.p<(opt.minP||.3))continue;res.push({x,r,give:gv,get:t,dx,dO,p:ac.p,ev:ac.p*dx})}}
 res.sort((a,b)=>b.ev-a.ev);const out=[],seen={},cnt={};for(const c of res){const key=c.r+c.get.join();if(seen[key]||(cnt[c.r]||0)>=(opt.perPartner||2))continue;seen[key]=1;cnt[c.r]=(cnt[c.r]||0)+1;out.push(c);if(out.length>=(opt.top||8))break}return out}
// Free agents that beat your current roster (rest of regular season), with the cheapest drop.
function faScan(M,top){const me=M.L.teams[M.L.me],res=M.L.reserve||me.reserve||[],roster=me.players.filter(p=>!res.includes(p)),base=rosLineup(M,roster),out=[];
 for(const f of (M.L.fa||[])){if(!M.val[f])continue;let best=null;for(const d of roster){const g=rosLineup(M,roster.filter(p=>p!==d).concat(f))-base;if(!best||g>best.g)best={g,d}}
  const wk0=lineupWeek(M,roster.filter(p=>p!==best.d).concat(f),0).t-lineupWeek(M,roster,0).t;if(best.g>.1||wk0>1)out.push({add:f,drop:best.d,gain:best.g,week:wk0})}
 return out.sort((a,b)=>b.gain-a.gain).slice(0,top||8)}
// Best lineup this week vs the starters currently set in Sleeper.
function startSit(M){const me=M.L.teams[M.L.me],res=me.reserve||[],roster=me.players.filter(p=>!res.includes(p)),best=lineupWeek(M,roster,0,p=>!['Out','Doubtful','IR','PUP','Sus'].includes(M.st(p))),cur=me.starters||[];
 const val=p=>M.val[p]?M.val[p][0]:0,curT=cur.reduce((t,p)=>t+val(p),0);return {best:best.out,bestT:best.t,cur,curT,ins:best.out.filter(p=>!cur.includes(p)),outs:cur.filter(p=>!best.out.includes(p))}}
function movesFor(c){return [...c.give.map(p=>[p,c.r]),...c.get.map(p=>[p,c.x])]}
root.TitleModel={pOver,prepare,engine,simulate,scan,accept,fitK,movesFor,lineupWeek,rosLineup,faScan,startSit,CHART};
})(typeof window!=='undefined'?window:globalThis);
