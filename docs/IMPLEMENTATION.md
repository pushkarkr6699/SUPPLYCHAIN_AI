# UI handoff

## Scope delivered

A new Python/Streamlit application in the previously empty workspace. Twenty-five authenticated pages, a public landing page and a separate login page, with grouped navigation and a shared analytical shell. All requested component modules and all seven stylesheet modules are present.

The component library includes active/hover/focus styling, risk labels in addition to colors, evidence panels, unavailable states, loading skeletons, a recoverable service-error panel, disabled actions, toast/confirmation equivalents, chart toolbars and native sidebar collapse.

## Data contract

`MockAnalyticsService` implements `AnalyticsService`. Its deterministic source contains fictional operational observations with order, date, geography, product, shipping, risk and demand dimensions. The UI does not scan the project for datasets or model files.

All illustrative observations, feature weights, comparison fixtures, scenario coefficients and analytical response copy are centralized in `services/mock_data.py`. Calculations are pure functions over supplied records. Health checks describe actual UI connectivity, not fabricated production metrics. Analytical pages include a Demo UI Mode notice and provenance.

The mock records are additive synthetic planning observations, **not a production demand schema**. Future demand ingestion must explicitly define product-day grain and distinguish retrospective validation, latest next-day forecasts and forecast horizons. Unsupported delivery-only filters must never silently produce misleading demand aggregates.

## Verified versus unavailable

| Capability | Current UI behavior |
| --- | --- |
| Delivery | Full demo UI; XGBoost and threshold 0.56 are supplied metadata; no artifact loaded |
| Demand | Full demo UI; synthetic actuals/forecasts and illustrative ranges |
| Profitability | Disabled placeholders; no scores, probabilities, performance or report generation |
| Cross-risk | Disabled matrix; no combined metrics |
| Explainability | Explicitly illustrative contribution charts; actual SHAP unavailable |
| Drift | Empty reference/current views; no invented drift statistics |
| Copilot | Offline deterministic responses; no LLM/provider |
| Authentication | Temporary session-only demonstration, no real authorization |

## Current UI limits

- No production datasets, trained-model loading, inference, training, SHAP execution, stock availability, data refresh jobs or external AI calls.
- Synthetic forecast ranges are illustrative, not calibrated confidence intervals. Stock attention is an explicit UI rule, not a stock-out forecast.
- The country view uses a ranked chart and a disabled choropleth preview until a verified geography source exists.
- Reports share an intentionally compact template; they export selected summary, chart, insight and record sections. No profitability/cross-risk PDF can be generated.
- Saved views, preferences, alert workflow state and conversations last only for the active session. There is no shared backend or multi-user persistence.
- System appearance follows the browser's media preference for the CSS shell. Plotly and some Streamlit-native canvas controls retain base-theme behavior; explicit Dark is the most consistent dark preview.
- Responsive CSS stacks analytical columns on small screens; the primary design target is desktop. The native sidebar remains the navigation surface.
- Date comparisons override the global date filter and explicitly keep other dimensions. Unequal custom periods compare raw volumes, not exposure-normalized rates.
- Future backend packages (joblib, scikit-learn, XGBoost, SHAP) are deliberately not installed or invoked for this UI task.

## Integration sequence

1. Create an approved artifact manifest. Check schemas, row keys, temporal coverage, preprocessing requirements and model/metric provenance read-only.
2. Add a separate delivery adapter for scored orders and a demand adapter for product-day forecasts. Preserve availability metadata and distinguish observed outcomes from predictions.
3. Add validated model metadata and feature/explanation adapters; replace illustrative fixture access with verified provider responses.
4. Add parameterized DuckDB access and schema/coverage tests. Keep real-data access out of page modules.
5. Register the real provider, replace demo provenance, and add explicit load/failure/staleness handling. Only then disable DEMO_MODE.
6. Replace session demo access with a real auth provider before any deployment using confidential data.
7. Keep profitability and combined risk gated until independently verified artifacts and join coverage exist.

No project data or trained-model artifact was loaded, modified or retrained during this implementation.

## Validation record

- **57 pytest / Streamlit AppTest checks passed** after the alert workflow, modular Copilot, executive report, and recoverable page-error changes. Route and interaction checks cover public and workspace rendering, navigation, filters/reset, saved views, Copilot evidence/actions, themes, preferences, report generation, exports, alert status persistence within a session, and unavailable-model gates.
- Service checks cover deterministic fixtures, filtered totals, threshold calculations, formula-safe labeled exports, unsupported Copilot prompts, in-memory DuckDB boundaries, and fail-closed behavior without a live provider.
- Python compile checks passed for `app.py`, `components/`, `services/`, `views/`, and `tests/`.
- The in-app browser was unavailable in this execution environment, so no connected-browser visual inspection or responsive/dark-mode sign-off is claimed. The optional local screenshot script still requires a browser-enabled environment.
- The app’s local HTTP health endpoint returned HTTP 200 / `ok`. PDF generation and download behavior are covered by automated tests; those tests do not constitute visual report review.

These checks validate the UI and demo contracts; they do not validate trained models, real operational data or production authentication.

