from pathlib import Path
p=Path('outputs/Sleeper Brief.app/Contents/Resources/sleeper_assistant.py')
s=p.read_text().replace('from collections import Counter','from collections import Counter\nfrom datetime import datetime, timezone\nfrom functools import lru_cache\nfrom itertools import zip_longest')
s=s.replace('def get(path):','@lru_cache(maxsize=256)\ndef get(path):')
s=s.replace('for slot, p in zip(slots, starters):','for slot, p in zip_longest(slots, starters, fillvalue=None):\n        if slot is None:\n            continue')
s=s.replace('No red flags in your starting lineup.','No flagged injuries or empty slots in the cached roster.').replace(' — natural partner',' — roster-count fit only')
s=s.replace("week = a.week or state.get(\"display_week\") or state.get(\"week\") or 1",'week = a.week or state.get("week") or state.get("display_week") or 1')
s=s.replace("f\"{me.get('points', 0):.1f} to {opp.get('points', 0):.1f}\"",'f"{score(me):.1f} to {score(opp):.1f}"')
s=s.replace('m["matchup_id"] == me["matchup_id"] and m["roster_id"] != rid','me.get("matchup_id") is not None and m.get("matchup_id") == me["matchup_id"] and m["roster_id"] != rid')
s=s.replace('added in {c:,} leagues (24h)','{c:,} adds (24h)')
s=s.replace('Thin at: {', 'Fewer rostered at: {').replace('. Deep at: {','. More rostered at: {')
s=s.replace('L += partners or ["- No clean positional match this week."]','L.append("Counts do not measure starter quality or trade value; injuries and reserve players can distort them.")\n    L += partners or ["- No complementary roster-count fit found."]')
s=s.replace('    L.append("")\n\n    # Waivers','    L.append("Reserve: " + (", ".join(name(p, P) + (f" [{flag(p, P)}]" if flag(p, P) else "") for p in (mine.get("reserve") or [])) or "—"))\n    L.append("Taxi: " + (", ".join(name(p, P) for p in (mine.get("taxi") or [])) or "—"))\n    L.append("")\n\n    # Waivers')
s=s.replace('For EACH league give me: (1) start/sit calls for any close decisions, (2) the one waiver move worth making\nand what to drop, (3) one specific trade offer to send and to whom. Be direct, no hedging. Account for each\nleague\'s scoring format (superflex / PPR / pass TD points).', 'For each league, evaluate close start/sit decisions, available waiver upgrades with a drop candidate,\nand possible trades. Cite dated sources, distinguish facts from opinions, and state uncertainty.\nUse the complete scoring settings, current ownership, injuries, and roster opportunity cost.\nDo not force a trade or treat positional counts as player value. Verify news before kickoff.')
insert='''
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
            "reserve":mine.get("reserve") or [], "market":market})
    return result

'''
s=s.replace('\ndef league_brief',insert+'\ndef league_brief')
s=s.replace('    out = Path(f"sleeper_brief_week{week}.md")','    context = build_context(leagues, uid, a.user, state, week, P)\n    Path("snapshot.json").write_text(json.dumps({"text": text, "context": context}))\n    out = Path(f"sleeper_brief_week{week}.md")')
p.write_text(s)
