# Data lineage

Supplied artifacts are recorded with path, role, source family, bytes, schema and SHA-256 in [data_registry.json](metadata/data_registry.json). Training notebooks are provenance, not proof of rerunning training. Registered auxiliary/evaluation/legacy sources retain their actual roles.

Delivery d1 uses **65,752 unique order-level rows**. The supplied scored table has **2,123 unique order keys**. Validated one-to-one coverage: 2,123 shared keys, 63,629 unscored primary orders, no unmatched scored keys. Scores remain null for unscored orders. Joined row counts and Sales independently reconcile.

Demand uses supplied product/day **web visits** and forecasts. It is not a purchase/order-demand dataset. Product/date history feeds the registered 15-day minimum lag/rolling contract. No forced access-log-to-order join is made.

Profitability uses separate line observations and supplied probabilities. Final delivery uses a separate line-observation experiment. Neither is silently merged into order-level d1 or demand. The cross-risk view exposes coverage and respects these grains.

Explicit joins inspect nulls, types, key uniqueness, duplicates, overlap and predicted row count. Null keys never match. Direct joins require one-to-one cardinality. A one-to-many child source must be explicitly aggregated first; many-to-many multiplication is refused. Uploaded joins stay session-local.

Missing raw sources: DataCoSupplyChainDataset.csv, DescriptionDataCoSupplyChain.csv, tokenized_access_logs.csv. Complete original customers/products/order-items/access-log relationships cannot be verified without them.

Evidence: [master_data_qa.json](metadata/master_data_qa.json), [master_inventory.json](metadata/master_inventory.json), [relationships.py](services/relationships.py), and the visible Data Lineage page.
