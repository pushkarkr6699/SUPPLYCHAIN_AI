# SUPPLYCHAIN AI

Decision Intelligence Platform — a **local classroom showcase** with connected historical datasets and validated trained inference.

The existing demo UI is preserved. Verified mode connects historical order-level delivery, next-day web-visit forecasts, profitability line items and the independent final delivery line-item experiment. Original trained models run through fixed, hash-validated portable exports; no retraining occurs. See [the latest integration handoff](docs/FINAL_HANDOFF.md).

Latest integration (2026-10-06): **166 regression tests passed**. Profitability diagnostics, threshold analysis, complete-input trained predictions, cross-risk coverage and PDF reports are connected. The final delivery line-item experiment is available under **Delivery Intelligence ? Explore final delivery line-item experiment**, and in Comparison Studio and data tools. Optional live AI uses `OPENAI_API_KEY` in the ignored local `.env`; local evidence remains available without a key. See [profitability and final delivery details](docs/PROFITABILITY_INTEGRATION.md).

## Run locally (PowerShell)

Final product polish (2026-10-05): all eight core upgrades and eight additional refinements are implemented. See [the complete implementation notes](docs/FINAL_POLISH.md). The latest full regression passed **120 tests**. The guided demo exercises Overview → Delivery → Order → Prediction → Report, with explicit trained-model execution and PDF download. Grouped navigation, compact filters, coverage summaries, pinned identifiers, order actions and report provenance are included. Demo units remain distinct from verified web-visit forecasts.

Choose **Guided demo → Start guided demo** after opening the platform. Updated report preview: `output/pdf/supplychain-delivery-polished-preview.pdf`. Browser, integration, security and measured performance evidence are saved under `metadata/`.

Latest UI audit (2026-10-05): the previous 18 workspace issues and all 16 Delivery issues are implemented. Numbered root causes and fixes: [workspace](docs/WORKSPACE_USABILITY_FIXES.md) and [Delivery](docs/DELIVERY_USABILITY_FIXES.md). Verification passed: 115 pytest tests, 27 integration routes, 26 source-artifact hashes, trained prediction controls, PDF exports, local security checks and 34 browser layout/theme measurements (14 workspace, 10 Delivery, 10 public pages). Demo mode and existing datasets/models are preserved.

Preview at **http://127.0.0.1:8501**. Choose **Open platform**, then **Delivery Intelligence**. Browser checks can be repeated with `.venv\Scripts\python.exe scripts/workspace_usability_qa.py`, `scripts/delivery_usability_qa.py` and `scripts/public_usability_qa.py` while the local server is running; their JSON reports are under `metadata/`.

