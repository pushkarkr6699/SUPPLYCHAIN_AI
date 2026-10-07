# SupplyChain AI current QA

<!-- master-release-2026-10-07 -->

Latest executed release: **348 passed**, zero failures/errors, 18 warnings. Actual data/model reconciliation, uploaded-data browser workflows, native chart controls, safe exports, security and dependency checks passed. This is a local demonstration release with explicit remaining scope, not blanket master-specification completion.

See [FINAL_IMPLEMENTATION_REPORT.md](FINAL_IMPLEMENTATION_REPORT.md) and the [199-section matrix](metadata/master_requirement_matrix.md) for current evidence and limitations. Earlier entries below are historical and retain their original dates/test counts.

---

# SUPPLYCHAIN AI — Final release QA

**Overall: READY WITH DOCUMENTED LIMITATIONS.**

Evidence assembled at 2026-10-05T08:07:37.826406+00:00. Scope: single-operator local classroom, teacher evaluation and portfolio showcase. This is not a public multi-user production certification.

## Release result

### Unified public/login/workspace follow-up ? 2026-10-06

The supplied recording was reviewed. The sidebar now releases all reserved width when closed, all seven navigation disclosures retain readable colors in Light/Dark/System states, and closing the Copilot drawer restores the dashboard width. Landing, login and workspace share branding and accessible interface motion. Settings ? Appearance provides a session animation toggle; device reduced motion takes priority. See [UNIFIED_EXPERIENCE.md](docs/UNIFIED_EXPERIENCE.md).

Regression: **120 passed**, two expected malformed-date fixture warnings. Public QA: **10 page/width combinations passed**. Chart QA: **14 layouts passed** with working zoom/pan/autoscale/reset/fullscreen/export. Local security audit: passed, no findings. Integrated browser QA: **8 functional groups passed, zero browser errors**. Evidence is recorded in `metadata/unified_experience_qa.json`, including sidebar collapse at 1512/1366/820/390/320px and the complete landing/login/logout flow.


### Shared chart controls follow-up ? 2026-10-05

The shared main application chart renderer now keeps toolbars visible, with contrasting 20px icons and 44px controls in Light and Dark themes. Controls wrap on narrow screens, have reserved space above the plot, and retain their native labels and handlers. Multi-series legends are separated from the toolbar and date labels. This applies to both demo and verified-data charts.

Browser QA covers 14 layouts across Overview, Delivery risk/segments/performance/threshold/calibration/explainability, and Demand overview/seasonality, including desktop, tablet, 390px and 320px widths, Dark theme and fullscreen. Actual zoom in/out, pan/zoom mode, autoscale, reset, fullscreen exit and PNG download passed. SVG dimensions are checked after resizing to catch stale fullscreen rendering. Full Python regression: **120 passed**, two expected malformed-date fixture warnings. Evidence: `metadata/chart_controls_qa.json`; rerun with `.venv\Scripts\python.exe scripts/chart_controls_qa.py` while the local preview is running.

The resize repair uses only repository-owned JavaScript and the already loaded Plotly API; no user data is inserted into executable code and no external script is loaded. Native controls are chart-type dependent: donut charts offer export/fullscreen, while axis charts additionally offer zoom/pan/autoscale/reset.


### Final product polish — 2026-10-05

Final formal acceptance: **65/65 passed, zero failed or blocked**, using the completed 32-step browser showcase. The final guided workflow also passed after the visible brand mark correction. Latest observed guide route transitions were approximately 3.7s Delivery, 1.8s Order, 0.9s Prediction and 0.6s Report on this local run.

All 16 requested upgrades are documented in [FINAL_POLISH.md](docs/FINAL_POLISH.md). Current full regression: **120 passed** (two expected malformed-date fixture warnings). Integration rerun: 27 routes, 26 source artifact hashes, both trained prediction controls and PDF exports passed. Rendered workspace/Delivery/public audits and the new guide/order/mobile workflow passed; the 32-step real-data showcase completed successfully. The earlier follow-up counts below are historical.

The final guide exercised keyboard disclosure navigation, selected-order trained inference, a guarded report-generation action and actual CSV/PDF downloads. PDF pages were rendered and inspected. Local security checks passed with no findings across 84 runtime Python files. Measured date filtering returned identical rows and reduced its median from approximately 62ms to 8ms on 65,752 rows; total browser route timings are recorded separately, without a loading-speed guarantee.

Evidence: `metadata/final_polish_qa.json`, `metadata/final_polish_performance.json`, `metadata/workspace_usability_qa.json`, `metadata/delivery_usability_qa.json`, `metadata/public_usability_qa.json`, `metadata/integration_qa.json`, `metadata/showcase_qa.json`, `metadata/security_audit.json`.

### Latest workspace and Delivery follow-up — 2026-10-05

The preceding 18 workspace issues and the new 16 Delivery issues are implemented, with numbered root-cause/fix notes in [WORKSPACE_USABILITY_FIXES.md](docs/WORKSPACE_USABILITY_FIXES.md) and [DELIVERY_USABILITY_FIXES.md](docs/DELIVERY_USABILITY_FIXES.md).

