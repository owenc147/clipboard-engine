import json,urllib.request,concurrent.futures
from pathlib import Path
R=Path(__file__).parent;C=json.loads((R.parent.parent/'outputs/daily-edition.json').read_text())['snapshot']['context'];out=[]
def get(path):
 p=R/'data'/('verify-'+path.replace('/','-')+'.json')
 if not p.exists():p.write_bytes(urllib.request.urlopen('https://api.sleeper.app/v1/'+path,timeout=25).read())
 return json.loads(p.read_text())
a=get('stats/nfl/regular/2026/3')
for l in C['leagues']:
 diffs=[];n=0
 for t in get('league/'+l['id']+'/matchups/3'):
  for pid,expected in (t.get('players_points') or {}).items():
   if pid not in a:continue
   st=a[pid];total=0
   for k,v in l['scoring'].items():
    stat=st.get(k,0)
    if k.startswith('bonus_') and k not in st:
     parts=k.rsplit('_',1)
     if parts[-1].isdigit():stat=float(st.get(parts[0][6:],0)>=int(parts[-1]))
    total+=v*stat
   n+=1
   if abs(total-expected)>.025:diffs.append(dict(id=pid,computed=total,sleeper=expected,error=total-expected))
 out.append(dict(league=l['name'],n=n,mismatches=diffs));print(l['name'],n,'compared, mismatches',len(diffs),diffs[:3],flush=True)
(R/'scoring-validation.json').write_text(json.dumps(out,indent=2))
