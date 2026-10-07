import pandas as pd
from services.analytics import summary


def compare_periods(df, current, previous):
    current_df = df[df.Date.dt.date.between(current[0], current[1])]
    previous_df = df[df.Date.dt.date.between(previous[0], previous[1])]
    return current_df, previous_df


def change_table(current, previous):
    a, b = summary(current), summary(previous)
    metrics = [("Delivery risk", "risk", True), ("High-risk orders", "high", False), ("Demand units", "actual", False), ("Forecast error (MAE)", "error", False), ("Stock attention", "stock", False), ("Order volume", "orders", False)]
    rows = []
    for name, key, rate in metrics:
        if a[key] is None or b[key] is None:
            continue
        difference = a[key] - b[key]
        rows.append({"Metric": name, "Current": a[key], "Comparison": b[key], "Absolute change": difference,
            "Percentage change": difference / b[key] if b[key] else None,
            "Percentage-point change": difference * 100 if rate else None,
            "Direction": "Observed increase" if difference > 0 else "Observed decrease" if difference < 0 else "No observed change"})
    return pd.DataFrame(rows)


def additive_contributions(current,previous,dimension,measure):
    """Reconcile additive segment deltas exactly; no causal attribution."""
    if any(c not in current or c not in previous for c in (dimension,measure)):raise ValueError('Choose available segment and additive measure fields.')
    if 'probability' in measure.lower() or not pd.api.types.is_numeric_dtype(current[measure]) or pd.api.types.is_bool_dtype(current[measure]):raise ValueError('Waterfall contributions require additive numeric amounts, not probabilities or proportions.')
    a=current.groupby(dimension,dropna=False,observed=True)[measure].sum(min_count=1)
    b=previous.groupby(dimension,dropna=False,observed=True)[measure].sum(min_count=1)
    # Absent segments contribute zero; all-null existing segments remain missing.
    labels=a.index.union(b.index)
    a=a.reindex(labels,fill_value=0);b=b.reindex(labels,fill_value=0)
    if a.isna().any() or b.isna().any():raise ValueError('All-null segment amounts cannot be treated as zero for a reconciled waterfall.')
    result=pd.DataFrame({'Current':a,'Previous':b,'Contribution':a-b}).reset_index()
    if abs(result.Contribution.sum()-(current[measure].sum()-previous[measure].sum()))>1e-6:raise ValueError('Contribution reconciliation failed.')
    return result