- Full regression: **115 passed**, two expected malformed-date fixture warnings.
- Workspace browser audit: **14 measurements and 9 functional groups passed**, zero browser errors.
- Delivery browser audit: **10 measurements and 3 functional groups passed**, zero browser errors. Daily risk aggregation also has direct unit tests covering missing values and source immutability.
- Public browser regression: **10 responsive route/width combinations passed**.
- Integration rerun: **27 routes**, **26 artifact hashes**, delivery/demand inference, dataset switching, Copilot and PDF generation passed.
- Local security audit: passed with no findings; model-path traversal rejected, DuckDB external access blocked, unsafe Copilot requests refused. Session access remains demo-only, without production authentication or multi-user authorization.

Evidence: `metadata/workspace_usability_qa.json`, `metadata/delivery_usability_qa.json`, `metadata/public_usability_qa.json`, `metadata/integration_qa.json`, `metadata/security_audit.json`. Screenshots are in `tmp/screenshots/workspace-experience/` and `tmp/screenshots/public-experience/`. The earlier 113-test public follow-up below is historical; the current full regression result is 115.

Public usability follow-up: all **19 landing and 12 login issues** have numbered root-cause and implementation notes in [docs/PUBLIC_USABILITY_FIXES.md](docs/PUBLIC_USABILITY_FIXES.md). The executed public browser audit passed all 10 route/width combinations (1512, 1366, 820, 390 and 320px), real login/navigation flows and workspace sidebar regression checks. The repeated login audit uses the native right-side submit arrow and verifies explicit field resets after sign-in/demo/logout. The original public browser workflow also passed. The latest full platform regression suite remained **113 passed**, with its two expected malformed-date source warnings (41.29s). See [metadata/public_usability_qa.json](metadata/public_usability_qa.json) for current computed measurements; this follow-up does not change the earlier data/model release evidence below.

| Area | Result | Evidence |
| --- | --- | --- |
| Application / runtime | PASS | 27 routes; recoverable missing-source handling; local health endpoint |
| Formal acceptance | 65/65 PASS; 0 FAIL; 0 BLOCKED | release_acceptance.json; history retained |
| Regression | 113 PASS; 2 warnings; 37.11s | Full pytest log; expected malformed-date parsing warnings |
| Browser teacher workflow | 32/32; PASSED | Actual isolated Chrome clicks and downloaded files |
| Delivery / demand data | PASS | 26 artifact hashes; exact source reconciliation |
| Model loading / prediction | PASS | Original fitted preprocessors + native XGBoost; both UI prediction controls |
| Security | PASSED in local-showcase scope | 79 runtime Python files; 162 tracked files; 0 known installed-dependency findings |
| UI / Copilot / reports / downloads | PASS | Source evidence, filter propagation, safe refusals, real CSV/XLSX/PDF files |
| Performance | PASS for local showcase | Measured timings below; no concurrency/SLA claim |
| Profitability ML / Cross-Risk ML | UNAVAILABLE | No verified independent model or compatible shared join key |
| Documentation | README, SECURITY, QA_REPORT and metadata updated | Reproducible commands and limitations |

## Dataset and source validation

The importer and audit preserve originals and register all 26 allowlisted d1/d2/d3 files. The dataset audit profiles every CSV's schema, row count, nulls, duplicates, finite numerics, date ranges and key integrity; models/notebooks/text references are hash-checked. No incomplete download is activated.

| Active artifact | Verified grain / coverage | UI behavior |
| --- | --- | --- |
| d1 primary orders | 65,752 unique Order Id; 30 columns; no null cells, full-row duplicates or nonfinite numeric cells; 2015-01-01 to 2018-01-31 | Source sales, profit and actual late labels; real market/region/country/shipping/segment/type filters |
| d1 final tuned scores | 2,123 unique matching IDs; one-to-one left join; shared fields checked | 63,629 orders stay unscored, not assigned observed outcomes as predictions |
| d2 advanced forecasts | 2,280 Product + DateOnly rows; 76 products; January 1–30, 2018 | DateOnly is base date; target is the following day's web visits, not sales/inventory units |
| d3 delivery reference | 24,369 line-item rows; 13,670 unique orders; duplicate IDs are valid at this separate grain | Kept separate; 0.56 threshold; no unsafe one-to-one merge |

Independent acceptance fixtures read the original CSVs and compare UI KPI sums, mean risk, scored coverage, risk distributions, chart arrays and filtered row IDs. Order case-file ID/date/market/region/country/shipping/sales are checked against the primary source. Browser CSV and Excel downloads contain the same source-filtered IDs; the downloaded PDF is parsed for provenance and filter context, then rendered for visual review.

