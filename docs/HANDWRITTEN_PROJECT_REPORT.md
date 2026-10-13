# SUPPLYCHAIN AI
## An AI-Assisted Supply-Chain Analytics and Business Dashboard

**Student Name:** ____________________

**Roll Number:** ____________________

**Course / Semester:** ____________________

**Submitted To:** ____________________

**Institution:** ____________________

This report follows the ten sections in the supplied assignment sample. It describes the implemented local project and distinguishes verified functions from future enhancements. Implementation and QA evidence was recorded on 7 October 2026.

## 1. Project Overview

SupplyChain AI is an interactive web application for analysing supply-chain information, examining trained-model predictions and presenting business findings. It brings delivery analysis, product-level web-visit forecasting, profitability analysis, visualisation, data uploads and AI assistance into one interface.

The main application is developed using Python and Streamlit. Custom HTML, CSS and JavaScript support the visual design, responsive layouts and interactions. Therefore, it extends the HTML/CSS/JavaScript business-dashboard concept in the assignment with data-processing services and machine-learning inference.

The project has an integrated landing page, login experience and dashboard. Users can explore registered historical datasets or upload their own data. Connected analytics uses actual supplied files, while a separate, clearly labelled demonstration mode preserves the original demonstration experience.

Its main purpose is to convert complex tables into understandable charts, filtered records, prediction results and evidence-based explanations. The current release is a tested local college-demonstration platform. It is not a publicly deployed or independently certified production system.

## 2. Business Need

Supply-chain information is often spread across order files, forecast outputs, model results and evaluation reports. Reading these sources separately makes it difficult to identify patterns, compare periods and determine which records need investigation.

The project addresses the following needs:

1. **Delivery visibility:** Analysts need to examine recorded delivery outcomes and available late-delivery probabilities across markets, regions and shipping methods.
2. **Forecast understanding:** Product-level forecasts need understandable units, dates and historical context. In this project, the available demand-related model forecasts web visits rather than purchases or inventory requirements.
3. **Profitability review:** Supplied profit observations and model probabilities need to be examined alongside model-quality limitations.
4. **Flexible comparisons:** Users need to select relevant fields and compare categories, periods and measures without manually rebuilding every chart.
5. **Self-service analysis:** Other users should be able to analyse uploaded data and, where appropriate, use the existing trained models.
6. **Clear explanations:** Non-technical users need understandable descriptions of calculated results and model outputs.
7. **Trust and privacy:** Users need source information, honest missing-data states, safe exports and protection of sensitive fields.

A unified dashboard supports faster investigation and clearer communication. These are intended benefits; measured financial savings or profit improvements have not been established.

## 3. Proposed Solution and Implemented Approach

The solution is a modular decision-support platform with shared services for calculations, data validation, model inference, privacy and reporting. Its main workflow is:

**Select a source or upload a file → validate and profile data → select fields and filters → analyse or predict → visualise results → review insights → export a report.**

The Executive Command Center presents an overview. Delivery Intelligence, Demand Intelligence and Profitability Intelligence provide specialised analysis. Order Explorer and Universal Explorer help users investigate records. Comparison Studio and Visualization Studio support user-selected analysis. Bring Your Data provides independent upload workflows.

Sevika is a floating AI assistant that follows the current page, selected dataset and filters. It provides local analytical help and optional live explanations based on approved anonymous numerical summaries. Separate governance pages explain data quality, lineage, model status and threshold behaviour.

The architecture maintains important distinctions: order records are not treated as line-item records, web visits are not treated as product sales, and unsupported model inputs are not invented. Unavailable data produces an explanation rather than a fabricated result.

## 4. Key Objectives

