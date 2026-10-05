"""UI configuration and allowlisted local artifact paths."""
from pathlib import Path
import os

ROOT = Path(__file__).parent
DEMO_MODE = True
APP_NAME = "SUPPLYCHAIN AI"

# Load only path/provider integration settings from the ignored local .env file.
# Credentials remain in environment/secret stores and are never parsed here.
_LOCAL_KEYS = {
    "SUPPLYCHAIN_PROVIDER", "DELIVERY_PRIMARY_URI", "DELIVERY_DATA_URI", "DEMAND_DATA_URI", "DELIVERY_THRESHOLD_URI",
    "DELIVERY_MODEL_COMPARISON_URI", "DELIVERY_FEATURE_IMPORTANCE_URI", "DELIVERY_FINAL_SUMMARY_URI",
    "DELIVERY_WINNING_MODEL_URI", "DELIVERY_BEST_THRESHOLD_URI", "DELIVERY_MODEL_URI",
    "DEMAND_MODEL_COMPARISON_URI",
}
_ENV_FILE = ROOT / ".env"
if _ENV_FILE.is_file():
    for _line in _ENV_FILE.read_text(encoding="utf-8").splitlines():
        _key, _sep, _value = _line.partition("=")
        _key, _value = _key.strip(), _value.strip().strip('"').strip("'")
        if _sep and _key in _LOCAL_KEYS:
            os.environ.setdefault(_key, _value)

def _artifact_path(key):
    value = os.getenv(key, "").strip()
    if not value:
        return ""
    path = Path(value).expanduser()
    return str(path if path.is_absolute() else (ROOT / path).resolve())


SUPPLYCHAIN_PROVIDER = os.getenv("SUPPLYCHAIN_PROVIDER", "demo").strip().lower()
DELIVERY_DATA_URI = _artifact_path("DELIVERY_DATA_URI")
DELIVERY_PRIMARY_URI = _artifact_path("DELIVERY_PRIMARY_URI")
DEMAND_DATA_URI = _artifact_path("DEMAND_DATA_URI")
DELIVERY_THRESHOLD_URI = _artifact_path("DELIVERY_THRESHOLD_URI")
DELIVERY_MODEL_COMPARISON_URI = _artifact_path("DELIVERY_MODEL_COMPARISON_URI")
DELIVERY_FEATURE_IMPORTANCE_URI = _artifact_path("DELIVERY_FEATURE_IMPORTANCE_URI")
DELIVERY_FINAL_SUMMARY_URI = _artifact_path("DELIVERY_FINAL_SUMMARY_URI")
DELIVERY_WINNING_MODEL_URI = _artifact_path("DELIVERY_WINNING_MODEL_URI")
DELIVERY_BEST_THRESHOLD_URI = _artifact_path("DELIVERY_BEST_THRESHOLD_URI")
DELIVERY_MODEL_URI = _artifact_path("DELIVERY_MODEL_URI")
DEMAND_MODEL_COMPARISON_URI = _artifact_path("DEMAND_MODEL_COMPARISON_URI")
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

