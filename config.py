"""UI configuration. No production artifacts are read by this application."""
from pathlib import Path

ROOT = Path(__file__).parent
DEMO_MODE = True
APP_NAME = "SUPPLYCHAIN AI"
PRODUCTION_THRESHOLD = 0.56  # Supplied project metadata; never changed by UI controls.
DELIVERY_MODEL = "XGBoost"
DEFAULTS = {
    "route": "landing", "authenticated": False, "theme": "Light",
    "density": "Comfortable", "presentation": False, "copilot_open": False,
    "copilot_enabled": True, "developer_mode": False, "labels": False,
    "gridlines": True, "compact_numbers": True, "animation": False,
    "page_size": 15, "default_days": 28, "filters": {}, "saved_views": {},
    "recent_searches": [], "conversation": [], "show_password": False,
    "remember_me": False, "login_error": None, "recovery_notice": False,
    "selected_order": None,
    "selected_product": None, "user_name": "Demo Analyst",
    "reviewed_alerts": {},
}

