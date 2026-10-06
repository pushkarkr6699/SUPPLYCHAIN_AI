# Profitability and final delivery integration — 6 October 2026

The original demo, order-level delivery and web-visit demand workflows remain available. These integrations use separate registered datasets and trained models.

## Profitability

All 15 supplied files from `D:\IBM Prac\DATA CO PRROFITABILITY` were copied and SHA-256 verified. CSV/TXT references live in `data/profitability/final/`; the original model and portable exports live in `models/profitability/`.

The scored dataset contains **27,078 line items across 14,593 unique orders**, dated June 2017–January 2018. An Order ID is not a unique row key. `Profitability Row` is a stable local source-row reference. Recorded profit describes the supplied observations, not independently established complete-order totals.

Open **Additional intelligence → Profitability Intelligence** for group comparisons, time trends, risk labels, diagnostics, calibration, feature importance, historical drift, exploratory thresholds, trained CSV inputs, AI evidence and exports. The same dataset is available in Comparison Studio, Copilot, Insight Center, data/quality/explorer/download tools and profitability reports. Order details show matching supplied profitability lines.

The operating threshold is **0.20**. All supplied rows predict profitable at that threshold. Actual profitable prevalence is 80.689%; balanced accuracy is 50%, and ROC-AUC is about **0.4978**. Accuracy largely reflects class prevalence. These results do not establish a useful future risk-ranking model. Risk bands are separate: below 0.40 is High Loss Risk, below 0.70 is Moderate Profitability, and at least 0.70 is High Profit Probability.

Market/category/shipping summaries, calibration bins and the five-row high-loss shortlist reconcile with supplied observations. All **238 transformed feature importances match the model**. Historical train/test drift means reconcile; constant-zero baselines retain undefined relative changes. Comparison and tuning references are labeled separately because their values differ from final scored rows and a matching profitability notebook was not supplied.

The original fitted model was exported in Linux to native XGBoost JSON and its fitted preprocessor. Windows inference matched 32 deterministic synthetic conversion probes within **2.68e-8** probability. No fitting occurred. This validates conversion fidelity only. The scored CSV omits required model features, so reproducing its saved scores from complete inputs is unavailable.

For new predictions, download the input template and provide all **23 named training features**. Missing columns, non-finite numbers, invalid discount/quantity/price values and missing text are rejected. Uploads stay in memory and never replace registered datasets or models.

## Cross-risk

Profitability observations are grouped once per Order before joining the main delivery dataset. All **14,593** profitability order IDs match on Order, date, market and country. The left join retains every main delivery order; unmatched profitability values remain missing. Mean line profitability and maximum line loss probability are descriptive summaries. They are neither calibrated order probabilities nor a combined model. Demand is not joined.

## Final delivery experiment

The eight files supplied under `D:\IBM Prac\DATACO FINAL` are byte-for-byte identical to the earlier registered d3 artifacts. They are reused with new source aliases; original files and the main model are unchanged.

Open **Delivery Intelligence → Explore final delivery line-item experiment** or **Model Intelligence → Delivery → Inspect final delivery experiment**. Independent scores, grouped graphs, diagnostics, threshold exploration, complete-input trained prediction, optional AI and downloads are connected. Comparison Studio, Data Explorer, Data Quality and Universal Explorer offer this separate source.

There are **24,369 exported line observations across 13,670 orders**. The source includes **1,757 exact repeated observations**; these are retained because no unique source line key was supplied. Counts always describe exported observations. The saved threshold is **0.56**, and risk bands use **0.41/0.71** boundaries, corroborated by the previously registered notebook's threshold ± 0.15 rule. Main order-level delivery remains at **0.35** with its own bands.

Recomputed final-score metrics match the summary: accuracy 69.490%, balanced accuracy 71.205%, ROC-AUC 0.75356, PR-AUC 0.81955 and MCC 0.44111. The supplied comparison and threshold tables are separate references. All **4,349 transformed feature importances match the final model**.

The original pipeline was portably exported without fitting. Windows matched 32 synthetic probes within **2.63e-8** probability. New predictions require all **31 training inputs**, including numeric categorical `Product Card Id`. The 14-column scored CSV cannot provide those inputs; its saved probabilities remain usable. Synthetic probe validation is not scored-row parity or predictive-quality validation.

## Live AI setup

Set `HF_TOKEN` privately in the ignored project `.env`; optionally set `HF_MODEL` to the supported model you wish to use. The current default is `openai/gpt-oss-120b:groq`. Never paste a secret into chat or commit it. Refresh and open **Settings → Copilot → Check live AI connection**, then explicitly generate insights in the desired view.

The request sends the user's question and locally computed aggregate facts. Dataset rows and identifying group labels stay local; segment names are anonymized. The structured response cites checked evidence IDs. No AI-generated code executes. Changed data, filters or questions invalidate prior output. Local facts remain available without a key.

The external request has not been verified in this workspace because no API key was configured at the last check. The generated-response UI lifecycle was tested with a mocked API; that is separate from a successful external request.

## Evidence

See `metadata/profitability_data_validation.json`, `profitability_inference_validation.json`, `profitability_functional_qa.json`, `final_delivery_data_validation.json`, `final_delivery_inference_validation.json` and the current browser/security reports. Source data, portable models and backups are Git-ignored and must accompany a local restore.
