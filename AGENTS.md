# SupplyChain AI project guidance

Preserve the existing Streamlit UI and explicitly labelled demonstration mode.
Use actual registered source files for connected analytics. Never create new
synthetic business rows, fabricated model metrics, predictions, routes,
coordinates or missing input columns. An absent source must produce an honest
unavailable state. Synthetic test fixtures are confined to tests, never offered
as connected business data.

Keep numerical definitions and calculations in shared services. Validate model
hashes, original preprocessing, feature order, positive-class semantics and
decision thresholds. Schema compatibility is not evidence of predictive quality.
Keep order, line-item and product/day grains separate unless an explicit join
has validated unique keys and reconciled counts; aggregate child measures before
joining so that parent amounts are not duplicated.

Never expose Customer Password or credentials. Minimize personal contact fields
before previews, charts, exports and AI. Do not deserialize uploaded artifacts,
execute uploaded code, generate arbitrary SQL or log raw records/questions.
Uploaded data and results remain session-local and are cleared on explicit reset
or logout. Never cache user uploads in a shared process cache. Live AI uses only
approved anonymous numerical summaries; new uploads require their own consent.

Extend shared components and services instead of rebuilding the application.
Use bounded charts, labelled sampling, exact tables, theme tokens, visible focus
and reduced-motion behavior. Run appropriate regression, real-data reconciliation,
browser, export, security and performance checks after meaningful changes.
Record actual evidence and missing assets in the final audit; never claim an
untested feature is complete or call local demo access production authentication.
