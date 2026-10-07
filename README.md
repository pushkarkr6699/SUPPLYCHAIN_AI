# SUPPLYCHAIN AI

A local decision-intelligence platform using supplied historical delivery, demand, profitability and final-delivery data. The existing UI and clearly labelled demo are preserved.

Preview: **https://supplychain-ai-er9a.onrender.com/**. Choose **Open platform**. The current local server is already running.

Read [FINAL_IMPLEMENTATION_REPORT.md](FINAL_IMPLEMENTATION_REPORT.md) for the final evidence, known limits and exact completion status. The [199-section requirement matrix](metadata/master_requirement_matrix.md) separates verified work from missing source-dependent capabilities. Earlier handoffs under `docs/` retain their original dates and test counts.

## Available workflows

- Delivery, demand, profitability, cross-risk coverage, order/product exploration, period changes, quality, lineage and model governance use actual connected data at their documented grains.
- Visualization Studio has **25 chart types**, up to **10 chart cards**, per-card edits, duplication, ordering, sorting, exact analysis tables and source-checked settings.
- Bring Your Data supports **CSV, TSV, XLSX, JSON and Parquet**. Choose raw analytics or compatible trained-model inference. Review profiling, missing values, duplicates, field types, filters and graph recommendations.
- All four active trained adapters have fixed contracts, original preprocessing, trusted artifacts and explicit compatibility checks. Missing inputs are never fabricated.
- Explicit cross-source joins validate types, nulls, uniqueness, overlap and row count. Repeated child observations require aggregation; many-to-many expansion is refused.
- Sevika follows the current page, selected fields, filters and uploaded dataset. Local numerical analysis works without a provider. Uploaded live AI needs consent for that specific file and sends anonymous numerical summaries.
- Observed momentum, acceleration, transparent investigation priorities, favorable observed segments, IQR anomaly classifications and a reconciled Sales waterfall support decisions without causal claims.
- Reports include current-source PDFs and a **connected executive briefing across all four separate sources**, with six management questions, source-specific filters, KPI evidence and model limits. CSV/Excel and chart PNG exports are available.

## Run locally

The configured environment is already installed. To run it again in PowerShell:

```powershell
cd D:\SUPPLYCHAIN_AI
.\.venv\Scripts\python.exe -m streamlit run app.py --server.address=127.0.0.1 --server.port=8501
```

`./run.ps1` is the launcher shortcut. The server binds to loopback.

