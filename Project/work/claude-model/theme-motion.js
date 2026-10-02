/* Clipboard motion layer: view-enter stagger, score count-up, play-diagram draw. Respects Reduce Motion. */
(function(){
const reduce=matchMedia('(prefers-reduced-motion: reduce)').matches;
function sweep(){document.querySelectorAll('.hero,.research-intro,.desk-hero,.lineup-hero').forEach(h=>{if(!h.querySelector('.cb-play'))h.insertAdjacentHTML('afterbegin','<svg class="cb-play" viewBox="0 0 300 220" aria-hidden="true"><path class="los" d="M10 150H290"/><g class="o"><circle cx="70" cy="168" r="9"/><circle cx="150" cy="168" r="9"/><circle cx="230" cy="168" r="9"/><circle cx="150" cy="200" r="9"/></g><g class="x"><path d="M95 112l14 14m0-14l-14 14"/><path d="M196 112l14 14m0-14l-14 14"/></g><path class="rt" d="M70 156V70c0-20 20-30 50-30h40"/><path class="ah" d="M152 32l10 8-10 8"/><path class="rt d2" d="M230 156V100l-40-50"/><path class="ah" d="M186 62l3-14 12 6"/><path class="rt d3" d="M150 188c40 0 70-10 100-40"/></svg>')})}
function countUp(){if(reduce)return;document.querySelectorAll('.scores > span, .pt-odds').forEach(el=>{const m=(el.textContent||'').trim().match(/^(\d+(?:\.\d+)?)(%?)$/);if(!m||el.dataset.bncDone===m[0])return;const end=parseFloat(m[1]),dec=(m[1].split('.')[1]||'').length,suf=m[2],t0=performance.now(),D=650;el.dataset.bncDone=m[0];(function f(t){const p=Math.min(1,(t-t0)/D),e=1-Math.pow(1-p,3);el.textContent=(end*e).toFixed(dec)+suf;if(p<1)requestAnimationFrame(f);else el.textContent=m[0]})(t0)})}
let lastView=null;
function after(){try{const c=document.getElementById('content');const v=typeof currentView!=='undefined'?currentView:null;if(c&&v!==lastView&&!reduce){c.classList.remove('bnc-enter');void c.offsetWidth;c.classList.add('bnc-enter');setTimeout(()=>c.classList.remove('bnc-enter'),700)}lastView=v;sweep();countUp()}catch(e){}}
if(typeof render==='function'){const prev=render;render=function(){const r=prev.apply(this,arguments);after();return r}}
new MutationObserver(()=>{sweep()}).observe(document.body,{childList:true,subtree:true});
after();
})();
