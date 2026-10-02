# Binocular — Mac + iPhone account preview

A new shared SwiftUI app with genuine email-code account authentication and server-backed profile syncing, ready to connect to a Supabase project. The existing desktop football app remains in outputs/Binocular.app.

## Implemented in this preview

- One shared Mac/iOS source tree and a generated multi-platform Xcode project.
- Supabase email-code sign-up/sign-in, Keychain session storage, token refresh, sign-out and account deletion.
- An account-owned Sleeper username and favorite league IDs, refreshed on foregrounding and at 60-second intervals while active. Server revisions reject stale saves rather than silently overwriting another device.
- Native Sleeper league discovery without Python or a Sleeper password. A linked username is public lookup, not identity verification.
- User-bound database functions, row-level read policies, and a server-only account deletion function.
- Original Binocular icon assets and shared football styling. No personal roster snapshots or research are bundled.

## What is not live yet

The Supabase project URL and publishable key are configured. Backend/001_accounts.sql was applied successfully through the project SQL editor on September 17, 2026. Email sign-in, cross-device syncing, row-level isolation and deletion still require integration testing. The deletion Edge Function was deployed on September 17, 2026 with server-side Auth.getUser token verification. A live invalid-token request returned HTTP 401 and "Sign in required"; no account was deleted. A valid-account deletion test remains pending. The current default email sends a link; this code-based app needs an OTP email template. The dashboard requires custom SMTP or a paid template-editing option before that template can be changed. The configuration is now present, but receiving a usable sign-in code is blocked until the email template is configured.

League roster screens, a standings display, current-week transaction activity, and scoring details were added September 22. Player/trade research, feedback email delivery, and a hosted daily research worker have not yet been ported into this new app. Those remain available in the existing desktop version. This is not an App Store-ready replacement.

## Connect the backend

1. Create a Supabase project under your account. Keep its database password and service-role/secret keys private.
2. Apply Backend/001_accounts.sql to the project.
3. Enable email authentication. Change the Magic Link email template to include `{{ .Token }}` so users receive a code. Configure a production SMTP sender and appropriate OTP/rate-limit settings before public testing; the default development sender is not a public launch mail service.
4. Put only the HTTPS project URL and `sb_publishable_...` key in Sources/Binocular/ServiceConfig.plist. The app rejects secret keys. These two values are client configuration; RLS and authenticated server functions protect user data.
5. Deploy Backend/functions/delete-account as a Supabase Edge Function. Use the function configuration from Backend/config.toml. The function verifies the bearer token with Auth.getUser before deleting that exact user. The service-role key belongs only in server environment variables. No caller-controlled user ID is accepted.
6. Run the two-account/two-device checks in Backend/ACCEPTANCE.md. The database schema and function are prepared but were not integration-tested locally because Postgres, the Supabase CLI and a hosted project are unavailable.

## Build and test

Xcode 27 is installed at /Users/owen.coffer/Downloads/Installers/Xcode.app. The native Xcode UI successfully built the Mac target on September 17, 2026. Open Binocular.xcodeproj, select your Apple Developer team, and replace the provisional `app.binocular.preview` bundle identifier with one registered to your developer account. Choose a Mac or iPhone Simulator destination. The target supports macOS 14+ and iOS 17+; iPad compatibility uses the same layout.

The project file parses successfully with plutil. The full SwiftUI Mac sources compile using the installed macOS 26.5 SDK. The default macOS 27 SDK lacks a SwiftUI macro plugin in the current Command Line Tools installation. An iPhone Simulator build was attempted from the restricted command environment but failed on SwiftUI macro-plugin execution and Simulator service access. The native Xcode Mac build passed. On September 17, 2026, selecting iPhone 17 in Xcode and building also succeeded. Simulator launch was initiated, but its window was not accessible to the UI tool, so the running iPhone interface and live sign-in are still unverified. Xcode signing, sandbox entitlements, device testing and TestFlight distribution are still required.

`Tests/ServiceChecks.swift` runs with the installed Swift compiler and mocked networking; it checks username/path validation, token expiration, OTP request headers, rate-limit handling, unauthenticated sync rejection and revision decoding. It sends no real email. XCTest equivalents for pure model checks are in Tests/BinocularTests. SwiftPM's test runner is blocked by nested sandbox execution on this host; do not interpret that as a passing integration suite.

## Release work still required

Port the football features and hosted research pipeline; add feedback delivery with server-held email credentials; publish privacy/support pages and link them from onboarding/settings; finalize data retention and account deletion for every new table; configure release email/CAPTCHA protections as needed; run accessibility and offline/conflict tests; verify API/content rights; complete App Store privacy, screenshots, metadata and review requirements. Paid/public commercial use needs confirmation against Sleeper's non-commercial API terms.

Apple Developer membership: user confirmed available. Platforms: Mac and iPhone. Account model: Binocular login with cross-device syncing. Supabase project: osalhgbnygzbbgniqtpz; client configuration saved and account SQL deployed. Email sender/template and live account integration tests remain pending. See Backend/EMAIL_SETUP.md for the free Gmail preview path.

References:
- https://supabase.com/docs/guides/auth/auth-email-passwordless
- https://supabase.com/docs/guides/database/postgres/row-level-security
- https://supabase.com/docs/guides/functions/auth
- https://developer.apple.com/app-store/review/guidelines/

## September 22 league center update

League names now open a native league center with all teams, starters (including empty slots), bench, reserve, taxi, standings, scoring settings, and current-week transactions. Failed claims are distinguished from completed changes. Player metadata is cached in memory for 24 hours with shared in-flight requests. Refresh failures preserve the previously displayed snapshot and timestamp. No roster mutations are supported.

Validation: all shared SwiftUI and service sources passed type checking with macOS 26.5 SDK; mocked service checks passed, including bench/reserve/taxi separation, fractional standings points, and null transaction fields. Full Xcode build remains blocked in the restricted command environment by SwiftUI macro-plugin execution and Simulator service access. This new screen still needs native Xcode Mac/iPhone build and visual verification; the earlier September 17 binaries do not contain this update.

## September 23 preview build

Built the shared SwiftUI sources into outputs/Binocular Preview.app with the installed macOS 26.5 SDK and verified its ad-hoc signature. Live UI checks successfully discovered all three coffero leagues and loaded Jacked Pine standings. Public browsing is available from the login screen without an account; it does not save or sync favorites. Added clearer email-delivery and invalid-code errors and a resend button. Mock service checks passed, including those failure cases. iPhone/device testing and successful SMTP login remain pending. This is a local preview, not an App Store distribution build.

## September 28 usability update

The local preview now remembers the last successfully searched public Sleeper username and reloads its leagues when Explore opens. A successful initial email-code request starts the same 60-second cooldown as a resend; changing the email view cannot bypass it. Failed delivery does not impose a new local cooldown. Full shared Mac sources compiled and mocked service checks passed. The updated ad-hoc signed build is outputs/Binocular September 28.app; launch/visual verification was blocked by computer-use timeouts. iPhone build and live SMTP authentication remain unverified. Email templates were configured September 22; Gmail credential rejection, not the template, is the last confirmed delivery blocker.
