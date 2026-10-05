from io import BytesIO
import pandas as pd
from streamlit.testing.v1 import AppTest
from services.decision_context import coverage_context, decision_summary
from services.export_service import report_pdf
from config import ROOT


def test_decision_context_counts_missing_scores_and_uses_calendar_days():
    frame = pd.DataFrame({"Date": pd.to_datetime(["2018-01-01 01:00", "2018-01-01 21:00", "2018-01-02 15:00", "2018-01-02 16:00"]),
                          "Risk Probability": [.2, .6, .8, None], "Risk": ["Low", "Medium", "High", None]})
    frame.attrs["verified_artifacts"] = True
    original = frame.copy(deep=True)
    context = coverage_context(frame)
    assert context["scored"] == 3 and context["unscored"] == 1
    assert "no live refresh" in context["freshness"]
    text = decision_summary(frame)
    assert "+40.0 percentage points" in text and "2 → 1 scored orders" in text
    pd.testing.assert_frame_equal(frame, original)


def test_pdf_contains_provenance_dates_and_interpretation_limits():
    import pymupdf as fitz
    frame = pd.DataFrame({"Order": ["123"], "Date": pd.to_datetime(["2018-01-01"]),
                          "Risk Probability": [.8], "Risk": ["High"]})
    frame.attrs.update(verified_artifacts=True, artifact="primary.csv", score_artifact="scored.csv", model_name="Tuned XGBoost", production_threshold=.35)
    pdf = report_pdf(frame, "Delivery", {}, ["KPIs", "Charts", "Insights", "Records"])
    with fitz.open(stream=pdf, filetype="pdf") as document:
        text = " ".join(page.get_text() for page in document)
    for expected in ["Generated:", "01 Jan 2018", "primary.csv", "scored.csv", "Tuned XGBoost", "Sources and interpretation limits"]:
        assert expected in text


def test_demo_demand_summary_preserves_units_and_avoids_delivery_summary():
    frame = pd.DataFrame({"Risk Probability": [.2], "Risk": ["Low"], "Actual Demand": [10], "Forecast Demand": [12]})
    text = decision_summary(frame, "demand")
    assert "illustrative demo units" in text and "web visits" not in text and "high-risk" not in text


def test_guided_demo_preserves_filters_and_visits_all_steps():
    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=60)
    for key, value in {"authenticated": True, "route": "overview", "route_initialized": True}.items():
        at.session_state[key] = value
    at.run()
    at.button(key="guide_start").click().run()
    dates = at.session_state.filters["Date"]
    for route in ["delivery", "orders", "scenarios", "reports"]:
        at.button(key="guide_next").click().run()
        assert at.session_state.route == route and not at.exception
        assert at.session_state.filters["Date"] == dates
    assert at.session_state.report_type == "Delivery"
    at.button(key="guide_close").click().run()
    assert not at.session_state.guide_active


def test_repeated_report_generation_is_disabled_until_settings_change():
    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=60)
    for key, value in {"authenticated": True, "route": "reports", "route_initialized": True, "report_type": "Delivery"}.items():
        at.session_state[key] = value
    at.run()
    at.button(key="generate_report_pdf").click().run()
    assert not at.exception
    assert at.button(key="generate_report_pdf").disabled
    next(item for item in at.multiselect if item.label == "Sections").set_value(["KPIs"]).run()
    assert not at.button(key="generate_report_pdf").disabled