For a fresh Python environment:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt -r requirements-inference.txt
```

The supplied data and model binaries are local ignored assets. Cloning Git source alone does not include them. See [PROJECT_INVENTORY.md](PROJECT_INVENTORY.md), [data/README.md](data/README.md) and [DATA_LINEAGE.md](DATA_LINEAGE.md).

## Deploy to Render

Use the app's deployment config to run the Streamlit UI on Render:

```yaml
services:
  - type: web
    name: supplychain-ai
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: streamlit run app.py --server.address=0.0.0.0 --server.port=$PORT
```

This binds Streamlit to all interfaces and uses Render's provided `$PORT` so the app is reachable outside localhost.

## Configuration and access

`SUPPLYCHAIN_PROVIDER=demo` preserves the synthetic UI demonstration. `SUPPLYCHAIN_PROVIDER=verified` uses the supplied registered historical files. This workspace's ignored `.env` selects the connected provider. Restart after changing settings.

Default `SUPPLYCHAIN_AUTH_MODE=demo` provides explicitly labelled temporary session access. Optional private accounts use salted password hashes and server-side Admin, Analyst, Executive and Viewer permissions. To configure an account privately:

```powershell
.\.venv\Scripts\python.exe scripts/create_local_account.py
```

Set `SUPPLYCHAIN_AUTH_MODE=accounts` privately in `.env` and restart. Account hashes are stored in ignored `.streamlit/accounts.json`. No real account was created for this release. Demo accounts in account mode cannot read connected project files. Viewer sessions cannot register native exports or run trained predictions.

Optional live insights use the existing private Hugging Face/Groq configuration (`HF_TOKEN`). Never paste keys into chat or commit `.env`. The original four-source anonymous summaries were approved; new uploaded files require their own consent. Local analysis remains available when live AI is disabled or unavailable.

Uploads, conversations, saved views and the last 100 allowlisted audit events are session-local. Clear uploads or log out to remove session data. This is not public production identity, durable audit storage or a multi-tenant deployment.

## Data and model scope

| Source | Grain / meaning | Model validation |
| --- | --- | --- |
| Delivery d1 | 65,752 unique orders; 2,123 scored; 63,629 unscored | Real supplied-score parity on 2,123 rows; fixed threshold 0.35 |
| Demand d2 | 2,280 product/base-day forecasts across 76 products; next-day web visits | Real registered parity on 1,216 complete-history rows; minimum 15 consecutive daily observations |
| Profitability | Separate supplied line observations | Portable conversion fidelity on 32 probes; threshold 0.20; original complete features unavailable for historical re-scoring |
| Final delivery | Independent line-observation experiment | Portable conversion fidelity on 32 probes; threshold 0.56; original complete features unavailable for historical re-scoring |

Unscored delivery probabilities remain missing. Demand means web visits, not purchases or fulfilled units. Source-provided interval bounds are shown as supplied; they are not assumed calibrated. No calibrated interval is generated for new demand inference.

Profitability's supplied ROC-AUC is about 0.4978; schema compatibility does not establish model quality. Original fitted artifacts/preprocessors are preserved; no retraining occurred. Global feature rankings are attributed to their actual models. Conversion probes are test artifacts, never connected business data.

Missing original files: `DataCoSupplyChainDataset.csv`, `DescriptionDataCoSupplyChain.csv`, `tokenized_access_logs.csv`. Complete original customers/products/order-items/access-log relationships cannot be verified without them. Per-record SHAP, built-in route endpoints/coordinates and a defensible composite health score are unavailable. Uploaded actual coordinate pairs support point maps.

For broader historical market comparisons, choose **Settings -> Data -> All available history**, then reset filters. The default January 2018 delivery window contains Pacific Asia only; unavailable out-of-period filter values are refused by analytical commands.

## Analysis and assistant controls

Chart options depend on the actual selected fields. Coordinate maps need real coordinates; funnels need supplied ordered stages; stacked charts require additive measures. Display/sample limits are labelled and exact grouped exports remain available.

Saved chart settings contain fields, calculations, ordering, overrides, selected filter rules, source/schema/selection fingerprints and a timestamp. Restore the matching dataset, field types and filters first. A different selection is rejected; filter controls are not silently reapplied.

Local Copilot accepts supported analyses and bounded commands, for example `show table`, `show chart`, `filter Market to Pacific Asia`, `clear filters`, `select order <current ID>`, `analyze top 5 Market by total Sales`, `simulate shipping mode <available mode>` and `open reports`. State/model actions require the visible Run requested action control. Map and scenario requests require supporting data and permissions. A requested result is limited to 500 rows; use Downloads for the complete export.

Native compatible chart toolbars expose zoom in/out, pan, autoscale, reset, fullscreen and PNG export. Composition charts use composition controls rather than Cartesian axis zoom. Light/Dark/System themes, density, animation and presentation preferences are session-scoped; device reduced motion takes priority.

## Verification

Run the full suite:

```powershell
.\.venv\Scripts\python.exe -m pytest -q --junitxml=tmp/master_regression_final.xml
```

With the local server running and QA dependencies installed:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt -r requirements-security.txt
.\.venv\Scripts\python.exe scripts/master_data_qa.py
.\.venv\Scripts\python.exe scripts/master_browser_qa.py --lab-only
.\.venv\Scripts\python.exe scripts/master_workflow_qa.py
.\.venv\Scripts\python.exe scripts/chart_controls_qa.py
.\.venv\Scripts\python.exe scripts/security_audit.py
```

Browser tests use isolated headless Chrome profiles. Rendered screenshots/PDFs go to ignored `tmp/`; compact executed results are under `metadata/master_*`, `metadata/chart_controls_qa.json` and `metadata/uploads_browser_qa.json`. See [QA_REPORT.md](QA_REPORT.md) for current evidence and historical results.

## Project structure

| Path | Responsibility |
| --- | --- |
| `app.py`, `config.py`, `run.ps1` | Entry point, private configuration loading, launcher |
| `components/`, `styles/` | Preserved shared UI, safe controls, charts, themes and motion |
| `views/registry.py`, `views/` | Explicit public and workspace navigation; no auto-discovered authentication bypass |
| `services/` | Shared calculations, trained adapters, privacy, uploads, joins, profiles, visualization, AI and access control |
| `data/`, `models/`, `notebooks/` | Local supplied artifacts and research provenance |
| `metadata/` | Hash registries, validation, executed QA and requirement traceability |
| `scripts/`, `tests/` | Inventory, account setup, verification, browser checks and regression |
| `docs/` | Preserved earlier handoffs and implementation notes |

[DATA_DICTIONARY.md](DATA_DICTIONARY.md) records actual discovered schemas. [MODEL_REGISTRY.md](MODEL_REGISTRY.md) and [MODEL_HEALTH.md](MODEL_HEALTH.md) distinguish real-score parity, conversion fidelity and model limitations. [SECURITY.md](SECURITY.md) defines the local trust boundary.
