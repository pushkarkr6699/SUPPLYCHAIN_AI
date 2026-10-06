# Local showcase security

## Current application boundary

- The application binds to `127.0.0.1`. The verified provider connects supplied historical delivery and demand CSVs and runs registered trained models after parity validation. Demo mode remains selectable. No real identity provider is connected. Optional Hugging Face narration is implemented and requires a locally configured API key. This is a single-operator classroom release, not public multi-user production.
- Demo sign-in is a UI preview, not an authorization boundary. Never use it with confidential data. A production deployment must replace it with a verified authentication provider and server-side authorization.
- Do not commit `.env`, `.streamlit/secrets.toml`, credentials, access tokens, private keys, or private datasets. `.env.example` is a list of blank integration placeholders only.
- `services/mock_data.py` creates synthetic records in memory. Do not add silent demo fallback to a future production provider. Return an explicit unavailable/error state if live data cannot be served.
- `services/query_engine.py` accepts in-memory DataFrames only and disables DuckDB external access. Keep query values parameterized and never execute SQL or Python supplied by a user or Copilot.
- Copilot currently uses deterministic application code and supported intents. Any future provider/tool integration must validate inputs, constrain tool scope, preserve evidence/provenance, and fail closed for unsupported questions.
- CSV/Excel exports neutralize formula prefixes, including leading whitespace, tabs and carriage returns, and preserve source provenance. Numeric values remain numeric. Downloads are generated in memory. Before public deployment, add row-level authorization, export auditing and retention controls.

## Model, file and input boundaries

Only fixed, hash-registered model/preprocessor paths are accepted. Original artifact hashes, portable export hashes, named feature schemas, pinned runtime versions and successful parity reports gate inference. Uploaded or caller-selected pickle files are unsupported. Pickle/joblib loading can execute code: registration establishes identity with the supplied files, not safety of an untrusted model. Keep the registry and local artifacts under administrator control.

CSV uploads are in-memory data buffers and cannot specify executable code, SQL or model paths. Delivery features and demand histories are validated before scoring. Demand requires finite nonnegative visits, complete dimensions and at least 15 consecutive daily rows per product. Administrator-configured `.env` dataset paths are trusted configuration; they are not browser-entered paths. Streamlit's upload-size limit is not a complete resource-exhaustion defense.

Copilot has no shell, code interpreter or filesystem write tool. Its optional live Hugging Face mode sends the user question and computed aggregate evidence only on explicit request; raw dataset rows and group identifiers stay local. Unsafe execution/deletion/secret/threshold-change requests are refused before analytics intent routing. Fixed DuckDB queries use in-memory frames with external access disabled. Error panels show controlled unavailable/invalid-input states without raw tracebacks or absolute paths. Diagnostics requires a developer preference and is hidden in presentation mode; the preference is not authorization. Operator logs may contain technical details and must remain private.

`.env`, Streamlit secrets, source CSV/model directories, backups, environments, logs and temporary browser downloads are Git-ignored. Original notebooks are training provenance and may contain private dataset examples; do not distribute these artifacts without reviewing their contents. Temporary QA outputs stay in ignored `tmp/` and are never application routes or runtime configuration.

## Executed audit and reproducibility

Evidence is in [QA_REPORT.md](QA_REPORT.md), `metadata/security_audit.json` and `metadata/dependency_audit.json`. Checks cover runtime AST inspection, tracked-file credential patterns, ignored secret stores, loopback binding, model-path traversal, disabled DuckDB external reads, malicious Copilot requests, corrupted/missing inputs and spreadsheet formula payloads.

The initial dependency audit found advisories affecting pip 25.1.1. Updating the toolchain to pip 26.2.1 resolved the reported findings; model dependency pins were preserved. The subsequent installed-environment audit found no known vulnerabilities. `pip check` passed. These checks are point-in-time evidence, not a guarantee against future or undisclosed vulnerabilities. Regex scanning cannot establish absence of every possible credential; this is not an independent penetration test.

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-security.txt
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m pip_audit --format json --output metadata/dependency_audit.json
.\.venv\Scripts\python.exe scripts/security_audit.py
.\.venv\Scripts\python.exe -m pytest -q
```

Revalidate model parity whenever registered sources, models or inference dependencies change. Never remove validation gates or change thresholds to pass QA.

## Before public deployment

1. Review the dataset/model manifest, access permissions, schemas, row grain, retention and data classification. Historical data is not a refreshed feed.
2. Add secrets through the deployment secret manager or Streamlit secrets; never put values in source or committed environment files.
3. Replace session-only demo access with authentication and authorization.
4. Add durable per-user sessions, audit events, TLS, upload quotas, controlled artifact ingestion and monitoring.
5. Run a dedicated secret scanner and dependency/security review on the deployment revision.
6. Keep independent dataset grains and model thresholds separate. Profitability scores are line items; cross-risk uses a validated order-level aggregate join and does not produce a joint-model probability.

## Optional live AI boundary

The API key stays server-side in ignored `.env`, the server environment. Requests use a fixed HTTPS Hugging Face router endpoint, a 25-second timeout, zero automatic retries and a strict structured response schema. Evidence references are checked against local facts; generated interpretations still require review. User-entered questions are sent as written, so the UI discloses that transfer. Failed or unavailable requests show a controlled error. Changing filters or the question invalidates the previous answer. No model-generated code, SQL or tool instructions are executed.

Profitability and final delivery portable conversions were compared with their original fitted pipelines on 32 synthetic probes each. This establishes conversion fidelity, not parity with the supplied scored records, whose training inputs are incomplete. Registered preprocessors are trusted local artifacts, never browser uploads.

Hugging Face narration uses the OpenAI SDK against `https://router.huggingface.co/v1`, with `HF_TOKEN` server-only and `HF_MODEL` defaulting to `openai/gpt-oss-120b:groq`. Every action is explicit. Prompts are capped at 24,000 bytes and output at 2,048 tokens. Anonymous numeric aggregates and user questions are disclosed before transfer; provider retention and account credits follow Hugging Face and the selected provider policies. No unlimited free usage is promised. Configuration/status objects, upstream errors and rejected responses never expose the token.
