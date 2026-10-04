# Security & Data Policy

## Synthetic data only

Quillrange (this repo) contains **no real personal or financial data**. The
bank on screen is **Rookvale**, a fiction. Every customer, account number,
passport number, policy, and document is synthetic. IBANs use the fictional
country code `TB` (not a real bank product). Emails end in `@example.com` /
`@trustbank.example` (legacy path strings; not a live brand). If you believe
any data resembles a real individual or institution, open an issue and it will
be changed.

## Reporting a vulnerability

Do not open a public issue with exploit details.

- Prefer GitHub [private vulnerability reporting](https://github.com/sammy995/fiduciary/security/advisories/new)
- Or open an issue titled **Security — contact request** with no details

## Scope

Quillrange evaluates model *behavior* inside Rookvale scenarios. It is not a
production banking system and stores no real user data. Real model runs need
your own API keys or a local model server — keep keys in `.env` (gitignored),
never in the repository.
