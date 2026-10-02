#!/usr/bin/env python3
"""
Sleeper Fantasy Assistant
Pulls all your Sleeper leagues and writes a weekly brief per league:
  - lineup red flags (injured / inactive / empty starters)
  - waiver targets (trending adds that are still available in THAT league)
  - positional depth vs. the league -> who to trade with
  - this week's matchup + standings

Usage:
  python sleeper_assistant.py                    # brief for @coffero, current week
  python sleeper_assistant.py --user someone     # different Sleeper username
  python sleeper_assistant.py --ask              # also get Claude's start/sit + trade take
                                                   (needs: pip install anthropic, ANTHROPIC_API_KEY)
Output: sleeper_brief_week<N>.md  (paste it into Claude if you skip --ask)
No dependencies beyond the standard library unless you use --ask.
"""
import argparse, json, os, sys, time, urllib.request
from collections import Counter
from datetime import datetime, timezone
from functools import lru_cache
from itertools import zip_longest
from pathlib import Path
from league_tracker import track_league

API = "https://api.sleeper.app/v1"
CACHE = Path(os.environ.get("SLEEPER_CACHE", str(Path.home() / ".sleeper_cache")))
PLAYERS_TTL = 24 * 3600          # Sleeper asks you to pull /players at most once a day
FLAG_STATUSES = {"Out", "IR", "Doubtful", "Questionable", "PUP", "Sus", "NA"}
CORE_POS = ["QB", "RB", "WR", "TE"]
FLEX_MAP = {  # which positions each slot accepts
    "FLEX": {"RB", "WR", "TE"}, "WRRB_FLEX": {"RB", "WR"}, "REC_FLEX": {"WR", "TE"},
    "SUPER_FLEX": {"QB", "RB", "WR", "TE"},
}


