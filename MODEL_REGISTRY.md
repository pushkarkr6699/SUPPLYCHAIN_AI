# Model registry

Original fitted artifacts are registered, hash checked and executed through fixed portable XGBoost exports plus their original preprocessors. Uploaded models/code are never deserialized. No retraining occurred.

| Model | Original artifact | Inference | Threshold / target | Validation |
| --- | --- | --- | --- | --- |
| delivery_d1_tuned_xgboost | models/delivery/DataCo_Tuned_XGBoost.pkl | True | 0.35 | validated |
| delivery_d1_random_forest_baseline | models/delivery/DataCo_Late_Delivery_Model.pkl | False | reference | reference_only |
| demand_d2_xgboost | models/demand/AccessLogs_Final_XGBoost_Demand_Model.pkl | True | next-day web visits | validated |
| delivery_d3_line_item_xgboost | models/delivery/d3/Final_Late_Delivery_Model.pkl | True | 0.56 | conversion_fidelity_validated |
| profitability_tuned_xgboost | models/profitability/DataCo_Final_Trained_Model.pkl | True | 0.2 | conversion_fidelity_validated |

Only the four fixed active adapters accept compatible model inputs. The Random Forest baseline and legacy models remain reference/provenance artifacts. Feature importance is attributed to its actual model.

Exact feature lists, thresholds and positive-class semantics: [model_registry.json](metadata/model_registry.json), the portable registries and the per-model validation JSON.
