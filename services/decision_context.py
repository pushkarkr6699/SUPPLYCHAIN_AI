"""Descriptive decision context computed only from the selected source rows."""
import pandas as pd


def coverage_context(frame):
    dates = pd.to_datetime(frame.get("Date", pd.Series(dtype="datetime64[ns]")), errors="coerce").dropna()
    period = f"{dates.min():%d %b %Y} – {dates.max():%d %b %Y}" if len(dates) else "No records in this period"
    result = {"period": period, "rows": len(frame), "source": frame.attrs.get("artifact", "Synthetic demo snapshot"),
              "freshness": "Historical snapshot · no live refresh" if frame.attrs.get("verified_artifacts") else "Fixed synthetic demo snapshot"}
    if "Risk Probability" in frame:
        result["scored"] = int(frame["Risk Probability"].notna().sum())
        result["unscored"] = len(frame) - result["scored"]
    return result


def decision_summary(frame, dataset=None):
    if "Profitability Probability" in frame:
        return f"{len(frame):,} supplied profitability line items across {frame.Order.nunique():,} orders. Mean probability is {frame["Profitability Probability"].mean():.1%}; recorded profitable rate is {frame["Actual Profitable"].mean():.1%}. The saved threshold predicts every source row profitable; review model discrimination and calibration before relying on its ranking."
    if frame.attrs.get("dataset") == "delivery_final":
        return f"{len(frame):,} final delivery line observations across {frame.Order.nunique():,} orders. Mean late probability is {frame['Risk Probability'].mean():.1%}; observed late rate is {frame['Actual Late'].mean():.1%}. Saved threshold is 0.56. Repeated source observations are retained; interpret line-weighted results separately from main order-level delivery."
    if "Risk Probability" in frame and dataset != "demand":
        scored = frame.dropna(subset=["Risk Probability"])
        high = frame[frame["Risk"].isin(["High", "Critical"])] if "Risk" in frame else scored.iloc[:0]
        context = coverage_context(frame)
        source = "supplied" if frame.attrs.get("verified_artifacts") else "demo"
        text = f"{len(high):,} orders carry high-risk labels; {context['unscored']:,} orders have no {source} probability."
        if scored.empty:
            return text + " Broaden the date range to inspect available scores."
        daily = scored.assign(day=pd.to_datetime(scored.Date).dt.normalize()).groupby("day")["Risk Probability"].agg(["mean", "count"])
        if len(daily) >= 2:
            previous, latest = daily.iloc[-2], daily.iloc[-1]
            change = (latest["mean"] - previous["mean"]) * 100
            text += f" Last two available days: mean risk changed {change:+.1f} percentage points ({int(previous['count']):,} → {int(latest['count']):,} scored orders)."
        return text + " Inspect the highest scored orders first; these historical scores do not establish causes."
    if {"Actual Demand", "Forecast Demand"}.issubset(frame):
        units = "next-day web visits" if frame.attrs.get("verified_artifacts") else "illustrative demo units"
        grain = "product/day observations" if frame.attrs.get("verified_artifacts") else "synthetic planning records"
        return f"{len(frame):,} {grain} forecast {frame['Forecast Demand'].sum():,.0f} {units}. Review forecast errors and interval coverage before planning; inventory availability is not supplied." if frame.attrs.get("verified_artifacts") else f"{len(frame):,} {grain} forecast {frame['Forecast Demand'].sum():,.0f} {units}. These fixture values demonstrate the interface."
    return "Review source coverage before interpreting the selected records."
