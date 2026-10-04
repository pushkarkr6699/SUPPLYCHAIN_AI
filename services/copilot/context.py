from datetime import datetime, timezone


def snapshot(df, filters=None):
    dates = df.Date if len(df) and "Date" in df else None
    return {
        "source": "DEMO UI DATA · synthetic planning records",
        "filters": dict(filters or {}),
        "records": len(df),
        "date_range": (f"{dates.min():%Y-%m-%d} – {dates.max():%Y-%m-%d}" if dates is not None else "No records"),
        "calculated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "model": "No model executed · demo-ui-v1",
    }
