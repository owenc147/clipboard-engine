from pathlib import Path
import urllib.request,concurrent.futures
D=Path(__file__).parent/'data'
def get(y):
 p=D/f'pbp-{y}.csv.gz'
 if not p.exists():
  u=f'https://github.com/nflverse/nflverse-data/releases/download/pbp/play_by_play_{y}.csv.gz'
  with urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'Clipboard personal analytics'}),timeout=60) as r:p.write_bytes(r.read())
 print(y,p.stat().st_size,flush=True)
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:list(ex.map(get,[2022,2023,2024,2025]))
