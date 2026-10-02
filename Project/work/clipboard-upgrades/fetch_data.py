import urllib.request,json,concurrent.futures
from pathlib import Path
D=Path(__file__).parent/'data';D.mkdir(exist_ok=True)
def fetch(job):
 name,url=job;p=D/name
 if not p.exists():
  with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Clipboard personal research'}),timeout=90) as r:p.write_bytes(r.read())
 print(name,p.stat().st_size,flush=True)
jobs=[('games.csv','https://raw.githubusercontent.com/nflverse/nfldata/master/data/games.csv'),('ids.csv','https://raw.githubusercontent.com/dynastyprocess/data/master/files/db_playerids.csv'),('ff-release.json','https://api.github.com/repos/ffverse/ffopportunity/releases/tags/latest-data')]
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:list(ex.map(fetch,jobs))
r=json.loads((D/'ff-release.json').read_text());assets=r.get('assets',[])
print('Opportunity files:',[a['name'] for a in assets if 'weekly' in a['name']][-20:],flush=True)
for a in assets:
 if 'weekly' in a['name'] and any(str(y) in a['name'] for y in [2022,2023,2024,2025,2026]) and a['name'].endswith('.csv'):jobs.append((a['name'],a['browser_download_url']))
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:list(ex.map(fetch,jobs[3:]))