Earlier Random Forest predictions align by ID but differ from final tuned probabilities in 2,122 rows at 1e-7 comparison tolerance and in 1,103 predicted labels. They are reference outputs, never silently substituted for final scores. d3 test accuracy 69.49% and validation threshold-analysis accuracy 68.74% describe different splits, not a fabricated correction. The malformed classification-shaped XGBoost row in the demand model-comparison export is excluded from regression comparison; the trained demand artifact and actual saved forecasts are validated independently.

## Trained-model validation

| Model | Actual validation | Contract |
| --- | --- | --- |
| d1 Tuned XGBoost | 2,123 supplied scored orders; max probability difference 2.96714783e-08; all classes match | 26 named features; threshold 0.35; risk bands 0.40 / 0.70; tolerance 1e-6 |
| d2 XGBoost web-visit regressor | 1,216 complete-history rows; max forecast difference 1.5234375e-05 visits | 15 inputs reconstructed from current/past visits; first 14 days excluded; tolerance 1e-4 |

Original Colab pickles are preserved. Their fitted preprocessing and XGBoost weights were exported in isolated Linux without retraining because the original Windows pickle load failed. Runtime loading uses fixed, hash-checked portable artifacts with pinned scikit-learn 1.6.1, xgboost 3.4.1 and joblib 1.5.3. Scenario Lab's actual Run trained model control and Demand Intelligence's Run trained next-day forecast control passed the integration test. Scenario outputs are model sensitivity, not causal estimates. No new confidence intervals are invented.

The active 0.35 threshold was selected on the same scored January test rows; displayed accuracy is retrospective, not an independent post-selection estimate. The feature-importance file belongs to the earlier Random Forest baseline, not Tuned XGBoost and not per-order SHAP. Source bounds labeled 90% cover only 67.63% of supplied demand rows. These limitations remain visible.

## Issues found, fixes and retests

| Finding | Fix / treatment | Retest evidence |
| --- | --- | --- |
| Six initial adversarial checks failed | Refuse unsafe Copilot requests before routing; guard spreadsheet prefixes after whitespace/control characters | 14 targeted security cases; final pytest; TC-55/57/58/64 |
| Invalid source dimensions, infinities or risk/model metadata could pass adapters | Require complete dimensions/dates, finite numerics, valid stock flags and exact d1 model/threshold/risk contract | Corrupt-source regression cases; dataset audit |
| Date reset changed backend totals while date segments showed old bounds | Retained reset counter, new date widget and container identity | Browser showed 2015–2018 with 65,752 orders; reset regression; market count changes |
| Settings/diagnostics/route descriptions still claimed demo-only data | Describe the actual selected provider and validated models | Route acceptance and Settings regression |
| Cross-year date chip omitted the start year; search displayed a stale selection hint | Show both years across years; distinguish a previous selection from search result | Updated browser screenshots and order checks |
| Large spreadsheet regenerated on repeated renders/download clicks | Full-content/schema/cell-type/provenance keyed, bounded 32 MiB / 3-item cache; download without rerun; loading feedback | Workbook cell-type/provenance regression; repeated-export benchmark; browser downloads |
| pip 25.1.1 advisory findings | Update toolchain to pip 26.2.1; preserve inference package pins | Subsequent pip-audit: zero known findings; pip check passed |
| Initial QA runner selected empty January market/region options and wrong popover metadata | Choose source-populated filter cases, widen market range, inspect actual header elements | Complete final 65-case run; failed completed run retained in history |
| Browser helper tried to navigate with multiselect menu open | Close the visible menu with Escape before navigation | Exact 32-step workflow |
| Earlier run stopped before final case / fixture initially violated pandas dtype rules | Retain completed-run history; persist per-case progress; validate model before UI batches; correct corruption fixture dtype | Final full run and completed pytest evidence |

## Performance and visual QA

Measured browser initial workspace: **7.411s**. Page switching: median **0.715s**, maximum **14.599s**. Filter action: **1.304s**. Report generation: **0.545s**. Actual CSV/Excel/PDF transfers: **[0.569, 0.347, 0.241]s**.

Acceptance threshold for this machine's local showcase is completion within 60 seconds per measured workspace/page action without a crash, with loading feedback for spreadsheet generation. Large cold Excel generation can take several seconds; this is not a concurrency benchmark or a public latency SLA. CSV validation and order/score joins are cached by both source versions and return isolated frame copies. Spreadsheet caching hashes every row rather than sampling, with bounded process memory and cell-type/provenance invalidation.

Independent cold/warm benchmark (65,752 orders; 17,577 export rows): source reads 0.5236s / 0.013s; CSV generation 0.3228s; Excel 13.7846s / 0.1932s. Repeated workbook bytes and exported source row IDs were verified identical.

Desktop light/dark, order-case, demand, Copilot, trained prediction, public landing and mobile screenshots are in ignored `tmp/`. The browser uses an isolated Chrome profile and never reads personal sessions. The browser plugin could not initialize in this environment, so the documented fallback used the installed isolated Playwright/Chrome workflow. Screenshots and the rendered report first page were visually inspected. Native Streamlit controls retain some base-theme styling; no claim of universal device coverage is made.

## Security and remaining limitations

