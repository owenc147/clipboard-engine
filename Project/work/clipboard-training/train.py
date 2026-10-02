"""Reproducible chronological weekly calibration. Public Sleeper data only."""
import concurrent.futures,json,urllib.request,time,math,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parent;CACHE=ROOT/'cache';CACHE.mkdir(exist_ok=True)
API='https://api.sleeper.app';POS=['QB','RB','WR','TE']
def fetch(job):
 name,url=job;p=CACHE/(name+'.json')
 if p.exists():return name,json.loads(p.read_text())
 for attempt in range(3):
  try:
   with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Clipboard local model evaluation'}),timeout=40) as r:v=json.load(r)
   p.write_text(json.dumps(v));return name,v
  except Exception:
   if attempt==2:raise
   time.sleep(1+attempt)
jobs=[('players',API+'/v1/players/nfl')]
for y in range(2020,2026):jobs.append((f'season-{y}',f'{API}/v1/stats/nfl/regular/{y}'))
for y in [2023,2024,2025]:
 for w in range(1,18):
  jobs.extend([(f'proj-{y}-{w}',f'{API}/projections/nfl/{y}/{w}?season_type=regular&position[]=QB&position[]=RB&position[]=WR&position[]=TE'),(f'actual-{y}-{w}',f'{API}/v1/stats/nfl/regular/{y}/{w}')])
data={}
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
 for i,(k,v) in enumerate(pool.map(fetch,jobs)):
  data[k]=v
  if i%20==0:print('Loaded',i+1,'/',len(jobs),flush=True)
rows=[]
for y in [2023,2024,2025]:
 prior={}
 for w in range(1,18):
  actual=data[f'actual-{y}-{w}'];proj=data[f'proj-{y}-{w}'];assert isinstance(actual,dict) and isinstance(proj,list)
  for item in proj:
   pid=item['player_id'];pos=data['players'].get(pid,{}).get('position');p=item.get('stats',{}).get('pts_ppr',0);a=actual.get(pid,{})
   # Only scored appearances; inactive prediction is outside this calibration's scope.
   if pos not in POS or p<3 or not a.get('gp'):continue
   hs=hw=0
   for i,yr in enumerate(range(y-3,y)):
    h=data[f'season-{yr}'].get(pid,{})
    if h.get('gp',0)>0:hs+=(i+1)*(h.get('pts_ppr',0)/h['gp'])*min(h['gp'],17)/17;hw+=i+1
   hist=hs/hw if hw else p;cur=statistics.mean(prior[pid]) if prior.get(pid) else p
   rows.append(dict(year=y,week=w,id=pid,pos=pos,p=p,h=hist,c=cur,y=a.get('pts_ppr',0)))
  for pid,a in actual.items():
   if a.get('gp',0)>0:prior.setdefault(pid,[]).append(a.get('pts_ppr',0))
assert all(any(r['year']==y for r in rows) for y in [2023,2024,2025])
def pred(r,c):
 raw=c['weights'][0]*r['p']+c['weights'][1]*r['h']+c['weights'][2]*r['c'];return max(.6*r['p'],min(1.3*r['p'],raw))*c['scale']
def metrics(rs,c):
 err=[pred(r,c)-r['y'] for r in rs];return dict(n=len(rs),mae=statistics.mean(abs(e) for e in err),rmse=math.sqrt(statistics.mean(e*e for e in err)),bias=statistics.mean(err))
raw=dict(weights=[1,0,0],scale=1);result={};config={}
for pos in POS:
 rs={y:[r for r in rows if r['year']==y and r['pos']==pos] for y in [2023,2024,2025]}
 candidates=[]
 for hi in range(0,31,5):
  for ci in range(0,31-hi,5):
   c=dict(weights=[1-(hi+ci)/100,hi/100,ci/100],scale=1)
   base=[pred(r,c) for r in rs[2023]];scale=sum(p*r['y'] for p,r in zip(base,rs[2023]))/sum(p*p for p in base)
   c['scale']=max(.8,min(1.2,scale));candidates.append(c)
 chosen=min(candidates,key=lambda c:metrics(rs[2024],c)['rmse'])
 old=dict(weights=[.7,.2,.1] if pos=='QB' else [.95,.05,0],scale=.92 if pos=='QB' else 1)
 report={str(y):dict(candidate=metrics(rs[y],chosen),projection=metrics(rs[y],raw),previous_weekly_blend=metrics(rs[y],old)) for y in rs}
 # Validation determines the selection; held-out 2025 is reported, not optimized.
 deploy=report['2024']['candidate']['rmse']<min(report['2024']['projection']['rmse'],report['2024']['previous_weekly_blend']['rmse'])
 # Keep weekly forecast on an explicit fallback if neither trained candidate earns validation promotion.
 active=chosen if deploy else (raw if report['2024']['projection']['rmse']<=report['2024']['previous_weekly_blend']['rmse'] else old)
 ratios=[(r['y']-pred(r,active))/max(pred(r,active),3) for r in rs[2023] if pred(r,active)>=5]
 cv=max(.3,min(1.2,math.sqrt(statistics.mean(x*x for x in ratios))))
 config[pos]={**active,'cv':round(cv,4),'selected':'trained' if deploy else 'validation fallback'}
 result[pos]=dict(candidate=chosen,active=config[pos],metrics=report,test_active=metrics(rs[2025],active))
report=dict(created_at=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),method='2023 fit; 2024 validation selection; untouched 2025 evaluation. Weekly full-PPR predictions for players with >=3 projected points and a recorded appearance; excludes inactive/bye games. Future weeks/results are never features. Historical API projections may include retrospective corrections; no as-of archive supplied.',positions=result,rows=len(rows),limits=['This is weekly point-error evaluation, not championship-odds calibration.','Historical identifiers use current player-position metadata.','Four-point passing TD PPR data. Custom scoring beyond passing-TD adjustments requires a separate evaluation.','Personal trade acceptance is not calibrated: zero resolved journal offers.','Previously seeded accepted trades alone cannot estimate rejection likelihood.'])
(ROOT/'training-report.json').write_text(json.dumps(report,indent=2));(ROOT/'weekly-calibration.json').write_text(json.dumps(dict(version=1,**{k:report[k] for k in ['created_at','method','limits']},positions=config),indent=2));(ROOT/'rows.json').write_text(json.dumps(rows))
for pos,r in result.items():print(pos,'active',r['active'],'2025 RMSE',round(r['test_active']['rmse'],3),'projection',round(r['metrics']['2025']['projection']['rmse'],3),'previous',round(r['metrics']['2025']['previous_weekly_blend']['rmse'],3),flush=True)
