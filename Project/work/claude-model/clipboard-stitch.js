/* Clipboard — Sideline Tactical Call Sheet layer (Stitch design).
   Adds the top status bar (week + kickoff countdown, sync state, quick find, refresh),
   steel-clip rivets, record chips and an intel block in the sidebar, and the in-game
   win probability panel when the title model has run. Presentation only. */
(function(){
const $q=s=>document.querySelector(s),$$=s=>[...document.querySelectorAll(s)];
const ICON={clock:'<svg viewBox="0 0 24 24" fill="none" stroke-width="2.2"><circle cx="12" cy="13" r="8"/><path d="M12 9v4l3 2M9 2h6"/></svg>',
 search:'<svg viewBox="0 0 24 24" fill="none" stroke-width="2.2"><circle cx="11" cy="11" r="7"/><path d="m20 20-4-4"/></svg>',
 refresh:'<svg viewBox="0 0 24 24"><path d="M20 11a8 8 0 1 0-2.3 5.7M20 4v7h-7"/></svg>',
 gear:'<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="3"/><path d="M19 12a7 7 0 0 0-.1-1.2l2-1.6-2-3.4-2.4 1a7 7 0 0 0-2-1.2L14 3h-4l-.5 2.6a7 7 0 0 0-2 1.2l-2.4-1-2 3.4 2 1.6a7 7 0 0 0 0 2.4l-2 1.6 2 3.4 2.4-1a7 7 0 0 0 2 1.2L10 21h4l.5-2.6a7 7 0 0 0 2-1.2l2.4 1 2-3.4-2-1.6c.1-.4.1-.8.1-1.2z"/></svg>',
 copy:'<svg viewBox="0 0 24 24"><rect x="8" y="8" width="12" height="12"/><path d="M4 16V4h12"/></svg>',
 down:'<svg viewBox="0 0 24 24"><path d="M12 4v11m-5-5 5 5 5-5M4 20h16"/></svg>'};
const ord=n=>{n=+n;const s=['TH','ST','ND','RD'],v=n%100;return n+(s[(v-20)%10]||s[v]||s[0])};

/* next kickoff (Thu 8:15p, Sun 1:00p, Mon 8:15p ET) */
function etNow(){return new Date(new Date().toLocaleString('en-US',{timeZone:'America/New_York'}))}
function nextKick(){const n=etNow(),c=[[4,20,15],[0,13,0],[1,20,15]];let best=null;
 for(const [dow,h,m] of c){const d=new Date(n);d.setHours(h,m,0,0);let add=(dow-n.getDay()+7)%7;d.setDate(d.getDate()+add);if(d<=n)d.setDate(d.getDate()+7);if(!best||d<best)best=d}return best-n}
const fmt=ms=>{const s=Math.max(0,Math.floor(ms/1000)),h=Math.floor(s/3600),m=Math.floor(s%3600/60),x=s%60;return (h>=48?Math.floor(h/24)+'D ':'')+String(h>=48?h%24:h).padStart(2,'0')+':'+String(m).padStart(2,'0')+':'+String(x).padStart(2,'0')};

function topbar(){const main=$q('main');if(!main||$q('.cb-topbar'))return;
 const wk=(typeof reportWeek!=='undefined'&&reportWeek)||(typeof RESEARCH!=='undefined'&&RESEARCH.week)||'';
 main.insertAdjacentHTML('afterbegin',`<div class="cb-topbar" role="region" aria-label="Status"><div class="cb-lock">${ICON.clock}<span class="w">WEEK ${String(wk).padStart(2,'0')}</span> · NEXT KICKOFF IN <span class="t">--:--:--</span></div>
  <div class="cb-sync"><span class="cb-dot"></span><span class="s">SLEEPER SYNC</span></div><div class="spacer"></div>
  <label class="cb-find">${ICON.search}<input type="search" placeholder="Quick find player" aria-label="Quick find player"></label>
  <button class="action cb-refresh" type="button">${ICON.refresh}Refresh</button></div>`);
 main.insertAdjacentHTML('afterbegin','<span class="cb-rivet" style="left:calc(50% - 168px)"></span><span class="cb-rivet" style="left:calc(50% + 154px)"></span>');
 $q('.cb-refresh').onclick=()=>{try{send('refresh')}catch(e){$q('#refresh')?.click()}};
 const inp=$q('.cb-find input');inp.addEventListener('input',()=>{const q=inp.value.trim().toLowerCase();$$('.cb-hit').forEach(e=>e.classList.remove('cb-hit'));if(q.length<2)return;
  const hits=$$('.player-row,.lineup-row,.market-row,.scouted-player,.cb-scout,.desk-asset,tr').filter(r=>r.textContent.toLowerCase().includes(q));hits.forEach(h=>h.classList.add('cb-hit'));hits[0]?.scrollIntoView({block:'center',behavior:'smooth'})});
 inp.addEventListener('keydown',e=>{if(e.key==='Escape'){inp.value='';inp.dispatchEvent(new Event('input'))}});
 document.addEventListener('keydown',e=>{if(e.metaKey&&e.key.toLowerCase()==='f'){e.preventDefault();inp.focus();inp.select()}});
 const tick=()=>{const t=$q('.cb-lock .t');if(t)t.textContent=fmt(nextKick())};tick();setInterval(tick,1000)}
function status(){const w=$q('.cb-lock .w'),wk=(typeof reportWeek!=='undefined'&&reportWeek)||'';if(w&&wk)w.textContent='WEEK '+String(wk).padStart(2,'0');
 const s=$q('.cb-sync .s'),f=($q('#freshness')?.textContent||'');if(!s)return;const m=f.match(/League snapshot:\s*([^·]+)/);const txt=m?'SLEEPER SYNC · '+m[1].trim():'SLEEPER SYNC';if(s.textContent!==txt)s.textContent=txt;
 let stale=false;if(m){const d=new Date(m[1].trim()+' '+new Date().getFullYear());if(!isNaN(d))stale=Date.now()-d>6*3600e3}$q('.cb-sync')?.classList.toggle('stale',stale)}
function buttons(){$$('.top-actions .action').forEach(b=>{if(b.dataset.cbi)return;const t=b.textContent.trim();
 if(/Team settings/.test(t))return;let i=/Copy/.test(t)?ICON.copy:/Export/.test(t)?ICON.down:null;if(!i)return;b.dataset.cbi=1;b.insertAdjacentHTML('afterbegin',i);if(/Export/.test(t))b.classList.add('cb-export')})}
function own(i){try{const l=leagues[i];const line=(l.lines||[]).find(s=>s.startsWith('**Standings:**'))||'';const it=line.replace('**Standings:** ','').split(' · ').find(s=>s.startsWith('**'));
 if(!it)return null;const m=it.replace(/\*\*/g,'').match(/^(\d+)\. (.+) \(([^)]+)\)$/);return m?{rank:m[1],record:m[3]}:null}catch(e){return null}}
function sidebar(){if(typeof leagues==='undefined')return;$$('#nav .nav').forEach((b,i)=>{const o=own(i);if(!o)return;const t=o.record+' · '+ord(o.rank);let c=b.querySelector('.cb-rec-chip');
  if(!c){c=document.createElement('span');c.className='cb-rec-chip';b.append(c)}if(c.textContent!==t)c.textContent=t});
 const nav=$q('#nav');if(!nav)return;let box=$q('.cb-intel');if(!box){nav.insertAdjacentHTML('afterend','<div class="cb-intel"><h5>Operational intel</h5><div class="grid"><div><small>Standing</small><b class="a">—</b></div><div><small>Title odds</small><b class="b red">—</b></div></div></div>');box=$q('.cb-intel')}
 const o=own(typeof selected!=='undefined'?selected:0);const a=box.querySelector('.a'),b=box.querySelector('.b');const at=o?ord(o.rank):'—';if(a.textContent!==at)a.textContent=at;
 let bt='—';try{const lid=mLeagueId(),R=modelRuns[lid];if(R&&R.done){const r=R.acc.res[0];bt=(100*r.title/r.n).toFixed(1)+'%'}}catch(e){}if(b.textContent!==bt)b.textContent=bt}
function winProb(){const sc=$q('.hero .scores');if(!sc)return;let p=null;try{const lid=mLeagueId(),R=modelRuns[lid];if(R&&R.done){const r=R.acc.res[0];p=r.wk[0]/r.n}}catch(e){}
 let el=sc.querySelector('.cb-wp');if(p==null){if(el)el.remove();return}const pct=Math.round(100*p),opp=$$('.hero .team-name')[1]?.textContent?.trim()||'OPP';
 const html=`<small style="display:block;text-align:center;margin-bottom:6px">Win probability · model</small><b>${pct}%</b><div class="bar"><i style="width:${pct}%"></i><em></em></div><div class="lbl"><span>${pct}% you</span><span>${100-pct}% ${opp.slice(0,12)}</span></div>`;
 if(!el){el=document.createElement('div');el.className='cb-wp';sc.append(el)}if(el.dataset.p!==String(pct)){el.dataset.p=String(pct);el.innerHTML=html}}
function tiles(){const t=$$('.pt-row .pt-tile');const n=t.length;t.forEach((el,i)=>{if(el.querySelector('.cb-ttag'))return;const me=el.classList.contains('me');
 const [c,l]=me?['me','My team']:i===0?['fav','Favorite']:i<=2?['','Contender']:i>=n-2?['lot','Lottery']:['','Mid-tier'];el.insertAdjacentHTML('afterbegin','<span class="cb-ttag '+c+'">'+l+'</span>')})}

/* Depth chart: projections, floor/median/ceiling, opponent, game day, status, kickoff cadence, bench swaps (needs model data) */
const CVP={QB:.45,RB:.62,WR:.69,TE:.70,K:.45,DEF:.70};
function depthModel(){try{if(typeof modelData==='undefined'||!modelData)return null;const lid=mLeagueId();if(!lid)return null;const R=modelRuns[lid];
 return R&&R.M?R.M:(window.__cbM&&window.__cbM.lid===lid&&window.__cbM.b===modelData.built_at?window.__cbM.M:(window.__cbM={lid,b:modelData.built_at,M:TitleModel.prepare(modelData,lid,mMarket(lid))}).M)}catch(e){return null}}
function pidFor(M,name){const n=name.replace(/\s+D\/ST$/,'').trim().toLowerCase();const ps=Object.values(M.L.teams).flatMap(t=>t.players);
 return ps.find(p=>((modelData.players[p]||[])[0]||'').toLowerCase()===n)||ps.find(p=>p.toLowerCase()===n)||ps.find(p=>(modelData.players[p]||[])[1]==='DEF'&&n.includes(((modelData.players[p]||[])[0]||'~~').toLowerCase().split(' ').pop()))}
const DAYN=['SUN','MON','TUE','WED','THU','FRI','SAT'];
function gameOf(pid){const t=(modelData.players[pid]||[])[2]||((modelData.players[pid]||[])[1]==='DEF'?pid:null);const g=t&&modelData.nfl_week&&modelData.nfl_week[t];if(!g)return null;const d=new Date(g.date+'T12:00:00');return {...g,team:t,day:DAYN[d.getDay()],d}}
function band(mean,pos){if(pos==='K'||pos==='DEF'){const sd=(CVP[pos]||.6)*mean;return [Math.max(pos==='DEF'?-10:-2,mean-1.2816*sd),mean,mean+1.2816*sd]}const cv=CVP[pos]||.6,s=Math.sqrt(Math.log(1+cv*cv)),m=mean*Math.exp(-s*s/2);return [m*Math.exp(-1.2816*s),m,m*Math.exp(1.2816*s)]}
function depth(){if(typeof currentView==='undefined'||currentView!=='lineup')return;const rows=$$('.lineup-row');if(!rows.length)return;const M=depthModel();
 const hero=$q('.lineup-hero');if(!M){if(hero&&!hero.querySelector('.cb-dc-need'))hero.insertAdjacentHTML('beforeend','<p class="cb-dc-need">Load model data in Title odds to add projections, floor/ceiling ranges, opponents and kickoff days here.</p>');return}
 let tot=0,meds=0,flo=0,cei=0;const starters=[],today=new Date();today.setHours(0,0,0,0);
 rows.forEach(r=>{if(r.dataset.cbd)return;const nm=r.querySelector('.lineup-player strong')?.textContent||'';const pid=pidFor(M,nm);if(!pid)return;r.dataset.cbd=1;
  const pos=M.pos(pid),v=(M.val[pid]||[0])[0],[f,md,c]=band(v,pos),g=gameOf(pid),st=M.st(pid)||'';starters.push({pid,pos,v,g,nm,slot:r.querySelector('.slot')?.textContent});
  const lo=Math.max(0,f),hi=Math.max(c,1),x=Math.min(100,100*md/(hi*1.05)),a=Math.min(100,100*lo/(hi*1.05));
  const chip=st?'<span class="cb-st q">'+esc(st)+'</span>':'<span class="cb-st ok">Healthy</span>';
  const played=g&&g.d<today;
  r.insertAdjacentHTML('beforeend','<div class="cb-dc"><span class="opp">'+(g?(g.home?'vs ':'@ ')+g.opp:'BYE')+'</span><b class="proj">'+v.toFixed(1)+'</b><span class="rng"><i style="left:'+a+'%;right:'+(100-Math.min(100,100*c/(hi*1.05)))+'%"></i><em style="left:'+x+'%"></em><small>'+lo.toFixed(1)+'</small><small class="m">MED '+md.toFixed(1)+'</small><small>'+c.toFixed(1)+'</small></span>'+chip+'<span class="day">'+(g?(played?'FINAL':g.day):'—')+'</span></div>')});
 starters.forEach(s=>{tot+=s.v});
 if(hero&&!hero.querySelector('.cb-dc-sum')&&starters.length){const N=3000,sums=[];for(let i=0;i<N;i++){let t=0;for(const s of starters){const cv=CVP[s.pos]||.6,sg=Math.sqrt(Math.log(1+cv*cv));let u=0;while(!u)u=Math.random();const z=Math.sqrt(-2*Math.log(u))*Math.cos(6.2832*Math.random());t+=(s.pos==='K'||s.pos==='DEF')?Math.max(s.pos==='DEF'?-10:-2,s.v+cv*s.v*z):s.v*Math.exp(sg*z-sg*sg/2)}sums.push(t)}sums.sort((a,b)=>a-b);
  hero.insertAdjacentHTML('beforeend','<div class="cb-dc-sum"><div><small>Total projection</small><b>'+tot.toFixed(1)+'</b></div><div><small>Floor (10%)</small><b>'+sums[Math.floor(N*.1)].toFixed(1)+'</b></div><div><small>Median</small><b>'+sums[Math.floor(N*.5)].toFixed(1)+'</b></div><div><small>Ceiling (90%)</small><b>'+sums[Math.floor(N*.9)].toFixed(1)+'</b></div><div><small>Starters</small><b>'+starters.length+'/'+rows.length+'</b></div></div>')}
 const col=$q('.lineup-grid .research-column');if(col&&!col.querySelector('.cb-cadence')&&starters.length){const order=['THU','FRI','SAT','SUN','MON'],by={};starters.forEach(s=>{const k=s.g?s.g.day:'BYE';(by[k]=by[k]||[]).push(s)});
  const html=order.concat(['BYE']).filter(k=>by[k]).map(k=>{const done=by[k].every(s=>s.g&&s.g.d<today);return '<div class="cb-cad '+(done?'done':'')+'"><b>'+({THU:'Thursday',FRI:'Friday',SAT:'Saturday',SUN:'Sunday',MON:'Monday',BYE:'Bye / no game'}[k])+(done?' · locked':'')+'</b><small>'+by[k].length+' starter'+(by[k].length>1?'s':'')+'</small><ul>'+by[k].map(s=>'<li>'+esc(s.nm)+' <span>('+esc(s.slot||s.pos)+')'+(s.g?' '+(s.g.home?'vs ':'@ ')+s.g.opp:'')+'</span></li>').join('')+'</ul></div>'}).join('');
  col.insertAdjacentHTML('afterbegin','<section class="card cb-cadence"><div class="card-header"><h3>Kickoff lock cadence</h3><span class="small-label">BY GAME DAY</span></div><div class="card-body">'+html+'<p class="trade-note">Sleeper locks each player at his own kickoff. Exact kickoff times aren’t in the public schedule feed, so check late games in Sleeper.</p></div></section>')}
 $$('.bench-player').forEach(b=>{if(b.dataset.cbd)return;const pid=pidFor(M,b.querySelector('b')?.textContent||'');if(!pid)return;b.dataset.cbd=1;const pos=M.pos(pid),v=(M.val[pid]||[0])[0],g=gameOf(pid);
  const worst=starters.filter(s=>s.pos===pos).sort((a,c)=>a.v-c.v)[0];const better=worst&&v>worst.v+.5;
  b.insertAdjacentHTML('beforeend','<span class="cb-bench"><span class="slot '+esc(pos)+'">'+esc(pos)+'</span>'+(g?(g.home?'vs ':'@ ')+g.opp+' · '+g.day:'BYE')+'<b>'+v.toFixed(1)+'</b>'+(better?'<em>Start over '+esc(worst.nm)+' (+'+(v-worst.v).toFixed(1)+')</em>':'')+'</span>');if(better)b.classList.add('cb-swap')})}
function run(){try{topbar();status();buttons();sidebar();winProb();tiles();depth()}catch(e){}}
if(typeof render==='function'){const prev=render;render=function(){const r=prev.apply(this,arguments);run();return r}}
let pend=false;new MutationObserver(()=>{if(pend)return;pend=true;requestAnimationFrame(()=>{pend=false;run()})}).observe(document.body,{childList:true,subtree:true});
run();
})();
