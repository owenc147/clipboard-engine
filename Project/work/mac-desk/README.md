# Personal Mac Manager desk

Implemented only in outputs/Binocular.app. The public-app project is unchanged.

- Offer journal: manual sent/received offers, assets, other assets/picks, date, notes, status history. No private-offer API assumed. Historical names and market snapshot are retained.
- Trade builder: full-name paste matching, both-side FantasyCalc totals and net values. Unpriced assets explicitly excluded. Title and acceptance models are not connected; no invented odds.
- Starter guard: current NFL week, status transitions and pre-lock checks within 60 minutes of scheduled kickoff. Reserve/taxi/ineligible/locked bench players are excluded; a player is not allocated twice. Coverage uses health then market value, not projected points.
- Market board: league team count, QB count and PPR passed to FantasyCalc. Keeper leagues use redraft values. 30-day changes are provider data, not stored daily observations.
- Rival watch: retained Sleeper transactions plus observed roster/role differences, with rival-rival completed trades highlighted. Not a complete historic transaction archive.
- Bye grid: complete regular-season schedule required; maximum position matching for active roster depth, excluding reserve/taxi. Injuries are excluded from future bye coverage.
- JSON: saved after every successful desk operation, including offers, history, roster context, transactions, values, schedule, alert history, timestamps and model availability.

Storage: ~/Library/Application Support/Sleeper Brief/profiles/<username>/desk/
Files: desk.json (journal/state), binocular-export.json (reader snapshot), players-cache.json.
The Export JSON button also saves a copy through a normal Mac save dialog.

Monitoring: startup, every five minutes while app runs, and wake. Mac sleep/closed app are not monitored. In-app alerts and a Dock badge; no push service. Markets cached six hours, schedule twelve hours; timestamps/warnings shown. No Codex credits needed for these public-feed refreshes.

Public sources:
https://docs.sleeper.com/
https://fantasycalc.com/
https://api.fantasycalc.com/values/current
https://github.com/nflverse/nfldata/blob/master/data/games.csv

Validation: test_desk.py, live three-league refresh, native build/signature check and UI inspection. Test offers use temporary directories only.