No unresolved critical failure for the tested local-showcase scope remains when the release result is ready. See SECURITY.md for detailed trust boundaries. Public production still lacks real authentication, per-user authorization, durable sessions/audit records, rate limits and an independent penetration review. Loopback operation does not justify public exposure.

Alerts, saved views and settings are session-scoped. The datasets are historical snapshots. Private data/notebooks/models need controlled distribution. Some source country labels contain encoding artifacts retained as supplied. Profitability prediction, cross-risk joins, inventory signals, verified SHAP and operational drift require new artifacts. Copilot is deterministic source-aware analytics, not a generative LLM. Optional `.crdownload` files, conversion environments, QA downloads and screenshot/debug logs are not shipped as application features; they remain outside runtime in ignored tmp/backups. Prior implementation documents are historical references.

## 65 executed cases

Every status below comes from the executed runner. PASS for an unavailable capability means its explicit unavailable boundary was tested, not that the missing capability exists. Expected/actual/fix/retest details and timestamps also remain in machine-readable acceptance JSON.

| ID | Description | Expected | Actual | Status | Fix | Retest |
| --- | --- | --- | --- | --- | --- | --- |
| TC-01 | Application starts successfully | Application starts successfully using verified artifacts or explicit unavailable state | Running Streamlit health endpoint returned HTTP 200 / ok. | PASS | No fix required for this case | PASS |
| TC-02 | Streamlit loads without Python traceback | Streamlit loads without Python traceback using verified artifacts or explicit unavailable state | Actual app script rendered without exception or error panels. | PASS | No fix required for this case | PASS |
| TC-03 | Landing page renders correctly | Landing page renders correctly using verified artifacts or explicit unavailable state | Expected behavior executed and assertions passed against the source data/rendered UI. | PASS | No fix required for this case | PASS |
| TC-04 | Session login and logout behave correctly | Session login and logout behave correctly using verified artifacts or explicit unavailable state | Session-only access and logout executed; this is not production authentication. | PASS | No fix required for this case | PASS |
| TC-05 | Navigation loads every registered page | Navigation loads every registered page using verified artifacts or explicit unavailable state | All 25 authenticated routes executed, including developer diagnostics in developer mode. | PASS | No fix required for this case | PASS |
| TC-06 | Sidebar renders correctly | Sidebar renders correctly using verified artifacts or explicit unavailable state | Expected behavior executed and assertions passed against the source data/rendered UI. | PASS | No fix required for this case | PASS |
| TC-07 | Header renders correctly | Header renders correctly using verified artifacts or explicit unavailable state | Expected behavior executed and assertions passed against the source data/rendered UI. | PASS | No fix required for this case | PASS |
| TC-08 | Theme styles load | Theme styles load using verified artifacts or explicit unavailable state | Expected behavior executed and assertions passed against the source data/rendered UI. | PASS | No fix required for this case | PASS |
| TC-09 | Dark mode works | Dark mode works using verified artifacts or explicit unavailable state | Expected behavior executed and assertions passed against the source data/rendered UI. | PASS | No fix required for this case | PASS |
| TC-10 | Light mode works | Light mode works using verified artifacts or explicit unavailable state | Expected behavior executed and assertions passed against the source data/rendered UI. | PASS | No fix required for this case | PASS |
| TC-11 | Demo Mode loads correctly | Demo Mode loads correctly using verified artifacts or explicit unavailable state | Expected behavior executed and assertions passed against the source data/rendered UI. | PASS | No fix required for this case | PASS |
| TC-12 | Real repository snapshot mode loads correctly | Real repository snapshot mode loads correctly using verified artifacts or explicit unavailable state | Expected behavior executed and assertions passed against the source data/rendered UI. | PASS | No fix required for this case | PASS |
| TC-13 | Verified workspace does not display fabricated demo KPIs | Verified workspace does not display fabricated demo KPIs using verified artifacts or explicit unavailable state | All normal authenticated routes checked for synthetic HTML KPIs/chart annotations; public marketing preview is explicitly demo. | PASS | No fix required for this case | PASS |
| TC-14 | Primary Delivery dataset loads | Primary Delivery dataset loads using verified artifacts or explicit unavailable state | Expected behavior executed and assertions passed against the source data/rendered UI. | PASS | No fix required for this case | PASS |
| TC-15 | Delivery row count is verified | Delivery row count is verified using verified artifacts or explicit unavailable state | 65,752 primary orders; 2,123 scored rows; 2,123 unique matching scored IDs. | PASS | No fix required for this case | PASS |
| TC-16 | Delivery schema validates | Delivery schema validates using verified artifacts or explicit unavailable state | Expected behavior executed and assertions passed against the source data/rendered UI. | PASS | No fix required for this case | PASS |
| TC-17 | Delivery date fields parse | Delivery date fields parse using verified artifacts or explicit unavailable state | All dates parsed; range 2015-01-01 00:00:00 to 2018-01-31 23:38:00. | PASS | No fix required for this case | PASS |
| TC-18 | Delivery identifiers are unique and aligned | Delivery identifiers are unique and aligned using verified artifacts or explicit unavailable state | Expected behavior executed and assertions passed against the source data/rendered UI. | PASS | No fix required for this case | PASS |
| TC-19 | Delivery null and quality checks work | Delivery null and quality checks work using verified artifacts or explicit unavailable state | Expected behavior executed and assertions passed against the source data/rendered UI. | PASS | No fix required for this case | PASS |
| TC-20 | Delivery dashboard shows source KPI values | Delivery dashboard shows source KPI values using verified artifacts or explicit unavailable state | Expected behavior executed and assertions passed against the source data/rendered UI. | PASS | No fix required for this case | PASS |
| TC-21 | Delivery trend chart shows source data | Delivery trend chart shows source data using verified artifacts or explicit unavailable state | Expected behavior executed and assertions passed against the source data/rendered UI. | PASS | No fix required for this case | PASS |
| TC-22 | Delivery risk distribution shows source data | Delivery risk distribution shows source data using verified artifacts or explicit unavailable state | Expected behavior executed and assertions passed against the source data/rendered UI. | PASS | No fix required for this case | PASS |
| TC-23 | Market analysis shows source data | Market analysis shows source data using verified artifacts or explicit unavailable state | Expected behavior executed and assertions passed against the source data/rendered UI. | PASS | No fix required for this case | PASS |
| TC-24 | Regional analysis shows source data | Regional analysis shows source data using verified artifacts or explicit unavailable state | Expected behavior executed and assertions passed against the source data/rendered UI. | PASS | No fix required for this case | PASS |
| TC-25 | Country analysis shows source data | Country analysis shows source data using verified artifacts or explicit unavailable state | Expected behavior executed and assertions passed against the source data/rendered UI. | PASS | No fix required for this case | PASS |
| TC-26 | Shipping-mode analysis shows source data | Shipping-mode analysis shows source data using verified artifacts or explicit unavailable state | Expected behavior executed and assertions passed against the source data/rendered UI. | PASS | No fix required for this case | PASS |
| TC-27 | Global date filter works | Global date filter works using verified artifacts or explicit unavailable state | Expected behavior executed and assertions passed against the source data/rendered UI. | PASS | No fix required for this case | PASS |
| TC-28 | Market filter works | Market filter works using verified artifacts or explicit unavailable state | Expected behavior executed and assertions passed against the source data/rendered UI. | PASS | No fix required for this case | PASS |
| TC-29 | Region filter works | Region filter works using verified artifacts or explicit unavailable state | Expected behavior executed and assertions passed against the source data/rendered UI. | PASS | No fix required for this case | PASS |
| TC-30 | Country filter works | Country filter works using verified artifacts or explicit unavailable state | Expected behavior executed and assertions passed against the source data/rendered UI. | PASS | No fix required for this case | PASS |
| TC-31 | Shipping-mode filter works | Shipping-mode filter works using verified artifacts or explicit unavailable state | Expected behavior executed and assertions passed against the source data/rendered UI. | PASS | No fix required for this case | PASS |
| TC-32 | Customer-segment filter works | Customer-segment filter works using verified artifacts or explicit unavailable state | Expected behavior executed and assertions passed against the source data/rendered UI. | PASS | No fix required for this case | PASS |
| TC-33 | Order-type filter works | Order-type filter works using verified artifacts or explicit unavailable state | Expected behavior executed and assertions passed against the source data/rendered UI. | PASS | Added actual Type to available filters and order profile | PASS |
| TC-34 | Risk-level filter works | Risk-level filter works using verified artifacts or explicit unavailable state | Expected behavior executed and assertions passed against the source data/rendered UI. | PASS | No fix required for this case | PASS |
| TC-35 | Filters update KPIs | Filters update KPIs using verified artifacts or explicit unavailable state | Expected behavior executed and assertions passed against the source data/rendered UI. | PASS | No fix required for this case | PASS |
| TC-36 | Filters update charts | Filters update charts using verified artifacts or explicit unavailable state | Expected behavior executed and assertions passed against the source data/rendered UI. | PASS | No fix required for this case | PASS |
| TC-37 | Filters update tables | Filters update tables using verified artifacts or explicit unavailable state | Expected behavior executed and assertions passed against the source data/rendered UI. | PASS | No fix required for this case | PASS |
| TC-38 | Order Explorer loads | Order Explorer loads using verified artifacts or explicit unavailable state | Expected behavior executed and assertions passed against the source data/rendered UI. | PASS | No fix required for this case | PASS |
| TC-39 | Order ID search works | Order ID search works using verified artifacts or explicit unavailable state | Expected behavior executed and assertions passed against the source data/rendered UI. | PASS | No fix required for this case | PASS |
| TC-40 | Order detail matches source values | Order detail matches source values using verified artifacts or explicit unavailable state | Order 75287: ID/date/market/region/country/shipping/sales exactly match source. | PASS | No fix required for this case | PASS |
| TC-41 | Actual outcome is distinguished from prediction | Actual outcome is distinguished from prediction using verified artifacts or explicit unavailable state | Expected behavior executed and assertions passed against the source data/rendered UI. | PASS | No fix required for this case | PASS |
| TC-42 | Verified prediction and probability display correctly | Verified prediction and probability display correctly using verified artifacts or explicit unavailable state | Expected behavior executed and assertions passed against the source data/rendered UI. | PASS | No fix required for this case | PASS |
| TC-43 | High-risk order filtering works | High-risk order filtering works using verified artifacts or explicit unavailable state | Expected behavior executed and assertions passed against the source data/rendered UI. | PASS | No fix required for this case | PASS |
| TC-44 | Universal Explorer uses valid source columns | Universal Explorer uses valid source columns using verified artifacts or explicit unavailable state | Expected behavior executed and assertions passed against the source data/rendered UI. | PASS | No fix required for this case | PASS |
| TC-45 | Geographic Intelligence works | Geographic Intelligence works using verified artifacts or explicit unavailable state | Expected behavior executed and assertions passed against the source data/rendered UI. | PASS | No fix required for this case | PASS |
| TC-46 | What Changed compares sufficient historical data | What Changed compares sufficient historical data using verified artifacts or explicit unavailable state | Expected behavior executed and assertions passed against the source data/rendered UI. | PASS | No fix required for this case | PASS |
| TC-47 | Insight Center shows evidence-based observations | Insight Center shows evidence-based observations using verified artifacts or explicit unavailable state | Expected behavior executed and assertions passed against the source data/rendered UI. | PASS | No fix required for this case | PASS |
| TC-48 | Alert Center shows valid alerts | Alert Center shows valid alerts using verified artifacts or explicit unavailable state | Expected behavior executed and assertions passed against the source data/rendered UI. | PASS | No fix required for this case | PASS |
| TC-49 | Model Intelligence shows verified model information | Model Intelligence shows verified model information using verified artifacts or explicit unavailable state | Expected behavior executed and assertions passed against the source data/rendered UI. | PASS | No fix required for this case | PASS |
| TC-50 | Feature importance shows the actual baseline artifact | Feature importance shows the actual baseline artifact using verified artifacts or explicit unavailable state | Expected behavior executed and assertions passed against the source data/rendered UI. | PASS | No fix required for this case | PASS |
| TC-51 | Explainability does not fabricate local explanations | Explainability does not fabricate local explanations using verified artifacts or explicit unavailable state | Expected behavior executed and assertions passed against the source data/rendered UI. | PASS | No fix required for this case | PASS |
| TC-52 | Data Quality works | Data Quality works using verified artifacts or explicit unavailable state | Expected behavior executed and assertions passed against the source data/rendered UI. | PASS | No fix required for this case | PASS |
| TC-53 | Data Lineage works | Data Lineage works using verified artifacts or explicit unavailable state | Expected behavior executed and assertions passed against the source data/rendered UI. | PASS | No fix required for this case | PASS |
| TC-54 | Copilot answers real-data questions | Copilot answers real-data questions using verified artifacts or explicit unavailable state | Expected behavior executed and assertions passed against the source data/rendered UI. | PASS | No fix required for this case | PASS |
| TC-55 | Copilot numbers have source evidence | Copilot numbers have source evidence using verified artifacts or explicit unavailable state | Expected behavior executed and assertions passed against the source data/rendered UI. | PASS | Unsafe prompts now refused before analytics intent routing | PASS |
| TC-56 | Reports generate successfully | Reports generate successfully using verified artifacts or explicit unavailable state | Expected behavior executed and assertions passed against the source data/rendered UI. | PASS | No fix required for this case | PASS |
| TC-57 | CSV download exports source values | CSV download exports source values using verified artifacts or explicit unavailable state | Expected behavior executed and assertions passed against the source data/rendered UI. | PASS | Formula injection protection includes leading whitespace/control characters | PASS |
| TC-58 | Excel download exports source values | Excel download exports source values using verified artifacts or explicit unavailable state | Expected behavior executed and assertions passed against the source data/rendered UI. | PASS | Same neutralization for Excel exports | PASS |
| TC-59 | PDF generation and download are valid | PDF generation and download are valid using verified artifacts or explicit unavailable state | Expected behavior executed and assertions passed against the source data/rendered UI. | PASS | No fix required for this case | PASS |
| TC-60 | Demand page shows connected forecast values | Demand page shows connected forecast values using verified artifacts or explicit unavailable state | Expected behavior executed and assertions passed against the source data/rendered UI. | PASS | No fix required for this case | PASS |
| TC-61 | Demand filters and charts work | Demand filters and charts work using verified artifacts or explicit unavailable state | Expected behavior executed and assertions passed against the source data/rendered UI. | PASS | No fix required for this case | PASS |
| TC-62 | Empty and nonexistent-order states work | Empty and nonexistent-order states work using verified artifacts or explicit unavailable state | Expected behavior executed and assertions passed against the source data/rendered UI. | PASS | Preserved source-aware empty/unscored states | PASS |
| TC-63 | Missing model and CSV errors fail closed | Missing model and CSV errors fail closed using verified artifacts or explicit unavailable state | Missing model reports disable inference; missing CSV produces recoverable generic error, without traceback/path exposure. | PASS | Sanitized missing demand-artifact errors; diagnostics requires developer preference | PASS |
| TC-64 | Implemented security checks identify no unresolved critical local-showcase issue | Implemented security checks identify no unresolved critical local-showcase issue using verified artifacts or explicit unavailable state | Advisory, source-code, secret-pattern, controlled-tool, file-boundary and export checks passed for local showcase scope; not a penetration-test guarantee. | PASS | Updated vulnerable pip; hardened prompts/exports; validated finite inputs | PASS |
| TC-65 | Complete source-service-model-filter-UI-report-export workflow passes | Complete source-service-model-filter-UI-report-export workflow passes using verified artifacts or explicit unavailable state | Order 75082 model parity, filtered UI/source totals, CSV, Excel, PDF and actual 32-step browser showcase passed. | PASS | No fix required for this case | PASS |

