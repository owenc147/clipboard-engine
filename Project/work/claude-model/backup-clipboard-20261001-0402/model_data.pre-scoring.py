"""Claude title-model data feed for Binocular.

Called from desk.py with op 'model'. Fetches public Sleeper data (with a local cache)
and returns a compact dataset; the math runs in model.js inside the app.
No credentials, no writes to Sleeper.
"""
import json, time, urllib.request
from pathlib import Path

API = 'https://api.sleeper.app/v1'
SKILL = ('QB', 'RB', 'WR', 'TE')
# Accepted trade sides 2023-2026 from leagues of the managers in Owen's three leagues
# (perceived value-over-replacement difference, package shape). 2026 sides are computed live.
SEED_ACCEPTED = [{"id":"1009875134095769600:3","dl":0.63,"cons":0},{"id":"1009875134095769600:8","dl":-0.63,"cons":0},{"id":"1026894197359697920:1","dl":-3.4,"cons":0},{"id":"1026894197359697920:8","dl":3.4,"cons":0},{"id":"1142206178529820672:5","dl":-4.59,"cons":0},{"id":"1142206178529820672:7","dl":4.59,"cons":0},{"id":"1147266851609649152:6","dl":-0.09,"cons":0},{"id":"1147266851609649152:9","dl":0.09,"cons":0},{"id":"1147581821761409024:7","dl":0.67,"cons":0},{"id":"1147581821761409024:8","dl":-0.67,"cons":0},{"id":"1152300437089939456:3","dl":0.88,"cons":0},{"id":"1152300437089939456:7","dl":-0.88,"cons":0},{"id":"1151924920486662144:1","dl":2.72,"cons":1},{"id":"1151924920486662144:6","dl":-2.72,"cons":-1},{"id":"1157716316300791808:3","dl":5.07,"cons":1},{"id":"1157716316300791808:9","dl":-5.07,"cons":-1},{"id":"1165435552469147648:3","dl":1.86,"cons":1},{"id":"1165435552469147648:8","dl":-1.86,"cons":-1},{"id":"1273770231063396352:3","dl":-0.71,"cons":0},{"id":"1273770231063396352:7","dl":0.71,"cons":0},{"id":"1283966872605171712:3","dl":4.65,"cons":1},{"id":"1283966872605171712:7","dl":-4.65,"cons":-1},{"id":"1286602080349347840:1","dl":0.53,"cons":1},{"id":"1286602080349347840:8","dl":-0.53,"cons":-1},{"id":"1292306606205190144:9","dl":-0.15,"cons":1},{"id":"1292306606205190144:10","dl":0.15,"cons":-1},{"id":"1294852371565772800:3","dl":0.89,"cons":0},{"id":"1294852371565772800:9","dl":-0.89,"cons":0},{"id":"1297323470366982144:2","dl":-1,"cons":0},{"id":"1297323470366982144:7","dl":1,"cons":0},{"id":"1018601445962219520:5","dl":0.45,"cons":0},{"id":"1018601445962219520:7","dl":-0.45,"cons":0},{"id":"1018566394859905024:2","dl":20.41,"cons":-1},{"id":"1018566394859905024:7","dl":-20.41,"cons":1},{"id":"1025897781417951232:1","dl":-0.85,"cons":0},{"id":"1025897781417951232:9","dl":0.85,"cons":0},{"id":"1028024912155357184:2","dl":-2.15,"cons":-1},{"id":"1028024912155357184:11","dl":2.15,"cons":1},{"id":"1032395021229604864:1","dl":0,"cons":0},{"id":"1032395021229604864:9","dl":0,"cons":0},{"id":"1031347353191690240:1","dl":0,"cons":0},{"id":"1031347353191690240:8","dl":0,"cons":0},{"id":"1142571402902720512:1","dl":1.53,"cons":-1},{"id":"1142571402902720512:2","dl":-1.53,"cons":1},{"id":"1142208576598044672:1","dl":-0.89,"cons":0},{"id":"1142208576598044672:8","dl":0.89,"cons":0},{"id":"1144631152582529024:1","dl":-3.14,"cons":0},{"id":"1144631152582529024:5","dl":3.14,"cons":0},{"id":"1274537284129034240:8","dl":-1.68,"cons":-1},{"id":"1274537284129034240:10","dl":1.68,"cons":1},{"id":"1277109845941571584:2","dl":-0.15,"cons":0},{"id":"1277109845941571584:7","dl":0.15,"cons":0},{"id":"1279171965256478720:8","dl":2.26,"cons":-1},{"id":"1279171965256478720:12","dl":-2.26,"cons":1},{"id":"1283910859944398848:6","dl":0.71,"cons":0},{"id":"1283910859944398848:7","dl":-0.71,"cons":0},{"id":"1286833463353151488:2","dl":1.78,"cons":-1},{"id":"1286833463353151488:3","dl":-1.78,"cons":1},{"id":"1289261379588476928:1","dl":3.82,"cons":1},{"id":"1289261379588476928:2","dl":-3.82,"cons":-1},{"id":"1293724388037767168:1","dl":2.19,"cons":0},{"id":"1293724388037767168:2","dl":-2.19,"cons":0},{"id":"1293724328919052288:1","dl":0,"cons":0},{"id":"1293724328919052288:3","dl":0,"cons":0},{"id":"1292965522475847680:1","dl":1.62,"cons":0},{"id":"1292965522475847680:7","dl":-1.62,"cons":0},{"id":"1291947018150744064:1","dl":-1.93,"cons":1},{"id":"1291947018150744064:3","dl":1.93,"cons":-1},{"id":"1294423466035920896:7","dl":-4.13,"cons":0},{"id":"1294423466035920896:13","dl":4.13,"cons":0},{"id":"1137549397849985024:6","dl":1.76,"cons":0},{"id":"1137549397849985024:8","dl":-1.76,"cons":0},{"id":"1403560228015935488:1","dl":0,"cons":0},{"id":"1403560228015935488:4","dl":0,"cons":0},{"id":"1408682163938881536:2","dl":6.89,"cons":1},{"id":"1408682163938881536:7","dl":-6.89,"cons":-1},{"id":"1411167728017952768:4","dl":-0.67,"cons":0},{"id":"1411167728017952768:10","dl":0.67,"cons":0}]
# Owen's known offer outcomes (partner view: r = partner received, g = partner gave).
SEED_LABELS = [{"lid":"1403096266736422912","r":["8146"],"g":["5892","12529"],"y":1},{"lid":"1385050179488460800","r":["11604","11584"],"g":["8150","10236","5892"],"y":1},{"lid":"1360286127205912576","r":["4892","4983"],"g":["5927","6797"],"y":1},{"lid":"1360286127205912576","r":["12474"],"g":["12506"],"y":1},{"lid":"1403096266736422912","r":["4866","12529"],"g":["8138"],"y":0},{"lid":"1385050179488460800","r":["11604"],"g":["6813"],"y":0},{"lid":"1385050179488460800","r":["8150","10236"],"g":["3198"],"y":0}]

