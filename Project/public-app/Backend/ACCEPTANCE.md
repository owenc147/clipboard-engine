# Required integration checks before TestFlight

Use an isolated staging project, two newly created test accounts A/B, and two devices signed into A. Do not use real customer data.

1. Request an email code, verify it, and reopen the app. Confirm session restoration; wrong/expired/reused codes must fail. Confirm rate limits and production sender delivery.
2. Account A links a Sleeper username and favorites a league. Account A on the second device refreshes and sees the same username/favorite. Account B sees neither record, even if it requests A's user_id directly through REST. The client does not supply identity to the mutation RPC.
3. Direct authenticated INSERT/UPDATE/DELETE on binocular_profiles must be denied. Unauthenticated RPC calls must fail. Account B's get_profile/save_profile must only create/change B's row.
4. Both A devices fetch revision N. Save from device 1 to revision N+1. A device 2 save with N must fail with sync_conflict and leave device 1's change intact. Reload and explicitly retry.
5. Sign out A and sign in B on the same device; no old leagues/profile/favorites remain in memory. Simulate a revoked token and verify a return to sign-in. Never display raw tokens in logs.
6. Delete A through the app confirmation. Verify auth.users and profile deletion, old-token access denial, and B's unaffected state. Confirm the second A device returns to sign-in. Sleeper data must remain untouched.
7. Remove network access while signing in, linking and saving. Confirm an honest error, no false success and no silent overwriting of unsaved input.
8. Run on physical Mac and iPhone, use Dynamic Type and VoiceOver, then test a signed sandboxed release build. No /usr/bin/python3 or local Codex dependency may be needed.

These are pending checks, not a report of successful execution.

## September 17 deployment checks

- Profile SQL applied successfully to osalhgbnygzbbgniqtpz.
- delete-account deployed with Auth.getUser verification; legacy-only gateway verification disabled to match Backend/config.toml.
- Live POST with intentionally invalid bearer token returned 401 and `Sign in required`. No user account was deleted.
- Native Xcode Mac and iPhone 17 Simulator builds succeeded. iPhone runtime UI inspection, real login, account deletion and two-device/two-account acceptance checks remain pending.
