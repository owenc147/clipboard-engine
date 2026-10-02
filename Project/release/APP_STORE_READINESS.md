# Binocular public release readiness

Reviewed September 16, 2026. This is a release preparation assessment, not an App Store submission.

## What can carry forward

Original Binocular identity and stadium-inspired visual design; league navigation; read-only Sleeper roster, matchup and activity views; dated research with sources; ownership-aware player and trade cards. Local Sleeper profiles are not authenticated Binocular accounts and do not establish ownership of a Sleeper identity.

## Required engineering work

- Create a signed Xcode application project and test a sandboxed distribution build. Current host has Command Line Tools selected, and current bundle uses ad-hoc signing.
- Replace the reliance on /usr/bin/python3 and developer tools with native Swift networking or an appropriately bundled runtime. Mac App Store apps must be self-contained and sandboxed. Native networking also provides a path to iOS.
- Create first-run onboarding without bundled personal roster snapshots, personal research, local machine paths or a default owner's username. Ship synthetic demo data only if clearly labeled.
- Keep per-user profiles and preferences separate. If cloud accounts are chosen, use an actual authenticated identity such as Sign in with Apple, enforce server-side authorization for every user-owned record, and provide account deletion. Entering a Sleeper username is public lookup, not proof of account ownership.
- Move daily research generation to a hosted service for public users; do not require customers to keep this owner's Mac or Codex running. Separate shared NFL research from personalized league analysis. Cache public player data, limit requests, retain source dates, and expire stale advice.
- Replace owner-only Gmail SMTP with a server-side feedback endpoint and mail provider. Keep mail credentials off clients, validate inputs, rate-limit submissions, and send submitted feedback to ofc14700@gmail.com with subject BINOCULAR SUGGESTION. Do not automatically email player recommendations under that feedback subject.
- Finish onboarding, offline/error states, profile switching/deletion, accessibility, and testing with separate users. Keep feedback/history private if cloud sync is added.

## External release prerequisites

- Apple Developer Program membership and App Store Connect access. Apple lists membership at US$99 per year or local equivalent. The owner must handle enrollment, payment and agreements.
- Sleeper's documentation describes free API access for non-commercial purposes. Confirm permission/terms for the intended public distribution and any paid, subscription or advertising model before commercial launch.
- Use original art and appropriately licensed assets; visual inspiration does not grant rights to ESPN, Madden, NFL or team logos.
- Publish a real privacy policy and support URL; complete App Store privacy disclosures according to actual data handling. Prepare app metadata, screenshots, age rating, review notes and a working review account if login is required.
- Release through TestFlight for testing, then submit a finished build to Apple for review. Approval cannot be guaranteed.

## Decisions pending

Confirmed: Mac + iPhone, Binocular accounts with syncing, and existing Apple Developer membership. The shared account preview is in public-app/. Supabase project not yet created. Still pending: business model, hosting configuration/budget, full Xcode installation, live account integration tests, football feature migration, and App Store submission.

## Sources

- Apple review rules, including Mac App Store requirements and privacy: https://developer.apple.com/app-store/review/guidelines/
- Apple Developer enrollment: https://developer.apple.com/programs/enroll/
- Account deletion: https://developer.apple.com/support/offering-account-deletion-in-your-app
- Sleeper API access and usage: https://docs.sleeper.com/