1. Create an integrated, readable and responsive business dashboard.
2. Connect actual registered datasets without damaging the existing UI or demonstration mode.
3. Present delivery, forecasting and profitability information through appropriate indicators and charts.
4. Let users select multiple fields, filters and comparison factors.
5. Execute supplied trained models only when required inputs and model contracts are valid.
6. Offer both raw-data exploration and compatible trained-model prediction for uploads.
7. Provide understandable local observations and evidence-linked live AI explanations.
8. Support useful reports and safe data exports.
9. Protect credentials and minimise personal contact information.
10. Verify numerical integrity, interface behaviour, uploads, predictions, exports and security controls.
11. Document model limitations and missing sources honestly.
12. Provide a maintainable foundation for future operational integrations.

## 5. Project Scope and Deliverables

### A. Connected datasets and their roles

**Primary delivery data:** `DataCo_Final_Order_Level_Dataset.csv` contains 65,752 unique order-level records. Related files include `DataCo_Final_Scored_Orders.csv`, `DataCo_Late_Delivery_Predictions.csv` and `DataCo_Risk_Level_Summary.csv`. There are 2,123 supplied scored orders and 63,629 unscored orders. Missing probabilities remain missing and are not converted into zero risk.

**Demand-related data:** `AccessLogs_Final_Advanced_Forecast.csv` contains 2,280 product/base-day forecasts across 76 products. Registered history supports model inference. The target is next-day web visits, not purchases, units sold or confirmed inventory demand.

**Profitability data:** The supplied profitability source contains 27,078 line observations. Scored records are supported by category, market and shipping summaries, high-loss-risk records, feature rankings, model comparisons, threshold analysis, calibration checks and train/test drift information where supplied.

**Independent final-delivery data:** `Late_Delivery_Scored_Orders.csv` contains 24,369 line observations from a separate experiment. Related summary, comparison, feature-importance and threshold files retain their own context. This source does not replace the primary order-level delivery dataset.

The registry records 41 source artifacts, including analytical, evaluation, reference and provenance assets. Source paths, roles, schemas and hashes support traceability. Training notebooks are preserved as research provenance; the application integration did not rerun the training process.

### B. Prediction models

| Model and artifact | Purpose | Fixed decision or target |
|---|---|---|
| Tuned delivery XGBoost: `DataCo_Tuned_XGBoost.pkl` | Estimate late-delivery probability for compatible order inputs | Threshold 0.35 |
| Demand XGBoost: `AccessLogs_Final_XGBoost_Demand_Model.pkl` | Predict next-day web visits for a product | At least 15 consecutive historical daily observations |
| Profitability XGBoost: `DataCo_Final_Trained_Model.pkl` | Estimate the probability of the profitable class | Threshold 0.20 |
| Final-delivery XGBoost: `Final_Late_Delivery_Model.pkl` | Separate line-observation late-delivery experiment | Threshold 0.56 |

`DataCo_Late_Delivery_Model.pkl` is retained as a Random Forest baseline/reference, rather than an active prediction adapter.

Four active adapters preserve original preprocessing, feature order, positive-class meaning and fixed thresholds. Prediction workflows validate inputs before inference. Selecting arbitrary chart fields does not retrain a model. Threshold Lab supports exploratory comparisons without silently changing saved decision thresholds.

### C. Main analytical features

1. **Executive overview:** Summary indicators, coverage information and navigation to relevant investigations.
2. **Delivery Intelligence:** Recorded delivery outcomes, supplied probabilities, risk distribution, market/shipping comparisons and model diagnostics on available scored records.
3. **Demand Intelligence:** Product-level web-visit forecasts, available history, forecast comparisons and source-provided bounds where present. New inference does not invent calibrated prediction intervals.
4. **Profitability Intelligence:** Observed profit, scored probabilities, segment summaries, evaluation information and exploratory thresholds.
5. **Cross-Risk Command Center:** Review separate operational signals with their coverage and source context. Different grains are not silently combined into supposedly matched records.
6. **Order and data explorers:** Search, sorting, filtering, record details and prediction provenance where available.
7. **Comparison Studio:** Compare selected measures across available groups and periods using calculations, charts and exact tables.
8. **What Changed and decision summaries:** Examine observed momentum, acceleration, investigation priorities and favourable observed segments. These are descriptive findings, not causal conclusions or guaranteed forecasts.
9. **Anomaly review:** Interquartile-range analysis identifies unusual observed values when sufficient reference observations exist.
10. **Scenario Lab:** Compare supported model-input changes, such as shipping mode, against a baseline prediction. This demonstrates model sensitivity rather than proving that an action will cause a particular outcome.
11. **Alert Center:** Organise available signals for investigation; unsupported inventory or operational alerts remain unavailable.
12. **Model governance:** Inspect metadata, supplied comparisons, global feature importance, thresholds, reference drift information, quality and connectivity. Per-order SHAP explanations are not available.

