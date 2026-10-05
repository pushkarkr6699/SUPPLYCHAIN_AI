"""Separate-grain exports and dataset switches must never fall back to fixtures."""
from io import BytesIO

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from services.export_service import csv_bytes, report_pdf


def supplied_frames():
    dates = pd.to_datetime(["2018-01-01", "2018-01-02"])
    delivery = pd.DataFrame({"Order": ["1", "2"], "Date": dates, "Market": ["Europe", "Europe"],
        "Actual Late": [True, False], "Risk Probability": [.8, float("nan")], "Risk": ["High", None]})
    demand = pd.DataFrame({"Date": dates, "Product": ["A", "A"], "Category": ["C", "C"],
        "Actual Demand": [3., 0.], "Forecast Demand": [4., 1.], "Lower": [1., 0.], "Upper": [5., 2.]})
    for name, frame in [("delivery", delivery), ("demand", demand)]:
        frame.attrs.update(verified_artifacts=True, data_source=f"Supplied {name} source")
    return {"delivery": delivery, "demand": demand}


@pytest.mark.parametrize("dataset,report", [("delivery", "Delivery"), ("demand", "Demand"), ("delivery", "Executive"), ("demand", "Executive")])
def test_pdf_supports_separate_grains_and_missing_scores(dataset, report, monkeypatch):
    import services.export_service as exports
    frame = supplied_frames()[dataset]
    captured = []
    build = exports.SimpleDocTemplate.build

    def capture(doc, flowables, **kwargs):
        for item in flowables:
            if hasattr(item, "getPlainText"):
                captured.append(item.getPlainText())
        return build(doc, flowables, **kwargs)

    monkeypatch.setattr(exports.SimpleDocTemplate, "build", capture)
    result = report_pdf(frame, report, {}, ["KPIs", "Charts", "Insights", "Records"])
    assert result.startswith(b"%PDF")
    text = " ".join(captured)
    assert f"Supplied {dataset} source" in text
    assert "DEMO UI DATA" not in text
    exported = pd.read_csv(BytesIO(csv_bytes(frame)))
    assert exported.Source.eq(f"Supplied {dataset} source").all()
    if dataset == "delivery":
        assert exported["Risk Probability"].isna().sum() == 1


def test_pdf_refuses_wrong_dataset():
    frames = supplied_frames()
    with pytest.raises(ValueError, match="matching dataset"):
        report_pdf(frames["delivery"], "Demand", {}, ["KPIs"])
    with pytest.raises(ValueError, match="matching dataset"):
        report_pdf(frames["demand"], "Delivery", {}, ["KPIs"])


@pytest.mark.parametrize("view", ["data", "quality"])
def test_dataset_switch_loads_demand_instead_of_delivery(view, monkeypatch):
    import importlib
    module = importlib.import_module(f"views.{view}")
    frames = supplied_frames()
    requests = []

    class Service:
        demo = False

        def records(self, filters=None, dataset="demo"):
            assert dataset in frames, "A verified view requested demo data"
            requests.append((dataset, filters))
            return frames[dataset].copy()

    monkeypatch.setattr(module, "get_service", lambda: Service())
    script = f"import streamlit as st\nimport pandas as pd\nfrom views.{view} import render\nrender(pd.DataFrame())"
    at = AppTest.from_string(script, default_timeout=20)
    at.session_state["filters"] = {"Market": ["Europe"]}
    at.session_state["active_filter_dataset"] = "delivery"
    at.session_state["filters_by_dataset"] = {"demand": {"Product": ["A"]}}
    at.run()
    assert not at.exception, [error.message for error in at.exception]
    at.selectbox(key=f"{view}_dataset").set_value("demand").run()
    assert not at.exception, [error.message for error in at.exception]
    assert requests[-1] == ("demand", {"Product": ["A"]})
    if view == "data":
        assert "Forecast Demand" in at.dataframe[0].value
        assert "Risk Probability" not in at.dataframe[0].value