@lru_cache(maxsize=256)
def get(path):
    req = urllib.request.Request(API + path, headers={"User-Agent": "sleeper-assistant"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def players_db():
    CACHE.mkdir(parents=True, exist_ok=True)
    f = CACHE / "players.json"
    if f.exists() and time.time() - f.stat().st_mtime < PLAYERS_TTL:
        return json.loads(f.read_text())
    print("Downloading Sleeper player database (~5 MB, cached for 24h)...")
    data = get("/players/nfl")
    f.write_text(json.dumps(data))
    return data


def name(pid, P):
    if pid in (None, "0", ""):
        return "EMPTY"
    p = P.get(pid, {})
    if p.get("position") == "DEF" or not p:
        return f"{pid} DST" if pid.isalpha() else pid
    return f"{p.get('full_name', pid)} ({p.get('position')}, {p.get('team') or 'FA'})"


def flag(pid, P):
    p = P.get(pid, {})
    s = p.get("injury_status")
    if s in FLAG_STATUSES:
        return s
    if p and p.get("position") != "DEF" and not p.get("team"):
        return "no team"
    return None


def pos(pid, P):
    return P.get(pid, {}).get("position", "DEF" if pid.isalpha() else "?")


def depth_table(rosters, my_rid, P):
    """Count rostered players by position for every team; return my surplus/deficit vs league avg."""
    counts = {r["roster_id"]: Counter(pos(p, P) for p in (r.get("players") or [])) for r in rosters}
    n = len(counts)
    avg = {x: sum(c[x] for c in counts.values()) / n for x in CORE_POS}
    mine = counts[my_rid]
    return counts, avg, {x: round(mine[x] - avg[x], 1) for x in CORE_POS}


def trade_partners(counts, avg, my_diff, my_rid, owners):
    """Teams deep where I'm thin AND thin where I'm deep."""
    need = [x for x in CORE_POS if my_diff[x] <= -0.5]
    have = [x for x in CORE_POS if my_diff[x] >= 0.5]
    out = []
    for rid, c in counts.items():
        if rid == my_rid:
            continue
        gives = [x for x in need if c[x] - avg[x] >= 0.5]
        wants = [x for x in have if c[x] - avg[x] <= -0.5]
        if gives and wants:
            out.append(f"- **{owners.get(rid, rid)}** is deep at {'/'.join(gives)} and thin at "
                       f"{'/'.join(wants)} — roster-count fit only")
    return need, have, out


def score(matchup):
    value = matchup.get("custom_points")
    return float(value if value is not None else (matchup.get("points") or 0))


def build_context(leagues, uid, username, state, week, P):
    cache_file = CACHE / "players.json"
    result = {"user": username, "user_id": uid, "season": str(state.get("league_season") or state["season"]),
              "week": week, "nfl_week": state.get("week"), "display_week": state.get("display_week"),
              "fetched_at": datetime.now(timezone.utc).isoformat(),
              "players_as_of": datetime.fromtimestamp(cache_file.stat().st_mtime, timezone.utc).isoformat() if cache_file.exists() else None,
              "leagues": []}
    research = json.loads(Path(__file__).with_name("research.json").read_text())
    edition = Path(__file__).resolve().parents[3] / "daily-edition.json"
    if edition.exists():
        try:
            daily = json.loads(edition.read_text())["research"]
            if daily.get("user") == username and isinstance(daily.get("candidates"), list): research = daily
        except (OSError, ValueError, KeyError, TypeError): pass
    names = {c["name"] for c in research["candidates"]}
    for lg in leagues:
        lid = lg["league_id"]
        rosters = get(f"/league/{lid}/rosters")
        users = {u["user_id"]: u for u in get(f"/league/{lid}/users")}
        mine = next((r for r in rosters if r.get("owner_id") == uid or uid in (r.get("co_owners") or [])), None)
        if not mine:
            continue
        def owner(r):
            u = users.get(r.get("owner_id"), {})
            return (u.get("metadata") or {}).get("team_name") or u.get("display_name") or f"Team {r['roster_id']}"
        owners = {pid: owner(r) for r in rosters for pid in set((r.get("players") or []) + (r.get("reserve") or []) + (r.get("taxi") or []))}
        allowed = set()
        for slot in lg.get("roster_positions", []):
            if slot != "BN": allowed |= FLEX_MAP.get(slot, {slot})
        market = []
        for pid, player in P.items():
            full = player.get("full_name") or pid
            if full not in names and pid not in names: continue
            positions = set(player.get("fantasy_positions") or [player.get("position")])
            if not positions.intersection(allowed): continue
            market.append({"id":pid,"name":full,"position":player.get("position"),"team":player.get("team"),
                           "owner":owners.get(pid),"injury":flag(pid,P)})
        result["leagues"].append({"id":lid,"name":lg["name"],"scoring":lg.get("scoring_settings",{}),
            "slots":lg.get("roster_positions",[]),"settings":lg.get("settings",{}),
            "waiver_position":mine.get("settings",{}).get("waiver_position"),
            "roster": [{"id":pid,"name":P.get(pid,{}).get("full_name",pid),"injury":flag(pid,P)} for pid in mine.get("players") or []],
            "reserve":mine.get("reserve") or [], "market":market,
            "tracking":track_league(lg,rosters,users,P,get,max(0,int(state.get("week") or week)),result["fetched_at"],CACHE,result["season"],uid)})
    return result


def league_brief(lg, uid, week, trending, P):
    lid = lg["league_id"]
    rosters = get(f"/league/{lid}/rosters")
    users = {u["user_id"]: u for u in get(f"/league/{lid}/users")}
    owners = {r["roster_id"]: (users.get(r.get("owner_id"), {}).get("metadata", {}) or {}).get("team_name")
              or users.get(r.get("owner_id"), {}).get("display_name", f"Team {r['roster_id']}")
              for r in rosters}
    mine = next((r for r in rosters if r.get("owner_id") == uid or uid in (r.get("co_owners") or [])), None)
    if not mine:
        return f"## {lg['name']}\n_Couldn't find your roster._\n"
    rid = mine["roster_id"]
    slots = [s for s in lg.get("roster_positions", []) if s != "BN"]
    starters = mine.get("starters") or []
    bench = [p for p in (mine.get("players") or [])
             if p not in starters and p not in (mine.get("reserve") or []) and p not in (mine.get("taxi") or [])]
    sc = lg.get("scoring_settings", {})
    fmt = f"{'Superflex' if 'SUPER_FLEX' in slots else '1QB'}, {sc.get('rec', 0)} PPR, " \
          f"{int(sc.get('pass_td', 4))}pt pass TD, {lg.get('total_rosters')} teams"

    L = [f"## {lg['name']}", f"_{fmt}_", ""]

    # Standings
    table = sorted(rosters, key=lambda r: (-(r["settings"].get("wins", 0)),
                                           -(r["settings"].get("fpts", 0) + r["settings"].get("fpts_decimal", 0) / 100)))
    L.append("**Standings:** " + " · ".join(
        f"{'**' if r['roster_id'] == rid else ''}{i+1}. {owners[r['roster_id']]} "
        f"({r['settings'].get('wins',0)}-{r['settings'].get('losses',0)})"
        f"{'**' if r['roster_id'] == rid else ''}" for i, r in enumerate(table)))
    L.append("")

    # Matchup
    try:
        mu = get(f"/league/{lid}/matchups/{week}")
        me = next(m for m in mu if m["roster_id"] == rid)
        opp = next((m for m in mu if me.get("matchup_id") is not None and m.get("matchup_id") == me["matchup_id"] and m["roster_id"] != rid), None)
        if opp:
            L.append(f"**Week {week} opponent:** {owners[opp['roster_id']]} — score so far "
                     f"{score(me):.1f} to {score(opp):.1f}")
            L.append("Their starters: " + ", ".join(name(p, P) for p in (opp.get("starters") or []) if p != "0"))
            L.append("")
    except Exception as error:
        L.append(f"Matchup unavailable: {error}")

    # Lineup check
    L.append("### Lineup check")
    issues = []
    for slot, p in zip_longest(slots, starters, fillvalue=None):
        if slot is None:
            continue
        if p in (None, "0", ""):
            issues.append(f"- ⚠️ **{slot} slot is EMPTY**")
        elif flag(p, P):
            issues.append(f"- ⚠️ {slot}: {name(p, P)} — **{flag(p, P)}**")
    L += issues or ["- No flagged injuries or empty slots in the cached roster."]
    L.append("")
    L.append("Starters: " + ", ".join(f"{s} {name(p, P)}" for s, p in zip(slots, starters)))
    L.append("Bench: " + (", ".join(name(p, P) + (f" [{flag(p, P)}]" if flag(p, P) else "") for p in bench) or "—"))
    L.append("Reserve: " + (", ".join(name(p, P) + (f" [{flag(p, P)}]" if flag(p, P) else "") for p in (mine.get("reserve") or [])) or "—"))
    L.append("Taxi: " + (", ".join(name(p, P) for p in (mine.get("taxi") or [])) or "—"))
    L.append("")

    # Waivers
    rostered = {p for r in rosters for p in (r.get("players") or [])}
    allowed = set()
    for s in slots:
        allowed |= FLEX_MAP.get(s, {s})
    L.append("### Waiver targets (trending adds, still available here)")
    avail = [(t["player_id"], t["count"]) for t in trending
             if t["player_id"] not in rostered and pos(t["player_id"], P) in allowed
             and flag(t["player_id"], P) not in {"Out", "IR"}][:8]
    L += [f"- {name(p, P)} — {c:,} adds (24h)" for p, c in avail] or ["- Nothing trending is available."]
    L.append("")

    # Trades
    counts, avg, diff = depth_table(rosters, rid, P)
    need, have, partners = trade_partners(counts, avg, diff, rid, owners)
    L.append("### Trade angles")
    L.append("Your depth vs. league average: " + ", ".join(f"{x} {'+' if d >= 0 else ''}{d}" for x, d in diff.items()))
    if need:
        L.append(f"Fewer rostered at: {', '.join(need)}. More rostered at: {', '.join(have) or 'nothing'}.")
    L.append("Counts do not measure starter quality or trade value; injuries and reserve players can distort them.")
    L += partners or ["- No complementary roster-count fit found."]
    L.append("")
    L.append("### Scoring details")
    L += [f"- {key}: {value}" for key, value in sorted(sc.items())]
    L.append("")
    return "\n".join(L)


PROMPT = """You're my fantasy football analyst. Below is my weekly brief for my Sleeper leagues.
For each league, evaluate close start/sit decisions, available waiver upgrades with a drop candidate,
and possible trades. Cite dated sources, distinguish facts from opinions, and state uncertainty.
Use the complete scoring settings, current ownership, injuries, and roster opportunity cost.
Do not force a trade or treat positional counts as player value. Verify news before kickoff."""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--user", default="coffero")
    ap.add_argument("--week", type=int)
    ap.add_argument("--ask", action="store_true", help="send the brief to Claude for recommendations")
    a = ap.parse_args()

    state = get("/state/nfl")
    season = state.get("league_season") or state["season"]
    week = a.week or state.get("week") or state.get("display_week") or 1
    user = get(f"/user/{a.user}")
    if not user:
        sys.exit(f"Sleeper user '{a.user}' not found.")
    uid = user["user_id"]
    leagues = get(f"/user/{uid}/leagues/nfl/{season}")
    P = players_db()
    trending = get("/players/nfl/trending/add?lookback_hours=24&limit=100")

    doc = [f"# Sleeper brief — {season} Week {week} (@{a.user})", ""]
    for lg in leagues:
        print(f"Building {lg['name']}...")
        doc.append(league_brief(lg, uid, week, trending, P))
    text = "\n".join(doc)

    if a.ask:
        try:
            import anthropic
        except ImportError:
            sys.exit("pip install anthropic first (or drop --ask and paste the brief into Claude).")
        msg = anthropic.Anthropic().messages.create(
            model="claude-sonnet-5", max_tokens=3000,
            messages=[{"role": "user", "content": PROMPT + "\n\n" + text}])
        text += "\n\n---\n# Claude's calls\n\n" + "".join(b.text for b in msg.content if b.type == "text")
    else:
        text += "\n\n---\n_Paste this into Claude with:_\n\n> " + PROMPT.replace("\n", " ")

    context = build_context(leagues, uid, a.user, state, week, P)
    Path("snapshot.json").write_text(json.dumps({"text": text, "context": context}))
    out = Path(f"sleeper_brief_week{week}.md")
    out.write_text(text)
    print(f"\nWrote {out.resolve()}")


if __name__ == "__main__":
    main()
