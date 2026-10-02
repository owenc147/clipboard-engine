// Clipboard tracking: (1) model scorecard — logs each league's weekly win probability and checks it against
// the real result once the week is played (Brier score, hit rate, calibration); (2) offer log — one click to
// record a sent offer and its outcome (accepted / declined / countered) with response time. Resolved offers
// feed the acceptance model's labels. Stored in this Mac's app storage (localStorage); "Copy log" exports JSON.
(function(){
const PK='clipboard-predlog',OK='clipboard-offers';
const load=k=>{try{return JSON.parse(localStorage.getItem(k)||'[]')}catch(e){return[]}},save=(k,v)=>{try{localStorage.setItem(k,JSON.stringify(v))}catch(e){}};
const e=v=>esc(String(v??'')),p1=x=>(100*x).toFixed(1)+'%';
const hrs=ms=>{const h=ms/36e5;return h<1?Math.round(h*60)+' min':h<48?h.toFixed(1)+' h':(h/24).toFixed(1)+' days'};

/* ---- 1. prediction log ---- */
function record(lid){const R=modelRuns[lid];if(!R||!R.done||!modelData)return;const M=R.M,me=M.L.me,t=M.L.teams[me],b=R.acc.res[0],n=b.n;
 const log=load(PK);const key=lid+'|'+modelData.built_at;if(log.some(x=>x.key===key))return;
 log.push({key,lid,league:M.L.name,week:modelData.week,wins:t.w,losses:t.l,p:+(b.wk[0]/n).toFixed(4),title:+(b.title/n).toFixed(4),po:+(b.po/n).toFixed(4),ts:Date.now()});
 save(PK,log.slice(-400))}
function resolved(){const log=load(PK),out=[];const by={};
 for(const x of log){const k=x.lid+'|'+x.week;if(!by[k]||x.ts>by[k].ts)by[k]=x} // latest prediction made before each week
 for(const k in by){const a=by[k];const nxt=Object.values(by).filter(y=>y.lid===a.lid&&y.week===a.week+1)[0];if(!nxt)continue;
  const g=(nxt.wins+nxt.losses)-(a.wins+a.losses);if(g!==1)continue;out.push({...a,won:nxt.wins>a.wins?1:0})}
 return out.sort((x,y)=>x.week-y.week||x.league.localeCompare(y.league))}
function scorecard(){const r=resolved(),pend=load(PK).length;
 if(!r.length)return `<section class="desk-card cb-track"><h3>Model scorecard</h3><p>Logging this week’s win probabilities for each league. Results appear once a logged week has been played and the model is reloaded the next week (${pend} prediction${pend===1?'':'s'} logged so far). Brier score: 0 is perfect, 0.25 is a coin flip.</p></section>`;
 const brier=r.reduce((s,x)=>s+(x.p-x.won)**2,0)/r.length,hit=r.filter(x=>(x.p>=.5)===!!x.won).length/r.length;
 const bins=[[0,.4],[.4,.6],[.6,1.01]].map(([a,b])=>{const z=r.filter(x=>x.p>=a&&x.p<b);return z.length?`<span>${Math.round(a*100)}–${Math.min(100,Math.round(b*100))}%: predicted ${p1(z.reduce((s,x)=>s+x.p,0)/z.length)}, won ${p1(z.reduce((s,x)=>s+x.won,0)/z.length)} (${z.length})</span>`:''}).join('');
 return `<section class="desk-card cb-track"><h3>Model scorecard</h3><div class="cb-dc-sum"><div><small>Weeks scored</small><b>${r.length}</b></div><div><small>Brier score</small><b>${brier.toFixed(3)}</b></div><div><small>Called right</small><b>${p1(hit)}</b></div><div><small>Coin-flip Brier</small><b>0.250</b></div></div>
  <p class="cb-bins">${bins}</p><table class="table"><tr><td>Week</td><td>League</td><td>Win prob</td><td>Result</td></tr>${r.slice(-12).reverse().map(x=>`<tr><td>${x.week}</td><td>${e(x.league)}</td><td>${p1(x.p)}</td><td>${x.won?'W':'L'}</td></tr>`).join('')}</table></section>`}

/* ---- 2. offer log ---- */
function bestRows(lid){const R=modelRuns[lid];if(!R||!R.done)return[];const base=R.acc.res[0],n=base.n;
 return R.cands.map((c,i)=>{const s=R.acc.res[i+1],d=(s.title-base.title)/n;return {c,d,ev:c.p*d,before:base.title/n,after:s.title/n}}).filter(x=>x.d>0).sort((a,b)=>b.ev-a.ev)}
function logSent(lid,i){const x=bestRows(lid)[i];if(!x)return;const M=modelRuns[lid].M,o=load(OK);
 o.push({id:Date.now().toString(36),lid,league:M.L.name,partner:M.L.teams[x.c.r].name,give:x.c.give,get:x.c.get,giveN:x.c.give.map(mName),getN:x.c.get.map(mName),p:+x.c.p.toFixed(3),before:+x.before.toFixed(4),after:+x.after.toFixed(4),sent:Date.now(),status:'sent'});save(OK,o);mRender()}
function setStatus(id,st){const o=load(OK);const x=o.find(y=>y.id===id);if(!x)return;x.status=st;x.resolved=Date.now();save(OK,o);mRender()}
function offerPanel(){const o=load(OK);if(!o.length)return `<section class="desk-card cb-track"><h3>Offer log</h3><p>Hit “Log as sent” next to any offer above after you send it in Sleeper, then mark it accepted, declined or countered here. Every resolved offer trains the acceptance model.</p></section>`;
 const done=o.filter(x=>x.status!=='sent'),acc=done.filter(x=>x.status==='accepted');
 const rate=done.length?acc.length/done.length:null,pred=done.length?done.reduce((s,x)=>s+Math.min(.9,x.p),0)/done.length:null,lat=done.length?done.reduce((s,x)=>s+(x.resolved-x.sent),0)/done.length:null;
 const rows=o.slice().reverse().slice(0,20).map(x=>`<tr><td>${e(x.league)}<br><b>${e(x.partner)}</b></td><td>${e(x.giveN.join(' + '))} → ${e(x.getN.join(' + '))}</td><td>${Math.round(Math.min(.9,x.p)*100)}%</td><td>${x.status==='sent'?`<span class="cb-ol-btns"><button onclick="cbOffer('${x.id}','accepted')">Accepted</button><button onclick="cbOffer('${x.id}','declined')">Declined</button><button onclick="cbOffer('${x.id}','countered')">Countered</button></span><small>sent ${hrs(Date.now()-x.sent)} ago</small>`:`<b class="cb-ol-${x.status}">${x.status}</b><small>in ${hrs(x.resolved-x.sent)}</small>`}</td></tr>`).join('');
 return `<section class="desk-card cb-track"><h3>Offer log</h3><div class="cb-dc-sum"><div><small>Offers logged</small><b>${o.length}</b></div><div><small>Resolved</small><b>${done.length}</b></div><div><small>Accepted</small><b>${rate==null?'—':p1(rate)}</b></div><div><small>Model expected</small><b>${pred==null?'—':p1(pred)}</b></div><div><small>Avg response</small><b>${lat==null?'—':hrs(lat)}</b></div></div>
  <table class="table"><tr><td>Partner</td><td>You send → you get</td><td>Model</td><td>Outcome</td></tr>${rows}</table><p><button onclick="cbCopyLog()">Copy log as JSON</button></p></section>`}
window.cbOffer=setStatus;window.cbLogSent=logSent;
window.cbCopyLog=()=>{const txt=JSON.stringify({predictions:load(PK),offers:load(OK)},null,1);try{navigator.clipboard.writeText(txt)}catch(err){}const t=document.createElement('textarea');t.value=txt;document.body.append(t);t.select();try{document.execCommand('copy')}catch(err){}t.remove()};

/* resolved offers become acceptance-model labels (partner view: r = partner received = what you gave) */
if(typeof mLabels==='function'){const prev=mLabels;mLabels=function(){const base=prev();const seen=new Set(base.map(l=>l.lid+'|'+l.r.join()+'|'+l.g.join()));
 const extra=load(OK).filter(x=>x.status==='accepted'||x.status==='declined').map(x=>({lid:x.lid,r:x.give,g:x.get,y:x.status==='accepted'?1:0})).filter(l=>!seen.has(l.lid+'|'+l.r.join()+'|'+l.g.join()));
 return [...base,...extra]}}

/* hook into the Title odds render */
if(typeof window.mRender==='function'){const before=window.mRender;window.mRender=mRender=function(){before();try{const lid=mLeagueId();if(!lid)return;record(lid);
 const box=document.querySelector('#content .desk');if(!box||box.querySelector('.cb-track'))return;
 const rows=bestRows(lid);const tbl=[...box.querySelectorAll('.desk-card')].find(c=>/Best offers/i.test(c.querySelector('h3')?.textContent||''))?.querySelector('table');
 if(tbl){const tr=[...tbl.querySelectorAll('tr')];if(tr[0]&&!tr[0].querySelector('.cb-log-h'))tr[0].insertAdjacentHTML('beforeend','<td class="cb-log-h">Log</td>');
  const logged=load(OK).filter(x=>x.lid===lid&&x.status==='sent');tr.slice(1).forEach((r,i)=>{const x=rows[i];if(!x||r.querySelector('.cb-log'))return;const already=logged.some(o=>o.give.join()===x.c.give.join()&&o.get.join()===x.c.get.join());
   r.insertAdjacentHTML('beforeend',`<td class="cb-log">${already?'<small>Logged</small>':`<button onclick="cbLogSent('${lid}',${i})">Log as sent</button>`}</td>`)})}
 const foot=box.querySelector('.desk-foot');const html=offerPanel()+scorecard();if(foot)foot.insertAdjacentHTML('beforebegin',html);else box.insertAdjacentHTML('beforeend',html)}catch(err){console.error('tracking',err)}}}
})();
