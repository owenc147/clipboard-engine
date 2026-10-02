# Clipboard model cross-check

Review only. No application code, model weights, or user offers were changed.

## Historical comparison

11,562 eligible player-week records across 2023–2025. Fit on 2023, selected on 2024, evaluated on 3,902 records from 2025. The table compares the proposed weekly calibration with the current blend weights applied to a weekly approximation. It is not a replay of the full rest-of-season model. Lower RMSE is better; units are fantasy points.

| Position | 2025 records | Existing weights, weekly approximation | Candidate | Error reduction |
|---|---:|---:|---:|---:|
| QB | 512 | 7.693 | 7.655 | +0.49% |
| RB | 1042 | 6.714 | 6.760 | -0.68% |
| WR | 1633 | 6.567 | 6.584 | -0.26% |
| TE | 715 | 5.962 | 5.973 | -0.17% |

Recommendation: retain existing weights. The QB gain is small and has not been established as statistically reliable; RB/WR/TE candidates worsen held-out error. More training did not produce a broad improvement.

## Prioritized improvements to consider

1. **Apply complete league scoring.** The current feed retains PPR points and passing touchdowns, then adjusts passing TD value. It cannot reconstruct completion bonuses, altered passing-yard rates, interception penalties, threshold bonuses, or custom defense points. MSU uses +0.1/completion and 1 point per 22.5 passing yards. Netanyahu and MSU use -1/interception and yardage bonuses. Example: 25 completions and 300 yards contribute 2.5 + 1.33 = 3.83 additional MSU points versus a 0.04-yard/no-completion calculation, before interception and threshold-bonus differences. This is scoring arithmetic, not a predicted accuracy gain. Retain projected stat components and validate the scoring function against actual Sleeper matchup totals. Threshold bonuses require distributions or probabilities, not just applying thresholds to mean yards.

2. **Make acceptance estimates evidence-based.** The journal has zero resolved offers, but the existing model also contains seven seeded outcomes (four accepted, three rejected), plus accepted-trade sides. These are different datasets. Accepted-only transactions cannot establish the base rejection rate; seven labeled offers are too few to validate personalized odds. Capture offer-time features, timestamps and manager IDs, deduplicate trade/offer examples, preserve outcomes, and evaluate on later offers. Do not treat a fit evaluated on its training labels as accuracy.

3. **Verify bracket support without overstating the current defect.** Your settings show four playoff teams in Jacked Pine, six in Netanyahu, seven in MSU. The catch-all bracket is a seven-team shape; that matches MSU’s team count. It would incorrectly omit the eighth seed for an eight-team league. The code also loads a reseeding field but never uses it. That alone does not establish an error for your current leagues: the only enabled flag in the inspected settings is Jacked Pine’s four-team format. Add fixtures for every supported size and verify the provider field semantics before changing the bracket.

4. **Validate the actual decision outcomes.** A weekly point-error comparison does not validate title probabilities, trade acceptance, injury hazards, or start/sit gains. Add chronological league replays with league scoring, reserve and game-lock constraints; report calibration, uncertainty, and decision-level improvement against unchanged baseline rules.

## Evidence limits

- Historical projections were fetched today; original pregame snapshots were not available. Retrospective corrections cannot be ruled out.
- Sample excludes inactive/bye games and projections below three points; results do not measure availability prediction.
- Evaluation used standard full-PPR, four-point passing TD inputs, not every custom league rule.
- Player position metadata is current.
- No title-odds improvement or new acceptance accuracy was demonstrated.

## Sources and reproducibility

- Installed model-engine.js and model_data.py inspected against the work copies.
- Saved Sleeper league scoring/settings and local offer journal inspected.
- Public historical Sleeper projection and statistics responses retained in cache/.
- [Sleeper league and matchup documentation](https://docs.sleeper.com/).
- train.py reproduces the separate evaluation; training-report.json contains metrics and weekly-calibration.json contains experimental candidates. None is loaded into Clipboard.
