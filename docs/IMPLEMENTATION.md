# UI handoff

## Scope delivered

**Historical UI-stage record:** the final dataset/model implementation supersedes the integration status and validation counts below. See [FINAL_HANDOFF.md](FINAL_HANDOFF.md) and current metadata validation reports for the completed connections and trained inference.

A new Python/Streamlit application in the previously empty workspace. Twenty-five authenticated pages, a public landing page and a separate login page, with grouped navigation and a shared analytical shell. All requested component modules and all seven stylesheet modules are present.

The component library includes active/hover/focus styling, risk labels in addition to colors, evidence panels, unavailable states, loading skeletons, a recoverable service-error panel, disabled actions, toast/confirmation equivalents, chart toolbars and native sidebar collapse.

## Data contract

`MockAnalyticsService` implements `AnalyticsService`. Its deterministic source contains fictional operational observations with order, date, geography, product, shipping, risk and demand dimensions. The opt-in `VerifiedArtifactsService` reads only explicitly configured CSV files through strict read-only adapters; it does not scan for data or models.

All illustrative observations, feature weights, comparison fixtures, scenario coefficients and analytical response copy are centralized in `services/mock_data.py`. Calculations are pure functions over supplied records. Health checks describe actual UI connectivity, not fabricated production metrics. Analytical pages include a Demo UI Mode notice and provenance.

The mock records are additive synthetic planning observations, **not a production demand schema**. Future demand ingestion must explicitly define product-day grain and distinguish retrospective validation, latest next-day forecasts and forecast horizons. Unsupported delivery-only filters must never silently produce misleading demand aggregates.

## Verified versus unavailable

| Capability | Current UI behavior |
| --- | --- |
| Delivery | Demo remains selectable; verified mode reads pre-scored delivery rows and supplied analysis CSVs |
| Demand | Demo remains selectable; verified mode reads precomputed product/day forecasts |
| Profitability | Disabled placeholders; no scores, probabilities, performance or report generation |
| Cross-risk | Disabled matrix; no combined metrics |
| Explainability | Explicitly illustrative contribution charts; actual SHAP unavailable |
| Drift | Empty reference/current views; no invented drift statistics |
| Copilot | Offline deterministic responses; no LLM/provider |
| Authentication | Temporary session-only demonstration, no real authorization |

## Current UI limits

- No trained-model loading, live inference, training, SHAP execution, stock availability, data refresh jobs or external AI calls. Verified mode reads precomputed CSV outputs only.
- Synthetic forecast ranges are illustrative, not calibrated confidence intervals. Stock attention is an explicit UI rule, not a stock-out forecast.
- The country view uses a ranked chart and a disabled choropleth preview until a verified geography source exists.
- Reports share an intentionally compact template; they export selected summary, chart, insight and record sections. No profitability/cross-risk PDF can be generated.
- Saved views, preferences, alert workflow state and conversations last only for the active session. There is no shared backend or multi-user persistence.
- System appearance follows the browser's media preference for the CSS shell. Plotly and some Streamlit-native canvas controls retain base-theme behavior; explicit Dark is the most consistent dark preview.
- Responsive CSS stacks analytical columns on small screens; the primary design target is desktop. The native sidebar remains the navigation surface.
- Date comparisons override the global date filter and explicitly keep other dimensions. Unequal custom periods compare raw volumes, not exposure-normalized rates.
- Future backend packages (joblib, scikit-learn, XGBoost, SHAP) are deliberately not installed or invoked for this UI task.

## Integration status

Read-only delivery and demand CSV adapters, provider switching, separate dataset filters, source labels, registries, and verified-page states are implemented. Supplied CSVs are under `data/delivery/final/` and `data/demand/final/`; data and model files remain ignored by Git. The UI and demo provider are preserved.

The verified provider deliberately does not load pickle models. It uses pre-scored delivery rows and precomputed demand forecasts. Enable live inference only after validating the model artifact, feature order/types, preprocessing, package versions, decision threshold, and parity against known outputs. No profitability dataset or validated cross-grain join key is connected.

The order-level training dataset and a separate `DataCo_Late_Delivery_Predictions.csv` were not present in the supplied artifacts. The available scored-order CSV is wired directly; no missing file is fabricated. Delivery final-summary accuracy (69.49%) differs from scored-row agreement (68.74%) and remains explicitly unreconciled.

## Validation record

- **59 pytest / Streamlit AppTest checks passed** after the verified adapters and dataset-scoped filters were added. Route and interaction checks include public and workspace rendering, navigation, filters/reset, saved views, Copilot evidence/actions, themes, reports, exports, verified CSV schema checks, and unavailable-model gates.
- Service checks cover deterministic fixtures, filtered totals, threshold calculations, formula-safe labeled exports, unsupported Copilot prompts, in-memory DuckDB boundaries, and fail-closed behavior without a live provider.
- Python compile checks passed for `app.py`, `components/`, `services/`, `views/`, and `tests/`.
- The in-app browser was unavailable in this execution environment, so no connected-browser visual inspection or responsive/dark-mode sign-off is claimed. The optional local screenshot script still requires a browser-enabled environment.
- The app’s local HTTP health endpoint returned HTTP 200 / `ok`. PDF generation and download behavior are covered by automated tests; those tests do not constitute visual report review.

Demo tests validate the existing UI contracts. Read-only smoke checks also load the verified CSVs and render delivery, demand and model pages. These checks do not validate live model inference or production authentication.

