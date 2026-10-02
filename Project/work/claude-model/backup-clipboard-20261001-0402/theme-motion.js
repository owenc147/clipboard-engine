/* Binocular motion layer: view-enter stagger, score count-up, radar sweep. Respects Reduce Motion. */
(function(){
const reduce=matchMedia('(prefers-reduced-motion: reduce)').matches;
function sweep(){document.querySelectorAll('.hero,.research-intro,.desk-hero,.lineup-hero').forEach(h=>{if(!h.querySelector('.bnc-sweep')){const s=document.createElement('span');s.className='bnc-sweep';s.setAttribute('aria-hidden','true');h.prepend(s)}})}
function countUp(){if(reduce)return;document.querySelectorAll('.scores > span, .pt-odds').forEach(el=>{const m=(el.textContent||'').trim().match(/^(\d+(?:\.\d+)?)(%?)$/);if(!m||el.dataset.bncDone===m[0])return;const end=parseFloat(m[1]),dec=(m[1].split('.')[1]||'').length,suf=m[2],t0=performance.now(),D=650;el.dataset.bncDone=m[0];(function f(t){const p=Math.min(1,(t-t0)/D),e=1-Math.pow(1-p,3);el.textContent=(end*e).toFixed(dec)+suf;if(p<1)requestAnimationFrame(f);else el.textContent=m[0]})(t0)})}
let lastView=null;
function after(){try{const c=document.getElementById('content');const v=typeof currentView!=='undefined'?currentView:null;if(c&&v!==lastView&&!reduce){c.classList.remove('bnc-enter');void c.offsetWidth;c.classList.add('bnc-enter');setTimeout(()=>c.classList.remove('bnc-enter'),700)}lastView=v;sweep();countUp()}catch(e){}}
if(typeof render==='function'){const prev=render;render=function(){const r=prev.apply(this,arguments);after();return r}}
new MutationObserver(()=>{sweep()}).observe(document.body,{childList:true,subtree:true});
after();
})();