```powershell
cd D:\SUPPLYCHAIN_AI
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip install -r requirements-inference.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Open **http://127.0.0.1:8501** and choose **Open platform**. Once dependencies are installed, `./run.ps1` is a shortcut. The server binds to loopback only.

Sign In is explicitly a temporary demo session, not authentication. Continue in Demo Mode requires no credentials. Do not enter a real password. The transient password field is cleared on submit; no password is validated or persisted. Logout clears workspace state. A real authentication service must replace this flow before deployment.

## Files and responsibilities

| Path | Responsibility |
| --- | --- |
| `app.py` | Small public/authenticated entrypoint |
| `config.py` | Demo flag, defaults, immutable supplied threshold metadata |
| `.streamlit/config.toml` | Base theme and local server configuration |
| `views/` | Page presentation modules, explicitly registered in `registry.py` |
| `components/` | Reusable shell, filters, navigation, evidence, charts and UI states |
| `styles/` | Theme, layout, components, landing, auth, dashboard and presentation CSS |
| `services/mock_data.py` | All synthetic fixtures, fixture metadata, sample responses and illustrative values |
| `services/contracts.py` | Analytics and authentication service protocols |
| `services/provider.py` | Provider factory, filter options, filtered records and provenance |
| `services/analytics.py` | Pure KPI, aggregation, forecast-error and threshold calculations |
| `services/auth_service.py` | Session-only demo access and logout |
| `services/comparison_service.py` | Period comparisons and mathematically defined changes |
| `services/scenario_service.py` | Explicitly illustrative scenario rules; never real inference |
| `services/copilot_service.py` | Offline deterministic analytical response service |
| `services/copilot/` | Allowlisted Copilot intent, context, read-only tools, validation, response and actions |
| `services/health_service.py` | Actual UI connectivity checks; no invented production health |
| `services/query_engine.py` | In-memory DuckDB boundary with external access disabled |
| `services/export_service.py` | Labeled, formula-safe CSV/Excel and ReportLab PDF downloads |
| `tests/` | Route, interaction, calculation and service-boundary tests |
| `scripts/` | Browser screenshots and PDF render verification |
| `docs/IMPLEMENTATION.md` | Detailed handoff, validation, limitations and integration sequence |

The implementation deliberately uses `views/` instead of Streamlit's auto-discovered `pages/` directory, so the custom grouped navigation has a single source of truth and public login cannot be bypassed by an auto-generated sidebar.

## Navigation: 28 rendered routes

| Group | Pages |
| --- | --- |
| Public | Landing, Login |
| Command Center | Executive Overview |
| Intelligence | Delivery Intelligence, Demand Intelligence, Profitability Intelligence, Cross-Risk Command Center |
| Analysis | Universal Explorer, Order Explorer, Geographic Intelligence, What Changed?, Scenario Lab |
| AI | SupplyChain Copilot, Insight Center, Alert Center |
| ML Governance | Model Intelligence, Explainability, Threshold Lab, Drift Monitor, Model Health |
| Data | Data Quality, Data Lineage, Data Explorer |
| Outputs | Reports, Downloads |
| System | Settings, Developer / Diagnostics |

Developer navigation is enabled in Settings. It is a UI preference, not a security boundary. The native sidebar is collapsible. Presentation mode hides it and can be exited from the header. Query parameters reflect navigation; a new session must enter demonstration access.

## Reusable components

`app_shell`, `header`, `sidebar`, `navigation`, `breadcrumbs`, `filters`, `filter_chips`, `kpi_cards`, `charts`, `tables`, `section_header`, `insights`, `alerts`, `evidence`, `status`, `model_cards`, `empty_states`, `loading_states`, `error_states`, `search_bar`, `presentation`, `copilot_ui`, `auth_components`, `landing_components`.

## Interaction behavior

- Global date and nine dimensional filters update records, KPIs, charts and exports. Chips remove individual filters. Reset and saved session views are supported.
- The synthetic dataset covers **10 August–4 October 2026**, with a default last-28-day view. Dates describe the fixture, not a live feed.
- Search, order case files, geography and product profiles provide drill-downs. Tables have search, pagination and labeled downloads.
- The Copilot retains evidence from the question-time filter context; suggested prompts use deterministic responses. Its dashboard/filter/record/export actions are wired.
- Demo threshold analysis uses synthetic labels. Verified order-level inference keeps the supplied **0.35** threshold; the separate d3 reference uses **0.56**. Analysis never rewrites a trained model or saved score.
- Demo scenarios use illustrative rules. Verified Scenario Lab runs trained delivery inference; Demand Intelligence runs next-day web-visit inference. Neither is a causal simulation.
- Alerts have session-only New / Acknowledged / Resolved / Reopen actions. They are workflow UI states, not a live alert service or persisted audit history.
- Reports have section selection, previews, generation and downloads. Changed report context invalidates the previous generated download.
- CSV, Excel and PDF exports include provenance for the selected provider and dataset. Spreadsheet exports neutralize formula-like text. Chart PNG export uses the Plotly toolbar camera icon.
- Light, Dark, System, density and presentation preferences are session-scoped. Native Streamlit canvas widgets retain some base-theme styling.

## Validate

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Optional visual checks, with Chrome installed and the app running:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe scripts\verified_browser_qa.py
.\.venv\Scripts\python.exe scripts\showcase_qa.py
```

Visual outputs go to ignored `tmp/` directories. The browser script uses a fresh headless profile, without reading an existing user's profile or sessions.

## Data integration

The current UI and demo provider remain selectable. Choose `SUPPLYCHAIN_PROVIDER=demo` for the demo or `SUPPLYCHAIN_PROVIDER=verified` to read the pre-scored CSVs. The local ignored `.env` selects verified data for this workspace; `.env.example` defaults to demo. Restart Streamlit after changing provider settings.

Place delivery artifacts in `data/delivery/final/` and product/day demand artifacts in `data/demand/final/`. `data/README.md` lists accepted inputs and the dataset context to include. The adapters validate schemas, values, threshold agreement, row grain, error calculations and interval ordering. Delivery and demand are never joined. The copied source CSVs are ignored by Git and remain local.

