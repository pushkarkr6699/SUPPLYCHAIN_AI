"""Deterministic profiles and recommendations; no invented model outputs."""
import numpy as np
import pandas as pd
from services.privacy import minimize


def profile(frame):
    frame = minimize(frame)
    fields = []
    for column in frame:
        values = frame[column].dropna()
        numbers = pd.to_numeric(values, errors='coerce')
        numeric = bool(len(values) and numbers.notna().all() and np.isfinite(numbers.astype(float)).all()
                       and not pd.api.types.is_datetime64_any_dtype(values))
        row = {'Field': column, 'Type': str(frame[column].dtype), 'Missing': int(frame[column].isna().sum()),
               'Missing %': round(float(frame[column].isna().mean() * 100), 2), 'Distinct': int(values.nunique()),
               'Constant': bool(len(values) and values.nunique() == 1), 'Numeric candidate': numeric}
        lower=column.lower()
        row['Role hint']='Identifier' if lower.endswith((' id','_id')) or lower in {'id','order','identifier'} else 'Coordinates' if lower in {'lat','latitude','lon','longitude','lng'} else 'Probability / prediction' if 'probability' in lower or 'predicted' in lower or 'forecast' in lower else 'Target / outcome' if 'actual' in lower or 'target' in lower else 'Date' if pd.api.types.is_datetime64_any_dtype(values) or 'date' in lower else 'Measure' if numeric else 'Category'
        if row['Role hint']=='Identifier':numeric=False;row['Numeric candidate']=False
        if numeric:
            q1, q3 = numbers.quantile([.25, .75]); iqr = q3 - q1
            row.update(Minimum=float(numbers.min()), Maximum=float(numbers.max()), Mean=float(numbers.mean()),
                       Median=float(numbers.median()), IQR_outliers=int(((numbers < q1 - 1.5 * iqr) | (numbers > q3 + 1.5 * iqr)).sum()) if len(numbers) >= 4 else None)
        if pd.api.types.is_datetime64_any_dtype(values):
            row.update(First_date=str(values.min()), Last_date=str(values.max()))
        fields.append(row)
    return {'rows': len(frame), 'columns': len(frame.columns), 'memory_bytes': int(frame.memory_usage(deep=True).sum()),
            'duplicate_rows': int(frame.duplicated().sum()), 'missing_cells': int(frame.isna().sum().sum()),
            'fields': pd.DataFrame(fields), 'privacy': frame.attrs.get('privacy', {}),
            'outlier_rule': 'Outside Q1 - 1.5 * IQR or Q3 + 1.5 * IQR, at least four observations. Unusual values are not automatically errors.'}


def recommendations(frame):
    numeric = [c for c in frame if pd.api.types.is_numeric_dtype(frame[c])]
    dimensions = [c for c in frame if c not in numeric and not pd.api.types.is_datetime64_any_dtype(frame[c])]
    result = []
    if numeric:
        result += [('Histogram', 'Inspect numeric distributions and unusual observations.'), ('Box plot', 'Compare spread, median and tails without treating outliers as errors.')]
    if dimensions and numeric:
        result += [('Horizontal bars', 'Compare numeric measures across available categories.'), ('Donut', 'Show category record counts; probabilities are not additive sizes.')]
    if len(numeric) >= 2:
        result += [('Scatter', 'Investigate paired numeric associations; correlation does not establish causality.'), ('Correlation heatmap', 'Compare relationships using paired finite values.')]
    if 'Date' in frame and pd.api.types.is_datetime64_any_dtype(frame.Date) and numeric:
        result += [('Line', 'Track measured changes in chronological order.'), ('Moving average', 'Smooth an observed series with a disclosed three-period window; this is not a future forecast.')]
    return pd.DataFrame(result, columns=['Suggested visualization', 'Why'])
