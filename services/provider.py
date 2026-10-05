from config import (DEMO_MODE, SUPPLYCHAIN_PROVIDER, DELIVERY_DATA_URI, DELIVERY_PRIMARY_URI,
                    DEMAND_DATA_URI, DELIVERY_THRESHOLD_URI, PRODUCTION_THRESHOLD,
                    DELIVERY_MODEL_COMPARISON_URI, DELIVERY_FEATURE_IMPORTANCE_URI,
                    DELIVERY_FINAL_SUMMARY_URI, DELIVERY_WINNING_MODEL_URI,
                    DELIVERY_BEST_THRESHOLD_URI, DELIVERY_MODEL_URI,
                    DEMAND_MODEL_COMPARISON_URI)
from pathlib import Path
import pandas as pd
from services import mock_data
from services.contracts import AnalyticsService
from services.verified_data import (delivery_records, order_delivery_records, demand_records, threshold_records,
    tabular_artifact, summary_artifact, text_artifact, DELIVERY_MODEL_COLUMNS, FEATURE_COLUMNS)

FILTER_COLUMNS = ["Market", "Region", "Country", "Category", "Department", "Shipping Mode", "Customer Segment", "Risk", "Product"]


def filter_description(filters, empty_label="All demo records"):
    parts = []
    for key, values in filters.items():
        if not values:
            continue
        if key == "Date":
            parts.append("Dates: " + " – ".join(value.strftime("%d %b %Y") for value in values))
        else:
            parts.append(f"{key}: {', '.join(str(v) for v in values)}")
    return " · ".join(parts) or empty_label


class MockAnalyticsService:
    demo = True

    def records(self, filters=None, dataset="demo"):
        df = mock_data.fixture_records().copy()
        for key, values in (filters or {}).items():
            if key == "Date" and len(values) == 2:
                df = df[df.Date.dt.date.between(values[0], values[1])]
            elif key in FILTER_COLUMNS and values:
                df = df[df[key].isin(values)]
        return df.reset_index(drop=True)

    def options(self, dataset="demo"):
        df = self.records(dataset=dataset)
        return {c: sorted(df[c].dropna().unique().tolist()) for c in FILTER_COLUMNS if c in df}

    def data_source_label(self, dataset="demo"):
        return "DEMO UI DATA · synthetic planning records"

    def is_demo(self, dataset="demo"):
        return True

    def evidence(self, records, filters):
        return {"Dataset": mock_data.DEMO_LABEL + " · synthetic planning records", "Records analyzed": len(records),
            "Active filters": filter_description(filters),
            "Date range": f"{records.Date.min():%d %b %Y} – {records.Date.max():%d %b %Y}" if len(records) else "No records",
            "Metric / calculation": "Risk = mean probability; demand = sum of units; WAPE = sum absolute error / sum actual",
            "Model": "No model executed · demo-ui-v1", "Snapshot": mock_data.DEMO_AS_OF}

    def model_status(self):
        return mock_data.model_status()


