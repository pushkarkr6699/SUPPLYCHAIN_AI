"""Actual source availability, independent source filters and visible coverage."""
import pandas as pd

FAMILIES = {'delivery': 'Delivery orders', 'demand': 'Demand web visits',
            'profitability': 'Profitability line items', 'delivery_final': 'Final delivery line items'}


def connected_sources(service, contexts=None):
    result = {}
    for dataset, label in FAMILIES.items():
        try:
            frame = service.records((contexts or {}).get(dataset, {}), dataset=dataset)
            connected = bool(frame.attrs.get('verified_artifacts'))
            period = (f'{frame.Date.min():%d %b %Y} – {frame.Date.max():%d %b %Y}'
                      if len(frame) and 'Date' in frame else 'No matching dated records')
            result[dataset] = {'label': label, 'available': connected, 'frame': frame,
                               'rows': len(frame), 'period': period,
                               'status': 'Connected historical data' if connected else 'Synthetic demonstration',
                               'source': frame.attrs.get('data_source', 'Synthetic fixtures')}
        except (OSError, ValueError, RuntimeError, pd.errors.ParserError):
            result[dataset] = {'label': label, 'available': False, 'frame': None,
                               'rows': None, 'period': 'Unavailable',
                               'status': 'Source unavailable',
                               'source': 'Install the registered source files and validate their hashes.'}
    return result
