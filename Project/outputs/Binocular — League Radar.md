# Binocular — League Radar

Open **League Radar** (⌘4) to inspect other teams across the Sleeper leagues loaded for your account.

- **Activity feed:** trades, waiver results, free-agent moves, traded picks, and reported FAAB amounts. Each item shows its status and league.
- **All rosters:** starters, bench, reserve, taxi squad, position counts, and records for each team.
- **Manager filter:** follows the same Sleeper account across your loaded leagues, including co-managed teams. Similar display names remain separate accounts.
- **Search:** find a player across rosters or filter the activity feed by player, team, or manager.
- **Roster observations:** compares consecutive refreshes for additions, removals, lineup changes, and reserve moves. Times are when Binocular detected the difference, not the exact time of the action. Observations can overlap a transaction.

Refresh manually or enable **Refresh every 5 minutes while app is visible**. This setting is saved. It does not run when Binocular is closed, and it does not send notifications.

Roster data is current at the displayed refresh time, even if an older score week is selected. The feed loads the current NFL week and previous week, and retains up to 500 transactions plus 300 observations per league on this Mac. The first refresh establishes the observation baseline. An unavailable transaction endpoint is labeled and previously saved history is retained. A failed overall refresh preserves the previous snapshot.

Only the leagues loaded for your account are included. There is no access to private messages, hidden waiver intentions, or actions Sleeper does not report. Historical transaction participants are associated with roster managers as mapped when fetched. Player injury metadata uses the separately dated player cache.

Data comes from [Sleeper’s documented roster, user, and transaction endpoints](https://docs.sleeper.com/). The integration is read-only.
