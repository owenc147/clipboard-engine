"""Experimental team context. No narrative scalars; all features lagged before game."""
from pathlib import Path
import pandas as pd,numpy as np,json
R=Path(__file__).parent;D=R/'data';allrows=[]
cols=['game_id','season','week','season_type','posteam','play_id','play_type','qb_dropback','qb_kneel','qb_spike','pass_oe','xpass','epa','wp','qtr','game_seconds_remaining','drive']
for year in [2022,2023,2024,2025]:
 p=pd.read_csv(D/f'pbp-{year}.csv.gz',usecols=lambda c:c in cols,low_memory=False);p=p[p.season_type=='REG'].sort_values(['game_id','play_id']);p['elapsed']=p.groupby(['game_id','posteam','drive']).game_seconds_remaining.diff().mul(-1)
 p=p[p.play_type.isin(['run','pass'])&(p.qb_kneel!=1)&(p.qb_spike!=1)];p['neutral']=p.wp.between(.2,.8)&(p.qtr<=3);p['pace']=p.elapsed.where(p.neutral&p.elapsed.between(1,45));p['neutral_proe']=p.pass_oe.where(p.neutral)/100
 g=p.groupby(['season','week','game_id','posteam']).agg(plays=('play_id','size'),dropbacks=('qb_dropback','sum'),pace=('pace','mean'),proe=('neutral_proe','mean'),epa=('epa','mean')).reset_index();allrows.append(g)
a=pd.concat(allrows).sort_values(['posteam','season','week']);features=['plays','pace','proe','epa']
for col in features:a['lag_'+col]=a.groupby(['posteam','season'])[col].transform(lambda x:x.shift(1).rolling(4,min_periods=2).mean())
# Opponent prior tempo influences total opportunities too; neither current-game stat is a feature.
games=pd.read_csv(D/'games.csv');games=games[games.game_type=='REG'];look={}
for g in games.to_dict('records'):
 for side,other in [('home','away'),('away','home')]:look[(g['game_id'],g[side+'_team'])]=(g[other+'_team'],g[side+'_rest']-g[other+'_rest'])
a['opp']=a.apply(lambda r:look.get((r.game_id,r.posteam),('',0))[0],axis=1);a['rest_difference']=a.apply(lambda r:look.get((r.game_id,r.posteam),('',0))[1],axis=1)
opp=a[['game_id','posteam','lag_plays','lag_pace']].rename(columns={'posteam':'opp','lag_plays':'opp_lag_plays','lag_pace':'opp_lag_pace'});a=a.merge(opp,on=['game_id','opp'],how='left');a['dropback_rate']=a.dropbacks/a.plays
base=['lag_plays','opp_lag_plays'];extra=['lag_pace','opp_lag_pace','lag_proe','lag_epa','rest_difference'];a=a.dropna(subset=base+extra)
def fitpred(tr,te,cols,target):
 x=tr[cols].to_numpy();z=te[cols].to_numpy();mean=x.mean(0);sd=x.std(0);sd[sd<1e-8]=1;x=np.c_[np.ones(len(x)),(x-mean)/sd];z=np.c_[np.ones(len(z)),(z-mean)/sd];reg=np.eye(x.shape[1])*20;reg[0,0]=0;b=np.linalg.solve(x.T@x+reg,x.T@tr[target].to_numpy());return z@b
tr=a[a.season==2023];report={}
for target in ['plays','dropback_rate']:
 report[target]={}
 for year in [2024,2025]:
  te=a[a.season==year];b=fitpred(tr,te,base,target);q=fitpred(tr,te,base+extra,target)
  if target=='dropback_rate':b=np.clip(b,0,1);q=np.clip(q,0,1)
  report[target][str(year)]={'n':len(te),'baseline_rmse':float(np.sqrt(np.mean((b-te[target])**2))),'context_rmse':float(np.sqrt(np.mean((q-te[target])**2)))}
report['scope']='Team-game experiment using only prior games. Pace is a neutral-game-clock proxy, not tracking-derived snap-to-snap time. Team tendencies are not attributed causally to individual coaches. No production projection scalar enabled.'
report['implementation']='Predict team plays P, expected dropback share q; D=P*q, designed rushes=P*(1-q). Subtract sacks/scrambles from D for pass attempts, add scrambles to player rushing opportunities, allocate by forecast target/carry shares. Preserve team totals. Context coefficients must be learned and validated; no automatic rest/body-clock penalty.'
(R/'team-context-validation.json').write_text(json.dumps(report,indent=2));a.to_csv(D/'team-context.csv',index=False);print(json.dumps(report,indent=2))
