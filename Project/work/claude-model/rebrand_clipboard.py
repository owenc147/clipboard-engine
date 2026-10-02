import re,pathlib
R=pathlib.Path('outputs/Binocular.app/Contents/Resources'); W=pathlib.Path('work/claude-model')
# 1 theme colours
css=(W/'theme-primetime.css').read_text()
for a,b in {'4fe39a':'cdf03a','8ff5c0':'e6ff8a','167a4f':'6b8a0f','9af7c6':'eeff9e','0b2a1d':'1c2208','0a2018':'181d07','0e2a1f':'1e240b','0c1a14':'14170a','17332a':'2c3310','04140c':'121500'}.items():
    css=re.sub(a,b,css,flags=re.I)
css=css.replace('/* Binocular Optic theme — the app\'s own identity: ink black, optic green, scope reticle.','/* Clipboard theme — ink black, marker volt, X-and-O play diagrams.')
css+='''
/* ===================== Clipboard brand layer ===================== */
html body h1{text-transform:none;font-size:36px;letter-spacing:-1.3px}
html body .brand{font:800 21px var(--pt-round);letter-spacing:-.6px}
html body .logo{width:40px;height:40px;display:grid;place-items:center;background:linear-gradient(145deg,#ecff8a,#b8e01e);color:#121500;border-radius:11px;box-shadow:0 6px 22px #cdf03a40,inset 0 1px 0 #ffffff60}
html body .logo svg{width:30px;height:30px;fill:none}
html body .hero::after,html body .research-intro::after,html body .desk-hero::after,html body .lineup-hero::after{content:none!important}
html body .bnc-sweep{display:none!important}
.cb-play{position:absolute;right:3%;top:50%;transform:translateY(-50%);width:min(340px,36%);height:auto;pointer-events:none;opacity:.55;z-index:0}
.cb-play *{fill:none;stroke:#cdf03a;stroke-linecap:round;stroke-linejoin:round}
.cb-play .o{stroke:#f4f4f2;stroke-width:3}.cb-play .x{stroke:#f4f4f2;stroke-width:3.2}
.cb-play .rt{stroke-width:2.6;stroke-dasharray:240;stroke-dashoffset:240;animation:cb-draw 1.1s var(--ease-out) .25s forwards}
.cb-play .rt.d2{animation-delay:.45s}.cb-play .rt.d3{animation-delay:.65s;stroke-dasharray:2 7;stroke-dashoffset:0;opacity:0;animation:bnc-fade .6s var(--ease) .9s forwards}
.cb-play .ah{stroke-width:2.6;opacity:0;animation:bnc-fade .3s var(--ease) 1.2s forwards}
.cb-play .los{stroke:#ffffff26;stroke-width:1.2;stroke-dasharray:4 6}
@keyframes cb-draw{to{stroke-dashoffset:0}}
html body .hero>*:not(.cb-play),html body .research-intro>*:not(.cb-play),html body .desk-hero>*:not(.cb-play){position:relative;z-index:1}
html body .research-intro .stamp{z-index:2}
@media (prefers-reduced-motion:reduce){.cb-play .rt{stroke-dashoffset:0;animation:none}.cb-play .ah,.cb-play .rt.d3{opacity:1;animation:none}}
'''
(W/'theme-primetime.css').write_text(css)
# 2 motion js: play diagram instead of sweep
js=(W/'theme-motion.js').read_text()
PLAY='<svg class="cb-play" viewBox="0 0 300 220" aria-hidden="true"><path class="los" d="M10 150H290"/><g class="o"><circle cx="70" cy="168" r="9"/><circle cx="150" cy="168" r="9"/><circle cx="230" cy="168" r="9"/><circle cx="150" cy="200" r="9"/></g><g class="x"><path d="M95 112l14 14m0-14l-14 14"/><path d="M196 112l14 14m0-14l-14 14"/></g><path class="rt" d="M70 156V70c0-20 20-30 50-30h40"/><path class="ah" d="M152 32l10 8-10 8"/><path class="rt d2" d="M230 156V100l-40-50"/><path class="ah" d="M186 62l3-14 12 6"/><path class="rt d3" d="M150 188c40 0 70-10 100-40"/></svg>'
js=js.replace("function sweep(){document.querySelectorAll('.hero,.research-intro,.desk-hero,.lineup-hero').forEach(h=>{if(!h.querySelector('.bnc-sweep')){const s=document.createElement('span');s.className='bnc-sweep';s.setAttribute('aria-hidden','true');h.prepend(s)}})}",
 "function sweep(){document.querySelectorAll('.hero,.research-intro,.desk-hero,.lineup-hero').forEach(h=>{if(!h.querySelector('.cb-play'))h.insertAdjacentHTML('afterbegin','"+PLAY+"')})}")
js=js.replace('/* Binocular motion layer: view-enter stagger, score count-up, radar sweep.','/* Clipboard motion layer: view-enter stagger, score count-up, play-diagram draw.')
assert 'cb-play' in js
(W/'theme-motion.js').write_text(js)
# 3 index.html
MARK='<svg viewBox="0 0 40 40" aria-hidden="true" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"><rect x="13" y="1.5" width="14" height="5.5" rx="2.5" fill="currentColor" stroke="none"/><path d="M6.5 13l7 7m0-7l-7 7" stroke-width="3.6"/><circle cx="29" cy="30" r="5" stroke-width="3.4"/><path d="M17 14.5c7-2 15 1 16 8" stroke-width="3.2"/><path d="M29 20.5l4 3.5 3-4.3" stroke-width="3.2"/></svg>'
h=(R/'index.html').read_text()
h=re.sub(r'<div class="logo"><svg.*?</svg></div>binocular</div>','<div class="logo">'+MARK+'</div>clipboard</div>',h,count=1,flags=re.S)
h=h.replace('<title>Binocular','<title>Clipboard').replace('FOOTBALL SCOUTING DESK','FANTASY SIDELINE').replace('<h1>See the whole field.</h1>','<h1>Know every call.</h1>').replace('Read the field.<br>Independent Sleeper companion','Never takes a snap.<br>Knows every call.')
assert 'clipboard</div>' in h and 'Know every call' in h
(R/'index.html').write_text(h)
# 4 visible strings in JS
for f in ['binocular.js','research.js','lineup.js','desk.js','model-view.js','radar.js','moves.js','suggestions.js']:
    p=R/f;t=p.read_text();o=t
    t=t.replace('BINOCULAR FIELD NOTES','CLIPBOARD · CALL SHEET').replace("'SCOUTED / '","'CALLED / '").replace('BINOCULAR','CLIPBOARD')
    t=re.sub(r'\bBinocular\b','Clipboard',t)
    if t!=o:p.write_text(t);print('updated',f)
# 5 plist
P=pathlib.Path('outputs/Binocular.app/Contents/Info.plist');t=P.read_text()
t=t.replace('<string>Binocular</string>','<string>Clipboard</string>').replace('<string>BinocularStadium.icns</string>','<string>Clipboard.icns</string>');P.write_text(t)
for f in ['theme-primetime.css','theme-motion.js']:(R/f).write_text((W/f).read_text())
print('done')
