from config import DEMO_MODE
from services import mock_data
from services.contracts import AnalyticsService

FILTER_COLUMNS = ["Market", "Region", "Country", "Category", "Department", "Shipping Mode", "Customer Segment", "Risk", "Product"]


def filter_description(filters):
    parts = []
    for key, values in filters.items():
        if not values:
            continue
        if key == "Date":
            parts.append("Dates: " + " – ".join(value.strftime("%d %b %Y") for value in values))
        else:
            parts.append(f"{key}: {', '.join(str(v) for v in values)}")
    return " · ".join(parts) or "All demo records"


class MockAnalyticsService:
    demo = True

    def records(self, filters=None):
        df = mock_data.fixture_records().copy()
        for key, values in (filters or {}).items():
            if key == "Date" and len(values) == 2:
                df = df[df.Date.dt.date.between(values[0], values[1])]
            elif key in FILTER_COLUMNS and values:
                df = df[df[key].isin(values)]
        return df.reset_index(drop=True)

    def options(self):
        df = self.records()
        return {c: sorted(df[c].unique().tolist()) for c in FILTER_COLUMNS}

    def evidence(self, records, filters):
        return {"Dataset": mock_data.DEMO_LABEL + " · synthetic planning records", "Records analyzed": len(records),
            "Active filters": filter_description(filters),
            "Date range": f"{records.Date.min():%d %b %Y} – {records.Date.max():%d %b %Y}" if len(records) else "No records",
            "Metric / calculation": "Risk = mean probability; demand = sum of units; WAPE = sum absolute error / sum actual",
            "Model": "No model executed · demo-ui-v1", "Snapshot": mock_data.DEMO_AS_OF}

    def model_status(self):
        return mock_data.model_status()


def get_service() -> AnalyticsService:
    if not DEMO_MODE:
        raise RuntimeError("Live services are not connected. Configure a verified provider before disabling DEMO_MODE.")
    return MockAnalyticsService()