## Actual teacher workflow

| Step | Action | Actual result | Status |
| --- | --- | --- | --- |
| 1 | Start application | Health returned HTTP 200 / ok | PASS |
| 2 | Open dashboard | Executive Command Center rendered | PASS |
| 3 | Confirm real-data indicator | Verified repository snapshot explicitly distinguished from refreshed/live feed | PASS |
| 4 | Show real delivery KPI | 65752 orders matches source in widened date range 2015-01-01 to 2018-01-31 | PASS |
| 5 | Apply market filter | Pacific Asia | PASS |
| 6 | Verify KPI changes | 65752 to 17577 matches source predicate | PASS |
| 7 | Open Delivery Intelligence | Real-data delivery page loaded | PASS |
| 8 | Open risk analysis | Plotly risk chart rendered from supplied scores | PASS |
| 9 | Open Order Explorer | Order search and case file rendered | PASS |
| 10 | Search real Order ID | 75082 | PASS |
| 11 | Verify order against source | ID/date/market/region/country/shipping/sales exactly matched CSV | PASS |
| 12 | Show verified prediction and risk | Saved probability 0.75967735; threshold 0.35 | PASS |
| 13 | Open Model Intelligence | Governance page loaded | PASS |
| 14 | Show verified model | Tuned XGBoost with validated model status and 0.35 threshold | PASS |
| 15 | Show model metrics | Source comparison at 0.50 distinguished from test-selected 0.35 scores | PASS |
| 16 | Show feature importance | Actual earlier Random Forest artifact labeled separately | PASS |
| 17 | Open Data Quality | Real source page rendered without error | PASS |
| 18 | Open Data Lineage | Real source page rendered without error | PASS |
| 19 | Open Insight Center | Real source page rendered without error | PASS |
| 20 | Open Alert Center | Real source page rendered without error | PASS |
| 21 | Ask Copilot real-data question | Market-risk response displayed with current source/filter evidence | PASS |
| 22 | Generate report | Executive report generated for verified filtered delivery scope | PASS |
| 23 | Download CSV | Actual browser download row IDs and market match source filter | PASS |
| 24 | Download Excel | Actual browser workbook rows match source filter | PASS |
| 25 | Verify PDF report | Actual downloaded PDF parsed and provenance/filter text verified; first page rendered | PASS |
| 26 | Open Demand Intelligence | Separate product/base-day dataset loaded | PASS |
| 27 | Show connected demand forecasts | UI forecast sum matches source; web visits and next-day target labeled | PASS |
| 28 | Test demand filters | Single-product KPI matches saved source forecasts | PASS |
| 29 | Test empty state | Nonexistent product produces clear empty result without traceback | PASS |
| 30 | Switch theme | Dark theme selected and applied | PASS |
| 31 | Return to Executive Dashboard | Dashboard context retained | PASS |
| 32 | Confirm no runtime errors | 32-step browser workflow completed without exception panels | PASS |

