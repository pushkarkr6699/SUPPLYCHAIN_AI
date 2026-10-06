"""One explicit route registry; pages stay focused on presentation."""
from views import comparison, overview, delivery, demand, unavailable, explorer, orders, geography, changes, scenarios, copilot, insights, alerts, models, explainability, threshold, drift, health, quality, lineage, data, reports, downloads, settings, diagnostics

PAGES = {
    "comparison": ("Comparison Studio", "Compare your selected dataset fields, inspect evidence and run connected trained models.", comparison.render),
    "overview": ("Executive Command Center", "A unified operational view across predictive risk, forecast demand and model health.", overview.render),
    "delivery": ("Delivery Intelligence", "Explore predicted late-delivery risk across orders, markets, regions and shipping dimensions.", delivery.render),
    "demand": ("Demand Intelligence", "Explore next-day forecasts, uncertainty and product-level attention flags in the selected dataset.", demand.render),
    "profitability": ("Profitability Intelligence", "Architecture-ready profitability classification. Model not connected.", unavailable.profitability),
    "cross_risk": ("Cross-Risk Command Center", "Combine independent model signals to prioritize potentially critical operational records.", unavailable.cross_risk),
    "explorer": ("Universal Explorer", "Search the workspace. Follow an entity from a signal to its records.", explorer.render),
    "orders": ("Order Explorer", "An intelligence case file for every order in the active dataset context.", orders.render),
    "geography": ("Geographic Intelligence", "Understand where orders, delivery signals and forecast demand are concentrated.", geography.render),
    "changes": ("What Changed?", "Compare periods and investigate observed changes across operational segments.", changes.render),
    "scenarios": ("Scenario Lab", "Explore supported inputs in a clearly separated experimental workspace.", scenarios.render),
    "copilot": ("SupplyChain Copilot", "An evidence-first analytical workspace, connected to your current context.", copilot.render),
    "insights": ("Insight Center", "Deterministic observations with context, evidence and a next step.", insights.render),
    "alerts": ("Alert Center", "Prioritize critical, attention and informational signals across the workspace.", alerts.render),
    "models": ("Model Intelligence", "Inspect model metadata, comparison views, coverage and validation readiness.", models.render),
    "explainability": ("Explainability", "Explore how a model behaves, from global importance to individual records.", explainability.render),
    "threshold": ("Threshold Lab", "Explore classification trade-offs without changing the production threshold.", threshold.render),
    "drift": ("Drift Monitor", "Compare feature and prediction distributions once reference data is connected.", drift.render),
    "health": ("Model Health", "A transparent view of application, data and model connectivity.", health.render),
    "quality": ("Data Quality", "Inspect completeness, schema, coverage and validity in the selected dataset.", quality.render),
    "lineage": ("Data Lineage", "Trace the intended path from operational sources to analytical decisions.", lineage.render),
    "data": ("Data Explorer", "Inspect, search, sort and export non-sensitive records in your current view.", data.render),
    "reports": ("Reports", "Turn the current analytical context into a focused, shareable decision brief.", reports.render),
    "downloads": ("Downloads", "Export filtered source data, predictions, comparison metrics and reports.", downloads.render),
    "settings": ("Settings", "Customize your session, presentation preferences and analytical workspace.", settings.render),
    "diagnostics": ("Developer / Diagnostics", "Runtime visibility and safe integration diagnostics for the UI phase.", diagnostics.render),
}