Active delivery data contains **65,752 unique orders**, with **2,123 supplied scored orders**. Unscored orders retain missing probabilities. The active Tuned XGBoost threshold is **0.35**, selected on the same January 2018 test predictions. The d3 line-item experiment uses 0.56 and remains a separate reference. Its 69.49% test accuracy agrees with its summary; the 68.74% threshold-analysis figure belongs to validation.

Active demand data contains **2,280 product/base-day rows across 76 products**. Forecasts represent next-day **web visits**, not purchased units. Source bounds labeled 90% cover approximately 67.63% of supplied rows. Inventory is not connected.

Original Colab pickles are preserved. Native XGBoost JSON and original fitted preprocessors were exported in isolated Linux without retraining, then validated on Windows. Delivery reproduced all supplied scored orders (maximum probability difference 2.97e-8); demand reproduced all 1,216 complete-history rows (maximum difference 1.53e-5 visits). Validation reports are under `metadata/`.

**Run trained predictions:** use Scenario Lab for a selected order or uploaded order-level feature rows. In Demand Intelligence, open Run trained next-day web-visit forecast to use supplied history or upload daily visits with `DateOnly, Product, Category, Department, Visits`, including zero-visit days and at least 15 consecutive days per product. New forecasts are point estimates.

Run `.\.venv\Scripts\python.exe scripts\verify_integration.py` to verify all 26 artifact hashes, all 28 routes and both prediction controls. See [docs/FINAL_HANDOFF.md](docs/FINAL_HANDOFF.md) for setup, validation and remaining production deployment requirements.

Implementation references: [Streamlit chart API](https://docs.streamlit.io/develop/api-reference/charts/st.plotly_chart), [Streamlit testing API](https://docs.streamlit.io/develop/api-reference/app-testing).

## Final release QA

The public landing and login pages also have a numbered [usability audit and implemented fixes](docs/PUBLIC_USABILITY_FIXES.md). With the local preview running, execute `.\.venv\Scripts\python.exe scripts/public_usability_qa.py` for the responsive public-page checks and real login/workspace flows. Its measurements are saved in `metadata/public_usability_qa.json`; complete page screenshots are saved under ignored `tmp/screenshots/public-experience/`.

See [QA_REPORT.md](QA_REPORT.md) for the executed 65-case acceptance matrix, source reconciliation, 32-step teacher workflow, measured timings, fixes and final checklist. [SECURITY.md](SECURITY.md) defines the local trust boundary and public-deployment requirements. The older implementation audit documents describe earlier phases.

With the app running in verified mode and optional QA dependencies installed:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt -r requirements-security.txt
.\.venv\Scripts\python.exe scripts/audit_datasets.py
.\.venv\Scripts\python.exe scripts/security_audit.py
.\.venv\Scripts\python.exe scripts/verify_integration.py
.\.venv\Scripts\python.exe scripts/showcase_qa.py
.\.venv\Scripts\python.exe scripts/release_acceptance.py
.\.venv\Scripts\python.exe scripts/build_qa_report.py
```

Run the browser workflow before the acceptance suite: TC-65 requires its actual completed 32-step evidence. Supplied CSV/model files are local ignored assets; cloning source alone does not include them. `scripts/import_artifacts.py` uses the documented local artifact allowlist and preserves source originals.

For a market-filter demonstration, choose **Settings → Data → All available history**, return to the dashboard and press **Reset**, then choose a Market. The default January 2018 window contains only Pacific Asia. Reset recreates the date control so its displayed bounds agree with the applied filter. Settings → Dashboard can disable compact numbers for exact totals.

This platform has session-only access, alerts and saved views. Historical snapshots are not refreshed operational feeds. Profitability ML, cross-risk joins, SHAP, drift and inventory remain unavailable without verified artifacts. The active delivery threshold was selected on the same scored test rows, so performance is not an independent post-selection estimate. Demand forecasts measure web visits; source 90% bounds are empirically under-covering. Preserve these limitations when presenting the project.


## Comparison Studio

Use **Sidebar → Comparison Studio** to compare your selected delivery or demand dataset fields with groupings, A/B cohorts, numeric ranges, five chart types, computed insights, trained predictions and complete evidence exports. Both verified data and the original demo provider are supported. See [the workflow and optional OpenAI setup](docs/COMPARISON_STUDIO.md). AI narration requires `OPENAI_API_KEY` configured locally; it sends aggregate evidence and anonymous segment labels only. Local insights and trained inference work independently of that key.
