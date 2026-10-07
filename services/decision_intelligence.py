"""Transparent historical momentum, priority and opportunity calculations."""
import numpy as np
import pandas as pd


def momentum(frame,measure,operation='Mean',period='Day'):
    if 'Date' not in frame or not pd.api.types.is_datetime64_any_dtype(frame.Date) or measure not in frame:raise ValueError('Momentum requires an actual date and numeric measure.')
    if operation not in {'Mean','Sum'} or period not in {'Day','Week','Month'}:raise ValueError('Choose a supported aggregation and period.')
    data=frame[['Date',measure]].copy();data[measure]=pd.to_numeric(data[measure],errors='coerce').replace([np.inf,-np.inf],np.nan)
    dates=data.Date.dt.floor('D') if period=='Day' else data.Date.dt.to_period('W-SUN' if period=='Week' else 'M').dt.start_time
    grouped=data.assign(Period=dates).groupby('Period',observed=True)[measure]
    series=grouped.sum(min_count=1) if operation=='Sum' else grouped.mean()
    series=series.dropna().sort_index()
    if len(series)<3:raise ValueError('At least three observed periods with finite measures are needed for momentum and acceleration.')
    previous2,previous,current=map(float,series.tail(3))
    delta=current-previous;prior_delta=previous-previous2
    probability='probability' in measure.lower() or pd.api.types.is_bool_dtype(frame[measure])
    scale=100 if probability else 1
    state='STABLE' if abs(delta)<(.02 if probability else 1e-9) else ('INCREASING' if delta>0 else 'DECREASING')
    if probability and abs(delta)>=.05:state='RAPIDLY '+state
    return {'measure':measure,'operation':operation,'period':period,'level':current,'previous':previous,
            'momentum':delta*scale,'acceleration':(delta-prior_delta)*scale,
            'relative_change':delta/previous if previous else None,'change_units':'percentage points' if probability else 'source units',
            'state':state,'periods':[str(p) for p in series.tail(3).index],
            'series':series.rename('Observed value').reset_index(),
            'note':'Latest three observed nonempty bins; missing bins are not imputed. Partial periods and differing record volumes may affect comparison. This is historical change, not a prediction or causal effect.'}


def priorities(frame,dimension):
    if dimension not in frame or 'Risk Probability' not in frame:raise ValueError('Priority requires a real grouping field and supplied risk scores.')
    valid=frame.dropna(subset=['Risk Probability']).copy()
    if valid.empty:raise ValueError('No scored observations exist in this selection.')
    grouped=valid.groupby(dimension,dropna=False,observed=True)
    table=grouped['Risk Probability'].agg(Severity='mean',Scored_records='size').reset_index()
    table['Volume component']=table.Scored_records/table.Scored_records.max()
    weights={'Severity':.5,'Volume component':.3}
    if 'Sales' in valid:
        totals=grouped.Sales.sum(min_count=1).rename('Observed sales exposure').reset_index()
        table=table.merge(totals,on=dimension,validate='one_to_one')
        maximum=table['Observed sales exposure'].abs().max()
        if pd.notna(maximum) and maximum>0:
            table['Exposure component']=table['Observed sales exposure'].abs()/maximum;weights['Exposure component']=.2
    denominator=sum(weights.values())
    table['Investigation priority']=sum(table[c].fillna(0)*w for c,w in weights.items())/denominator*100
    return table.sort_values('Investigation priority',ascending=False,kind='stable'),{
        'formula':'100 * ('+' + '.join(f'{w:g} * {c}' for c,w in weights.items())+f') / {denominator:g}',
        'components':'Severity = mean supplied risk probability; volume = scored group count / largest scored group; exposure = absolute observed sales / largest absolute group sales when available.',
        'limitation':'Descriptive investigation ranking, not calibrated failure probability or monetary loss. All components use scored rows only; unscored records require separate review.'}


def opportunities(frame,dimension):
    if not {dimension,'Sales','Profit'}.issubset(frame):raise ValueError('Observed opportunities require actual sales and profit fields at the same grain.')
    table=frame.groupby(dimension,dropna=False,observed=True)[['Sales','Profit']].sum(min_count=1).reset_index()
    table['Observed margin']=table.Profit/table.Sales.where(table.Sales.ne(0))
    return table[table.Profit.gt(0)&table.Sales.gt(0)].sort_values('Profit',ascending=False,kind='stable')


def anomalies(frame, measure, period='Day'):
    """Describe observed temporal deviations without labelling them failures."""
    if period not in {'Day','Week','Month'} or 'Date' not in frame or not pd.api.types.is_datetime64_any_dtype(frame.Date):
        raise ValueError('Anomaly analysis requires a valid time field and Day, Week or Month interval.')
    data=frame[['Date']].copy()
    if measure=='Record volume':
        data['Value']=1.0
    elif measure=='Forecast error' and {'Actual Demand','Forecast Demand'}.issubset(frame):
        data['Value']=(pd.to_numeric(frame['Forecast Demand'],errors='coerce')-pd.to_numeric(frame['Actual Demand'],errors='coerce')).abs()
    elif measure in frame and pd.api.types.is_numeric_dtype(frame[measure]):
        data['Value']=pd.to_numeric(frame[measure],errors='coerce')
    else:raise ValueError('Choose an available numeric observation, record volume or aligned forecast error.')
    data.Value=data.Value.replace([np.inf,-np.inf],np.nan)
    dates=data.Date.dt.floor('D') if period=='Day' else data.Date.dt.to_period('W-SUN' if period=='Week' else 'M').dt.start_time
    groups=data.assign(Period=dates).groupby('Period',observed=True)
    operation='Mean' if 'probability' in measure.casefold() or measure=='Forecast error' else 'Sum'
    values=groups.Value.mean() if operation=='Mean' else groups.Value.sum(min_count=1)
    table=values.rename('Observed value').to_frame().join(groups.Value.count().rename('Valid observations')).dropna().reset_index()
    if len(table)<8:raise ValueError('At least eight observed periods with finite values are required for the IQR reference.')
    q1,q3=table['Observed value'].quantile([.25,.75]);spread=float(q3-q1)
    if spread<=0:raise ValueError('The observed interquartile range is zero; this method cannot provide a useful anomaly reference.')
    table['Reference median']=float(table['Observed value'].median())
    table['Deviation from median']=table['Observed value']-table['Reference median']
    table['Status']='NORMAL'
    unusual=(table['Observed value']<q1-1.5*spread)|(table['Observed value']>q3+1.5*spread)
    extreme=(table['Observed value']<q1-3*spread)|(table['Observed value']>q3+3*spread)
    table.loc[unusual,'Status']='UNUSUAL';table.loc[extreme,'Status']='HIGHLY UNUSUAL'
    return table,{'method':'IQR of observed '+period.lower()+' bins; '+operation.lower()+' of '+measure,
                  'q1':float(q1),'q3':float(q3),'iqr':spread,'ordinary_fences':[float(q1-1.5*spread),float(q3+1.5*spread)],
                  'extreme_fences':[float(q1-3*spread),float(q3+3*spread)],
                  'limitation':'Unusual does not mean a business problem. This descriptive reference uses the selected historical period, not an independently fitted detector. Missing bins are omitted; partial periods and differing coverage can affect deviations.'}
