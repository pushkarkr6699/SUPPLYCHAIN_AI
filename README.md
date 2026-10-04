# SUPPLYCHAIN AI

Decision Intelligence Platform — a complete **UI-first Streamlit application**.

All analytical records and illustrative results are **DEMO UI DATA**. No project CSVs, PKLs, ML models, credentials or external AI providers are opened or connected. No training occurs. Profitability and combined Delivery × Profitability analysis are disabled.

## Run locally (PowerShell)

```powershell
cd D:\SUPPLYCHAIN_AI
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Open **http://127.0.0.1:8501** and choose **Explore Demo**. Once dependencies are installed, `./run.ps1` is a shortcut. The server binds to loopback only.

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

## Navigation: 27 rendered routes

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

Developer navigation is enabled in Settings → Privacy / Security. It is a UI preference, not a security boundary. The native sidebar is collapsible. Presentation mode hides it and can be exited from the header. Query parameters reflect navigation; a new session must enter demo access.

## Reusable components

`app_shell`, `header`, `sidebar`, `navigation`, `breadcrumbs`, `filters`, `filter_chips`, `kpi_cards`, `charts`, `tables`, `section_header`, `insights`, `alerts`, `evidence`, `status`, `model_cards`, `empty_states`, `loading_states`, `error_states`, `search_bar`, `presentation`, `copilot_ui`, `auth_components`, `landing_components`.

## Interaction behavior

- Global date and nine dimensional filters update records, KPIs, charts and exports. Chips remove individual filters. Reset and saved session views are supported.
- The synthetic dataset covers **10 August–4 October 2026**, with a default last-28-day view. Dates describe the fixture, not a live feed.
- Search, order case files, geography and product profiles provide drill-downs. Tables have search, pagination and labeled downloads.
- The Copilot retains evidence from the question-time filter context; suggested prompts use deterministic responses. Its dashboard/filter/record/export actions are wired.
- Analysis threshold changes recompute synthetic confusion metrics and never change the supplied **0.56** production threshold.
- Scenarios use isolated illustrative rules. Neither model inference nor causal simulation is performed.
- Alerts have session-only New / Acknowledged / Resolved / Reopen actions. They are workflow UI states, not a live alert service or persisted audit history.
- Reports have section selection, previews, generation and downloads. Changed report context invalidates the previous generated download.
- CSV and Excel exports include a demo provenance column. PDFs include demo provenance on every page. Chart PNG export uses the Plotly toolbar camera icon.
- Light, Dark, System, density and presentation preferences are session-scoped. Native Streamlit canvas widgets retain some base-theme styling.

## Validate

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Optional visual checks, with Chrome installed and the app running:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe scripts\visual_qa.py
.\.venv\Scripts\python.exe scripts\verify_pdf.py
```

Visual outputs go to ignored `tmp/` directories. The browser script uses a fresh headless profile, without reading an existing user's profile or sessions.

## Data integration

The current UI and demo provider remain selectable. Choose `SUPPLYCHAIN_PROVIDER=demo` for the demo or `SUPPLYCHAIN_PROVIDER=verified` to read the pre-scored CSVs. The local ignored `.env` selects verified data for this workspace; `.env.example` defaults to demo. Restart Streamlit after changing provider settings.

Place delivery artifacts in `data/delivery/final/` and product/day demand artifacts in `data/demand/final/`. `data/README.md` lists accepted inputs and the dataset context to include. The adapters validate schemas, values, threshold agreement, row grain, error calculations and interval ordering. Delivery and demand are never joined. The copied source CSVs are ignored by Git and remain local.

This workspace currently uses scored delivery rows and precomputed demand forecasts. It does **not** deserialize pickle model files or run live inference. Before enabling inference, provide the fitted model, exact feature list/order and dtypes, preprocessing pipeline, dependency versions, training/validation split details, threshold definition, and a known-input/expected-output sample. Profitability remains unavailable until its own verified data and model are supplied.

Final-summary accuracy (69.49%) differs from agreement recomputed on the supplied scored rows (68.74%). The UI surfaces the discrepancy with an evaluation-provenance caveat; these figures are not reconciled or presented as independent validation.

Implementation references: [Streamlit chart API](https://docs.streamlit.io/develop/api-reference/charts/st.plotly_chart), [Streamlit testing API](https://docs.streamlit.io/develop/api-reference/app-testing).

