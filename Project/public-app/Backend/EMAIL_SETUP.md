# Email setup — free preview path

User prefers no domain or email subscription cost. Use a Gmail sender for the private preview; address choice is pending. A dedicated Binocular Gmail is preferable to publishing the owner's personal address. No new Gmail account, paid service, domain purchase or email transmission has been performed.

The user must create/sign into the chosen Gmail account and handle its password, two-step verification and app-password creation themselves. They should enter the app password directly in Supabase SMTP settings, not in chat, source files, or either app. App passwords may be unavailable depending on Google account settings.

Supabase Authentication → Emails → SMTP Settings:
- Sender name: Binocular
- Sender email and username: the chosen full Gmail address
- Host: smtp.gmail.com
- Port: 465 (TLS)
- Password: the app password entered privately by the user

After SMTP is configured, set the Magic link or OTP email subject to `Your Binocular sign-in code` and body to email-templates/login-code.html. Check the first-time Confirm sign up template too so both first-time and returning users receive a code. Verify the actual provider template behavior with a real approved sign-in before reporting success.

Gmail is for low-volume preview testing. Public release sender capacity and delivery must be reviewed before launch. Resend remains an option if a domain is acquired later.

Sources checked September 17, 2026:
https://support.google.com/accounts/answer/185833?hl=en
https://support.google.com/mail/answer/7104828?hl=en
https://supabase.com/docs/guides/auth/auth-smtp
https://resend.com/docs/send-with-supabase-smtp