### D. Visualization Studio

Users can build up to ten chart cards from 25 visualisation options:

1. Vertical bars
2. Horizontal bars
3. Line
4. Area
5. Scatter
6. Bubble
7. Histogram
8. Box plot
9. Violin plot
10. Empirical cumulative distribution function (ECDF)
11. Correlation heatmap
12. Density heatmap
13. Grouped heatmap
14. Treemap
15. Sunburst
16. Pie
17. Donut
18. Scatter matrix
19. Grouped bars
20. Stacked bars
21. Pareto
22. Moving average
23. Coordinate map
24. KPI indicators
25. Ordered funnel

Users can choose measures and grouping fields, apply filters, and edit, duplicate, reorder or remove cards. Exact analysis tables accompany bounded charts. Sampling limits are disclosed rather than presented as complete raw-data displays.

Chart availability depends on the fields. Maps require actual coordinates; funnels require actual ordered stages; stacked charts require additive measures. Compatible Cartesian charts provide zoom, pan, autoscale, reset, fullscreen and PNG export. Composition charts use appropriate controls instead of meaningless axis zoom.

Chart settings can be exported and restored against the matching source, schema and current selection. Stored filters are available for review; importing settings does not automatically reapply them.

### E. Bring Your Data

The upload feature accepts CSV, TSV, XLSX, flat JSON and Parquet. It provides two paths:

**Raw-data exploration:** Profile columns, types, missing values, duplicates, ranges and distributions; select fields and filters; create charts; ask supported local questions; generate reports.

**Trained-model prediction:** Select a registered model, map supplied columns and review compatibility. Compatible, Partial, Unknown and Incompatible states explain readiness. Missing required features are not fabricated, and arbitrary uploaded models or executable code are not accepted.

Uploads and their results remain session-local. Changing the file clears stale outputs and revokes previous file consent. Reset or logout clears the session data. A safe parser applies file, row, column and processing limits.

### F. Sevika and SupplyChain Copilot

Sevika offers page-related suggestions and explains selected results in understandable language. Local analysis supports bounded requests such as rankings, trends, distributions, correlations and comparisons over available fields.

Live AI uses the configured Hugging Face/Groq provider. It interprets approved anonymous numerical summaries; it does not receive raw rows or credentials. Every new uploaded file requires its own consent. Evidence references help users connect explanations to calculated results. Local analytical help remains available when the live provider is unavailable.

Copilot supports validated navigation, filter, selection, chart, table, analysis, scenario and report commands. State-changing and prediction actions require a visible user action. Arbitrary SQL and uploaded code execution are not supported. AI explanations do not replace the registered numerical calculations or trained models.

### G. Reports, design and safeguards

Deliverables include filtered CSV/Excel exports, analysis PDFs, per-chart PNG/CSV exports, conversation JSON and a four-source executive briefing with management questions, evidence and model limitations. The analysis PDF lists selected chart types and the global analysis table; it does not embed every chart image.

The integrated interface includes grouped navigation, Light/Dark/System themes, mobile layouts, visible focus, consistent cards, restrained animations, reduced-motion support and readable empty/error states.

Privacy services remove credentials and minimise personal contact fields before display, export and AI use. Spreadsheet formula injection is prevented in exports. Optional private accounts support Admin, Analyst, Executive and Viewer roles with server-side permission checks. Current presentation access remains explicitly labelled demo/session access.

