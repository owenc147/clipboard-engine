"""Chronological candidate evaluation. Never mutates the installed app."""
import json,math,urllib.request,concurrent.futures
from pathlib import Path
import numpy as np,pandas as pd
R=Path(__file__).parent;D=R/'data';OLD=R.parent/'clipboard-training/cache'
players=json.loads((OLD/'players.json').read_text());ids=pd.read_csv(D/'ids.csv',dtype=str);idmap=dict(zip(ids.gsis_id,ids.sleeper_id));games=pd.read_csv(D/'games.csv');games=games[games.game_type=='REG'];team=lambda s:{'LA':'LAR','OAK':'LV','SD':'LAC','STL':'LAR'}.get(s,s)
gmap={}
for g in games.to_dict('records'):
 for ishome in [True,False]:
  t=team(g['home_team'] if ishome else g['away_team']);opp=team(g['away_team'] if ishome else g['home_team']);spread=g['spread_line']*(1 if ishome else -1)
  gmap[(int(g['season']),int(g['week']),t)]=dict(game=g['game_id'],opp=opp,total=g['total_line'],spread=spread,implied=(g['total_line']+spread)/2,opp_implied=(g['total_line']-spread)/2,indoor=int(g.get('roof') in ['dome','closed']))
def getkd(y,w):
 p=D/f'kd-{y}-{w}.json'
 if not p.exists():
  u=f'https://api.sleeper.app/projections/nfl/{y}/{w}?season_type=regular&position[]=K&position[]=DEF'
  p.write_bytes(urllib.request.urlopen(u,timeout=30).read())
 return json.loads(p.read_text())
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:list(ex.map(lambda z:getkd(*z),[(y,w) for y in [2023,2024,2025] for w in range(1,18)]))
rows=[]
for y in [2023,2024,2025]:
 for w in range(1,18):
  actual=json.loads((OLD/f'actual-{y}-{w}.json').read_text());pr=json.loads((OLD/f'proj-{y}-{w}.json').read_text())+getkd(y,w)
  for p in pr:
   pid=p['player_id'];a=actual.get(pid,{});ps=p.get('player',{}).get('position') or players.get(pid,{}).get('position') or ('DEF' if pid.isalpha() else None);t=team(p.get('team') or p.get('player',{}).get('team') or pid);gm=gmap.get((y,w,t));proj=p.get('stats',{}).get('pts_ppr')
   if proj is None or not a.get('gp') or not gm:continue
   if ps in ['QB','RB','WR','TE'] and proj<3:continue
   rows.append(dict(season=y,week=w,id=pid,pos=ps,team=t,projection=proj,actual=a.get('pts_ppr',0),**gm))
f=pd.DataFrame(rows);f=f.drop_duplicates(['season','week','id']);report={'limitations':['Historical Sleeper projections are revised, not guaranteed pregame snapshots.','Historical game lines are not timestamped to the projection horizon.','Experiments are retrospective screening, not deployment-grade live validation.']}
def rmse(y,p):return float(np.sqrt(np.mean((np.array(y)-np.array(p))**2)))
def regression(train,test,cols,alpha=20):
 a=train[cols].to_numpy(float);b=test[cols].to_numpy(float);mu=a.mean(0);sd=a.std(0);sd[sd<1e-9]=1;x=np.c_[np.ones(len(a)),(a-mu)/sd];z=np.c_[np.ones(len(b)),(b-mu)/sd];reg=np.eye(x.shape[1])*alpha;reg[0,0]=0;coef=np.linalg.solve(x.T@x+reg,x.T@train.actual.to_numpy());return z@coef
report['kicker_defense']={}
for pos in ['K','DEF']:
 q=f[f.pos==pos].dropna(subset=['projection','implied','opp_implied','spread']);a=q[q.season==2023];v=q[q.season==2024];t=q[q.season==2025];cols=['projection','implied','opp_implied','indoor'];pv=regression(a,v,cols);pt=regression(a,t,cols)
 report['kicker_defense'][pos]={'train_n':len(a),'validation_n':len(v),'test_n':len(t),'validation_baseline':rmse(v.actual,v.projection),'validation_candidate':rmse(v.actual,pv),'test_baseline':rmse(t.actual,t.projection),'test_candidate':rmse(t.actual,pt),'deployment':'shadow only: missing pregame timestamps'}
print('K/DST',report['kicker_defense'],flush=True)
# XFP: only PRIOR games become forecasting features. Provider model trained 2006-20.
x=[]
for y in [2022,2023,2024,2025,2026]:
 p=D/f'ep_weekly_{y}.csv'
 if p.exists():x.append(pd.read_csv(p))
