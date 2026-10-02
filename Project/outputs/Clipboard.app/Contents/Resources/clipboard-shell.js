/* Clipboard shell — header, copy, settings drawer and motion.
   Sits on top of the existing app; touches presentation only. */
(function(){
const reduce=matchMedia('(prefers-reduced-motion: reduce)').matches;
const $q=s=>document.querySelector(s),$$=s=>[...document.querySelectorAll(s)];

/* 1. Tab names, in the voice of a sideline */
const TABS={'overview-view':'Gameday','research-view':'Call sheet','lineup-view':'Depth chart','radar-view':'Press box',
  'moves-view':'The wire','suggestions-view':'Mailbag','desk-view':'Front office','model-view':'Title odds'};
function relabel(){for(const id in TABS){const b=document.getElementById(id);if(b&&b.dataset.cb!==TABS[id]){b.textContent=TABS[id];b.dataset.cb=TABS[id];b.title=TABS[id]}}}

/* 2. Settings drawer: profile / username / week live behind one button */
function settings(){const bar=$q('.top-actions');if(!bar||$q('.cb-settings-btn'))return;
  const b=document.createElement('button');b.className='action cb-settings-btn';b.type='button';b.textContent='Team settings';b.setAttribute('aria-expanded','false');
  b.onclick=()=>{const open=document.body.classList.toggle('cb-settings-open');b.setAttribute('aria-expanded',open);if(open)$q('#user')?.focus()};
  bar.prepend(b);
  const r=$q('#refresh');if(r)r.textContent='Pull latest';
  const ex=[...bar.querySelectorAll('.action')].find(x=>/Export/.test(x.textContent));if(ex)ex.textContent='Export';
  const cp=[...bar.querySelectorAll('.action')].find(x=>/Copy brief/.test(x.textContent));if(cp)cp.textContent='Copy notes'}

/* 3. Header reads like the top of a real call sheet */
const OPP={};function header(){try{
  const k=$q('#season'),h=$q('main h1');if(!k||!h)return;
  const league=$q('.league-head h2')?.textContent?.trim()||$q('.nav.active .nav-name')?.textContent?.trim()||'';
  const names=$$('.hero .team-name').map(e=>e.textContent.trim());const key=($q('.nav.active .nav-name')?.textContent||'')+'|'+(typeof reportWeek!=='undefined'?reportWeek:'');if(names[1])OPP[key]=names[1];else if(OPP[key])names[1]=OPP[key];
  const wk=(typeof reportWeek!=='undefined'&&reportWeek)||(typeof RESEARCH!=='undefined'&&RESEARCH.week)||'';
  const kt=[league,wk?'Week '+wk:'','Call sheet'].filter(Boolean).join('  ·  '),ht=names[1]?'vs. '+names[1]:'Know every call.';
  if(k.textContent!==kt)k.textContent=kt;if(h.textContent!==ht)h.textContent=ht;
}catch(e){}}

/* 4. Copy pass on fixed strings the core app renders */
const COPY=[['Current roster','Roster'],['Waiver watch','On the wire'],['Saved league data','Working from the last saved pull.'],
  ['Review your suggested starters','Your starters are set — give them a look'],['View lineup →','Open depth chart'],['Read the reasoning ↗','See the call'],
  ['No points recorded','No snaps yet'],['As of last refresh','Last pull'],['Opponent lineup','Their lineup'],['Evidence notebook','Receipts'],
  ['Waiver radar','Wire check'],['Your starting point.','Depth chart & starting personnel'],['Suggested starters','Starting personnel'],['The close calls','Coach’s tactical audit'],['Suggested bench & reserve','Bench reserve & swaps'],['What could change this call?','What flips this call?'],['League standing','Standing'],['No flagged injuries or empty slots in the cached roster.','Everyone’s healthy and every slot is filled.']];
function copy(root){const w=document.createTreeWalker(root||document.body,NodeFilter.SHOW_TEXT);let n;while(n=w.nextNode()){const t=n.nodeValue.trim();if(!t)continue;for(const [a,b] of COPY){if(t===a){n.nodeValue=n.nodeValue.replace(a,b);break}}}}

/* 5. Motion: content slides in on a view change; scores count up like a scoreboard */
function countUp(){if(reduce)return;$$('.scores > span, .pt-odds, .week-badge b').forEach(el=>{const m=(el.textContent||'').trim().match(/^#?(\d+(?:\.\d+)?)(%?)$/);
  if(!m||el.dataset.cbDone===m[0])return;const pre=el.textContent.trim().startsWith('#')?'#':'',end=parseFloat(m[1]),dec=(m[1].split('.')[1]||'').length,suf=m[2],t0=performance.now(),D=700;
  el.dataset.cbDone=m[0];(function f(t){const p=Math.min(1,(t-t0)/D),e=1-Math.pow(1-p,4);el.textContent=pre+(end*e).toFixed(dec)+suf;if(p<1)requestAnimationFrame(f);else el.textContent=m[0]})(t0)})}

/* 6. Team colours: the fan picks an NFL team; the sheet dresses in it. Colours only, no logos. */
const NFL={AFC:{East:[['BUF','Buffalo','Bills','#00338D','#C60C30'],['MIA','Miami','Dolphins','#008E97','#FC4C02'],['NE','New England','Patriots','#002244','#C60C30'],['NYJ','New York','Jets','#125740','#FFFFFF']],
 North:[['BAL','Baltimore','Ravens','#241773','#9E7C0C'],['CIN','Cincinnati','Bengals','#FB4F14','#000000'],['CLE','Cleveland','Browns','#311D00','#FF3C00'],['PIT','Pittsburgh','Steelers','#FFB612','#101820']],
 South:[['HOU','Houston','Texans','#03202F','#A71930'],['IND','Indianapolis','Colts','#002C5F','#A2AAAD'],['JAX','Jacksonville','Jaguars','#006778','#D7A22A'],['TEN','Tennessee','Titans','#0C2340','#4B92DB']],
 West:[['DEN','Denver','Broncos','#FB4F14','#002244'],['KC','Kansas City','Chiefs','#E31837','#FFB81C'],['LV','Las Vegas','Raiders','#000000','#A5ACAF'],['LAC','Los Angeles','Chargers','#0080C6','#FFC20E']]},
 NFC:{East:[['DAL','Dallas','Cowboys','#003594','#869397'],['NYG','New York','Giants','#0B2265','#A71930'],['PHI','Philadelphia','Eagles','#004C54','#A5ACAF'],['WAS','Washington','Commanders','#5A1414','#FFB612']],
 North:[['CHI','Chicago','Bears','#0B162A','#C83803'],['DET','Detroit','Lions','#0076B6','#B0B7BC'],['GB','Green Bay','Packers','#203731','#FFB612'],['MIN','Minnesota','Vikings','#4F2683','#FFC62F']],
 South:[['ATL','Atlanta','Falcons','#A71930','#000000'],['CAR','Carolina','Panthers','#0085CA','#101820'],['NO','New Orleans','Saints','#D3BC8D','#101820'],['TB','Tampa Bay','Buccaneers','#D50A0A','#FF7900']],
 West:[['ARI','Arizona','Cardinals','#97233F','#FFB612'],['LAR','Los Angeles','Rams','#003594','#FFA300'],['SF','San Francisco','49ers','#AA0000','#B3995D'],['SEA','Seattle','Seahawks','#002244','#69BE28']]}};
const ALL={};for(const c in NFL)for(const d in NFL[c])for(const t of NFL[c][d])ALL[t[0]]=t;
const hx=h=>[1,3,5].map(i=>parseInt(h.slice(i,i+2),16)),toHex=a=>'#'+a.map(v=>Math.round(v).toString(16).padStart(2,'0')).join('');
const lum=h=>{const c=hx(h).map(v=>{v/=255;return v<=.03928?v/12.92:Math.pow((v+.055)/1.055,2.4)});return .2126*c[0]+.7152*c[1]+.0722*c[2]};
const contrast=(a,b)=>{const x=lum(a),y=lum(b);return (Math.max(x,y)+.05)/(Math.min(x,y)+.05)};
const lift=(h,bg,min)=>{let c=hx(h),k=0,o=h;while(contrast(o,bg)<min&&k<20){k++;c=c.map(v=>v+(255-v)*.12);o=toHex(c)}return o};
const SHEET='#1a1814';
function applyTeam(code){const r=document.documentElement.style,t=ALL[code];
  if(!t){['--accent','--accent-2','--team-bg','--team-fg','--team-bar'].forEach(v=>r.removeProperty(v));return}
  const [,, ,p,s]=t;const sat=h=>{const c=hx(h);return Math.max(...c)-Math.min(...c)};
  const grey=h=>sat(h)<40;const pOK=contrast(p,SHEET)>=3,sOK=contrast(s,SHEET)>=3&&!grey(s);
  const main=pOK?p:(sOK?s:p),other=main===p?s:p;const a=lift(main,SHEET,4.6),b=lift(other,SHEET,4.6);
  const bg=lum(p)<.02&&grey(p)?s:p;
  r.setProperty('--accent',a);r.setProperty('--accent-2',b===a?'#d8a646':b);r.setProperty('--team-bg',bg);r.setProperty('--team-fg',lum(bg)>.4?'#15130f':'#ffffff');r.setProperty('--team-bar',a)}
function getTeam(){try{return localStorage.getItem('clipboard-team')}catch(e){return null}}
function setTeam(code){try{localStorage.setItem('clipboard-team',code||'HOUSE')}catch(e){}applyTeam(code);header();chip()}
function chip(){const b=$q('.cb-settings-btn');if(!b)return;const t=ALL[getTeam()];b.innerHTML='<span class="cb-chip"></span>'+(t?t[0]+' · ':'')+'Team settings'}
function picker(){if($q('.cb-pick'))return;const cur=getTeam();let sel=ALL[cur]?cur:null;
  const tile=t=>{const fg=lum(t[3])>.4?'#15130f':'#fff';return '<button class="cb-team'+(cur===t[0]?' on':'')+'" data-t="'+t[0]+'" style="--c1:'+t[3]+';--c2:'+t[4]+';--fg:'+fg+'"><b>'+t[0]+'</b><span>'+t[1]+' '+t[2]+'</span></button>'};
  let h='<div class="cb-pick" role="dialog" aria-modal="true" aria-label="Pick your team"><div class="cb-pick-inner">'+
   '<div class="cb-pk-head"><div><span class="cb-pk-tag">Franchise alignment</span><h2>Who do you ride with?</h2><p>Pick your NFL team. Clipboard takes on its colours: header bars, tabs, alerts and your score. Switch any time from Team settings.</p></div>'+
   '<div class="cb-pk-sel"><small>Selected franchise</small><b class="cb-pk-name">House colours</b></div></div>'+
   '<div class="cb-pk-filter" role="tablist"><button class="on" data-f="all">All 32 clubs</button><button data-f="AFC">AFC (16)</button><button data-f="NFC">NFC (16)</button><span>Click a tile, then confirm</span></div><div class="cb-pk-confs">';
  for(const c in NFL){h+='<section class="cb-pk-conf" data-c="'+c+'"><div class="cb-conf"><i></i>'+c+' // '+(c==='AFC'?'American':'National')+' Football Conference<small>16 teams · 4 divisions</small></div><div class="cb-grid">';
   let k=0;for(const d in NFL[c]){k++;h+='<div class="cb-div"><small>'+c+' '+d+'<em>DIV // 0'+(c==='AFC'?k:k+4)+'</em></small><div class="cb-tiles">'+NFL[c][d].map(tile).join('')+'</div></div>'}h+='</div></section>'}
  h+='</div><div class="cb-pk-foot"><span class="cb-pk-sw"></span><div><small>Ready to deploy · <span class="cb-pk-st">No team selected</span></small><b class="cb-pk-big">Neutral clipboard masonite</b></div><button class="cb-house" data-t="HOUSE">No team — keep house</button><button class="cb-pk-go">Confirm affiliation →</button></div></div></div>';
  document.body.insertAdjacentHTML('beforeend',h);const el=$q('.cb-pick');
  const show=()=>{const t=ALL[sel];el.querySelectorAll('.cb-team').forEach(b=>b.classList.toggle('on',b.dataset.t===sel));
    el.querySelector('.cb-pk-name').textContent=t?t[1]+' '+t[2]:'House colours';el.querySelector('.cb-pk-big').textContent=t?t[1]+' '+t[2]:'Neutral clipboard masonite';
    el.querySelector('.cb-pk-st').textContent=t?t[0]+' selected':'No team selected';const sw=el.querySelector('.cb-pk-sw');sw.style.background=t?'linear-gradient(135deg,'+t[3]+' 60%,'+t[4]+' 60%)':'#2a211b';if(t)applyTeam(sel);else applyTeam(null)};
  el.addEventListener('click',e=>{const f=e.target.closest('[data-f]');if(f){el.querySelectorAll('[data-f]').forEach(x=>x.classList.toggle('on',x===f));el.querySelectorAll('.cb-pk-conf').forEach(s=>s.hidden=f.dataset.f!=='all'&&s.dataset.c!==f.dataset.f);return}
    if(e.target.closest('.cb-pk-go')){setTeam(sel);el.remove();return}
    const b=e.target.closest('[data-t]');if(!b)return;if(b.dataset.t==='HOUSE'){setTeam(null);el.remove();return}sel=b.dataset.t;show()});
  el.addEventListener('keydown',e=>{if(e.key==='Escape'){setTeam(ALL[cur]?cur:null);el.remove()}});show();el.querySelector('.cb-team.on,.cb-team')?.focus()}
function teamUI(){const tb=$q('.toolbar');if(tb&&!$q('.cb-team-open')){const b=document.createElement('button');b.type='button';b.className='action cb-team-open';b.textContent='Team colours';b.onclick=picker;tb.insertBefore(b,$q('#refresh'))}chip()}
window.clipboardPickTeam=picker;
applyTeam(getTeam());
let lastView=null;
function after(){try{relabel();settings();teamUI();header();copy($q('main'));
  const c=$q('#content'),v=typeof currentView!=='undefined'?currentView:null;
  if(c&&v!==lastView&&!reduce){c.classList.remove('cb-enter');void c.offsetWidth;c.classList.add('cb-enter');setTimeout(()=>c.classList.remove('cb-enter'),500)}
  lastView=v;countUp()}catch(e){}}
if(typeof render==='function'){const prev=render;render=function(){const r=prev.apply(this,arguments);after();return r}}
let pend=false;new MutationObserver(()=>{if(pend)return;pend=true;requestAnimationFrame(()=>{pend=false;relabel();copy($q('main'));header()})}).observe(document.body,{childList:true,subtree:true});
after();
if(!getTeam())setTimeout(picker,350);
})();
