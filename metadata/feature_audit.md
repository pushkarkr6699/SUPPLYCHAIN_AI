# Feature audit and completion status

**Historical UI-stage audit:** see [FINAL_HANDOFF.md](../docs/FINAL_HANDOFF.md), capability_matrix.json and integration_qa.json for current completed dataset connections and validated delivery/demand inference.

**Audit date:** 2026-10-04  
**Scope:** Current `D:\SUPPLYCHAIN_AI` checkout. All analytical records are synthetic UI fixtures unless a row below explicitly says otherwise.

## Implemented

- Public landing/login demo flow, authenticated workspace shell, grouped navigation, deep links, responsive CSS, theme/density/presentation preferences.
- Shared date and dimensional filters, filter chips/reset, session-scoped saved views with page/analysis metadata, open/rename/delete, and session persistence.
- Global workspace search across capabilities, metric definitions, demo alerts, and matching entity values; progressive exploration by dimension, metric, chart/table, and records.
- Order, delivery, demand, geographic, scenario, comparison, insights, alerts, model-governance, data-quality, lineage, settings, and diagnostics interface routes. Data-derived outputs are visibly demo/illustrative.
- Alert list filtering and session-only New/Acknowledged/Resolved/Reopen workflow. It is not a live alert service and does not persist across users or restarts.
- Alert rows expose demo rule source, snapshot timestamp, active-context evidence, and session workflow status.
- Formula-safe CSV/Excel exports, demo-labeled PDF reports, report context invalidation, and chart export through Plotly controls.
- Download Center displays active filters, row/column counts, and generation time. Executive PDF includes all ten requested section headings and explicit unavailable/not-selected statuses.
- Copilot deterministic intent dispatch, supported-intent responses and evidence tables. No user prompt is executed as Python or SQL; unsupported requests stay unsupported.
- Session-safe query boundary (in-memory frames, DuckDB external access disabled), generic recoverable page error UI with server-side exception logging, and explicit empty/unavailable states.
- `.env.example`, `.env` ignore rule, and `SECURITY.md` deployment guidance.

## Partially implemented

- Delivery analytics, threshold curves, confusion matrix, calibration preview, and feature ranking run only against synthetic records. They are demonstrations, not verified model evaluation or individual prediction explanations.
- Demand forecast/error metrics run on synthetic additive observations. Product-day grain, forecast horizon, actuals cutoff, uncertainty coverage, and source lineage need an approved dataset contract.
- Geographic charts use synthetic country/region/market labels. No geocoding, verified country identifiers, or map geometry is connected.
- Copilot now has a modular allowlisted intent/context/tools/response/action boundary and safe UI, but no configured LLM or live provider. “Explain” cannot provide model-backed explanations.
- Alert lifecycle, saved views, user preferences, and investigation state are session-only; there is no authenticated multi-user persistence, audit log, notification delivery, or ownership model.
- Executive PDFs include all ten requested section headings and clearly identify unavailable modules; selected KPI/chart/insight/record content remains a demo summary, not operational advice.
- Search is in-memory across the current filtered demo dataset and route catalog; it is not an indexed cross-source search service.
- Generic error handling covers page rendering and data-service failures but does not provide centralized telemetry, structured request IDs, or production alerting.
- Caching is limited to deterministic in-memory fixtures. No shared cache, invalidation strategy, or production latency benchmark exists.

## Missing

- Verified delivery scored-order/model artifact package and provenance; the filenames listed in the supplied brief were not found in this checkout. The application does not scan for or load them.
- Verified demand dataset/model integration, profitability signals, independent cross-risk signals and validated join/coverage contract.
- Production authentication/authorization, tenant isolation, backend persistence, deployment secrets, and operational monitoring.
- Live alert rules and delivery, approved model inference, and validated explanations for individual records.
- Connected-browser visual review at desktop/tablet/mobile breakpoints and dark mode. This execution environment did not expose a connected browser.
- Full operational executive report with all requested verified sections, and production search indexing.

## Broken

- No reproducible broken feature was identified by the automated route/service checks run for this audit. This status describes checked paths only and is not a production reliability claim.

## Duplicate

- No duplicate registered route or second mock-data source was identified in the audited registry/provider path. Similar metrics appear in different analysis pages by design.

## Needs redesign

- Revisit the alert lifecycle and saved-investigation model before multi-user use: status changes and ownership require server-side identity, timestamps, authorization, and audit history.
- Revisit the report builder once business definitions and verified metrics exist; current selectable sections do not meet the full executive report specification.
- Separate demo-only delivery diagnostics from a future model-governance page so synthetic evaluation cannot be confused with artifact-backed performance.

## Real-data integration required

1. Obtain an approved read-only artifact manifest and validate paths, hashes, schemas, keys, date coverage, targets, model version, threshold provenance, split strategy, and licensing.
2. Specify order-grain delivery and product-day demand contracts independently; validate nulls, duplicates, coverage, and filter semantics before enabling a provider.
3. Implement providers behind `services/contracts.py`, add integration tests with approved representative fixtures, and retain source/version/filter evidence in every output.
4. Integrate profitability independently. Enable combined risk only after independently validated signal definitions and a join-key coverage test; do not manufacture a joint score.
5. Add real authentication, authorization, tenant boundaries, managed secrets, persistence, telemetry, and deployment controls before using confidential or operational data.

## Verification record

Final verification: **57 pytest / Streamlit AppTest checks passed**, Python compilation passed for app/components/services/views/tests, and the local Streamlit health endpoint returned HTTP 200 / `ok`. AppTest confirms rendered behavior but does not replace browser-based visual QA or real-data integration tests.
