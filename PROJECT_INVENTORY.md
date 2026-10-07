# Project inventory

This inventory was captured before the master-prompt implementation. Existing UI and labelled demo mode are preserved.

## Actual data and model assets

| Path | Bytes | Rows | Role / format | Integrity |
|---|---:|---:|---|---|
| `data/cache/final_delivery_conversion_probe.csv` | 14,762 | 32 | csv | Discovered; see JSON |
| `data/cache/profitability_conversion_probe.csv` | 11,063 | 32 | csv | Discovered; see JSON |
| `data/delivery/final/DataCo_Feature_Importance.csv` | 172,379 | 4349 | csv | Discovered; see JSON |
| `data/delivery/final/DataCo_Final_Order_Level_Dataset.csv` | 16,448,000 | 65752 | primary order-level analytical dataset | Verified registry hash |
| `data/delivery/final/DataCo_Final_Scored_Orders.csv` | 344,347 | 2123 | Tuned XGBoost scored test orders | Verified registry hash |
| `data/delivery/final/DataCo_Late_Delivery_Predictions.csv` | 167,922 | 2123 | earlier Random Forest prediction reference | Verified registry hash |
| `data/delivery/final/DataCo_Model_Comparison.csv` | 734 | 4 | csv | Discovered; see JSON |
| `data/delivery/final/DataCo_Risk_Level_Summary.csv` | 184 | 3 | scored risk aggregation reference | Verified registry hash |
| `data/delivery/final/DataCo_Threshold_Analysis.csv` | 7,266 | 62 | csv | Discovered; see JSON |
| `data/delivery/final/evaluation/DataCo_Feature_Importance.csv` | 10,789 | 264 | Random Forest importance | Verified registry hash |
| `data/delivery/final/evaluation/DataCo_Final_Model_Comparison.csv` | 497 | 3 | model evaluation reference | Verified registry hash |
| `data/delivery/final/evaluation/DataCo_Model_Comparison (1).csv` | 477 | 4 | model evaluation reference | Verified registry hash |
| `data/delivery/final/evaluation/DataCo_Model_Comparison.csv` | 477 | 4 | model evaluation reference | Verified registry hash |
| `data/delivery/legacy/d3/Late_Delivery_Feature_Importance.csv` | 172,379 | 4349 | separate line-item model reference | Verified registry hash |
| `data/delivery/legacy/d3/Late_Delivery_Final_Summary.csv` | 307 | 15 | separate line-item model reference | Verified registry hash |
| `data/delivery/legacy/d3/Late_Delivery_Model_Comparison.csv` | 734 | 4 | separate line-item model reference | Verified registry hash |
| `data/delivery/legacy/d3/Late_Delivery_Scored_Orders.csv` | 3,154,402 | 24369 | separate line-item model reference | Verified registry hash |
| `data/delivery/legacy/d3/Late_Delivery_Threshold_Analysis.csv` | 7,266 | 62 | separate line-item model reference | Verified registry hash |
| `data/delivery/legacy/previous_integration/DataCo_Final_Scored_Orders_d7a2a33d1cf5.csv` | 3,154,402 | 24369 | csv | Discovered; see JSON |
| `data/delivery/legacy/previous_integration/DataCo_Risk_Level_Summary_5aedde122d32.csv` | 307 | 15 | csv | Discovered; see JSON |
| `data/demand/final/AccessLogs_Final_Advanced_Forecast.csv` | 373,431 | 2280 | forecast output | Verified registry hash |
| `data/demand/final/AccessLogs_Final_Model_Comparison.csv` | 486 | 3 | mixed comparison reference | Verified registry hash |
| `data/demand/final/AccessLogs_Model_Comparison.csv` | 486 | 3 | csv | Discovered; see JSON |
| `data/demand/legacy/d3/AccessLogs_Final_Advanced_Forecast.csv` | 373,431 | 2280 | duplicate forecast reference | Verified registry hash |
| `data/profitability/final/DataCo_Calibration_Check.csv` | 266 | 5 | training evaluation reference | Verified registry hash |
| `data/profitability/final/DataCo_CatBoost_Tuning.csv` | 525 | 4 | training evaluation reference | Verified registry hash |
| `data/profitability/final/DataCo_Category_Summary.csv` | 2,943 | 45 | training evaluation reference | Verified registry hash |
| `data/profitability/final/DataCo_Feature_Importance.csv` | 11,338 | 238 | training evaluation reference | Verified registry hash |
| `data/profitability/final/DataCo_Final_Project_Summary.csv` | 259 | 14 | training evaluation reference | Verified registry hash |
| `data/profitability/final/DataCo_Final_Scored_Orders.csv` | 4,816,291 | 27078 | scored line items | Verified registry hash |
| `data/profitability/final/DataCo_High_Loss_Risk_Orders.csv` | 1,099 | 5 | training evaluation reference | Verified registry hash |
| `data/profitability/final/DataCo_Market_Summary.csv` | 241 | 3 | training evaluation reference | Verified registry hash |
| `data/profitability/final/DataCo_Model_Comparison.csv` | 760 | 6 | training evaluation reference | Verified registry hash |
| `data/profitability/final/DataCo_Shipping_Summary.csv` | 276 | 4 | training evaluation reference | Verified registry hash |
| `data/profitability/final/DataCo_Threshold_Analysis.csv` | 4,648 | 62 | training evaluation reference | Verified registry hash |
| `data/profitability/final/DataCo_Train_Test_Drift.csv` | 1,120 | 15 | training evaluation reference | Verified registry hash |
| `models/delivery/d3/DataCo_Final_Delivery.json` | 547,328 | - | json | Discovered; see JSON |
| `models/delivery/d3/DataCo_Final_Delivery_Preprocessor.joblib` | 110,605 | - | joblib | Discovered; see JSON |
| `models/delivery/d3/Final_Late_Delivery_Model.pkl` | 564,421 | - | separate line-item model | Verified registry hash |
| `models/delivery/DataCo_Late_Delivery_Model.pkl` | 7,031,579 | - | serialized model; not executed by importer | Verified registry hash |
| `models/delivery/DataCo_Tuned_XGBoost.json` | 819,876 | - | json | Discovered; see JSON |
| `models/delivery/DataCo_Tuned_XGBoost.pkl` | 599,153 | - | serialized model; not executed by importer | Verified registry hash |
| `models/delivery/DataCo_Tuned_XGBoost_Preprocessor.joblib` | 9,937 | - | joblib | Discovered; see JSON |
| `models/demand/AccessLogs_Final_XGBoost_Demand_Model.json` | 819,433 | - | json | Discovered; see JSON |
| `models/demand/AccessLogs_Final_XGBoost_Demand_Model.pkl` | 666,138 | - | serialized demand model | Verified registry hash |
| `models/demand/AccessLogs_Final_XGBoost_Demand_Preprocessor.joblib` | 7,809 | - | joblib | Discovered; see JSON |
| `models/profitability/DataCo_Final_Trained_Model.pkl` | 1,486,850 | - | trained model | Verified registry hash |
| `models/profitability/DataCo_Profitability.json` | 2,197,224 | - | json | Discovered; see JSON |
| `models/profitability/DataCo_Profitability_Preprocessor.joblib` | 10,630 | - | joblib | Discovered; see JSON |
| `notebooks/delivery/d3/Welcome_To_Colab.ipynb` | 1,633,988 | - | training provenance | Verified registry hash |
| `notebooks/delivery/Welcome_To_Colab (2).ipynb` | 2,064,886 | - | training provenance | Verified registry hash |
| `notebooks/demand/Welcome_To_Colab (1).ipynb` | 1,179,386 | - | training provenance | Verified registry hash |

