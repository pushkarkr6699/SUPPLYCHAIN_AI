# Sevika - contextual supply-chain assistant

Open http://127.0.0.1:8501, choose **Open platform**, and click **Sevika** at the bottom right. The same assistant is available on the landing and login pages, where only public product help is loaded.

## Using the assistant

1. Choose the dashboard page and filters first. Sevika reads that selected dataset locally, including the selected order on order/scenario pages.
2. Open **Questions for this page**, choose **Explore a field**, or type your own question. Ask for totals, means, group comparisons, score coverage, model limitations or workflow help. Live AI responds in the language of your question.
3. **Live AI** uses the server's privately configured Hugging Face token and the Groq route for GPT-OSS. **Local analysis** computes evidence and explains workflows without an external request; it is explicitly labeled and does not pretend to be generative AI.
4. In verified delivery/demand contexts, click **Run trained prediction** before asking about new outputs. Delivery scores up to 50 selected orders using the registered model; demand computes next-day historical web-visit forecasts. Neither button trains a model or invents missing inputs.
5. Expand **Supporting evidence** to inspect local values. **Download conversation** saves the current page/source conversation as JSON. **Clear** removes that context's conversation and prediction outputs; logout clears all session state.

## Data and interpretation

All four supplied datasets support live summary explanations: order-level delivery, next-day web-visit demand, profitability line items and the independent final-delivery line-item experiment. These are historical snapshots, not live shipment feeds. Questions remain constrained to the available evidence and project workflows; unavailable facts are described as missing.

Profitability and final-delivery supplied scores are connected. Re-scoring their existing records requires original feature-complete inputs that are absent from the supplied scored CSVs. Complete-input model inference remains available in their existing prediction views. Sevika does not manufacture those missing features, claim source-score parity, or join experiments with incompatible row grains.

## Privacy and controls

The user approved anonymous numeric summaries being sent to Hugging Face/Groq. Aggregate evidence replaces original group names with anonymous segment labels. Raw dataset rows, customer/order IDs, original group names and filter values are omitted. Evidence containing original labels stays local; local-answer history is never sent upstream. The current question and previous live question/answer text are sent as written, so avoid entering private identifiers.

The token remains server-side in the ignored `.env`. No browser JavaScript calls the provider directly. Public help forcibly discards any supplied private frame. Chat cannot execute code, SQL, tools, modify datasets/models or expose credentials. Structured responses and evidence references are validated; failures display sanitized errors and leave local analysis available. Requests are explicit with no automatic retries or silent fallback, a 25-second provider timeout and bounded prompts/outputs.

History is session-only: at most six dataset/page/filter contexts with six turns per context; only the three most recent live turns enter model memory, under a bounded payload. Filter, source or selected-order changes isolate the conversation. Generated text remains an interpretation, not a guarantee of model accuracy.

## Verification

- Full automated regression: **207 passed**, zero failures; 13 pre-existing dependency/date-parsing warnings.
- Actual live API answers on all four supplied datasets: `metadata/sevika_dataset_live_qa.json`.
- Privacy checks for all four summary payloads: `metadata/sevika_payload_qa.json`.
- Actual browser-rendered public help and conversation download: `metadata/sevika_live_qa.json`.
- Actual browser delivery-summary live answer, evidence and download, with no browser token or direct provider request: `metadata/sevika_live_dataset_browser_qa.json`.
- Current navigation, themes, mobile layouts, registered prediction and conversation checks: `metadata/sevika_browser_qa.json`.
- Local security review: `metadata/security_audit.json`.

Repeat local browser checks with `.venv\Scripts\python.exe scripts/sevika_browser_qa.py --local-only` while the preview is running. Omitting that flag performs one real public-help request. Automated unit tests mock transport and independently cover payload privacy, selected context, unsafe requests, malformed outputs, failures, bounded memory, local math and prediction prerequisites.

The project remains a local showcase with temporary demo access. Existing production identity, hosting and missing-feature limitations are documented in `SECURITY.md` and the integration handoff.