Start the preview, choose Open platform, then use Settings → Data → All available history and Reset before comparing markets. A January-only window contains one market. Browser evidence includes additional setup actions needed for meaningful source comparisons.

## Final checklist

### Application

- [x] Starts
- [x] No critical traceback
- [x] Navigation works
- [x] UI polished
- [x] Dark mode
- [x] Light mode
- [x] Demo mode
- [x] Live mode (verified historical snapshot)

### Data

- [x] Delivery data connected
- [x] Demand data connected
- [x] Schemas validated
- [x] Counts verified
- [x] Data displayed in UI
- [x] Filters verified

### Model

- [x] Active project model identified (not a deployed production claim)
- [x] Dependencies compatible
- [x] Model loading tested
- [x] Prediction tested
- [x] Probability tested where supported
- [x] Threshold verified
- [x] Prediction consistency verified

### Analytics

- [x] Executive dashboard
- [x] Delivery intelligence
- [x] Demand intelligence
- [x] Order Explorer
- [x] Universal Explorer
- [x] Geographic Intelligence
- [x] What Changed
- [x] Insights
- [x] Alerts
- [x] Model Intelligence
- [x] Explainability (baseline importance; local SHAP explicitly unavailable)
- [x] Data Quality
- [x] Data Lineage

### Copilot