## 6. Technology Stack

| Technology | Purpose and role |
|---|---|
| Python | Shared analytics, validation, inference, privacy and application logic |
| Streamlit | Interactive web application, controls and session management |
| HTML and CSS | Custom structure, themes, spacing, typography and responsive presentation |
| JavaScript | Supported interface interactions, animation and chart/layout behaviour |
| pandas and NumPy | Tabular processing, filtering, grouping and numerical calculations |
| Plotly | Interactive charts, hover details and chart controls |
| XGBoost, scikit-learn and joblib | Supplied model integration, original preprocessing and trusted artifact support |
| DuckDB | Controlled analytical support with external access disabled |
| ReportLab | PDF report generation |
| openpyxl and PyArrow | Excel and Parquet support |
| OpenAI-compatible SDK | Server-side communication with the configured live AI provider |
| pytest and Playwright | Automated regression and browser verification |
| Git and JSON registries | Version checkpoints, source/model metadata and traceability |

The OpenAI-compatible SDK describes the API interface; the configured live service is Hugging Face/Groq.

## 7. Implementation Plan and Verification

| Phase | Activity | Output |
|---|---|---|
| 1 | Review requirements and preserve the existing UI | Defined scope and safe integration approach |
| 2 | Inventory and register supplied data/models | Source roles, hashes, schemas and missing-asset records |
| 3 | Analyse grain, coverage and relationships | Reconciled counts and validated join rules |
| 4 | Build shared analytical and privacy services | Reusable calculations and safe data handling |
| 5 | Integrate trained prediction adapters | Fixed feature/preprocessing/threshold contracts |
| 6 | Connect dashboard pages, charts and comparisons | Unified analytical workflows |
| 7 | Add uploads, Sevika, Copilot and reports | Self-service exploration and evidence-based assistance |
| 8 | Refine layout, themes, motion and recovery | Improved presentation and usability |
| 9 | Run verification and fix identified issues | Recorded regression, reconciliation, browser and security results |
| 10 | Save a release checkpoint and audit | Reviewable local demonstration version |

Recorded final verification includes:

- The latest verification passed **368 automated tests**, with zero failures, errors or skips. Full evidence and remaining limits are in FINAL_IMPLEMENTATION_REPORT.md.
- **36 final browser checks**, covering navigation, ten real-data chart cards, Parquet uploads, local questions, settings, PDF downloads, mobile layouts and logout.
- Additional evidence covers 13 upload-browser checks, 14 chart layouts and five connected-workflow checks.
- Local Sevika and conversation workflows were verified. Earlier live answers were successful, but the latest live request on 13 October was rejected because Hugging Face credits are exhausted. Live AI requires restored credits before presentation.
- Delivery output reproduction was verified on 2,123 real scored orders; demand reproduction was verified on 1,216 registered history/forecast rows.
- Profitability and final-delivery portability was checked using 32 conversion probes each. This is not historical real-row accuracy validation.
- A local source security scan reported zero findings, and 92 installed packages had no known vulnerabilities at that scan. These checks are not an independent penetration test.
- Local service measurements recorded approximately 0.81 seconds for a cold source load, 0.014 seconds for a cached source load and 1.32 seconds for ten chart constructions. These are not end-to-end page timings or a multi-user guarantee.

Data checks also reconciled delivery totals, scored coverage, filtered exports and safe joins. Meaningful bugs involving empty exports, question submission and PDF persistence were fixed before final verification.

## 8. Expected Business Value