x=pd.concat(x,ignore_index=True);x=x[x.game_id.str.contains('_',na=False)].copy();x['id']=x.player_id.map(idmap);x=x[x.id.notna()];x=x.sort_values(['id','season','week']);
# Recompute standard PPR xFP from components, rather than assuming provider's default scoring.
x['xfp']=.04*x.pass_yards_gained_exp+4*x.pass_touchdown_exp-2*x.pass_interception_exp+.1*(x.rec_yards_gained_exp+x.rush_yards_gained_exp)+6*(x.rec_touchdown_exp+x.rush_touchdown_exp)+x.receptions_exp
x['lag_xfp']=x.groupby(['id','season']).xfp.transform(lambda s:s.shift(1).rolling(3,min_periods=2).mean())
f=f.merge(x[['id','season','week','lag_xfp']].drop_duplicates(['id','season','week']),how='left',on=['id','season','week']);report['xfp']={}
for pos in ['QB','RB','WR','TE']:
 q=f[(f.pos==pos)&f.lag_xfp.notna()];a=q[q.season==2023];v=q[q.season==2024];t=q[q.season==2025]
 baseline_cols=['projection'];cols=['projection','lag_xfp'];bv=regression(a,v,baseline_cols);pv=regression(a,v,cols);bt=regression(a,t,baseline_cols);pt=regression(a,t,cols)
 report['xfp'][pos]={'train_n':len(a),'validation_n':len(v),'test_n':len(t),'validation_projection_calibrated':rmse(v.actual,bv),'validation_with_xfp':rmse(v.actual,pv),'test_projection_calibrated':rmse(t.actual,bt),'test_with_xfp':rmse(t.actual,pt),'deployment':'shadow only: projection archive revised'}
print('XFP',report['xfp'],flush=True)
# Residual correlations: use observed same-game pairs; inspect validation and test independently.
f['residual']=f.actual-f.projection;pairrows=[]
for (y,game),g in f.groupby(['season','game']):
 for qb in g[g.pos=='QB'].itertuples():
  for other in g[(g.team==qb.opp)&g.pos.isin(['WR','TE','DEF'])].itertuples():pairrows.append(dict(season=y,kind='qb_dst' if other.pos=='DEF' else 'bringback',x=qb.residual,y=other.residual))
pairs=pd.DataFrame(pairrows);report['correlation']={}
for kind,q in pairs.groupby('kind'):
 report['correlation'][kind]={str(y):{'n':len(z),'rho':float(z.x.corr(z.y))} for y,z in q.groupby('season')}
print('Correlation',report['correlation'],flush=True)
# Math recommendation + cap comparison. Deterministic, vectorized, floating arrays.
rng=np.random.default_rng(427);mathrows=[]
for pos,cv in [('QB',.45),('RB',.62),('WR',.69),('TE',.7),('DEF',.7)]:
 for m in [5.,15.,25.]:
  sig=np.sqrt(np.log1p(cv*cv));scores=m*np.exp(sig*rng.standard_normal(500000)-.5*sig*sig);cap=min(75,4.5*m);clipped=np.minimum(scores,cap)
  mathrows.append(dict(position=pos,mean_target=m,cv_target=cv,raw_mean=float(scores.mean()),raw_cv=float(scores.std()/scores.mean()),cap=cap,capped_mean=float(clipped.mean()),mean_loss_pct=float(100*(1-clipped.mean()/scores.mean())),cap_mass=float(np.mean(scores>=cap)),raw_p99=float(np.quantile(scores,.99))))
report['distribution_caps']=mathrows
# Actual tails are descriptive because forecasts may have been revised after kickoff.
report['observed_tails']={p:{'n':len(q),'negative':int((q.actual<0).sum()),'zero':int((q.actual==0).sum()),'above_75':int((q.actual>75).sum()),'above_4_5x':int((q.actual>4.5*q.projection).sum())} for p,q in f.groupby('pos')}
report['manager_behavior']={'resolved_journal_offers':0,'deployment':'Do not fit personalized probabilities until sufficient dated accepted/rejected/silent offer evidence exists. Activity is descriptive, not an acceptance label.'}
(R/'evaluation.json').write_text(json.dumps(report,indent=2,allow_nan=False));f.to_csv(D/'evaluation-rows.csv',index=False)
print('Evaluation saved',len(f),'rows',flush=True)
