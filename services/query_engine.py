"""DuckDB boundary ready for verified, read-only real services.

Only caller-supplied in-memory frames are registered. No project file discovery,
CSV loading, arbitrary UI SQL, extension installation or model loading.
"""
import duckdb
import pandas as pd


class QueryEngine:
    def __init__(self, records: pd.DataFrame):
        self.connection = duckdb.connect(":memory:", config={"enable_external_access": "false"})
        self.connection.register("records", records)

    def market_summary(self):
        return self.connection.execute('SELECT "Market", count(*) AS "Orders", avg("Risk Probability") AS "Risk Probability" FROM records GROUP BY "Market"').df()

    def close(self):
        self.connection.close()

