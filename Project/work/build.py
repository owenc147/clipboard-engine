from pathlib import Path
import plistlib
root=Path('outputs/Sleeper Brief.app/Contents')
(root/'Info.plist').write_bytes(plistlib.dumps({'CFBundleExecutable':'SleeperBrief','CFBundleIdentifier':'local.coffero.sleeperbrief','CFBundleName':'Sleeper Brief','CFBundleDisplayName':'Sleeper Brief','CFBundlePackageType':'APPL','CFBundleShortVersionString':'1.0','CFBundleVersion':'1','LSMinimumSystemVersion':'13.0','NSHighResolutionCapable':True}))
p=root/'Resources/sleeper_assistant.py'
s=p.read_text().replace('CACHE = Path.home() / ".sleeper_cache"','CACHE = Path(os.environ.get("SLEEPER_CACHE", str(Path.home() / ".sleeper_cache")))').replace('CACHE.mkdir(exist_ok=True)','CACHE.mkdir(parents=True, exist_ok=True)').replace('except (StopIteration, Exception):\n        pass','except Exception as error:\n        L.append(f"Matchup unavailable: {error}")')
p.write_text(s)