- [x] Real data
- [x] Controlled tools
- [x] No arbitrary code
- [x] Numerical evidence
- [x] Safe refusals

### Reporting

- [x] PDF
- [x] CSV
- [x] Excel
- [x] Filter-aware exports

### Security

- [x] Secrets checked
- [x] Pickle handling checked
- [x] File paths checked
- [x] Downloads checked
- [x] Copilot checked
- [x] Error exposure checked
- [x] Temporary files checked

### Testing

- [x] 65 test cases executed
- [x] Failed cases fixed where possible
- [x] Failed cases retested
- [x] pytest passed
- [x] integration tests passed
- [x] runtime tests passed
- [x] browser/showcase workflow passed

### Release

- [x] README updated
- [x] QA_REPORT updated
- [x] SECURITY.md updated
- [x] Metadata updated
- [x] No obsolete debug artifacts in application runtime
- [x] Final Git diff/status reviewed (local snapshot; no remote publication)
- [x] Final project ready for local demonstration

## Reproduce

Run the commands in README.md. Browser workflow precedes the formal suite because TC-65 consumes its completed actual evidence. Keep supplied local assets and pinned inference dependencies. After changing runtime files or artifacts, rerun relevant tests and regenerate this report.

## Comparison Studio validation — 6 October 2026

