# Hugging Face AI integration - 2026-10-06

## Configuration and implementation

The application uses Hugging Face Inference Providers through the fixed HTTPS endpoint `https://router.huggingface.co/v1`, the OpenAI Python SDK `3.24.0`, and `openai/gpt-oss-120b:groq`. Public Hugging Face provider mapping showed the Groq conversational route available; actual requests confirmed the model responds. No OpenAI API credential or direct OpenAI endpoint is required.

Keep `HF_TOKEN` private in the ignored local `.env` or server environment. `HF_MODEL` optionally overrides the default. Environment values override `.env`. `.env.example` contains a blank token. The existing allowlisted local configuration loader is preserved; no dotenv dependency or duplicate AI SDK was installed.

`services/ai_provider.py` owns server-side authentication, routing, timeout, request bounds and sanitized failures. `services/ai_narration.py` preserves the analyst response schema and validates evidence references. Existing views call that service; no routes, dataset schemas or trained model contracts were replaced. The automatic startup API experiment was removed to prevent calls on every Streamlit rerun. A private ignored backup preserves that prior file.

## Features and validation

All nine AI entrypoints passed controlled response, error and result lifecycle checks: Executive Overview, Delivery Intelligence, Demand Intelligence, Profitability, Final Delivery, Insight Center, Copilot Live AI, Comparison Studio and Settings connection check. Comparison Studio, Insight Center and Copilot were also exercised on delivery, demand, profitability and final-delivery data. These controlled tests deliberately mock transport; they are not proof of a live call on the supplied datasets.

Actual external verification passed:

- Capital of France: GPT-OSS through Hugging Face/Groq returned a valid answer identifying Paris.
- Settings connection check: actual browser -> Streamlit -> central AI service -> Hugging Face -> validated JSON -> browser success. Its payload is synthetic connection evidence, with no dataset sent.
- Executive Overview: actual synthetic demo fixture aggregates -> Hugging Face -> validated insight display and downloaded JSON brief. An ordinary rerun reuses the cached answer.

The complete regression suite passed **188 tests, zero failed**, with 13 existing dependency/date-validation warnings. All **28 routes** were separately exercised with verified registered datasets. **41 source artifact hashes** matched. Delivery/demand trained predictions, local Copilot, dataset switching and PDFs passed. Profitability and cross-risk PDFs and all four comparison source paths passed functional checks. Browser checks and security evidence are recorded separately under `metadata/`.

## Security and request limits

The token stays in server-side configuration and the upstream authentication header. Browser HTML/Streamlit-frame scans found no credential; no direct browser requests went to Hugging Face/Groq. Tracked/new-file scans and local logs had zero token findings. `.env` is Git-ignored, `.env.example` has a blank token, and CORS and XSRF protection remain enabled.

Requests are explicit, capped at 24,000 prompt bytes and 2,048 output tokens, with a 25-second timeout and zero automatic retries. Answers are scoped to dataset, filters, question and provider/model; changing the AI model invalidates comparison narration independently of trained predictions. There is no silent mock fallback and no claim of unlimited free usage. Provider retention, available credits and account quotas apply.

Tests cover missing credentials, rejected credentials, quota/rate limits, unavailable model/provider, connection failure, timeout, empty/refused/truncated responses, malformed JSON, unexpected fields, invalid evidence references and credential echoes. Errors leave local analysis available. Generated code, SQL and tools are never executed.

## Remaining live verification

Automatic approval review rejected exporting the supplied-business dataset aggregates, even after local checks proved they contain only anonymous numerical evidence. The user has been asked for explicit approval to transfer these summaries to Hugging Face/Groq. **Until that approval arrives, live calls using delivery, demand, profitability and final-delivery supplied data remain unverified.** No workaround exports that data. The configured UI remains available; controlled local tests and synthetic live tests are distinguished above.

This preserves the existing local showcase scope. Session/demo access is not production identity or multi-user authorization. Profitability/final-delivery source-score parity still requires unavailable original complete model inputs; synthetic conversion probes establish conversion fidelity only. See `SECURITY.md` and `docs/PROFITABILITY_INTEGRATION.md`.

## Start and reproducible checks

From `D:\SUPPLYCHAIN_AI`:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py --server.address=127.0.0.1 --server.port=8501
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe scripts/hf_ui_qa.py
.\.venv\Scripts\python.exe scripts/hf_browser_qa.py
```

The browser harness requires the local preview to be running and makes one live synthetic Settings connection request. `--demo-operation` targets a separately launched synthetic demo server on port 8502. The UI harness uses controlled transport only and never exports supplied data.

The subsequent security recheck added explicit provider-refusal and JSON-escaped credential-echo tests. All **188 tests** passed, including these safeguards. `scripts/hf_live_dataset_qa.py` now provides an offline preflight for all four supplied sources (zero network calls by default), with an explicit execution mode for the remaining approved live tests. The current key is configured; the outstanding supplied-data test is a transfer-approval constraint, not a missing `OPENAI_API_KEY`.

The latest public dependency advisory scan checked 92 installed packages and found no known vulnerabilities. The final private-token scan checked 247 project files with zero findings; these are point-in-time checks, not an independent penetration test.

After the refusal/escaped-credential fixes, both the actual Settings connection and synthetic Overview insight generation passed again. The browser harness now waits for the actual generated result or controlled error, avoiding a premature check of the previous settled UI. The synthetic brief download, cached rerun and browser credential checks passed. Supplied-data live requests still await explicit transfer approval.
