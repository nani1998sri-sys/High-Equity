# Production release status — NOT APPROVED

Status: source-only handover; no verified production Android APK or live NSE ingestion. Date: 2026-11-22.

## Present
- Android Studio project and HTML UI for EQ close=high, latest non-EQ information, filters, 5-year candle views, SMA-20, RSI-14, % change.
- Local offline import pipeline supporting selected cash market CSV/ZIP header aliases, SQLite 5-year prices and 1-year materialized EQ flags.
- GitHub Actions workflow intended to run importer tests and build a DEBUG APK artifact after push to main.
- GitHub public JSON snapshot refresh on demand / on app opening; no automated data extraction.

## Release blockers (must be completed and verified before production)
1. Obtain suitable rights to access, store, and publicly redistribute NSE data. Do not upload market data or operate a public data mirror without confirming license terms.
2. Backfill actual FIVE YEARS of all requested EQ stocks and non-EQ data; check dated files, market calendar, missing days, corporate actions and source revisions.
3. Create an authorized and reliable daily post-final-file import job with idempotence, retry, reconciliation, failure alerts and audit trail. The current workflow BUILDS CODE ONLY.
4. Replace selected-symbol <=35 mobile JSON demo export with complete scalable backend or optimized incremental store and enforce one-year flag/5-year candle retention for the full market; verify network and Android storage at scale.
5. Run CI and instrumented tests on Android; fix any Gradle/Kotlin errors, validate indicator and percent-change calculations and full source-file schema in real data, and test imported-file consistency and offline behavior.
6. Prepare production app signing with secure signing keys, distribution/update process, privacy/security review, monitoring, user disclosures, and rollout plan.

## What the artifact contains
Workflow output, if a GitHub runner builds successfully, is a DEBUG APK in an expiring GitHub Actions artifact. It is NOT a production-signed application. Source archive itself is NOT an APK and has not been deployed by this assistant.
