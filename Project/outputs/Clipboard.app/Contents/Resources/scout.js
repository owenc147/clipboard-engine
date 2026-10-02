// Film room: scouting every manager in the selected league (any of Owen's leagues).
// Uses model data (scouts = every 2026 league each manager plays in) plus the title model's
// own runs: Owen's scan (best offer to each manager) and the rival scan (the model run as each manager).
(function(){
const S={};
const pct=x=>Math.round(100*x)+'%',p1=x=>(100*x).toFixed(1)+'%',accTxt=x=>x>=.9?'likely (90%+)':'~'+Math.round(100*x)+'%',e=v=>esc(String(v??''));
const ago=ms=>{if(!ms)return 'no moves yet';const d=(Date.now()-ms)/864e5;return d<1?'today':d<2?'yesterday':Math.round(d)+' days ago'};
function need(M){ // weakest starting position per team vs the league, and deepest bench position
 const L=M.L,slots=L.slots||[],cnt={QB:0,RB:0,WR:0,TE:0};slots.forEach(s=>{if(cnt[s]!==undefined)cnt[s]++});
 const flex=slots.filter(s=>s==='FLEX'||s==='WRRB_FLEX'||s==='REC_FLEX').length;if(flex){cnt.RB+=flex>1?1:.5;cnt.WR+=flex>1?1:.5}if(slots.includes('SUPER_FLEX'))cnt.QB+=1;
 const v=p=>M.val[p]?M.val[p][0]:0,pos=p=>(modelData.players[p]||[])[1];
 const out={};for(const r in L.teams){const ps=L.teams[r].players;const st={},bench={};for(const k in cnt){const a=ps.filter(p=>pos(p)===k).map(v).sort((x,y)=>y-x);const n=Math.ceil(cnt[k]);st[k]=a.slice(0,n).reduce((s,x)=>s+x,0)/Math.max(cnt[k],1);bench[k]=a.slice(n,n+2).reduce((s,x)=>s+x,0)}out[r]={st,bench}}
 const z={};for(const k in cnt){const xs=Object.values(out).map(o=>o.st[k]),m=xs.reduce((a,b)=>a+b,0)/xs.length,sd=Math.sqrt(xs.reduce((a,b)=>a+(b-m)**2,0)/xs.length)||1;for(const r in out)(z[r]=z[r]||{})[k]=(out[r].st[k]-m)/sd}
 const res={};for(const r in out){const zs=Object.entries(z[r]).sort((a,b)=>a[1]-b[1]);const deep=Object.entries(out[r].bench).sort((a,b)=>b[1]-a[1])[0];res[r]={need:zs[0][0],needZ:zs[0][1],strong:zs[zs.length-1][0],deep:deep&&deep[1]>0?deep[0]:null}}return res}
function tier(p){const moves=p.trades+p.waivers+p.fa,rate=moves/Math.max(p.league_weeks,1),idle=p.last?(Date.now()-p.last)/864e5:99;
 if(idle>16)return ['Dormant',0];if(rate>=3)return ['Hyperactive',3];if(rate>=1.5)return ['Active',2];if(rate>=.6)return ['Steady',1];return ['Quiet',0]} // moves per league per week
function tradeWeek(p){return 1-Math.exp(-(p.trades+.3)/(p.league_weeks+6))} // chance of a completed trade in any one league this week (shrunk toward quiet)
function top(o){const a=Object.entries(o||{}).filter(([k])=>['QB','RB','WR','TE'].includes(k)).sort((a,b)=>b[1]-a[1]);return a.length?a[0][0]:null}
function predict(p,n,t,tw){const out=[];
 if(t[0]==='Dormant')out.push('Hasn’t made a move in over two weeks anywhere. Offers will sit; nudge them in person.');
 else if(t[0]==='Quiet')out.push('Rarely moves. Expect them to ride their roster unless an injury forces it.');
 if(n.needZ<-.6)out.push(`Weakest spot is <b>${n.need}</b>${top(p.pos_in)===n.need?' and it’s what they keep adding':''} — most likely next move is a ${n.need} ${t[1]>=2?'off waivers or by trade':'pickup'}.`);
 else if(t[1]>=2)out.push(`Roster is balanced; their churn is mostly ${top(p.pos_in)||'depth'} adds.`);
 if(n.deep&&n.deep!==n.need)out.push(`Has spare <b>${n.deep}</b> depth to deal from.`);
 if(p.trades>=2)out.push(`Deal-maker: ${p.trades} trades this year${p.gave>p.got?', usually consolidating 2-for-1':p.got>p.gave?', usually buying depth':''}. Will counter.`);
 else if(p.trades===0&&t[1]>=1)out.push('Works the wire but hasn’t traded yet — show them a clear lineup upgrade.');
 out.push(`Chance they complete a trade somewhere this week: ~${pct(1-Math.pow(1-tw,Math.max(1,p.leagues.length)))}.`);return out.join(' ')}
function panel(lid){const R=modelRuns[lid];if(!R||!R.done||!modelData)return '';const M=R.M,me=M.L.me,base=R.acc.res[0],n=base.n,sc=modelData.scouts||{};
 if(sc._error)return `<section class="desk-card"><h3>Film room</h3><p>Scouting data failed to load: ${e(sc._error)}. Refresh model data.</p></section>`;
 const N=need(M);
 const myBest={};R.cands.forEach((c,i)=>{const s=R.acc.res[i+1];if(!s)return;const d=(s.title-base.title)/n,cur=myBest[c.r];if(!cur||c.p*d>cur.ev)myBest[c.r]={c,d,ev:c.p*d,after:s.title/n}});
 const top1=Object.values(myBest).filter(x=>x.d>0).sort((a,b)=>b.ev-a.ev)[0];
 const theirs={};if(R.rivals&&R.rivals.done)R.rivals.picks.forEach((c,i)=>{const a=R.rivals.acc[i]&&R.rivals.acc[i].res[0];if(a)theirs[c.x]={c,their:(a.titles[c.x]||0)/a.n-(base.titles[c.x]||0)/n,theirB:(base.titles[c.x]||0)/n,theirA:(a.titles[c.x]||0)/a.n,mine:a.title/a.n-base.title/n,mineA:a.title/a.n}});
 const rows=Object.entries(M.L.teams).filter(([r])=>r!==me).map(([r,t])=>({r,t,odds:(base.titles[r]||0)/n,p:sc[t.owner]})).sort((a,b)=>b.odds-a.odds);
 const homes=lid2=>modelData.leagues[lid2]?modelData.leagues[lid2].name:null;
 const cards=rows.map(({r,t,odds,p})=>{const nn=N[r];if(!p)return `<article class="cb-scout"><header><h4>${e(t.name)}</h4><span class="pill">No scouting data</span></header></article>`;
  const ti=tier(p),tw=tradeWeek(p),also=p.home.filter(h=>h!==lid).map(homes).filter(Boolean),mb=myBest[r]&&myBest[r].d>0?myBest[r]:null,th0=theirs[r],th=th0&&th0.their>0.002?th0:null,toMe=!!(th&&th.c.r===me);
  const race=th&&top1&&th.c.r!==me&&(th.c.r===top1.c.r||th.c.get.some(x=>top1.c.get.includes(x)));
  const moves=p.moves.slice(0,6).map(m=>`<li><b>${e(m.type==='free_agent'?'Free agent':m.type==='waiver'?'Waiver':'Trade')}</b> · ${e(m.league)} · wk ${e(m.week)}: ${m.add.length?'+ '+e(m.add.join(', ')):''}${m.drop.length?' &nbsp;− '+e(m.drop.join(', ')):''}${m.with.length?' (with '+e(m.with.join(', '))+')':''}</li>`).join('');
  return `<article class="cb-scout${race||toMe?' race':''}"><header><h4>${e(t.name)}</h4><span class="cb-rec">${e(t.w+'-'+t.l)}</span><span class="pill cb-tier t${ti[1]}">${ti[0]}</span><span class="cb-odds">${pct(odds)}<small>title</small></span></header>
  <div class="cb-facts"><span><b>${p.leagues.length}</b> leagues</span><span><b>${p.trades}</b> trades</span><span><b>${p.waivers+p.fa}</b> adds</span><span>Last move <b>${e(ago(p.last))}</b></span>${also.length?`<span>Also in your <b>${e(also.join(', '))}</b></span>`:''}</div>
  <p class="cb-read">${predict(p,nn,ti,tw)}</p>
  ${mb?`<p class="cb-line"><span>Your best offer</span>${e(mb.c.give.map(mName).join(' + '))} → ${e(mb.c.get.map(mName).join(' + '))} · accept ${accTxt(mb.c.p)} · your title odds ${p1(base.title/n)} → ${p1(mb.after)}</p>`:''}
  ${th?`<p class="cb-line"><span>Their best move</span>${e(th.c.give.map(mName).join(' + '))} → ${e(th.c.get.map(mName).join(' + '))} with ${e(M.L.teams[th.c.r].name)} · accept ${accTxt(th.c.p)} · their title odds ${p1(th.theirB)} → ${p1(th.theirA)} · yours ${p1(base.title/n)} → ${p1(th.mineA)}</p>`:''}
  ${!th&&th0?`<p class="cb-line"><span>Their best move</span>No trade the model finds raises their title odds. Expect them to hold or work the wire.</p>`:''}
  ${toMe?`<p class="cb-alert">${th.mineA>base.title/n?'They may bring this to you. Take it':'They may bring this to you. Decline'}: your title odds ${p1(base.title/n)} → ${p1(th.mineA)}.</p>`:''}
  ${race&&!toMe?`<p class="cb-alert">Race: this move targets the same ${th.c.r===top1.c.r?'partner':'player'} as your top offer. Send yours first.</p>`:''}
  ${moves?`<details><summary>Recent moves across all leagues</summary><ul>${moves}</ul></details>`:''}</article>`}).join('');
 const status=!R.rivals?'Running the model as each manager…':!R.rivals.done?'Running the model as each manager…':'Model run as every manager in this league.';
 const nLeagues=new Set(rows.flatMap(x=>x.p?x.p.leagues.map(l=>l.id):[])).size;
 return `<section class="desk-card cb-film"><h3>Film room</h3><p>Every manager in ${e(M.L.name)}, tracked across ${nLeagues} Sleeper leagues this season. ${e(status)} Activity and trade odds come from their real 2026 moves; “their best move” is the title model run from their side.</p>${cards}</section>`}
window.cbFilmPanel=panel;
if(typeof window.mRender!=='function')return;
const before=window.mRender;
window.mRender=mRender=function(){before();try{const lid=mLeagueId(),R=modelRuns[lid];if(!R||!R.done)return;
 if(!R.rivals&&!S[lid]){S[lid]=1;setTimeout(()=>{if(modelRuns[lid]&&!modelRuns[lid].rivals)mRunRivals(lid)},60)}
 const box=document.querySelector('#content .desk');if(!box||box.querySelector('.cb-film'))return;
 const foot=box.querySelector('.desk-foot');const html=panel(lid);if(foot)foot.insertAdjacentHTML('beforebegin',html);else box.insertAdjacentHTML('beforeend',html);
 box.querySelectorAll('.desk-actions button').forEach(b=>{if(/Scan every rival/.test(b.textContent))b.closest('.desk-actions').remove()})}catch(err){console.error('film room',err)}};
})();