class VerifiedArtifactsService(MockAnalyticsService):
    """Read-only pre-scored CSV provider; separate grains are never joined."""
    demo = False

    def _dataset(self, dataset):
        if dataset == "demo" or dataset is None:
            dataset = "delivery"
        if dataset == "delivery":
            if not DELIVERY_DATA_URI:
                raise RuntimeError("Delivery scored CSV path is not configured.")
            frame = order_delivery_records(DELIVERY_PRIMARY_URI, DELIVERY_DATA_URI) if DELIVERY_PRIMARY_URI else delivery_records(DELIVERY_DATA_URI)
        elif dataset == "demand":
            if not DEMAND_DATA_URI:
                raise RuntimeError("Demand forecast CSV path is not configured.")
            frame = demand_records(DEMAND_DATA_URI)
        else:
            raise ValueError(f"Unsupported verified dataset: {dataset}")
        frame.attrs.update(verified_artifacts=True)
        return frame

    def records(self, filters=None, dataset="demo"):
        df = self._dataset(dataset)
        for key, values in (filters or {}).items():
            if key == "Date" and len(values) == 2 and "Date" in df:
                df = df[df.Date.dt.date.between(values[0], values[1])]
            elif key in df and values:
                df = df[df[key].isin(values)]
        attrs = dict(df.attrs)
        result = df.reset_index(drop=True).copy()
        result.attrs.update(attrs)
        return result

    def options(self, dataset="demo"):
        df = self._dataset(dataset)
        columns = [name for name in FILTER_COLUMNS if name in df]
        return {name: sorted(df[name].dropna().unique().tolist()) for name in columns}

    def data_source_label(self, dataset="demo"):
        return str(self._dataset(dataset).attrs.get("data_source", "Verified scored output"))

    def is_demo(self, dataset="demo"):
        return False

    def evidence(self, records, filters):
        if not records.attrs.get("verified_artifacts"):
            return super().evidence(records, filters)
        source = records.attrs.get("data_source", "Verified scored output")
        context = {"Dataset": source, "Artifact": records.attrs.get("artifact", "CSV"),
                   "Records analyzed": len(records), "Active filters": filter_description(filters, "All records in artifact"),
                   "Date range": f"{records.Date.min():%d %b %Y} – {records.Date.max():%d %b %Y}" if len(records) else "No records",
                   "Model inference": "Not executed · probabilities/forecasts are precomputed artifact columns"}
        if "Risk Probability" in records:
            context["Calculation"] = "Mean probability and outcome agreement use supplied scored rows only; unscored orders retain missing predictions."
            context["Score coverage"] = f'{records["Risk Probability"].notna().sum():,} / {len(records):,} orders in this context'
            context["Evaluation"] = records.attrs.get("evaluation_note", "Supplied scores; see source provenance")
            context["Decision threshold"] = f'{records.attrs.get("production_threshold", PRODUCTION_THRESHOLD):.2f} · supplied scored labels match this threshold'
        if "Forecast Demand" in records:
            coverage = records["Actual Demand"].between(records["Lower"], records["Upper"]).mean()
            context["Calculation"] = "WAPE = sum absolute forecast error / sum supplied next-day actuals; interval coverage is measured on these rows."
            context["Observed interval coverage"] = f"{coverage:.1%} · source bounds are labeled 90%; calibration is unverified"
        return context

    def threshold_analysis(self):
        if DELIVERY_PRIMARY_URI:
            from services.analytics import threshold_curve
            frame = threshold_curve(self.records(dataset="delivery"))
            frame.attrs.update(data_source="Supplied January 2018 test scores", evaluation_note="Retrospective test diagnostics; operating threshold selected on these same rows")
            return frame
        if not DELIVERY_THRESHOLD_URI:
            raise RuntimeError("Delivery threshold analysis CSV path is not configured.")
        frame = threshold_records(DELIVERY_THRESHOLD_URI)
        supplied = frame.loc[(frame.Threshold - PRODUCTION_THRESHOLD).abs().idxmin()]
        if abs(float(supplied.Threshold) - PRODUCTION_THRESHOLD) > 1e-9:
            raise ValueError("Threshold artifact does not contain the configured production threshold 0.56.")
        return frame

    def model_comparison(self):
        if not DELIVERY_MODEL_COMPARISON_URI:
            return None
        frame = tabular_artifact(DELIVERY_MODEL_COMPARISON_URI, {"Model"}, "Delivery model comparison")
        frame.attrs["evaluation_note"] = "d1 comparison uses threshold 0.50; scored output uses 0.35" if DELIVERY_PRIMARY_URI else "Separate d3 validation comparison"
        return frame

    def feature_importance(self):
        if not DELIVERY_FEATURE_IMPORTANCE_URI:
            return None
        frame = tabular_artifact(DELIVERY_FEATURE_IMPORTANCE_URI, FEATURE_COLUMNS, "Delivery feature importance")
        frame["Importance"] = pd.to_numeric(frame.Importance, errors="raise")
        frame.attrs["model_name"] = "Random Forest baseline" if DELIVERY_PRIMARY_URI else "d3 XGBoost"
        return frame.sort_values("Importance", ascending=False)

    def final_summary(self):
        if not DELIVERY_FINAL_SUMMARY_URI:
            return None, None
        return summary_artifact(DELIVERY_FINAL_SUMMARY_URI)

    def demand_model_comparison(self):
        if not DEMAND_MODEL_COMPARISON_URI:
            return None
        frame = tabular_artifact(DEMAND_MODEL_COMPARISON_URI, {"Model"}, "Demand model comparison")
        # This artifact mixes regression baselines with a classification-only XGBoost row.
        # Keep only rows with genuine regression metrics; never relabel classification metrics.
        metrics = [column for column in ("MAE", "RMSE", "R2", "WAPE", "SMAPE") if column in frame]
        if not metrics:
            return None
        frame[metrics] = frame[metrics].apply(pd.to_numeric, errors="coerce")
        return frame.loc[frame[metrics].notna().any(axis=1)].copy()

    def metadata(self):
        status = {"Winning model": "Tuned XGBoost", "Best threshold": "0.35", "Evaluation": "Retrospective January 2018 scores; threshold selected on test predictions", "Feature importance": "Random Forest baseline reference"} if DELIVERY_PRIMARY_URI else {}
        for label, path, kind in [
            ("Winning model", DELIVERY_WINNING_MODEL_URI, "Winning model"),
            ("Best threshold", DELIVERY_BEST_THRESHOLD_URI, "Best threshold"),
        ]:
            if path:
                status[label] = text_artifact(path, kind)[0]
        if DELIVERY_MODEL_URI:
            path = Path(DELIVERY_MODEL_URI).expanduser()
            from services.inference_service import inference_status
            state = inference_status()
            status["Serialized model"] = "Validated · trained inference available in Prediction Lab" if state["enabled"] else state["reason"]
        return status

    def model_status(self):
        from services.inference_service import status as delivery_status
        from services.demand_inference import status as demand_status
        delivery, demand = delivery_status(), demand_status()
        return [
            {"Capability": "Delivery scored outputs", "Status": "Connected CSV", "Source": Path(DELIVERY_DATA_URI).name if DELIVERY_DATA_URI else "Not configured"},
            {"Capability": "Delivery model artifact / inference", "Status": "Validated · available" if delivery["available"] else delivery["reason"]},
            {"Capability": "Demand precomputed forecasts", "Status": "Connected CSV", "Source": Path(DEMAND_DATA_URI).name if DEMAND_DATA_URI else "Not configured"},
            {"Capability": "Demand model inference", "Status": "Validated · available" if demand["available"] else demand["reason"]},
            {"Capability": "Profitability model", "Status": "Unavailable · no verified artifact"},
        ]


def get_service() -> AnalyticsService:
    if SUPPLYCHAIN_PROVIDER == "verified":
        return VerifiedArtifactsService()
    if SUPPLYCHAIN_PROVIDER != "demo":
        raise ValueError("SUPPLYCHAIN_PROVIDER must be demo or verified.")
    if not DEMO_MODE:
        raise RuntimeError("Live services are not connected. Configure a verified provider before disabling DEMO_MODE.")
    return MockAnalyticsService()

