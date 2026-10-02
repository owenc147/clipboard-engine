# Claude title model in Binocular

Added Sep 30, 2026 at Owen's request. New view: **Title model** (next to Manager desk).

Files (in outputs/Binocular.app/Contents/Resources):
- model_data.py — called by desk.py with op "model". Fetches public Sleeper data (projections weeks 1-17, 2026 weekly stats, 2022-25 season totals, schedules, rosters, completed trades in Owen's leagues and the Jacked Pine managers' leagues). Cached in the desk folder as model-cache.json.
- model-engine.js — pure math: history-blended values, optimal weekly lineups, player-level Monte Carlo (injury hazard, team correlation, playoff bracket), 1-for-1 to 3-for-3 trade scan, acceptance model (accepted-trade history + FantasyCalc + weekly chart, refit on offer-journal outcomes).
- model-view.js — UI. Also adds "Run title model on this offer" to the Manager desk trade builder.
- desk.py — one added branch for op "model"; index.html — two script tags.

Backups of the original desk.py and index.html: work/claude-model/backup-*/
Tests: work/claude-model/test_model_data.py (offline). Engine validated against Claude's browser runs (same title odds within noise).
To remove: restore the two backup files and delete the three model files.
If macOS reports the app as damaged after these edits, re-sign locally: codesign --force --deep --sign - outputs/Binocular.app

- theme-primetime.css: "Prime Time" cinematic dark theme (loaded last). Remove its <link> in index.html to restore the original look.

