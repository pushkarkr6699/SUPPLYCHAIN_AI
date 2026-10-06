# Visualization Studio

Open the platform and choose **Visualization Studio** in the sidebar, or **Open Visualization Studio** in the final section of Executive Overview.

1. Choose **Visualization dataset**: Delivery orders, Demand forecasts, Profitability line items, or Final delivery line observations. Demo mode keeps its existing synthetic workspace available.
2. Set workspace date/dimension filters for the primary source.
3. Choose up to two grouping fields, four numeric measures and eight visualization types per board, then click **Build visualizations**.
4. Use **Additional datasets** to display other sources in independent boards. Each has its own date range and chart choices. Extra sources initially use their full history; primary-source filters are not silently applied to them. Different datasets are never joined or interpreted as paired records. Sevika follows the primary workspace source.
5. Use each compatible chart toolbar for zoom, pan, autoscale, reset, fullscreen and PNG download. Composition charts do not have Cartesian axis zoom. Open **Analysis table and downloads** for the complete grouped CSV and a JSON chart-settings manifest. Source captions stay below each chart so mobile labels remain clear; CSV/settings downloads carry provenance alongside the PNG graph.

## Available visualizations

Vertical bars, horizontal bars, line, area, scatter, bubble, histogram, box plot, violin plot, ECDF, correlation heatmap, density heatmap, grouped heatmap, treemap, sunburst, pie, donut and scatter matrix: **18 options**.

- Bars and time/distribution charts put measures with different units in separate panels.
- Scatter/density charts use the first two measures. Bubble uses the third measure's absolute magnitude as area, not confidence. Scatter matrix compares all selected measures.
- Grouped heatmap needs exactly two grouping fields; correlation needs at least two nonconstant measures and three paired finite observations.
- Pie, donut, treemap and sunburst default to **record counts**. For **First measure (sum)**, choose Sum and a nonnegative additive measure. Probabilities and Boolean flags cannot be summed. Negative profit uses bars/distributions instead.
- Mean/median omit missing/non-finite values. Missing scores stay missing. The table includes record and valid-value counts. Composition combines undisplayed groups into **[Other groups]**, preserving the total.
- Record plots use a deterministic sample of at most 3,000 rows and say so. Correlation uses all matching rows. Group charts show 5-50 groups; time charts cap display at 12 series and the latest 180 time bins. The complete grouped CSV is not truncated by chart display limits. Table preview caps at 1,000 groups.
- Area curves overlap without stacking group means. Historical relationships are observational, not causal. Demand measures are next-day web visits; source monetary units are not relabeled as a currency that was not supplied.

Charts refresh when workspace/date filters change. Chart field/type settings apply when Build is clicked and persist per source during the session. Empty selections and incompatible charts show a specific recovery message instead of generating made-up values.

This feature reads connected data and uses the existing export and chart components. It does not retrain models, execute inference, transfer data to AI providers or change source artifacts. Existing Comparison Studio, prediction views, Sevika, landing/login and demo access remain available.

## Verification

The final full regression passed **240 tests**, zero failures, with 13 pre-existing dependency/date-parsing warnings. All 18 chart types were constructed on every connected source with compatible fields. Browser controls, multi-source boards, exports, source switching and desktop/mobile themes passed.

Tests cover every chart type, source preservation, aggregation/coverage, negative composition, probability restrictions, deterministic sample limits, empty/constant/non-finite values, compatible field prerequisites, chronological nonstacked areas, demand units and real/demo Streamlit controls. Browser evidence is in `metadata/visualization_browser_qa.json`; additional local source/security verification is in `metadata/visualization_release_qa.json`. The final mobile axis/source spacing and bounded legend check is recorded in `metadata/visualization_polish_qa.json`.

Repeat the browser check with `.venv\Scripts\python.exe scripts/visualization_browser_qa.py` while the preview runs on localhost:8501. It uses an isolated Chrome profile and makes no external AI request.