1. **Clearer visibility:** Users can inspect indicators, records and model evidence in one workspace.
2. **Faster exploration:** Filters, comparisons and multiple charts reduce repeated manual preparation.
3. **Prioritised investigation:** Available risk signals and observed anomalies help analysts decide what to examine next.
4. **Better communication:** Reports and Sevika explanations make findings easier to present to non-technical audiences.
5. **Broader usefulness:** Bring Your Data lets other users analyse their own files rather than relying only on project datasets.
6. **Reproducibility:** Registered sources, fixed model contracts and saved chart settings support consistent analysis.
7. **Trust:** Visible coverage, source units, privacy safeguards and model limitations reduce misleading interpretations.
8. **Educational value:** The project combines interface design, data engineering, machine-learning integration, AI assistance and software testing.

These benefits support decisions; no deployment study has yet demonstrated a specific reduction in delivery delays, costs or losses.

## 9. Future Enhancements and Current Limitations

### Current limitations

The original complete DataCo CSV, official description file and raw tokenized access logs are unavailable. Therefore, complete original customer/product/order-item/access-log relationships cannot be verified.

Profitability and final-delivery scored files omit some required historical model inputs, preventing complete historical re-scoring validation. The supplied profitability model has ROC-AUC of approximately 0.4978, indicating weak discrimination. A working prediction adapter does not prove that a model is suitable for business deployment.

Per-record SHAP explanations, validated built-in route endpoints and a calibrated composite health score remain unavailable. Uploads and audit events are session-local. The platform has not undergone public production deployment, enterprise identity integration or multi-user load certification.

### Planned enhancements

1. **Complete source integration:** Obtain the missing raw datasets and validate additional relationships and original definitions.
2. **Improve predictive quality:** Assess leakage, feature availability and evaluation splits; retrain where justified and test on independent recent data.
3. **Better uncertainty and explanations:** Add validated calibration, appropriate forecast intervals and reproducible local feature contributions.
4. **Operational integrations:** Connect approved ERP, warehouse and shipment systems for genuinely refreshed data.
5. **Actual unit-demand forecasting:** Add purchase or inventory datasets and suitable models; web visits should not be relabelled as purchases.
6. **Geospatial analysis:** Obtain valid coordinates, shipment endpoints and constraints before adding route analysis or optimisation.
7. **Durable user workspaces:** Introduce secure databases, authorised project storage, collaboration and retention policies.
8. **Production access and hosting:** Add enterprise identity, multi-factor authentication, tenant isolation, backups and deployment hardening.
9. **Scalability:** Conduct concurrency tests and improve large-dataset processing and monitoring.
10. **Richer reports:** Embed chart images and per-card tables and add controlled scheduling and report templates.
11. **Expanded assistant:** Add validated multilingual support and retrieval from approved documentation, with privacy and evidence controls.
12. **Accessibility:** Broaden keyboard and assistive-technology testing and collect feedback from users.

## 10. Conclusion

SupplyChain AI demonstrates how a business dashboard can combine connected historical data, controlled trained-model inference, flexible visualisation, user uploads and AI explanations in one application.

Its distinctive features are Comparison Studio, 25-option Visualization Studio, two-path Bring Your Data, context-aware Sevika, controlled scenarios and evidence-based reporting. Shared services and validation rules help preserve numerical integrity and privacy.

The recorded tests support its use as a local college-demonstration project. Missing original sources and model-quality limitations are documented, providing a clear direction for future work. The project provides a practical foundation for a more advanced supply-chain decision-support platform.

---

## Optional diagram for handwritten submission

Draw boxes connected by arrows:

**Registered datasets / User upload**

↓

**Privacy, schema checks and data profiling**

↓

**Filters and shared analytical services**

↓

**Charts / Registered trained models / Approved AI summaries**

↓

**Dashboard findings and reports**

Below the diagram write: “Missing sources are shown as unavailable; predictions require compatible inputs; uploads remain session-local.”

## Local reference documents

- FINAL_IMPLEMENTATION_REPORT.md
- DATA_LINEAGE.md
- DATA_DICTIONARY.md
- MODEL_REGISTRY.md
- MODEL_HEALTH.md
- metadata/master_regression_qa.json
- metadata/master_browser_qa.json
- metadata/master_data_qa.json