class Feed:
    def __init__(self, path):
        self.path = path
        try:
            self.cache = json.loads(path.read_text())
        except Exception:
            self.cache = {}
        self.calls = 0

    def get(self, url, ttl, trim=None):
        ent = self.cache.get(url)
        if ent and time.time() - ent['t'] < ttl:
            return ent['v']
        req = urllib.request.Request(url, headers={'User-Agent': 'Binocular title model'})
        with urllib.request.urlopen(req, timeout=25) as f:
            v = json.loads(f.read())
        self.calls += 1
        if trim:
            v = trim(v)
        self.cache[url] = {'t': time.time(), 'v': v}
        return v

    def prefetch(self, urls, ttl, workers=12):
        """Warm the cache for many URLs in parallel; failures are skipped."""
        from concurrent.futures import ThreadPoolExecutor
        todo = [u for u in dict.fromkeys(urls) if not (self.cache.get(u) and time.time() - self.cache[u]['t'] < ttl)]
        def one(u):
            try: self.get(u, ttl)
            except Exception: pass
        with ThreadPoolExecutor(workers) as ex: list(ex.map(one, todo))

    def save(self):
        tmp = self.path.with_suffix('.tmp')
        tmp.write_text(json.dumps(self.cache))
        tmp.replace(self.path)

def trim_players(v):
    out = {}
    for pid, p in v.items():
        pos = p.get('position')
        if pos in SKILL or pos in ('K', 'DEF'):
            out[pid] = [p.get('full_name') or (str(p.get('first_name', '')) + ' ' + str(p.get('last_name', ''))).strip() or pid,
                        pos, p.get('team'), p.get('injury_status'), p.get('age')]
    return out

def trim_proj(v):
    out = {}
    for x in v:
        s = x.get('stats') or {}
        pts = s.get('pts_ppr') or 0
        if pts:
            out[x['player_id']] = [round(pts, 2), round(s.get('pass_td') or 0, 2)]
    return out

def trim_week(v):
    return {pid: [round(s.get('pts_ppr') or 0, 2), round(s.get('pass_td') or 0, 2), s.get('gp') or 0]
            for pid, s in v.items() if (s.get('gp') or 0) > 0}

