from pathlib import Path
import pytest
from streamlit.testing.v1 import AppTest
from components.navigation import ROUTES

APP = str(Path(__file__).resolve().parents[1] / "app.py")


def app(route="overview", **state):
    at = AppTest.from_file(APP, default_timeout=30)
    for key, value in {"authenticated": True, "route": route, "route_initialized": True, **state}.items():
        at.session_state[key] = value
    return at.run()


@pytest.mark.parametrize("route", ["landing", "login", *ROUTES])
def test_every_route_renders(route):
    at = app(route, developer_mode=True)
    assert not at.exception, [e.message for e in at.exception]


def test_demo_login_and_logout_clear_session():
    at = app("login", authenticated=False)
    at.text_input(key="login_username").set_value("Session Tester")
    at.text_input(key="login_password").set_value("sample-only")
    at.button(key="login_demo").click().run()
    assert at.session_state.authenticated
    assert at.session_state.route == "overview"
    assert not at.exception
    next(b for b in at.button if b.label == "Log out").click().run()
    assert not at.session_state.authenticated
    assert at.session_state.route == "login"
    assert at.text_input(key="login_username").value == ""
    assert at.text_input(key="login_password").value == ""
    assert not at.exception


def test_login_does_not_keep_password():
    at = app("login", authenticated=False)
    at.text_input(key="login_username").set_value("UI Tester")
    at.text_input(key="login_password").set_value("nonsecret-demo-input")
    next(b for b in at.button if b.label == "Sign In").click().run()
    assert at.session_state.user_name == "UI Tester"
    assert not at.exception
    assert "login_password" not in at.session_state or at.session_state.login_password == ""


def test_navigation_all_sidebar_buttons():
    at = app(developer_mode=True)
    for route in ROUTES:
        at.button(key=f"nav_{route}").click().run()
        assert not at.exception, f"{route}: {[e.message for e in at.exception]}"
        assert at.session_state.route == route


def test_filter_empty_reset_and_saved_view():
    at = app()
    at.multiselect(key="filter_Market").set_value(["Europe"]).run()
    assert at.session_state.filters["Market"] == ["Europe"]
    at.text_input(key="view_name").set_value("Europe desk").run()
    next(b for b in at.button if b.label == "Save current view").click().run()
    assert at.session_state.saved_views["Europe desk"]["Market"] == ["Europe"]
    at.multiselect(key="filter_Country").set_value(["India"]).run()
    assert not at.exception
    next(b for b in at.button if b.label == "Reset").click().run()
    assert not at.session_state.filters["Market"]
    next(b for b in at.button if b.label == "Open view").click().run()
    assert at.session_state.filters["Market"] == ["Europe"]
    assert not at.exception


def test_saved_investigation_metadata_rename_and_delete():
    at = app("explorer")
    at.multiselect(key="filter_Market").set_value(["Europe"]).run()
    at.text_input(key="view_name").set_value("Market review").run()
    at.button(key="save_workspace_view").click().run()
    assert at.session_state.saved_views["Market review"]["Market"] == ["Europe"]
    assert at.session_state.saved_views["Market review"]["__meta__"]["page"] == "explorer"
    at.text_input(key="rename_view_name").set_value("Europe investigation").run()
    at.button(key="rename_workspace_view").click().run()
    assert "Europe investigation" in at.session_state.saved_views
    at.button(key="delete_workspace_view").click().run()
    assert "Europe investigation" not in at.session_state.saved_views
    assert not at.exception


def test_threshold_change_preserves_production():
    at = app("threshold")
    at.slider(key="analysis_threshold").set_value(.80).run()
    assert not at.exception
    from config import PRODUCTION_THRESHOLD
    assert PRODUCTION_THRESHOLD == .56


def test_copilot_evidence_snapshot_and_filter_action():
    at = app("copilot")
    at.button(key="prompt_2").click().run()
    assert len(at.session_state.conversation) == 1
    answer = at.session_state.conversation[0]
    assert "Dataset" in answer["evidence"]
    at.button(key="copilot_apply_0").click().run()
    assert at.session_state.route == "delivery"
    assert at.session_state.filters["Risk"] == ["High", "Critical"]
    assert not at.exception


def test_presentation_and_theme():
    at = app()
    at.button(key="presentation_button").click().run()
    assert at.session_state.presentation
    at.radio(key="theme").set_value("Dark").run()
    assert at.session_state.theme == "Dark"
    assert not at.exception


def test_unavailable_pages_have_disabled_actions():
    for route in ["profitability", "cross_risk"]:
        at = app(route)
        assert any(b.disabled for b in at.button)
        assert not at.get("plotly_chart")


def test_report_preview_and_generate():
    at = app("reports")
    next(b for b in at.button if b.label == "Preview report").click().run()
    assert not at.exception
    next(b for b in at.button if b.label == "Generate Executive Report").click().run()
    assert at.session_state.generated_report[1].startswith(b"%PDF")
    assert not at.exception


def test_preferences_persist_across_multiple_routes():
    at = app("settings")
    at.radio(key="density").set_value("Compact").run()
    at.toggle(key="developer_mode").set_value(True).run()
    at.radio(key="settings_section").set_value("Dashboard").run()
    at.toggle(key="labels").set_value(True).run()
    for route in ["delivery", "overview", "diagnostics"]:
        at.button(key=f"nav_{route}").click().run()
        assert at.session_state.density == "Compact"
        assert at.session_state.developer_mode is True
        assert at.session_state.labels is True
        assert not at.exception


def test_download_branches_and_data_sort():
    at = app("downloads")
    for category in ["Predictions", "Model Metrics", "Reports", "Charts", "Filtered Data"]:
        next(r for r in at.radio if r.label == "Download category").set_value(category).run()
        assert not at.exception, category
    at.button(key="nav_data").click().run()
    next(s for s in at.selectbox if s.label == "Sort by").set_value("Order").run()
    next(c for c in at.checkbox if c.label == "Descending").set_value(False).run()
    frame = at.dataframe[0].value
    assert frame.Order.is_monotonic_increasing
    assert not at.exception


@pytest.mark.parametrize("route", ["overview", "demand", "orders", "copilot", "quality", "changes", "reports"])
def test_no_matches_is_recoverable(route):
    at = app(route, filters={"Market": ["Europe"], "Country": ["India"]})
    assert not at.exception
    next(b for b in at.button if b.label == "Reset").click().run()
    assert not at.exception


def test_alert_workflow_survives_navigation():
    at = app("alerts")
    at.button(key="alert_ack_0").click().run()
    assert at.session_state["alert_statuses"]["0"] == "Acknowledged"
    at.button(key="nav_overview").click().run()
    at.button(key="nav_alerts").click().run()
    assert at.session_state["alert_statuses"]["0"] == "Acknowledged"
    assert any(button.key == "alert_resolve_0" for button in at.button)
    assert not at.exception

