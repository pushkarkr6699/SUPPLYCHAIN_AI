# Model health and validation

| Adapter | Validation rows | Supplied real-score parity | Result |
| --- | --- | --- | --- |
| delivery | 2123 | True | validated |
| demand | 1216 | True | validated |
| profitability | 32 | False | validated |
| delivery_final | 32 | False | validated |

Delivery: 2,123 real scored orders reproduced. Demand: 1,216 real registered history/forecast rows reproduced. Profitability and final delivery: 32 conversion probes each verify portability only, with maximum probability differences below 3e-8. Probes are test artifacts, never connected business records.

Historical row-level parity for profitability/final delivery is **not verified** because the supplied scored CSVs omit required original model inputs. Compatibility and conversion fidelity do not establish predictive quality.

The supplied profitability evaluation is weak (ROC-AUC about 0.4978); its fixed threshold is 0.20. Delivery d1 threshold 0.35 and final-delivery threshold 0.56 remain separate. Threshold sensitivity is analytical, never a silent production threshold change.

Demand estimates web visits, not purchases. Source-provided forecast bounds are displayed as supplied; no calibrated interval is invented for new inference. Per-record SHAP artifacts and validated route coordinates are unavailable.

Evidence: [master_data_qa.json](metadata/master_data_qa.json), [model_registry.json](metadata/model_registry.json), and the dedicated inference validation reports.
