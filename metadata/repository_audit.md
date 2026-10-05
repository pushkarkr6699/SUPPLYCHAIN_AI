# Repository audit

**Final local-showcase release:** [QA_REPORT.md](../QA_REPORT.md) and [SECURITY.md](../SECURITY.md) contain current executed data, model, runtime, security, browser and acceptance evidence. The historical audit below is retained for provenance.

**Historical UI-stage audit:** current dataset/model implementation is documented in [FINAL_HANDOFF.md](../docs/FINAL_HANDOFF.md), the v2 registries and runtime QA reports. Its trained inference and source counts supersede the UI-only status below.

**Audit date:** 2026-10-04  
**Scope:** `D:\SUPPLYCHAIN_AI`, excluding virtual-environment, cache, and temporary-output directories.

## Architecture

- `app.py` is a small Streamlit entry point. It initializes session state/styles and routes public landing/login pages separately from the authenticated workspace.
- `views/registry.py` is the single registry for 25 authenticated pages. `components/navigation.py` defines the grouped sidebar routes and navigation callback.
- `components/app_shell.py` owns shared session initialization, theme/style loading, sidebar, header, global filters, page dispatch, empty-state handling, evidence, and timing metadata.
- `components/` contains shared navigation, filters/chips, KPI, chart, table, evidence, status, loading/error/empty-state, presentation, insight, alert, and authentication components.
- `services/contracts.py` defines analytics and authentication protocols. `services/provider.py` returns the deterministic mock provider and fails closed if demo mode is disabled without a real provider.
- `services/mock_data.py` is the single source for synthetic records and UI fixtures. `services/analytics.py`, `comparison_service.py`, `scenario_service.py`, `copilot_service.py`, `services/copilot/`, and `export_service.py` operate on those records. The Copilot package separates intent, context, allowlisted tools, validation, response assembly, and navigation/filter actions.
- `services/query_engine.py` uses an in-memory DuckDB connection with external access disabled. It accepts caller-provided frames; it does not discover files.
- `styles/` separates theme, shared layout/components, dashboard, presentation, landing, and authentication styles.
- `tests/` uses pytest and Streamlit AppTest for service calculations, safety boundaries, route rendering, navigation, filters, and workflows. `scripts/` contains optional browser/PDF QA utilities.

## Routes and navigation

The single authenticated registry contains 25 routes: Executive Overview; Delivery Intelligence; Demand Intelligence; Profitability Intelligence; Cross-Risk Command Center; Universal Explorer; Order Explorer; Geographic Intelligence; What Changed?; Scenario Lab; SupplyChain Copilot; Insight Center; Alert Center; Model Intelligence; Explainability; Threshold Lab; Drift Monitor; Model Health; Data Quality; Data Lineage; Data Explorer; Reports; Downloads; Settings; and Developer / Diagnostics. Landing and Login are public routes outside the workspace registry.

Navigation is grouped in the collapsible native Streamlit sidebar. Route buttons update session state and the `page` query parameter. Preferences, filters, saved views, alert review, and Copilot conversation state are session-scoped. They are not shared across users or persisted to a backend.

## Data and model artifacts

- `DEMO_MODE` remains enabled. UI fixtures are deterministic and isolated in `services/mock_data.py`; the mock provider does not read project CSV, PKL, or model files.
- `PRODUCTION_THRESHOLD` is `0.56`; the analysis slider is separate and does not mutate it. XGBoost is displayed as supplied project metadata, not as a loaded model.
- The brief names `Late_Delivery_Scored_Orders.csv`, model comparison/feature-importance/final-summary/threshold-analysis CSVs, `Best_Threshold.txt`, `Winning_Model.txt`, and `Final_Late_Delivery_Model.pkl`. None of those artifact files were found in the repository file inventory at audit time. Their existence outside this checkout has not been verified here. They were not opened or loaded.
- No verified demand artifact path was present in the repository inventory. Mock demand observations are explicitly additive UI fixtures, not an assumed production product-day schema.
- No profitability model/data artifact is present in the project inventory. Profitability remains unavailable; cross-risk does not create a combined score.

## Security and file access

- The static credential-pattern scan did not identify committed key/token/private-key literals in the inspected source/config files. This is a limited source scan, not a secret-scanner or deployment audit.
- `.streamlit/secrets.toml` is ignored. `.env` is now ignored; `.env.example` contains only blank, non-secret integration settings.
- Demo sign-in is not authentication: credentials are not checked or sent to a provider. A real auth boundary is required before confidential data is introduced.
- `services/mock_data.py` generates fixtures in memory. `QueryEngine` registers only caller-supplied in-memory frames and disables DuckDB external access. Exports are generated in memory and formula-safe.
- Copilot responses are deterministic dispatch over supported intents and allowlisted functions. No model call, arbitrary Python execution, UI-supplied SQL, or unrestricted tool execution is enabled.

## Findings

| Area | Audit result | Follow-up |
| --- | --- | --- |
| Routing | Implemented; one registry and every registered route has a view | Keep route tests as pages evolve |
| Shared shell | Implemented; page-aware filters, chips, reset, save/open, search, theme, presentation | Browser-level responsive and dark-mode QA remains outstanding in environments without a connected browser |
| Delivery | Demo UI and fixed threshold are present; named model package was not found in this checkout | Verify the approved artifact manifest before connecting predictions or reporting model metrics |
| Demand | Demo forecast/error/interval views exist | Define and validate a real product-day grain, forecast horizon, and metric contract |
| Profitability | Correctly unavailable | Keep gated until independent verified dataset/model/output exist |
| Cross-risk | Descriptive capability state only; no joint score | Require independent verified signals and a validated join/coverage contract |
| Search/explorer | Application search and progressive dimension/metric exploration are implemented over the current demo context | Add production search indexing only with approved data services |
| Copilot | Offline, deterministic, evidence-preserving tools and intent dispatch | No LLM/provider is configured; unsupported questions must remain unavailable |
| Alerts/insights | Demo rules, evidence, session-only New/Acknowledged/Resolved workflow, and investigation actions are implemented | No live alert/insight engine, persisted audit history, or notification delivery |
| Reports/downloads | Filter-aware demo CSV, Excel, PDF and chart-export paths | Production report sections depend on connected verified services |
| Saved investigations | Save, open, rename, delete, and session-scoped metadata are implemented | No backend persistence or multi-user sharing |
| Error/empty states | Recoverable service and page-render states preserve workspace settings; exceptions are logged server-side | Production telemetry and alerting require service integration |
| Responsive/theme | CSS breakpoints, semantic variables and Plotly theme switching are present | Automated AppTest cannot establish visual fidelity; verify in a connected browser before sign-off |