## Training log (Sep 30, 2026)
- Projection blend backtested on 2024 + 2025 (1,630 player snapshots, rest-of-season PPG): RB/WR/TE 95% projection / 5% history; QB 70/20/10 with 0.92 projection-bias correction. The original 60/25/15 blend was worse than projections alone.
- Weekly CV from 2024-25 actual/projected: QB .45, RB .62, WR .69, TE .70.
- Injury hazard from 2024-25 absence runs: RB .04, WR .038, TE .04, QB .03 per week; 18% season-ending; multi-week absences average ~3.3 weeks.
- Head-to-head calibration on 441 real matchups (Champions League 2023-26 and Owen's leagues): team-score CV 18.6%; Brier 0.220 vs 0.25 for a coin flip; big favorites win slightly more often than the model says.
- Acceptance training set expanded to 78 seeded sides + live 2026 sides (managers' other leagues added); known-outcome fit unchanged (6 of 7).

## App update (Sep 30, late)
- Title model view: "This week" card (start/sit check against your Sleeper starters, weekly win-odds strip by opponent), "Free agents worth a claim" (top 60 unrostered players by projection, gain after the cheapest drop), ⌘7 shortcut.
- model_data.py now sends each team's starters/reserve and each league's free-agent pool.

## Clipboard rebrand (Oct 1, 2026)
- App renamed **Clipboard** (display name, icon `Clipboard.icns`, copy). Bundle folder is still `Binocular.app` so scripts and scheduled tasks keep working.
- Design system: `clipboard.css` (night-game call sheet: charcoal laminate, chalk ink, DIN Condensed heads, Avenir Next body, square ruled boxes, print-colour section bars).
- `clipboard-shell.js`: tab names (Gameday, Call sheet, Depth chart, Press box, The wire, Mailbag, Front office, Title odds), header "vs. <opponent>", settings drawer, copy pass, count-up and enter motion, NFL team picker (32 teams, colours only, no logos; stored in localStorage `clipboard-team`; contrast-checked against the sheet).
- Revert: in index.html swap `clipboard.css` → `theme-primetime.css` and `clipboard-shell.js` → `theme-motion.js`. Full pre-rebrand backup: `backup-clipboard-20261001-0402/`.
- If macOS says the app is damaged after these edits: `codesign --force --deep --sign - outputs/Binocular.app`

## Film room — scouting in all three leagues (Oct 1, 2026)
- `model_data.py` now tracks every manager in Jacked Pine, Netanyahu Ball and MSU Munches across all of their 2026 Sleeper leagues (`scouts`), with parallel cached fetches. Acceptance training now uses trades from every league of every manager in all three leagues (was house league only).
- `scout.js` adds a Film room panel to Title odds for whichever league is selected: activity tier, leagues/trades/adds, weakest spot and spare depth, predicted next move, chance of a trade this week, your best offer to them, their best move (the title model run from their side, auto-run), race and incoming-offer alerts, recent moves across all leagues.
- Rival scans in leagues over 12 teams use depth 8 and 3,000 sims to stay fast.

## Training log — Oct 1, 2026: review follow-up
- Weights: kept as is. The proposed QB blend change improved test error only 0.5%, and RB/WR/TE got worse.
- Scoring accuracy (fixed): the model used Sleeper's PPR total plus a pass-TD adjustment, so it missed league rules. `model_data.py` now keeps raw stat columns (KEYS) and each league's `score` and `bonus` settings; `model-engine.js` scores every QB/RB/WR/TE with that league's own rules: MSU's 0.1 per completion and 1 pt per 22.5 passing yards, -1 INT in NB/MSU, 6-pt pass TD in Jacked Pine, and the 100/200-yd rush/rec and 300/400-yd passing bonuses in NB/MSU. Bonuses use an expected value for projections (lognormal yardage, CV pass .28, rush .55, rec .6) and exact values for played games. K/DEF stay on Sleeper's PPR total. Week 5 check against live projections, custom minus PPR per rostered player: MSU QB +3.4/wk (range +2.8 to +4.3), NB QB +0.3, Jacked Pine QB +2.6 (already handled before by the TD adjustment), RB/WR/TE about +0.1. Cache moved to model-cache-v2.json. Players with no stat columns fall back to PPR.
- Brackets: added an 8-team bracket (1v8, 4v5, 2v7, 3v6). The current leagues use 4, 6 and 7 teams, which were already correct.
- Acceptance: still only 7 seeded outcomes and nothing resolved in the desk journal. Market weight stays bounded at 0.04-0.12 until 15+ labels. Log every sent offer's outcome in Front office.

## App name and icon (Oct 1, 2026)
- The bundle was renamed to `outputs/Clipboard.app`. `outputs/Binocular.app` is now a symlink to it, so existing scripts and scheduled tasks keep working.
- Window title and app menu now say "Clipboard". The two strings were patched in the binary (same length); `work/App.swift` has the same change for the next native build. The bundle id `local.coffero.binocular` is unchanged so saved Keychain items (Gmail app password) still work.
- Icon: the app sets its Dock icon at runtime from `BinocularStadium.icns`. That file and `Binocular.icns` now hold the Clipboard icon, and the originals are in backup-clipboard-20261001-0402/.
- The binary changed, so the app must be re-signed once on the Mac: `codesign --force --deep --sign - ~/Documents/Codex/2026-09-15/i-x20/outputs/Clipboard.app`

## Stitch design pass (Oct 1, 2026)
- Owen designed three screens in Google Stitch (Gameday, Title odds/Film room, team picker). `clipboard-stitch.css` + `clipboard-stitch.js` implement that "Sideline Tactical Call Sheet" system on top of clipboard.css: walnut sidebar with record chips and an intel block, top status bar (week, live kickoff countdown, Sleeper sync, quick find with ⌘F, refresh), steel clip with rivets, red index tabs with [01 · …] numbering, three-panel live matchup with model win probability, NEXT CALL banner, dense zebra roster rows, index-card title-odds board with tape and tier tags, coloured week strip, dossier-grid Film room.
- The team picker (in clipboard-shell.js) is now the "Franchise alignment" matrix: AFC/NFC columns, 2×2 divisions, filters, select-then-confirm with live colour preview.
- Fonts bundled for offline use in Resources/fonts (Barlow Condensed 500-700, Archivo Narrow 400-700; SIL Open Font License).
- Revert: remove the clipboard-stitch.css <link> and clipboard-stitch.js <script> from index.html (backup: backup-clipboard-20261001-0402/index.pre-stitch.html).
- Depth chart (Stitch screen 4): with model data loaded, each starter shows opponent, model projection (league scoring), a 10th–90th percentile range bar with median, injury status and game day. The header shows total projection and a simulated lineup floor/median/ceiling. A "Kickoff lock cadence" card groups starters by game day, and bench players show projections with "Start over X" when they beat the weakest starter at their position. model_data.py now includes this week's NFL schedule (`nfl_week`: opponent, home/away, date). The public schedule has dates only, no kickoff times.

## Training log — Oct 1, 2026: external review follow-up
- Variance fix: the weekly CVs (QB .45, RB .62, WR .69, TE .70) are backtested *total* actual/projection spread, but the simulator added the season-talent draw (σ .12, rookies .18) and the shared NFL-team factor (σ .15) on top. Now the individual noise is σI = sqrt(σT² − σteam² − σtalent²), so total spread equals the backtest. Effect: slightly less randomness, so favourites' odds rise a little and long shots fall.
- K/DEF: now an additive normal (sd = CV × mean), floored at −10 (DEF) and −2 (K), so zero and negative games are possible. The depth chart ranges use the same rule.
- Not adopted: hard clipping (biases the mean), sentiment-based trade values (noise), behavioural penalties before data exists.
- tracking.js: Model scorecard (logs each league's weekly win probability per model load, scores it against the real result the next week: Brier, hit rate, calibration bins) and Offer log ("Log as sent" on each recommended offer, then Accepted/Declined/Countered with response time). Resolved offers are added to the acceptance-model labels automatically. Stored in the app's localStorage; "Copy log as JSON" exports both logs.
- Next candidates: opponent correlations (QB with opposing WRs, against opposing DEF), estimated from 2024–25 game logs; Sunday 11:45 ET inactive check.
- Compound Poisson-lognormal (Oct 1, 2026): QB/RB/WR/TE weekly scores are now yards-and-catches (lognormal) plus whole touchdowns (Poisson), so a TD is a real 4- or 6-point jump. Expected TD counts and TD points per week come from each player's own projected pass/rush/rec TDs, scored with that league's rules (6-pt pass TD in Jacked Pine), not fixed positional shares. The TD rate is tied to the same game shock as the yardage (γ = 0.35, mean-preserving), and to the talent and team factors. The yardage spread is solved by bisection from the exact variance formula so total spread still equals the backtested CV. Check on sample players: mean 16.50 vs 16.50 target, CV 0.694/0.620/0.450 vs 0.69/0.62/0.45 for WR/RB/QB. Quantiles barely move (WR p10/50/90 5.5/13.8/30.6 vs about 6.1/13.6/30.2 before); the gain is realistic lumpy outcomes, not a different average. drawP is exported for tests.
- Win-probability lineup (Oct 1, 2026): `TitleModel.winLineup(M,E)` simulates 4,000 copies of this week (same player draws as the season model, including Q/Doubtful miss odds and shared NFL-team factors). It starts from the max-points lineup and hill-climbs one-player swaps that raise P(beat this week's opponent) by at least 0.4 points, checking slot eligibility by matching. It runs in about 25 ms. Shown in Title odds → This week with your current Sleeper lineup, max-points and best lineups. Test: as a 29% underdog it kept the max-points lineup (already the best); as an 81% favourite it swapped a WR flex for a slightly lower-scoring RB (+0.5 pts win chance, lower variance). Limit: every player at a position has the same volatility (backtested CV), so "boom WR vs possession WR" at equal projections looks identical. Player-specific volatility needs weekly game logs.
- Deferred from the same review: Vegas kicker adjustment (needs a sportsbook feed; kickers are a small share of points), live in-game re-simulation (needs live stats plus game clock; Sleeper's public feed has live stats but no clock).