## Schema and provenance

Exact columns, types, row counts, missing cells, duplicates and hashes are in `metadata/master_inventory.json`.
Delivery: order-grain primary records and a scored test subset. Demand: product/day web visits, not purchased units. Profitability and final delivery: supplied line observations, not interchangeable with delivery orders.
Portable model registries define input order, preprocessors, artifact hashes and decision thresholds. No uploaded serialized model may execute.

## Missing assets and limitations

- Missing: `DataCoSupplyChainDataset.csv`.
- Missing: `DescriptionDataCoSupplyChain.csv`.
- Missing: `tokenized_access_logs.csv`.
- Profitability/final-delivery scored files omit required training inputs; real-row source-score parity is unavailable. Existing conversion probes are test evidence, never business data.
- Original raw access logs, description dictionary, calibrated future intervals, route endpoints and per-record SHAP evidence are not supplied.

## Implementation gaps identified before edits

- Remove credentials and unnecessary personal information before upload previews, charts, exports and AI context.
- Add Parquet, richer profiling and automatic compatibility checks for all four existing model contracts.
- Extend chart boards to ten slots, portable configuration restoration and per-card controls.
- Expose registered analytical sources and validate any requested cross-source joins.
- Add deterministic uploaded-data questions, momentum/acceleration and investigation evidence.
- Reconcile real data, run regression/browser/security/performance checks and issue an evidence-backed audit.

## Security boundary

Private .env values are excluded. Dataset passwords are never authentication credentials. Session-only demo access is not production authentication. External AI receives only consented anonymous numerical summaries.
