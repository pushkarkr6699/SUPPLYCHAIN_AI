from datetime import timedelta
from io import BytesIO
import pandas as pd
import pytest
from config import PRODUCTION_THRESHOLD
from services.provider import get_service
from services.analytics import summary, classification, threshold_curve
from services.comparison_service import compare_periods, change_table
from services.export_service import csv_bytes, excel_bytes, report_pdf
from services.copilot_service import respond
from services.query_engine import QueryEngine


def test_filters_totals_and_empty_context():
    service = get_service()
    all_records = service.records()
    end = all_records.Date.max().date()
    filters = {"Market": ["Europe"], "Risk": ["High", "Critical"], "Date": (end - timedelta(days=6), end)}
    filtered = service.records(filters)
    assert len(filtered) > 0
    assert filtered.Market.eq("Europe").all()
    assert filtered.Risk.isin(["High", "Critical"]).all()
    assert filtered.Date.dt.date.between(*filters["Date"]).all()
    assert summary(filtered)["forecast"] == filtered["Forecast Demand"].sum()
    assert summary(service.records({"Market": ["Missing"]}))["orders"] == 0


def test_threshold_analysis_cannot_mutate_production():
    df = get_service().records()
    low, high = classification(df, 0), classification(df, 1)
    assert low["FN"] == 0 and high["FP"] == 0
    assert low["TP"] + low["TN"] + low["FP"] + low["FN"] == len(df)
    assert PRODUCTION_THRESHOLD == .56
    assert len(threshold_curve(df)) > 1


def test_mock_data_is_deterministic_and_isolated():
    service = get_service()
    a = service.records()
    a.loc[0, "Market"] = "Changed"
    assert service.records().loc[0, "Market"] != "Changed"
    assert all(x["Status"] != "Ready" for x in service.model_status())
    assert service.model_status()[-1]["Status"] == "Not connected"


def test_exports_are_labeled_and_formula_safe():
    df = pd.DataFrame({"name": ["=1+1", "@unsafe", "normal"]})
    exported = pd.read_csv(BytesIO(csv_bytes(df)))
    assert exported.name.iloc[0] == "'=1+1"
    assert exported.Source.eq("DEMO UI DATA").all()
    excel = pd.read_excel(BytesIO(excel_bytes(df)))
    assert excel.Source.eq("DEMO UI DATA").all()


def test_unavailable_report_types_fail_closed():
    with pytest.raises(ValueError):
        report_pdf(get_service().records(), "Profitability", {}, ["KPIs"])
    with pytest.raises(ValueError):
        report_pdf(get_service().records(), "Cross-Risk", {}, ["KPIs"])


def test_duckdb_boundary_matches_pandas():
    df = get_service().records({"Market": ["Europe"]})
    engine = QueryEngine(df)
    try:
        rows = engine.market_summary()
        assert rows.Orders.sum() == len(df)
        assert rows["Risk Probability"].iloc[0] == pytest.approx(df["Risk Probability"].mean())
    finally:
        engine.close()


def test_copilot_unsupported_and_filtered_evidence():
    df = get_service().records({"Market": ["Europe"]})
    result = respond("Show high-risk orders", df)
    assert result["records"] == len(df)
    assert result["table"].Market.eq("Europe").all()
    assert respond("Tell me today's weather", df)["intent"] == "unsupported"


def test_copilot_tools_fail_closed_and_gate_unverified_model_outputs():
    from services.copilot.tools import get_model_metrics, get_feature_importance
    from services.copilot.validation import validate_route, validate_filter
    df = get_service().records()
    assert get_model_metrics()["available"] is False
    assert get_feature_importance()["available"] is False
    assert validate_route("delivery") == "delivery"
    with pytest.raises(ValueError, match="allowlisted"):
        validate_route("../secrets")
    with pytest.raises(ValueError, match="not supported"):
        validate_filter(df, "Order", [df.Order.iloc[0]])
    with pytest.raises(ValueError, match="1–1000"):
        respond("x" * 1001, df)
    simulated = respond("Run a delivery scenario", df, mode="Simulate")
    assert simulated["intent"] == "unsupported"
    assert simulated["route"] == "scenarios"
    assert simulated["evidence_context"]["source"].startswith("DEMO UI DATA")


