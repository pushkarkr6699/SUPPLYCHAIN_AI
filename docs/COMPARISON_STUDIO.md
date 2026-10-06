# Comparison Studio

Open the local preview at http://127.0.0.1:8501, select **Open platform**, then **Comparison Studio** in the sidebar.

1. Choose Delivery orders or Demand forecasts. Workspace date and category filters stay isolated by dataset.
2. Optionally filter up to four additional dataset fields. Numeric ranges and categorical selections use actual values.
3. Select Segments or Two cohorts. Cohort A/B values must be nonempty and disjoint.
4. Choose up to three grouping fields (two plus Cohort for A/B), and one to eight numeric/Boolean measures. Numeric fields can be grouping fields too; a field cannot occupy both roles.
5. Choose Mean, Sum, Median, Minimum or Maximum; date grouping; graph type; scale; and analysis focus. Press **Apply comparison**.
6. Explore bars, date trends, scatter plots, correlations and distributions. The shared chart toolbar supplies zoom, pan, autoscale, reset, image export and fullscreen where applicable to the chart type.
7. Read **Key insights** for computed findings with evidence IDs, or generate optional OpenAI narration.
8. Open **Predictions** and run the registered trained model. Delivery scores matching orders using the validated training features. Demand forecasts next-day web visits for selected products, retaining earlier history to build lags.
9. Download the complete comparison CSV, evidence JSON brief, or trained predictions. Chart display limits do not truncate the comparison export.

## Optional OpenAI narration

In the ignored local `.env`, configure:

```dotenv
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-4o-mini
```

Keep the real key out of chat and Git. Refresh the page after configuring it, then press **Generate AI insights**. Environment values override `.env`. API usage is billed separately by the API provider.

Narration is an explicit server-side request using the [OpenAI Responses API with Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs?api-mode=responses). Only computed aggregate values, field names, analysis focus and anonymous segment labels are sent. Order IDs, product names, raw rows and selected cohort values stay local. Responses use `store=false`, strict JSON schema and validated evidence references. A timeout, missing key, quota error or refused response leaves local analysis usable. Returned text is displayed without executing HTML or code.

Generated narratives and predictions belong to the current data and calculation signature. Changing selections hides stale results. Current AI narration is included in the evidence brief. Trained inference is independent of generative AI and requires verified artifacts; synthetic demo records never execute trained inference.

## Interpretation and scope

- Delivery and demand have different grains and are never joined.
- Missing/non-finite measurements are excluded and counted. Entirely missing sums remain missing. Boolean means are proportions.
- Separate panels retain each field's source units. The optional index normalizes each displayed measure by its maximum absolute value; it is a display transform.
- Trends show the latest displayed date groups in chronological order, with distinct traces for other grouping fields. Scatter/distribution use a deterministic sample of up to 5,000 matching rows; correlations and evidence use all matching rows.
- Numeric groups use exact values. Identifiers or near-unique measures can create many groups; prefer meaningful dimensions for a readable comparison.
- Trained features are fixed by the model contract. Selecting display fields does not train a new model or create an arbitrary target prediction.
- Delivery threshold is 0.35. Historical training/test and threshold-selection limitations still apply. Demand is web visits, not inventory or purchased units. New demand predictions are point estimates.
- Evidence IDs check attribution, not the truth of every AI sentence. Review the cited local calculations. Correlation does not establish causation.
- This is a local presentation platform with session access; deploying publicly still requires the authentication and operational work documented in SECURITY.md.

## Validation

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe scripts/comparison_functional_qa.py
.\.venv\Scripts\python.exe scripts/comparison_browser_qa.py
.\.venv\Scripts\python.exe scripts/comparison_chart_qa.py
```

Reports are saved under `metadata/comparison_*_qa.json`; screenshots and downloaded QA artifacts are ignored under `tmp/screenshots/comparison/`. OpenAI request format, evidence validation, credential handling and failure behavior are tested using mocked responses. A live OpenAI call requires a locally configured key and is not claimed as verified without one.

## Added registered line-item sources (6 October 2026)

Profitability and Final delivery line observations are selectable independently in verified mode. Their predictions require complete uploaded training inputs: 23 and 31 columns respectively. Selecting comparison metrics does not substitute for these inputs. Their saved scores remain available for charts and local evidence. Final delivery has threshold 0.56 and 0.41/0.71 bands; profitability has threshold 0.20 and its own bands. These source grains never silently replace the primary delivery or demand source. See [integration details](PROFITABILITY_INTEGRATION.md).
