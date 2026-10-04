# Dataset handoff

Put approved files in the matching `final/` folder and update `.env` paths if their names differ. Keep one row per documented grain and retain the original column names until the adapter mapping is reviewed. Do not place secrets in these files.

Delivery inputs: scored orders plus optional threshold analysis, model comparison, feature importance and summary CSVs under `data/delivery/final/`. Demand inputs: product/day forecast CSV and optional model comparison under `data/demand/final/`. Put only genuinely different historical versions under `data/delivery/legacy/`. The currently supplied files did not include the separate order-level training dataset or a separate `DataCo_Late_Delivery_Predictions.csv`; those remain optional inputs and are not fabricated from the scored file.

Send or copy the CSV files into these folders in the workspace, or provide their full local paths in `.env`. Include a short note with the target definition, row grain/key, date/time meaning, train/validation/test split, metric provenance, and whether predictions are already scored. Include a model file only when requested; this UI's safe provider will not deserialize pickle files.
