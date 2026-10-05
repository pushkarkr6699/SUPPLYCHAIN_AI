"""Corrupt-source and unavailable-capability regression tests."""
from pathlib import Path
import pandas as pd
import pytest
from services.verified_data import demand_records, order_delivery_records, _read
from services.export_service import report_pdf

ROOT = Path(__file__).resolve().parents[1]


def test_reset_date_widget_matches_full_history(monkeypatch):
    from services import provider
    from streamlit.testing.v1 import AppTest
    monkeypatch.setattr(provider, "SUPPLYCHAIN_PROVIDER", "verified")
    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=60)
    for key, value in {"authenticated": True, "route": "overview", "route_initialized": True, "default_days": 3650}.items():
        at.session_state[key] = value
    at.run()
    last_day = at.session_state.filters["Date"][1]
    at.date_input(key="filter_Date_delivery").set_value((last_day, last_day)).run()
    at.button(key="reset_workspace_filters").click().run()
    assert not at.exception
    assert at.session_state.date_reset_revision == 1
    assert at.date_input(key="filter_Date_delivery_1").value == at.session_state.filters["Date"]
    assert str(at.session_state.filters["Date"][0]) == "2015-01-01"
    at.session_state.default_days = 28
    at.button(key="chip_Date").click().run()
    assert not at.exception
    assert at.session_state.date_reset_revision == 2
    assert at.date_input(key="filter_Date_delivery_2").value == at.session_state.filters["Date"]
    assert (at.session_state.filters["Date"][1] - at.session_state.filters["Date"][0]).days == 27


def test_verified_settings_describe_connected_data(monkeypatch):
    from services import provider
    from streamlit.testing.v1 import AppTest
    monkeypatch.setattr(provider, "SUPPLYCHAIN_PROVIDER", "verified")
    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=60)
    for key, value in {"authenticated": True, "route": "settings", "route_initialized": True, "settings_section": "Data"}.items():
        at.session_state[key] = value
    at.run()
    assert not at.exception
    assert any("Supplied delivery and web-visit datasets are connected" in item.value for item in at.info)
    assert 3650 in at.selectbox(key="default_days").options or "All available history" in at.selectbox(key="default_days").options


def test_excel_export_preserves_changed_cell_types_and_provenance():
    from io import BytesIO
    from openpyxl import load_workbook
    from services.export_service import excel_bytes
    first = pd.DataFrame({"value": pd.Series([1, "text"], dtype=object)})
    second = pd.DataFrame({"value": pd.Series(["1", "text"], dtype=object)})
    for frame, source, expected_type in ((first, "source A", "n"), (second, "source A", "s"), (second, "source B", "s")):
        workbook = load_workbook(BytesIO(excel_bytes(frame, source)))
        assert workbook.active["A2"].data_type == expected_type
        assert workbook.active["B2"].value == source
        workbook.close()


def test_missing_delivery_registry_does_not_expose_local_path(monkeypatch, tmp_path):
    from services import inference_service
    monkeypatch.setattr(inference_service, "REGISTRY_PATH", tmp_path / "missing-registry.json")
    state = inference_service.status()
    assert not state["available"]
    assert str(tmp_path) not in state["reason"]
    assert "unavailable" in state["reason"]


@pytest.mark.parametrize("corruption", ["duplicate", "invalid_date", "null_product", "infinite_visits", "negative_visits", "bad_flag", "missing_column"])
def test_demand_corrupt_source_is_rejected(tmp_path, corruption):
    frame = pd.read_csv(ROOT / "data/demand/final/AccessLogs_Final_Advanced_Forecast.csv").head(2)
    if corruption == "duplicate": frame = pd.concat([frame, frame.iloc[:1]])
    elif corruption == "invalid_date": frame.loc[0, "DateOnly"] = "invalid"
    elif corruption == "null_product": frame.loc[0, "Product"] = None
    elif corruption == "infinite_visits":
        frame["Visits"] = frame.Visits.astype(float)
        frame.loc[0, "Visits"] = float("inf")
    elif corruption == "negative_visits": frame.loc[0, "Visits"] = -1
    elif corruption == "bad_flag": frame.loc[0, "Stock_Attention_Flag"] = "unknown"
    else: frame = frame.drop(columns="Product")
    path = tmp_path / "bad.csv"
    frame.to_csv(path, index=False)
    with pytest.raises(ValueError): demand_records(path)


@pytest.mark.parametrize("corruption", ["risk_mapping", "model_identifier", "invalid_date", "null_market", "infinite_sales"])
def test_delivery_corrupt_source_is_rejected(tmp_path, corruption):
    scored = pd.read_csv(ROOT / "data/delivery/final/DataCo_Final_Scored_Orders.csv").head(2)
    primary = pd.read_csv(ROOT / "data/delivery/final/DataCo_Final_Order_Level_Dataset.csv")
    primary = primary[primary["Order Id"].isin(scored["Order Id"])].copy()
    if corruption == "risk_mapping": scored["Risk_Level"] = "High Risk" if scored.Risk_Level.iloc[0] != "High Risk" else "Low Risk"
    elif corruption == "model_identifier": scored["Prediction_Model"] = "Different model"
    elif corruption == "invalid_date": primary["Order_Date"] = "invalid"
    elif corruption == "null_market": primary["Market"] = None
    else: primary["Sales"] = float("inf")
    a, b = tmp_path / "primary.csv", tmp_path / "scored.csv"
    primary.to_csv(a, index=False); scored.to_csv(b, index=False)
    with pytest.raises(ValueError): order_delivery_records(a, b)


@pytest.mark.parametrize("kind", ["missing", "empty", "malformed"])
def test_unreadable_csv_is_rejected(tmp_path, kind):
    path = tmp_path / "bad.csv"
    if kind == "empty": path.write_text("")
    elif kind == "malformed": path.write_text('a,b\n"unterminated')
    with pytest.raises((ValueError, OSError)): _read(path, {"a"}, "Test source")


@pytest.mark.parametrize("report", ["Profitability", "Cross-Risk"])
def test_unavailable_reports_never_fabricate_outputs(report):
    with pytest.raises(ValueError, match="unavailable"):
        report_pdf(pd.DataFrame(), report, {}, [])


def test_cached_join_does_not_share_mutable_values():
    a = ROOT / "data/delivery/final/DataCo_Final_Order_Level_Dataset.csv"
    b = ROOT / "data/delivery/final/DataCo_Final_Scored_Orders.csv"
    frame = order_delivery_records(a, b)
    expected = frame.loc[0, "Market"]
    frame.loc[0, "Market"] = "Mutated UI copy"
    assert order_delivery_records(a, b).loc[0, "Market"] == expected
