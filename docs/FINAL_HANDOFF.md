# Connected dataset/model handoff - 6 October 2026

The existing UI and original demo mode are preserved. The ignored `.env` selects verified mode; `.env.example` defaults to demo. Restart Streamlit after changing the provider.

## Connected capabilities

| Source | Grain / saved threshold | Connected use |
| --- | --- | --- |
| Main delivery | 65,752 unique orders; 2,123 scored; 0.35 | Existing delivery/order/geography/report workflows and trained scoring |
| Demand | 2,280 product/base-day observations | Next-day web-visit analytics and trained forecasts with complete history |
| Profitability | 27,078 lines / 14,593 orders; 0.20 | Comparisons, calibration, diagnostics, historical drift, thresholds, trained complete-input uploads, reports and exports |
| Final delivery | 24,369 observations / 13,670 orders; 0.56 | Separate final scores, diagnostics, importances, thresholds, trained complete-input uploads, comparison and data tools |
| Cross-risk | Profitability aggregated once per Order; shared identity verified | Coverage and descriptive delivery/profitability comparison; no joint model |
| Optional live AI | Computed aggregate evidence plus user question | Explicit dashboard, comparison, profitability/final delivery, Insight Center and Copilot insights |

All **41 original artifacts** are SHA-256 registered. The eight newly supplied DATACO FINAL files exactly match existing d3 imports; registry aliases record both locations. Originals and saved thresholds remain unchanged. Model conversions preserve fitted preprocessing and classifiers without retraining.

Main delivery reproduced all 2,123 supplied scores within 2.97e-8 probability. Demand reproduced 1,216 rows with complete history within 1.53e-5 visits. Profitability and final delivery each reproduced their original pipeline on 32 synthetic conversion probes within 2.68e-8 and 2.63e-8 probability. Their scored CSVs omit full inputs, so scored-row inference parity is unavailable.

## Preview

Run `./run.ps1` in the project and open **http://127.0.0.1:8501 -> Open platform**.

- Profitability: **Additional intelligence -> Profitability Intelligence**.
- Final delivery: **Delivery Intelligence -> Explore final delivery line-item experiment**, also under Model Intelligence's Delivery tab.
- Flexible dataset comparisons: **Comparison Studio**, choose the source and actual fields.
- Reports: Profitability and Cross-Risk are connected; final delivery exports include its own PDF.
- Live AI: privately configure `HF_TOKEN` in ignored `.env`, refresh, then **Settings -> Copilot -> Check live AI connection**. `HF_MODEL` defaults to `openai/gpt-oss-120b:groq`.

New profitability and final delivery predictions require all 23 and 31 named training features. Download the templates; absent inputs are refused. CSV uploads stay in memory and never overwrite registered datasets or models. Existing saved scores remain usable without those inputs. Uploaded models are never loaded.

Set `SUPPLYCHAIN_PROVIDER=demo` in `.env` and restart to return to the original synthetic demo. Demo sign-in is session access, not production authentication.

## Validation and restore

Run `.venv/Scripts/python.exe -m pytest -q`. Integration, source reconciliation, functional, browser and security scripts are under `scripts/`; current results are in `QA_REPORT.md` and `metadata/`. PDF reports were rendered and reviewed; a footer-only final-page defect was fixed. External AI remains unverified until a key is configured; mocked API tests cover generated-response and stale-result behavior.

Source assets are Git-ignored. Restore CSV/model/notebook assets together with registries and portable exports from the release archive in `metadata/release_backup_manifest.json`; earlier backups are retained. Credentials are excluded from archives and Git.

## Material limits

Profitability ROC-AUC is about 0.4978, balanced accuracy 0.50, and all saved labels are profitable at threshold 0.20. The app surfaces this weakness. Final delivery ROC-AUC is about 0.75356; its 1,757 exact repeated observations are retained because no unique source line key was supplied. Conversion fidelity is separate from real-world model performance.

Cross-risk summaries are not calibrated order-profitability or combined-model probabilities. SHAP, operational drift, inventory-on-hand and refreshed feeds are absent. Source demand bounds labeled 90% cover about 67.63% of supplied rows. Main delivery threshold selection used its test predictions. Source history ends January 2018.

Public deployment requires real identity/authorization, persistent storage, hosting, data refresh and monitoring. Saved views, alert workflows and conversations remain session-scoped. See `SECURITY.md` and [detailed integration notes](PROFITABILITY_INTEGRATION.md).
