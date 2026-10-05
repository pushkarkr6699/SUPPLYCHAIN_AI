from datetime import datetime, timezone
from copy import deepcopy


def snapshot(df, filters=None):
    dates = df.Date if len(df) and "Date" in df else None
    return {
        "source": df.attrs.get("data_source", "DEMO UI DATA · synthetic planning records"),
        "filters": deepcopy(filters or {}),
        "records": len(df),
        "date_range": (f"{dates.min():%Y-%m-%d} – {dates.max():%Y-%m-%d}" if dates is not None else "No records"),
        "calculated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "model": "Supplied outputs · no model executed" if df.attrs.get("verified_artifacts") else "No model executed · demo-ui-v1",
        "verified_artifacts": bool(df.attrs.get("verified_artifacts")),
        "artifact": df.attrs.get("artifact"),
        "scored_records": int(df["Risk Probability"].notna().sum()) if "Risk Probability" in df else None,
    }