def test_copilot_segment_and_demand_questions_return_matching_aggregations():
    df = get_service().records()
    markets = respond("Which markets have the highest delivery risk?", df)
    regions = respond("Which regions should I investigate?", df)
    growth = respond("Which products have increasing demand?", df)
    assert markets["intent"] == "market_risk" and markets["chart_x"] == "Market"
    assert regions["intent"] == "region_risk" and regions["chart_x"] == "Region"
    assert growth["intent"] == "demand_growth" and "Direction" in growth["table"]


def test_verified_csv_adapters_keep_delivery_and_demand_grains_separate(tmp_path, monkeypatch):
    from services.verified_data import delivery_records, demand_records
    import services.provider as provider
    delivery_path = tmp_path / "scored.csv"
    pd.DataFrame([
        {"Order Id": 101, "Market": "Europe", "Order Region": "West", "Order Country": "France",
         "Category Name": "Apparel", "Department Name": "Outdoors", "Customer Segment": "Retail",
         "Shipping Mode": "Standard", "Order_Date": "2018-01-01", "Actual_Late_Delivery": 1,
         "Late_Delivery_Probability": .7, "Predicted_Late_Delivery": 1, "Correct_Prediction": 1,
         "Delivery_Risk_Level": "High Risk"},
    ]).to_csv(delivery_path, index=False)
    demand_path = tmp_path / "forecast.csv"
    pd.DataFrame([
        {"DateOnly": "2018-01-01", "Product": "A", "Category": "C", "Department": "D", "Visits": 2,
         "Next_Day_Visits": 2.0, "Predicted_Next_Day_Visits": 3.0, "Error": -1.0, "Absolute_Error": 1.0,
         "Prediction_Lower_90": 0.0, "Prediction_Upper_90": 4.0, "Demand_Level": "Low Demand", "Stock_Attention_Flag": "Normal"},
    ]).to_csv(demand_path, index=False)
    delivery = delivery_records(delivery_path)
    demand = demand_records(demand_path)
    assert delivery.Order.iloc[0] == "101" and delivery.Risk.iloc[0] == "High"
    assert delivery.attrs["verified_artifacts"] if "verified_artifacts" in delivery.attrs else delivery.attrs["data_source"].startswith("Verified")
    assert "Actual Demand" not in delivery and "Risk Probability" not in demand
    assert demand["Forecast Error"].iloc[0] == -1.0

    monkeypatch.setattr(provider, "SUPPLYCHAIN_PROVIDER", "verified")
    monkeypatch.setattr(provider, "DELIVERY_DATA_URI", str(delivery_path))
    monkeypatch.setattr(provider, "DEMAND_DATA_URI", str(demand_path))
    service = provider.get_service()
    assert service.records(dataset="delivery").attrs["verified_artifacts"]
    assert service.records(dataset="demand").attrs["verified_artifacts"]
    assert service.is_demo("demo") is True


def test_verified_csv_adapter_rejects_threshold_or_schema_mismatch(tmp_path):
    from services.verified_data import delivery_records
    path = tmp_path / "invalid.csv"
    pd.DataFrame({"Order Id": [1], "Late_Delivery_Probability": [.7]}).to_csv(path, index=False)
    with pytest.raises(ValueError, match="missing required columns"):
        delivery_records(path)


def test_live_mode_fails_closed(monkeypatch):
    import services.provider as provider
    monkeypatch.setattr(provider, "DEMO_MODE", False)
    with pytest.raises(RuntimeError, match="not connected"):
        provider.get_service()

