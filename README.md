# NSE EOD Android pilot (source code, not published to GitHub)

## Build and download the Android app from GitHub Actions artifacts

1. Create a GitHub repository, unzip this source ZIP **locally**, and commit/push the *contents of the `nse-eod-pilot` directory* at the **root** of the repository. In particular, `.github/workflows/build-android.yml` must be at the root; uploading the ZIP as a single file will not run the workflow.
2. Push to the `main` branch. Alternatively, on GitHub select **Actions → Build Android pilot APK → Run workflow**. GitHub Actions runs the offline importer tests, builds a debug-signed APK, and uploads an artifact called **nse-eod-pilot-debug-apk** *if all steps pass*.
3. In the completed green workflow run, scroll to **Artifacts**, download **nse-eod-pilot-debug-apk**, extract its ZIP, and install `app-debug.apk` on an Android device (allow installation of the APK from that source when prompted). The APK is a **debug pilot build**, not a production signed release or Play Store package. You may need to sign in to GitHub to obtain the artifact; artifacts are set to expire after 30 days (subject to repository policy).
4. This ZIP includes **source and the build workflow, not an already built APK**. No GitHub repository has been created or Actions run from this workspace, so APK build/install success is not yet verified. Read workflow logs and address build errors if any.

**Daily market data is a different workflow:** Import your legitimately obtained NSE EOD file locally using `pipeline/ingest.py`, regenerate `data/mobile.json`, and push it to the public repository. In the installed app set GitHub owner/repo + `main` + `data/mobile.json` under **Settings**, then tap **Refresh now**. Rebuilding/downloading the APK daily is *not required* for data-only updates. The current mobile export only includes selected EQ symbols, so it is **not full-market coverage**. This repository does not contain NSE data by default and does not automate NSE collection. Do not commit `market.db`, private data, or unauthorized redistribution of NSE market files.

## What this pilot provides
- Android Studio Kotlin project (`android/`) wrapping bundled, offline HTML/ECharts using `WebViewAssetLoader`. Only a GitHub snapshot read needs network permission; no APK is supplied; **Android build/device run have not been verified in this environment**.
- `preview.html`: identical, self-contained desktop/mobile browser preview with an embedded ECharts runtime.
- Settings at the bottom: public GitHub `owner/repo`, branch (simple branch name; no slash), JSON path; save, tap **Refresh now**, or enable **Check for updated data on app opening**. The Android native bridge downloads only a validated HTTPS `raw.githubusercontent.com` JSON snapshot, validates it, and persists it in app-private storage. Refresh errors keep current data. **GitHub source code alone is insufficient**: `data/mobile.json` must be regenerated and committed after every day’s EOD source is imported. No token or private repository support; no background polling or automatic market ingestion.
- Synthetic, reproducible weekday sample; **not actual NSE market data, market calendar, or live prices**.
- EQ close=high results (latest dataset session or trailing year), daily % change, latest-session informational non-EQ table, per-column filters (including searchable value checkboxes, numeric/date ranges), sorting, 35-row pages.
- For selected EQ symbols: up to five-year daily/weekly/monthly candles, volume, per-period SMA-20, Wilder RSI-14 and % change (tooltip and optional purple line).
- `pipeline/ingest.py`: Python 3 standard-library-only user-supplied CSV/ZIP -> SQLite -> mobile JSON; older than five-year prices removed, one-year EQ flags materialized, import deduplicates on (date,symbol,series).

## Try it
1. Open `preview.html` in a browser, or open `android/` in Android Studio and build/run the app on an API 26+ device with JDK 17 and installed Android SDK 35. The project requires Gradle/AGP/Kotlin dependencies from configured repositories on the development machine. A Gradle wrapper and prebuilt APK are **not** included; the GitHub Actions workflow installs Gradle 8.11.1 to build the APK.
2. To enable GitHub updates, publish the desktop-exported JSON at `data/mobile.json` in a **public** repository. At the bottom, save `owner/repo`, a simple branch such as `main`, and `data/mobile.json`. Tap **Refresh now** each time the JSON is updated in GitHub. The app also offers an optional check **on app opening** (not background synchronization). The browser preview depends on the browser permitting fetch of public GitHub raw files; the Android app uses a native HTTPS bridge.
3. Click **Trailing year** or **Latest session**, filter any header using ▼, and tap an EQ row for candles. Switch Daily / Weekly / Monthly. The initial demo is synthetic.
4. For your own locally obtained NSE end-of-day cash-market files (legacy CSV or one-CSV ZIP), from the repo root run:

   `python pipeline/ingest.py --db market.db --import-file /path/to/day1.csv --import-file /path/to/day2.zip`

   `python pipeline/ingest.py --db market.db --export mobile.json --symbols SYMBOL1,SYMBOL2`

   Import `mobile.json` with the app's **Import export JSON** picker. Existing imported data is replaced, not merged in-app. Repeat desktop ingestion for each day; the app does **not** automatically download or schedule NSE files. Valid source files and permitted data usage must be checked independently.
5. Run importer checks (on a Python environment providing `sqlite3`): `python -m unittest discover -s tests -v`.

## Cross-check sample (illustrative, not real NSE securities)
Input UDiFF-shaped CSV:

```csv
TradDt,TckrSymb,SctySrs,OpnPric,HghPric,LwPric,ClsPric,PrvsClsgPric,TtlTradgVol
2026-11-20,TEST,EQ,100,105,99,105,100,1500
2026-11-20,OTHER,BE,200,210,198,208,200,3000
```

Expected: `TEST` appears in EQ signals with **+5.00%**; `OTHER` appears in non-EQ information with **+4.00%**; `TEST`'s daily candle is O100 H105 L99 C105. Importing twice changes neither row count nor signal count. A 2025-11-18 close=high signal is excluded when newest date is 2026-11-20, but its underlying EQ candle survives until its five-year cutoff. `tests/test_pipeline.py` contains this cross-check.

## Pilot limitations / next production steps
- Mobile export intentionally limited to **1–35 chosen EQ symbols** with five-year EQ candles plus the **latest-date non-EQ universe**, max 150,000 rows. It does not yet show *all* NSE EQ signals if those symbols were not exported. For full-market coverage, replace mobile in-memory/localStorage datasets with a paginated query backend and indexed time-series chart endpoint.
- Non-EQ is latest-session only in this pilot (the earlier proposed one-year selectable non-EQ table history is not implemented). Non-EQ charting is not implemented.
- Android refreshed data persists in app-private storage (up to 18 MB); browser preview uses localStorage when within its storage quota, otherwise only this session. Desktop SQLite is the durable five-year store. No end-to-end five-year NSE history is bundled or sourced automatically.
- Importer supports the listed aliases; inspect the *actual* official file headers before onboarding a new NSE schema. It does not enforce exchange calendar, source completeness, corporate-action adjustments, or redistributable-data licensing. Daily % uses the file's previous-close; absent/zero values show N/A. Chart period % compares adjacent chart period closes.
- The Android app does not download executable GitHub code or update its APK from GitHub. Changed UI/app code still requires a rebuilt and distributed APK.
- Test on a physical Android device, verify source formats and rights, add scheduler, retries/checksums/audit logging, backend pagination/auth, corporate action handling, validated dates and a production data service before deployment.

## License note
The JavaScript chart runtime in `android/app/src/main/assets/echarts.min.js` is Apache ECharts, distributed under the Apache License 2.0; review upstream notices for redistribution. This pilot's own example code is supplied for evaluation without a separate license grant.
