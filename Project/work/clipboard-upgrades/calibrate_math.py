from pathlib import Path
import json,math
import numpy as np,pandas as pd
from statistics import NormalDist
R=Path(__file__).parent;D=R/'data';OLD=R.parent/'clipboard-training/cache';f=pd.read_csv(D/'evaluation-rows.csv',dtype={'id':str});c=json.loads((R.parent.parent/'outputs/daily-edition.json').read_text())['snapshot']['context'];out={'version':1,'trained_season':2023,'evaluated_seasons':[2024,2025],'residuals':{},'correlations':{},'limits':['Historical projections may contain postgame corrections. These are distribution-shape checks, not validated championship probabilities.','Skills CV is the marginal active-game CV, including season-long talent uncertainty.','Projections are treated as conditional on playing; provider injury-adjustment semantics are unverified.']};evals={}
qs=np.array([.05,.1,.25,.5,.75,.9,.95]);z=np.array([NormalDist().inv_cdf(q) for q in qs])
def loss(actual,pred):
 e=np.array(actual)[:,None]-pred;return float(np.maximum(qs*e,(qs-1)*e).mean())
for l in c['leagues']:
 vals={'K':[],'DEF':[]}
 for y in [2023,2024,2025]:
  for w in range(1,18):
   a=json.loads((OLD/f'actual-{y}-{w}.json').read_text())
   for p in json.loads((D/f'kd-{y}-{w}.json').read_text()):
    pid=p['player_id'];pos='DEF' if pid.isalpha() else 'K';st=a.get(pid,{})
    if not st.get('gp'):continue
    pred=sum(v*p['stats'].get(k,0) for k,v in l['scoring'].items());act=sum(v*st.get(k,0) for k,v in l['scoring'].items());vals[pos].append((y,pred,act))
 out['residuals'][l['id']]={};evals[l['name']]={}
 for pos,rows in vals.items():
  a=np.array(rows);tr=a[a[:,0]==2023];res=np.sort(tr[:,2]-tr[:,1]);res-=res.mean();q=np.quantile(res,qs);metrics={}
  for y in [2024,2025]:
   t=a[a[:,0]==y];m=t[:,1];cv=.45 if pos=='K' else .7;sig=math.sqrt(math.log1p(cv*cv)+.12**2)
   baseline=m[:,None]*np.exp(sig*z-.5*sig*sig);candidate=m[:,None]+q
   metrics[str(y)]={'n':len(t),'baseline_pinball':loss(t[:,2],baseline),'empirical_pinball':loss(t[:,2],candidate)}
  enabled=all(v['empirical_pinball']<v['baseline_pinball'] for v in metrics.values())
  out['residuals'][l['id']][pos]={'enabled':enabled,'centered_errors':res.round(5).tolist(),'n':len(res)};evals[l['name']][pos]={'enabled':enabled,**metrics}
# Gaussian-copula correlations on projection errors, grouped by position and season.
f=f[f.pos.isin(['QB','WR','TE','DEF'])].copy();f['res']=f.actual-f.projection
f['z']=f.groupby(['season','pos']).res.transform(lambda s:s.rank(method='average').map(lambda r:NormalDist().inv_cdf((r-.5)/len(s))))
ps=[]
for (year,game),g in f.groupby(['season','game']):
 for q in g[g.pos=='QB'].itertuples():
  for o in g[(g.team==q.opp)&g.pos.isin(['WR','TE','DEF'])].itertuples():ps.append((year,'qb_dst' if o.pos=='DEF' else 'bringback',q.z,o.z))
p=pd.DataFrame(ps,columns=['season','kind','x','y']);ce={}
for kind,g in p.groupby('kind'):
 tr=g[g.season==2023];rho=float(np.clip(tr.x.corr(tr.y),-.5,.15));metrics={}
 for y in [2024,2025]:
  t=g[g.season==y];baseline=.5*(t.x**2+t.y**2);cand=.5*np.log(1-rho*rho)+(t.x**2+t.y**2-2*rho*t.x*t.y)/(2*(1-rho*rho))
  metrics[str(y)]={'n':len(t),'independent_nll':float(baseline.mean()),'correlated_nll':float(cand.mean())}
 enabled=all(x['correlated_nll']<x['independent_nll'] for x in metrics.values())
 out['correlations'][kind]={'rho':rho,'enabled':enabled};ce[kind]={'rho':rho,'enabled':enabled,**metrics}
(R/'stage/model-calibration.json').write_text(json.dumps(out,indent=2));(R/'math-validation.json').write_text(json.dumps({'residuals':evals,'correlations':ce},indent=2));print(json.dumps({'residuals':evals,'correlations':ce},indent=2))
