# Final dataset and trained-model handoff

The existing UI and demo provider are preserved. The ignored local `.env` selects verified data; `.env.example` defaults to demo. Restart Streamlit after changing providers.

## Delivered

All 26 allowlisted artifacts from d1/d2/d3 were imported with SHA-256 verification. Original source files and pickles remain unchanged. Earlier conflicting imports were archived under `data/delivery/legacy/previous_integration/`. Incomplete downloads are excluded. Registries record paths, roles, hashes and duplicate versions.

Delivery uses d1's 65,752 unique orders with 2,123 one-to-one matching final scores. Missing scores remain null. Delivery, orders, geography, threshold analysis, comparison, quality, reports and downloads use supplied data. Active threshold is 0.35; d3's 0.56 belongs to a separate line-item experiment. Random Forest feature importance is labeled as baseline, not tuned XGBoost explanation.

Demand uses d2's 2,280 product/base-day observations across 76 products. Forecasts predict next-day web visits. Independent filters keep delivery and demand grains separate. Copilot, insights and alerts use source-aware deterministic analytics. Exports retain provenance and missing predictions.

Both Colab models were converted in isolated Linux to native XGBoost JSON with their same fitted preprocessing. No model fitting occurred. Windows delivery inference reproduced every supplied scored order within 2.97e-8 probability and all labels matched. Demand reproduced all 1,216 rows with complete prior history within 1.53e-5 visits; the first 14 base dates were excluded. Hash and runtime checks disable changed artifacts until revalidation.

## Use and preview

```powershell
cd D:\SUPPLYCHAIN_AI
.\.venv\Scripts\python.exe -m pip install -r requirements.txt -r requirements-inference.txt
.\run.ps1
```

Open http://127.0.0.1:8501 and use the existing demo-session access flow. That flow grants local session access; verified mode still reads your datasets.

- Scenario Lab: select an order and compare a shipping input, or upload CSV rows with the 26 named training features shown in the page. Estimates are not causal effects. Profit inputs must be available at scoring time; training provenance does not establish pre-fulfillment availability.
- Demand Intelligence: expand Run trained next-day web-visit forecast. Use supplied history or upload `DateOnly,Product,Category,Department,Visits`, with at least 15 consecutive days per product including zero-visit days. Product category/department must remain stable. Current and earlier visits are inputs; future targets are never inputs. Output shows both base date and forecast date. New history receives point forecasts without reused source intervals.
- Uploaded CSVs are processed in memory and do not replace registered datasets. Uploaded models are never loaded.
- Set `SUPPLYCHAIN_PROVIDER=demo` in `.env` and restart to return to the original demo.

## Verify

```powershell
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider
.\.venv\Scripts\python.exe -m services.inference_service --validate
.\.venv\Scripts\python.exe -m services.demand_inference
.\.venv\Scripts\python.exe scripts\verify_integration.py
```

Actual-artifact QA verifies 26 hashes, 27 routes and both trained prediction controls. Results are in `metadata/integration_qa.json`, `metadata/inference_validation.json` and `metadata/demand_inference_validation.json`. Browser QA uses isolated headless Chrome and saves previews under `tmp/screenshots/verified/`. Models and CSVs are ignored by Git and must be backed up separately alongside registries and portable exports. The supplied originals remain at `D:\IBM Prac`.

Final regression result: **77 passed, zero failed**. Actual-data interactions also passed dataset switching, delivery/demand Copilot questions and both PDF reports. Desktop, dark and mobile browser captures were reviewed. A local dataset/model/notebook ZIP backup was integrity-checked under `backups/`; its location and SHA-256 are recorded in `metadata/backup_manifest.json`.

## Remaining production requirements

This is a locally working dataset/model platform. Public production deployment still needs real identity/authorization, persistent multi-user storage, hosting, operational refresh, monitoring and private-artifact backups. Current login, saved views, alert workflows and conversations remain session-only. Copilot does not call an external LLM.

Profitability prediction needs an approved model/dataset; recorded delivery Sales/Profit are historical analytics. Cross-risk needs a validated shared grain/key. Drift needs reference/current windows. Actual SHAP and demand feature-importance outputs are absent. Inventory-on-hand is absent.

Delivery threshold was selected on its test predictions, so evaluation is retrospective. Source demand bounds named 90% cover about 67.63% of supplied rows. History ends January 2018; current predictions need current input data. These limitations are explicit in the UI rather than replaced by invented outputs.