def trim_season(v):
    return {pid: [round(s.get('pts_ppr') or 0, 2), s.get('gp') or 0, round(s.get('pass_td') or 0, 2)]
            for pid, s in v.items() if (s.get('gp') or 0) > 0}

def slot_share(rp):
    c = {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0}
    for s in rp:
        if s in c: c[s] += 1
        elif s == 'FLEX': c['RB'] += .45; c['WR'] += .45; c['TE'] += .1
        elif s == 'SUPER_FLEX': c['QB'] += .8; c['RB'] += .08; c['WR'] += .1; c['TE'] += .02
        elif s == 'WRRB_FLEX': c['RB'] += .5; c['WR'] += .5
        elif s == 'REC_FLEX': c['WR'] += .8; c['TE'] += .2
    return c

def replacement(rp, teams, prior, players):
    pool = {k: [] for k in SKILL}
    for pid, (pts, gp, _) in prior.items():
        pos = players.get(pid, [None, None])[1]
        if pos in pool: pool[pos].append(pts / gp)
    c = slot_share(rp); out = {}
    for k in SKILL:
        a = sorted(pool[k], reverse=True)
        out[k] = round(a[min(len(a) - 1, round(teams * c[k] * 1.15))], 2) if a else 8
    return out

def build(root, context):
    feed = Feed(Path(root) / 'model-cache.json')
    state = feed.get(API + '/state/nfl', 1800)
    season = int(state.get('season') or context.get('season'))
    cur = int(state.get('week') or state.get('display_week') or 1)
    players = feed.get(API + '/players/nfl', 12 * 3600, trim_players)
    proj = {}
    for w in range(1, 18):
        url = f'https://api.sleeper.app/projections/nfl/{season}/{w}?season_type=regular&position[]=QB&position[]=RB&position[]=WR&position[]=TE&position[]=K&position[]=DEF'
        proj[w] = feed.get(url, 6 * 3600 if w >= cur else 7 * 86400, trim_proj)
    weekly = {w: feed.get(f'{API}/stats/nfl/regular/{season}/{w}', 6 * 3600 if w >= cur - 1 else 7 * 86400, trim_week) for w in range(1, cur)}
    seasons = {y: feed.get(f'{API}/stats/nfl/regular/{y}', 30 * 86400, trim_season) for y in range(season - 4, season)}
    prior = seasons[season - 1]

    def ppg_to_date(pid, wk):
        t = g = 0
        for w in range(1, wk):
            s = weekly.get(w, {}).get(pid)
            if s: t += s[0]; g += 1
        return (t / g if g else None), g

    def perceived(pid, wk):
        std, g = ppg_to_date(pid, wk)
        p = prior.get(pid); prev = p[0] / p[1] if p else None
        if std is None and prev is None: return 5
        if std is None: return prev
        if prev is None: return std if g >= 2 else (std + 8) / 2
        a = .6 if g >= 3 else .3
        return a * std + (1 - a) * prev

    leagues = {}; wanted = set(); league_ids = [l['id'] for l in context.get('leagues', [])]
    for lid in league_ids:
        lg = feed.get(f'{API}/league/{lid}', 3600)
        ro = feed.get(f'{API}/league/{lid}/rosters', 120)
        us = feed.get(f'{API}/league/{lid}/users', 3600)
        st = lg.get('settings', {})
        last = int(st.get('playoff_week_start') or 15) - 1
        names = {u['user_id']: u.get('display_name') for u in us}
        teams = {}
        me = None
        for r in ro:
            rid = str(r['roster_id'])
            s = r.get('settings', {})
            teams[rid] = {'name': names.get(r.get('owner_id'), 'Team ' + rid), 'owner': r.get('owner_id'),
                          'players': r.get('players') or [], 'w': s.get('wins', 0), 'l': s.get('losses', 0),
                          'pf': (s.get('fpts') or 0) + (s.get('fpts_decimal') or 0) / 100,
                          'starters': [x for x in (r.get('starters') or []) if x and x != '0'], 'reserve': r.get('reserve') or []}
            wanted.update(r.get('players') or [])
            if r.get('owner_id') == context.get('user_id'): me = rid
        sched = {}
        for w in range(cur, last + 1):
            mu = feed.get(f'{API}/league/{lid}/matchups/{w}', 6 * 3600)
            g = {}
            for m in mu:
                if m.get('matchup_id') is not None: g.setdefault(m['matchup_id'], []).append(str(m['roster_id']))
            sched[w] = [v for v in g.values() if len(v) == 2]
        rp = [s for s in lg.get('roster_positions', []) if s != 'BN']
        repl = replacement(lg.get('roster_positions', []), len(ro), prior, players)
        leagues[lid] = {'name': lg.get('name'), 'ptd': (lg.get('scoring_settings') or {}).get('pass_td', 4), 'slots': rp,
                        'playoff_teams': st.get('playoff_teams', 6), 'last': last, 'reseed': st.get('playoff_seed_type') == 1,
                        'trade_deadline': st.get('trade_deadline'), 'teams': teams, 'me': me, 'sched': sched, 'repl': repl,
                        'qbs': 2 if 'SUPER_FLEX' in rp or rp.count('QB') > 1 else 1}
        owned = {p for r in ro for p in (r.get('players') or [])}
        ptd = (lg.get('scoring_settings') or {}).get('pass_td', 4)
        def ros(pid):
            return sum((proj[w].get(pid, [0, 0])[0] + (ptd - 4) * proj[w].get(pid, [0, 0])[1]) for w in range(cur, last + 1))
        pool = {pid for w in range(cur, last + 1) for pid in proj[w] if pid not in owned and players.get(pid, [0, ''])[1] in SKILL + ('K', 'DEF')}
        leagues[lid]['fa'] = sorted(pool, key=ros, reverse=True)[:60]
        wanted.update(leagues[lid]['fa'])
        leagues[lid]['pv'] = {pid: round(max(0, perceived(pid, cur) - repl.get(players.get(pid, [0, 'X'])[1], 8)), 2)
                              for r in ro for pid in (r.get('players') or []) if players.get(pid, [0, ''])[1] in SKILL}

    # 2026 accepted trade sides: Owen's leagues plus every 2026 league of every manager in all three of his leagues.
    accepted = list(SEED_ACCEPTED); seen = {a['id'] for a in accepted}
    trade_leagues = set(league_ids)
    owners_all = {t['owner'] for L in leagues.values() for t in L['teams'].values() if t['owner']}
    feed.prefetch([f"{API}/user/{o}/leagues/nfl/{season}" for o in owners_all], 86400)
    for o in owners_all:
        try:
            for l in feed.get(f"{API}/user/{o}/leagues/nfl/{season}", 86400) or []:
                trade_leagues.add(l['league_id'])
        except Exception:
            pass
    feed.prefetch([f"{API}/league/{l}" for l in trade_leagues], 86400)
    feed.prefetch([f"{API}/league/{l}/transactions/{w}" for l in trade_leagues for w in range(1, cur + 1)], 1800)
    for lid in trade_leagues:
        try:
            lg = feed.get(f'{API}/league/{lid}', 86400)
            txw = {w: feed.get(f'{API}/league/{lid}/transactions/{w}', 1800 if w >= cur - 1 else 86400) or [] for w in range(1, cur + 1)}
        except Exception:
            continue
        repl = leagues[lid]['repl'] if lid in leagues else replacement(lg.get('roster_positions', []), lg.get('total_rosters', 10), prior, players)
        for w in range(1, cur + 1):
            for t in txw[w]:
                if t.get('type') != 'trade' or t.get('status') != 'complete' or len(t.get('roster_ids') or []) != 2: continue
                for side in t['roster_ids']:
                    key = f"{t['transaction_id']}:{side}"
                    if key in seen: continue
                    R = [p for p, r in (t.get('adds') or {}).items() if r == side]
                    G = [p for p, r in (t.get('drops') or {}).items() if r == side]
                    if not R or not G: continue
                    wk = max(1, t.get('leg') or w)
                    def pkg(ids):
                        v = sorted((max(0, perceived(p, wk) - repl.get(players.get(p, [0, 'X'])[1], 8)) for p in ids), reverse=True)
                        return sum(x * (1 if i == 0 else .4) for i, x in enumerate(v))
                    accepted.append({'id': key, 'dl': round(pkg(R) - pkg(G), 2), 'cons': 1 if len(G) > len(R) else -1 if len(G) < len(R) else 0, 'season': season})
                    seen.add(key)


    # Scouting: every manager in every one of Owen's leagues, tracked across all of their 2026 Sleeper leagues.
    scouts = {}
    try:
        owners = {}
        for lid, L in leagues.items():
            for rid, t in L['teams'].items():
                if t['owner'] and t['owner'] != context.get('user_id'):
                    owners.setdefault(t['owner'], {'name': t['name'], 'home': []})['home'].append(lid)
        feed.prefetch([f"{API}/user/{o}/leagues/nfl/{season}" for o in owners], 86400)
        their = {o: [l for l in (feed.get(f"{API}/user/{o}/leagues/nfl/{season}", 86400) or []) ] for o in owners}
        lg_meta = {}
        for o, ls in their.items():
            for l in ls: lg_meta[l['league_id']] = {'name': l.get('name'), 'size': l.get('total_rosters'), 'status': l.get('status')}
        weeks = range(1, cur + 1)
        feed.prefetch([f"{API}/league/{l}/rosters" for l in lg_meta], 3600)
        feed.prefetch([f"{API}/league/{l}/users" for l in lg_meta], 86400)
        feed.prefetch([f"{API}/league/{l}/transactions/{w}" for l in lg_meta for w in weeks], 1800)
        pname = lambda p: (players.get(p) or [p, '?'])[0]
        ppos = lambda p: (players.get(p) or [p, '?'])[1]
        for o, ls in their.items():
            prof = {'name': owners[o]['name'], 'home': owners[o]['home'], 'leagues': [], 'trades': 0, 'waivers': 0, 'fa': 0,
                    'league_weeks': 0, 'pos_in': {}, 'pos_out': {}, 'partners': {}, 'gave': 0, 'got': 0, 'moves': [], 'last': 0}
            for l in ls:
                lid2 = l['league_id']
                try:
                    ros = feed.get(f"{API}/league/{lid2}/rosters", 3600)
                    us = feed.get(f"{API}/league/{lid2}/users", 86400)
                except Exception:
                    continue
                mine = next((str(r['roster_id']) for r in ros if r.get('owner_id') == o or o in (r.get('co_owners') or [])), None)
                if not mine: continue
                rid2name = {str(r['roster_id']): next((u.get('display_name') for u in us if u['user_id'] == r.get('owner_id')), '?') for r in ros}
                prof['leagues'].append({'id': lid2, 'name': lg_meta[lid2]['name'], 'size': lg_meta[lid2]['size'], 'mine': lid2 in leagues})
                prof['league_weeks'] += max(1, cur)
                for w in weeks:
                    try: txs = feed.get(f"{API}/league/{lid2}/transactions/{w}", 1800)
                    except Exception: continue
                    for t in txs or []:
                        if t.get('status') != 'complete' or mine not in [str(x) for x in (t.get('roster_ids') or [])]: continue
                        adds = [p for p, r in (t.get('adds') or {}).items() if str(r) == mine]
                        drops = [p for p, r in (t.get('drops') or {}).items() if str(r) == mine]
                        typ = t.get('type')
                        if typ == 'trade':
                            prof['trades'] += 1; prof['got'] += len(adds); prof['gave'] += len(drops)
                            for r in t.get('roster_ids') or []:
                                if str(r) != mine: prof['partners'][rid2name.get(str(r), '?')] = prof['partners'].get(rid2name.get(str(r), '?'), 0) + 1
                        elif typ == 'waiver': prof['waivers'] += 1
                        elif typ == 'free_agent': prof['fa'] += 1
                        else: continue
                        for p in adds: prof['pos_in'][ppos(p)] = prof['pos_in'].get(ppos(p), 0) + 1
                        for p in drops: prof['pos_out'][ppos(p)] = prof['pos_out'].get(ppos(p), 0) + 1
                        ts = t.get('status_updated') or t.get('created') or 0
                        prof['last'] = max(prof['last'], ts)
                        partner = [rid2name.get(str(r), '?') for r in (t.get('roster_ids') or []) if str(r) != mine]
                        prof['moves'].append({'ts': ts, 'league': lg_meta[lid2]['name'], 'lid': lid2, 'type': typ, 'week': t.get('leg') or w,
                                              'add': [pname(p) + ' (' + ppos(p) + ')' for p in adds], 'drop': [pname(p) + ' (' + ppos(p) + ')' for p in drops],
                                              'with': partner if typ == 'trade' else []})
            prof['moves'] = sorted(prof['moves'], key=lambda m: -m['ts'])[:15]
            scouts[o] = prof
    except Exception as e:
        scouts = {'_error': str(e)}

    for l in leagues.values():
        for t in l['teams'].values(): wanted.update(t['players'])
    for lab in SEED_LABELS: wanted.update(lab['r'] + lab['g'])
    out = {
        'built_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), 'season': season, 'week': cur,
        'leagues': leagues,
        'players': {p: players[p] for p in wanted if p in players},
        'proj': {p: [proj[w].get(p) for w in range(cur, 18)] for p in wanted},
        'hist': {p: {str(y): seasons[y].get(p) for y in seasons if seasons[y].get(p)} for p in wanted},
        's26': {p: [weekly[w][p] for w in weekly if p in weekly[w]] for p in wanted},
        'accepted': accepted, 'labels': SEED_LABELS, 'scouts': scouts, 'requests': feed.calls,
    }
    feed.save()
    return out
