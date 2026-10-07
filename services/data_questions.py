"""Controlled natural-language questions over the current frame; no generated code."""
import re
import pandas as pd
from services import parameter_comparison as analysis
from services.privacy import minimize


def answer(frame, question):
    frame=minimize(frame)
    text=question.strip()
    if not text or len(text)>1000:raise ValueError('Ask a question of at most 1,000 characters.')
    if re.search(r'\b(exec|eval|import|execute|shell|powershell|subprocess|delete|drop|insert|update|password|secret|api.key)\b|__|\.env|https?://',text,re.I):
        raise ValueError('Only read-only questions about the active dataset are supported. Code, SQL, files and credentials cannot be accessed.')
    found=[c for c in sorted(frame.columns,key=len,reverse=True) if re.search(r'(?<!\w)'+re.escape(c)+r'(?!\w)',text,re.I)]
    metrics=[c for c in found if pd.api.types.is_numeric_dtype(frame[c])]
    groups=[c for c in found if c not in metrics and not pd.api.types.is_datetime64_any_dtype(frame[c])]
    if re.search(r'\bby\b',text,re.I) and not groups and 'Date' not in found:
        raise ValueError('Name an existing grouping field after "by". No missing field is guessed.')
    if not metrics:raise ValueError('Name an existing numeric measure. Available measures: '+', '.join(c for c in frame if pd.api.types.is_numeric_dtype(frame[c])))
    if len(metrics)>4 or len(groups)>2:raise ValueError('Specify up to four measures and two grouping fields.')
    operation='Sum' if re.search(r'\b(sum|total)\b',text,re.I) else 'Median' if re.search(r'\bmedian\b',text,re.I) else 'Mean'
    if operation=='Sum' and any('probability' in c.lower() or pd.api.types.is_bool_dtype(frame[c]) for c in metrics):raise ValueError('Use average for probabilities and Boolean proportions; these are not additive totals.')
    period='Month' if re.search(r'\b(month|monthly)\b',text,re.I) else 'Week' if re.search(r'\b(week|weekly)\b',text,re.I) else 'Day'
    intent='comparison';kind='Horizontal bars'
    if re.search(r'\b(correlation|correlate)\b',text,re.I):
        if len(metrics)<2:raise ValueError('Correlation needs at least two numeric fields.')
        table=analysis.clean_numeric(frame,metrics).corr(min_periods=3);intent='correlation';kind='Correlation heatmap'
    elif re.search(r'\b(anomalies|outliers|unusual)\b',text,re.I):
        series=analysis.clean_numeric(frame,[metrics[0]])[metrics[0]]
        if series.count()<4:raise ValueError('At least four finite values are required for IQR outliers.')
        q1,q3=series.quantile([.25,.75]);iqr=q3-q1
        table=frame.loc[(series<q1-1.5*iqr)|(series>q3+1.5*iqr),found].copy();intent='IQR outliers';kind='Box plot'
    else:
        if re.search(r'\b(trend|monthly|weekly|over time)\b',text,re.I):
            if 'Date' not in frame or not pd.api.types.is_datetime64_any_dtype(frame.Date):raise ValueError('Apply an actual time field before requesting a trend.')
            groups=['Date',*groups][:2];intent='trend';kind='Line'
        elif re.search(r'\b(distribution|histogram)\b',text,re.I):intent='distribution';kind='Histogram'
        elif re.search(r'\btop\b',text,re.I):
            if not groups:raise ValueError('Top-N requires an existing grouping field, such as Market or Product.')
            intent='top-N'
        elif not re.search(r'\b(compare|comparison|average|mean|sum|total|median|by|show)\b',text,re.I):
            raise ValueError('Try top 10 [group] by [measure], trend [measure] monthly, distribution [measure], correlation [A] and [B], or anomalies [measure].')
        table=analysis.comparison(frame,groups,metrics,operation,period)
        if intent=='top-N':
            match=re.search(r'\btop\s+(\d+)\b',text,re.I);n=int(match.group(1)) if match else 10
            if not 1<=n<=50:raise ValueError('Choose a top-N value from 1 to 50.')
            table=table.sort_values(metrics[0],ascending=False,kind='stable').head(n)
    return {'intent':intent,'table':table,'chart':kind,'groups':groups,'metrics':metrics,'operation':operation,'period':period,
            'note':f'{len(frame):,} selected records; {operation} unless a distribution/correlation/IQR method is stated. Missing values are not zero. Historical association is not causality or a guaranteed prediction.'}
