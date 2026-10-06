# Bring Your Data

Open the dashboard and select **Bring Your Data** in the sidebar, or **Analyze your own dataset** at the end of Executive Overview. This section is independent of the built-in demo and verified datasets; neither is replaced, merged with uploads, or retrained.

## Supported imports

- CSV: UTF-8/BOM or Windows-1252, with automatic or explicit comma, semicolon, tab or pipe delimiter.
- TSV: tab-delimited values.
- XLSX: choose a worksheet from a values-only workbook. Formula cells, macros, external workbook links, XML entity declarations, excessive ZIP expansion and oversized sparse coordinates are rejected.
- JSON: an array of flat record objects, with no nested arrays/objects or duplicate keys.

Imports are limited to 20 MB, 50,000 data rows, 100 columns, 128-character headers, 4,096-character cells and 80 MB parsed memory. Prediction batches are limited to 5,000 selected rows. Header names must be unique after whitespace trimming. Uploaded scripts, notebooks, pickles and model files are never accepted or executed.

CSV fields initially remain text to preserve identifiers such as `001`. Numeric candidates exclude common identifier fields and values with leading zeros. Review the choices under **Treat fields as numeric**, choose an optional time field and its date format, then select **Apply field types**. Invalid conversions are reported rather than replaced with fabricated values. Missing numeric values remain missing. Without a numeric measure, category analysis uses a clearly labelled generated count of one per record. Time charts require an explicitly valid time field.

## Raw data exploration

1. Upload a supported file and review the preview, missing-value counts, distinct values and duplicate rows.
2. Select **Raw data exploration** and apply numeric/date types.
3. Optionally filter records by one uploaded field. Empty categorical selection includes all records. The first 200 distinct categorical values are selectable; numeric range filters exclude missing values.
4. Select up to two grouping fields, four numeric measures and eight graphs from 18 chart types, then select **Build visualizations**.
5. Inspect the local evidence under **Sevika insights for this upload** using its own grouping fields, measures and calculation. Charts and evidence always name their applied choices.
6. Download the selected data as formula-safe CSV or Excel (Excel up to 5,000 rows), grouped analysis CSV, chart settings, or chart PNG.

Charts include bars, lines, area, scatter, bubble, histogram, box, violin, ECDF, correlation/density/grouped heatmaps, treemap, sunburst, pie, donut and scatter matrix. Controls use the platform's existing zoom, pan, autoscale, reset, fullscreen and PNG export. Each chart states its display/sample limits; incompatible selections receive an explanation.

## Registered trained-model predictions

Download a required-column CSV template before uploading, or after selecting a model. The template contains headers only. Populate the original training features; a model cannot predict arbitrary unrelated data merely because it is uploaded.

| Model | Data contract | Output |
| --- | --- | --- |
| Delivery order risk | One feature-complete row per order, including the original engineered features | Late-delivery probability, class at 0.35, risk band |
| Next-day web visits | DateOnly, Product, Category, Department, Visits; at least 15 consecutive days per product, including zero-visit days; stable category and department | One next-day web-visit forecast per product |
| Profitability line items | Complete original numeric and categorical line-item features | Profitability/loss probabilities, fixed-threshold class, risk band |
| Final delivery line items | Complete original final experiment numeric and categorical features | Late-delivery probability, class at 0.56, risk band |

Select **Trained-model predictions**, choose the registered model and map every required input to a distinct uploaded column. The application checks types, missing values, finite numbers, applicable ranges and the existing model validators before running inference. Existing prediction column names must be removed or renamed before rescoring. Missing inputs disable prediction; they are never invented. No uploaded model is loaded. Only internally registered artifacts with successful provenance/runtime checks are used.

Predictions retain uploaded row order. Required numeric source fields are exposed as the same validated numbers used by the model, so charts can compare input values with predictions while identifiers remain preserved. Demand forecasts return one row per product rather than every historical input row. Results provide a preview, prediction CSV, optional prediction time field, the same visualization builder and local/live Sevika evidence. Changing the model, feature mapping, selected records or file hides stale predictions until inference is run again.

Compatibility is not evidence of accuracy on a new population. Validate model performance on representative labelled data before using it for real decisions. Profitability historical ROC-AUC is about 0.4978. Profitability and final-delivery portable conversion fidelity is validated, but parity with the incomplete supplied scored records is unavailable. No upload is automatically retrained, calibrated or joined to built-in datasets.

## Live AI and privacy

Local computed evidence needs no external service. Live Sevika insight generation requires the configured server-side Hugging Face/Groq provider, a deliberate button click and explicit consent for the current upload. The review panel shows the exact request before submission.

The request contains aggregate numeric evidence, anonymous field names (`Measure 1`, `Dimension 1`), anonymous segment labels, registered model identity/threshold and limitations. It excludes raw rows, original column names, filenames, customer/order/product identifiers and original group names. The question text is sent as written: do not include confidential details. The local legend maps anonymous measure names back to uploaded fields, and validated evidence IDs connect the answer to local calculations.

Changing the file, delimiter, encoding or worksheet revokes upload consent and clears derived state. Changing field types/filters/insight choices prevents stale answers from being displayed. Clear uploaded data with the explicit clear control; logout clears the complete session. Uploads and their Excel exports do not enter the shared built-in data/export caches, are not written to project files, and are never passed to the floating global Sevika chat. The floating assistant can explain this workflow; use the inline consented panel for upload-specific AI.

This remains a local showcase with session demo access, not a public multi-tenant service with production authentication. Session privacy and bounded parsing do not replace real authentication, authorization, rate limiting, encrypted persistent storage or an independent security review if deployed publicly.

## Verification

Run `.venv\Scripts\python.exe -m pytest tests/test_uploads.py -q` for parsers, limits, actual registered predictions, incomplete-input rejection, safe exports, consent and anonymization checks. With the loopback preview running, run `.venv\Scripts\python.exe scripts/uploads_browser_qa.py` for isolated Chrome upload workflows, downloads, recovery, mobile themes and a consented synthetic live AI request. Results are recorded in `metadata/uploads_browser_qa.json`.
