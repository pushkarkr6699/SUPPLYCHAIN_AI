# Security notes

## Current application boundary

- The application is configured for local loopback use and deterministic demo data. `DEMO_MODE` is `True`; no operational dataset, model artifact, external AI provider, or real identity provider is connected.
- Demo sign-in is a UI preview, not an authorization boundary. Never use it with confidential data. A production deployment must replace it with a verified authentication provider and server-side authorization.
- Do not commit `.env`, `.streamlit/secrets.toml`, credentials, access tokens, private keys, or private datasets. `.env.example` is a list of blank integration placeholders only.
- `services/mock_data.py` creates synthetic records in memory. Do not add silent demo fallback to a future production provider. Return an explicit unavailable/error state if live data cannot be served.
- `services/query_engine.py` accepts in-memory DataFrames only and disables DuckDB external access. Keep query values parameterized and never execute SQL or Python supplied by a user or Copilot.
- Copilot currently uses deterministic application code and supported intents. Any future provider/tool integration must validate inputs, constrain tool scope, preserve evidence/provenance, and fail closed for unsupported questions.
- CSV/Excel exports add formula guards and a demo provenance column. Before exposing real records, review row-level authorization, export auditing, data minimization, and retention requirements.

## Before handling real data

1. Review and approve the dataset/model artifact manifest, access permissions, schemas, row grain, retention, and data classification.
2. Add secrets through the deployment secret manager or Streamlit secrets; never put values in source or committed environment files.
3. Replace session-only demo access with authentication and authorization.
4. Add provider validation, safe query parameterization, audit logging, and integration tests.
5. Run a dedicated secret scanner and dependency/security review on the deployment revision.
6. Keep profitability and combined-risk routes unavailable until their independent artifacts, permissions, validation, and join coverage are approved.
