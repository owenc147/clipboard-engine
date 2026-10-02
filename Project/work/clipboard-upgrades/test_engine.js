const assert=require('assert');require('./stage/model-engine.js');const T=globalThis.TitleModel;
function make(pos,score,stats){const keys=Object.keys(stats).filter(k=>k!=='pts_ppr');return {season:2026,week:4,keys,players:{p:['Test',pos,'BUF','',26]},leagues:{l:{ptd:4,score,bonus:{},slots:[pos],last:14,teams:{1:{players:['p']}},qbs:1}},proj:{p:[[stats.pts_ppr||0,...keys.map(k=>stats[k])]]},hist:{},s26:{}}}
// Raw points are the direct scoring output before the unchanged learned history blend.
let d=make('QB',{pass_cmp:.1,pass_yd:2/45,pass_td:4,pass_int:-1},{pts_ppr:20,pass_cmp:25,pass_yd:300,pass_td:2,pass_int:1});assert(Math.abs(T.prepare(d,'l').raw.p[0]-(2.5+300*2/45+8-1))<1e-10);
d=make('DEF',{pts_allow_0:14,sack:1},{pts_ppr:10,pts_allow_0:1,sack:2});assert.equal(T.prepare(d,'l').raw.p[0],16);
d=make('DEF',{pts_allow_35p:-4},{pts_ppr:2,pts_allow_35p:1});assert.equal(T.prepare(d,'l').raw.p[0],-4);
d=make('K',{xpm:1,xpmiss:-1},{pts_ppr:4,xpm:1,xpmiss:1});assert.equal(T.prepare(d,'l').raw.p[0],0);
d=make('RB',{rush_yd:0},{pts_ppr:10,rush_yd:100});assert.equal(T.prepare(d,'l').raw.p[0],0);
console.log('5 custom-scoring assertions passed.');
// End-to-end simulation: mean, CV, negative DST scores and chunk reproducibility.
const cal=require('./stage/model-calibration.json');
const data={season:2026,week:14,players:{},leagues:{l:{ptd:4,slots:['QB','DEF'],last:14,me:'1',qbs:1,playoff_teams:4,teams:{},sched:{14:[['1','2'],['3','4']]},raw_scoring:cal.scoring['1403096266736422912']}},proj:{},hist:{},s26:{},research_inputs:{games:{14:{BUF:{opponent:'NYJ'},NYJ:{opponent:'BUF'},MIA:{opponent:'NE'},NE:{opponent:'MIA'}}}},calibration:{...cal,residuals:{l:cal.residuals['1403096266736422912']},scoring:{l:cal.scoring['1403096266736422912']}}};
['BUF','NYJ','MIA','NE'].forEach((tm,i)=>{const q='q'+i,k='d'+i;data.players[q]=[q,'QB',tm,'',26];data.players[k]=[k,'DEF',tm,'',26];data.proj[q]=[[15,0]];data.proj[k]=[[5,0]];data.hist[q]={2025:[255,17,0]};data.hist[k]={2025:[85,17,0]};data.leagues.l.teams[String(i+1)]={players:[q,k],w:0,l:0,pf:0}});
const M=T.prepare(data,'l'),E=T.engine(M),a={diagnostics:{}},sc=[{name:'baseline'}];
T.simulate(M,E,sc,50000,a,4921);
for(let i=0;i<E.pl.length;i++){const d=a.diagnostics[i],mean=d.sum/d.n,cv=Math.sqrt(d.squares/d.n-mean*mean)/mean;if(E.pl[i].pos==='QB'){assert(Math.abs(mean-E.pl[i].mean[0])<.2,'Mean drift '+mean);assert(Math.abs(cv-.45)<.02,'CV drift '+cv)}else{assert(Math.abs(mean-5)<.2);assert(d.negative>0,'DST never negative')}}
const one={},chunks={};T.simulate(M,E,sc,1000,one,81);for(let i=0;i<10;i++)T.simulate(M,E,sc,100,chunks,81);assert.deepEqual(one.res,chunks.res,'Results depend on chunking');
require('fs').writeFileSync('work/clipboard-upgrades/simulation-validation.json',JSON.stringify(a.diagnostics,null,2));console.log('Simulation mean/CV/negative-DST and chunk reproducibility checks passed (50,000 seasons).');