The new comparison workspace is integrated into the existing app and both providers. The full regression suite passed **144 tests** (two expected warnings from intentionally malformed-date fixtures). All **28 routes** passed registered-artifact integration checks. Comparison controls produced trained predictions for **1,918 selected delivery orders** and **76 demand products**. The original synthetic demo remains usable and blocks trained inference on demo records.

Rendered browser QA covers all five chart types, real prediction actions, CSV/JSON downloads, missing-key recovery, light/dark themes and desktop/390px/320px layouts. Separate chart checks verify zoom in/out, pan/zoom, autoscale/reset, fullscreen exit and valid PNG export. Evidence is saved in `metadata/comparison_functional_qa.json`, `metadata/comparison_browser_qa.json` and `metadata/comparison_chart_qa.json`. Screenshots are local under ignored `tmp/screenshots/comparison/`.

Optional OpenAI narration uses only aggregate evidence and anonymous segment labels. Structured response success, missing key, invalid evidence references, HTTP failures, malformed/refused responses and timeouts are tested with mocked API responses. No live OpenAI call was verified because no local API key was configured. Follow [the Comparison Studio setup](docs/COMPARISON_STUDIO.md) to enable it. Existing deployment and model limitations above continue to apply.

## Profitability, optional live AI and final delivery release - 6 October 2026

- Full regression: **166 passed**, zero failures. Warnings concern joblib/NumPy compatibility and intentionally malformed date inputs.
- Profitability: all 15 files hash-verified, 27,078 lines / 14,593 orders, summaries/calibration/shortlist/drift reconciled; 238 feature importances match the model.
- Final delivery: the eight new files match registered d3 hashes exactly; 24,369 observations / 13,670 orders, 1,757 repeated exported observations retained, summary metrics and 4,349 importances reconciled.
- Portable conversion: original fitted models preserved without training; each reproduced on 32 synthetic probes within 2.68e-8 probability. Source-score parity is unavailable because CSVs omit trained inputs.
- Functional QA passed profitability dataset switches, downloads, governance, Copilot, Profitability/Cross-Risk PDF generation, mocked live-AI results and invalidation; final delivery passed comparison/data/quality/explorer/delivery/model routes.
- Browser QA passed actual incomplete/complete upload paths and downloads, light/dark desktop/390px/320px profitability layouts, visible chart controls, final model prediction and comparison selection. No JavaScript page errors.
- Profitability, Cross-Risk and final delivery PDFs were rendered and reviewed. A trailing spacer caused a footer-only page and was removed; regression coverage now rejects blank report pages.
- External live AI remains unverified: OPENAI_API_KEY is not configured. Aggregate evidence is available locally.
- Originals and demo mode are preserved. Integrity-checked asset backup: `metadata/release_backup_manifest.json`. Current evidence: `metadata/profitability_*`, `metadata/final_delivery_*` and `metadata/security_audit.json`.

The release security audit passed with zero findings across 96 runtime Python files and 234 tracked files. It checked ignored secrets, fixed model paths, loopback binding, DuckDB external access and unsafe local Copilot requests. This is a scoped local review, not a public-production penetration test.

Final preview smoke passed: original-field duplicate counting, actual final delivery PDF download, and 390px/320px final delivery layouts without page overflow. Current integration QA passed all 28 routes and 41 original source hashes.
