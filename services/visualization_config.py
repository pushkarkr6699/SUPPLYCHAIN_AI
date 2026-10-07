"""Bounded portable chart configurations tied to the exact dataset/schema."""
import json
from hashlib import sha256
from datetime import datetime, timezone
from services.visualization_service import CHART_TYPES
from services.parameter_comparison import OPERATIONS

MAX_CHARTS = 10


def signature(frame, dataset):
    schema = [(c, str(frame[c].dtype)) for c in frame]
    version = frame.attrs.get('upload_digest') or frame.attrs.get('artifact_hash') or frame.attrs.get('source_sha256')
    if not version:
        version = sha256(__import__('pandas').util.hash_pandas_object(frame, index=True).values.tobytes()).hexdigest()
    selection_hash=sha256(__import__('pandas').util.hash_pandas_object(frame,index=True).values.tobytes()).hexdigest()
    return {'dataset': dataset, 'version': version, 'selection_hash':selection_hash,'schema_hash': sha256(json.dumps(schema).encode()).hexdigest()}


def encode(frame, dataset, plan):
    selection={'records':len(frame),'filters':frame.attrs.get('analysis_filters',[])}
    if 'Date' in frame and __import__('pandas').api.types.is_datetime64_any_dtype(frame.Date):
        selection['date_coverage']=[str(frame.Date.min()),str(frame.Date.max())]
    return json.dumps({'format': 'supplychain-analysis-v1', 'source': signature(frame, dataset),
                       'selection':selection,'saved_utc': datetime.now(timezone.utc).isoformat(), 'plan': plan}, indent=2).encode('utf-8')


def decode(data, frame, dataset):
    if len(data) > 65536:raise ValueError('Settings must be smaller than 64 KB.')
    try:
        value = json.loads(data)
        if value['format'] != 'supplychain-analysis-v1' or value['source'] != signature(frame, dataset):
            raise ValueError('This configuration belongs to different data, filters or field types. Restore the matching selection first.')
        plan = value['plan']
        validate(plan, frame)
        return plan
    except (KeyError, TypeError, UnicodeError, json.JSONDecodeError):
        raise ValueError('Invalid analysis settings. Use a configuration exported by this workspace.') from None


def validate(plan, frame):
    if not isinstance(plan, dict):raise ValueError('Invalid chart configuration.')
    if not isinstance(plan.get('charts'), list) or not 1 <= len(plan['charts']) <= MAX_CHARTS or any(c not in CHART_TYPES for c in plan['charts']):
        raise ValueError('Choose 1-10 supported visualizations.')
    if not isinstance(plan.get('groups'), list) or not isinstance(plan.get('metrics'), list):raise ValueError('Invalid field selections.')
    groups, metrics = plan['groups'], plan['metrics']
    import pandas as pd
    if len(groups) > 2 or not 1 <= len(metrics) <= 4 or len(set(groups + metrics)) != len(groups + metrics) or any(c not in frame for c in groups + metrics):raise ValueError('Configuration fields do not match this dataset.')
    if any(not pd.api.types.is_numeric_dtype(frame[c]) for c in metrics):raise ValueError('Configuration measures must be numeric.')
    if plan.get('operation') not in OPERATIONS or plan.get('period') not in {'Day','Week','Month'} or plan.get('size') not in {'Record count','First measure (sum)'}:
        raise ValueError('Unsupported chart settings.')
    if type(plan.get('limit')) is not int or not 5 <= plan['limit'] <= 50 or plan['limit'] % 5 or plan.get('sort_by', 'Records') not in ['Records', *metrics] or type(plan.get('ascending', False)) is not bool:
        raise ValueError('Invalid sorting or group limits.')
    overrides=plan.get('overrides',[])
    if not isinstance(overrides,list) or len(overrides) not in {0,len(plan['charts'])}:raise ValueError('Chart overrides must match the chart count.')
    for index,override in enumerate(overrides):
        if not isinstance(override,dict) or set(override)-{'groups','metrics','operation','sort_by'}:raise ValueError('Unsupported per-chart settings.')
        validate({**{k:v for k,v in plan.items() if k!='overrides'},**override,'charts':[plan['charts'][index]]},frame)
    return plan
