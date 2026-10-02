"""Refresh public Sleeper data into the workspace; leave the installed app untouched."""
import os,shutil,subprocess,sys
from pathlib import Path
BASE=Path(__file__).resolve().parents[1]
cache=BASE/'work/daily-cache';cache.mkdir(exist_ok=True)
support=Path.home()/'Library/Application Support/Sleeper Brief/cache'
if support.exists():
 for source in support.glob('*.json'):
  dest=cache/source.name
  if not dest.exists() or source.stat().st_mtime>dest.stat().st_mtime:shutil.copy2(source,dest)
run=BASE/'work/daily-run';run.mkdir(exist_ok=True)
env=dict(os.environ,SLEEPER_CACHE=str(cache),PYTHONDONTWRITEBYTECODE='1')
subprocess.run([sys.executable,str(BASE/'outputs/Binocular.app/Contents/Resources/sleeper_assistant.py'),'--user','coffero'],cwd=run,env=env,check=True)
print('Fresh snapshot:',run/'snapshot.json')
