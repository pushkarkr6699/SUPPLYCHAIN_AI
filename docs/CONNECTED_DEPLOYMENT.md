# Connected data locally and on the hosted server

Connected analytics is now the default (`SUPPLYCHAIN_PROVIDER=verified`). Explicit `SUPPLYCHAIN_PROVIDER=demo` preserves the labelled synthetic demonstration. Authentication and datasets are separate settings: session-only access does not mean synthetic data. No production identity provider is claimed.

The real-data landing page contains aggregate counts and a forecast series derived from registered files. It never shows individual customer/order records. The workspace keeps delivery orders, product/day web visits, profitability lines and the final-delivery experiment separate. Missing files show unavailable states, never replacement synthetic records.

## Local preview

Run `run.ps1`, or use the Python environment to run `streamlit run app.py`. Open http://localhost:8501 and choose **Open platform**. The supplied profitability records are available in Profitability Intelligence, Overview, Model Intelligence, Comparison/Visualization Studio, Insights, Alerts, Copilot/Sevika, explorers, quality, threshold, explanation, drift and exports. Historical re-scoring still requires the missing original trained inputs; compatibility alone does not establish accuracy.

## Private hosting assets

Git deliberately excludes source data, model binaries, secrets and private notebook originals. Pushing application changes cannot install those assets on Render.

A prepared private bundle is at `backups/deployment/supplychain-connected-assets.zip`. Its companion `bundle_manifest.json` contains the pinned SHA-256. The bundle includes 48 exact registered data/model/portable assets; it excludes credentials, application code and notebook outputs. Keep it private. Do not add it to Git or publicly host it.

To rebuild it:

```powershell
.\.venv\Scripts\python.exe scripts/package_connected_assets.py
```

The hosting service must be configured with:

- Build: `pip install -r requirements.txt -r requirements-inference.txt`
- Start: `python scripts/launch_hosted.py`
- `SUPPLYCHAIN_PROVIDER=verified`
- `SUPPLYCHAIN_ASSET_BUNDLE_URL`: a private HTTPS download URL accessible by the server, configured in server-only environment settings.
- `SUPPLYCHAIN_ASSET_BUNDLE_SHA256`: the checksum in the private bundle manifest.
- Existing private AI provider settings, if live AI is needed and provider credits are available.

The launcher downloads without logging the URL, validates the pinned archive and every member against repository hashes, rejects extra/missing files, links, excessive sizes and changed existing assets, then validates all four fixed model adapters in the hosted runtime. It never accepts arbitrary user-uploaded models. A validation failure prevents a false inference-ready claim.

No private hosting/storage account connection is available to the coding agent. The bundle has been prepared locally; downloading it into Render remains blocked until the account owner supplies the private storage/environment configuration. The hosted connected release must then be checked separately. A successful local test is not a hosted deployment test.

## Current limitations

Profitability uses supplied line observations and precomputed probabilities. Its historical ROC-AUC is approximately 0.4978; this limitation remains visible. New predictions require the complete fixed feature contract. Profitability/final-delivery scored files alone cannot supply omitted trained inputs.

Live AI previously failed because Hugging Face inference credits were exhausted. Local numerical insights and Sevika analytical help remain available. Newly uploaded data still needs its own anonymous-summary consent before external AI.
