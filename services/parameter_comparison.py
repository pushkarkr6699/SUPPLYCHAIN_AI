"""Read-only, field-driven comparison calculations with explicit evidence."""
from hashlib import sha256
import json
import numpy as np
import pandas as pd
from pandas.api.types import is_numeric_dtype, is_bool_dtype, is_datetime64_any_dtype

OPERATIONS = {'Mean':'mean','Sum':'sum','Median':'median','Minimum':'min','Maximum':'max'}


def catalog(frame):
    numeric=[c for c in frame if is_numeric_dtype(frame[c]) or is_bool_dtype(frame[c])]
    dimensions=list(frame.columns)
    return dimensions, numeric


def clean_numeric(frame, metrics):
    return frame[metrics].apply(lambda s: pd.to_numeric(s,errors='coerce').astype(float)).replace([np.inf,-np.inf],np.nan)


def filter_field(frame, field, selection=None, bounds=None):
    if field not in frame: raise ValueError('Choose an available dataset field.')
    result=frame
    if selection:
        result=result[result[field].isin(selection)]
    if bounds is not None:
        if len(bounds)!=2 or bounds[0]>bounds[1]: raise ValueError('Choose an increasing numeric range.')
        result=result[pd.to_numeric(result[field],errors='coerce').between(*bounds)]
    return result.copy()


def cohorts(frame, field, left, right):
    if field not in frame: raise ValueError('Choose an available cohort field.')
    if not left or not right: raise ValueError('Select values for both cohorts.')
    if set(left)&set(right): raise ValueError('Cohorts must have different, non-overlapping values.')
    a=frame[frame[field].isin(left)].copy();b=frame[frame[field].isin(right)].copy()
    if a.empty or b.empty: raise ValueError('Both cohorts need matching records. Adjust filters or values.')
    a['Cohort']='A';b['Cohort']='B'
    result=pd.concat([a,b],ignore_index=True);result.attrs.update(frame.attrs)
    return result


def comparison(frame, dimensions, metrics, operation='Mean', period='Day'):
    if operation not in OPERATIONS: raise ValueError('Choose a supported aggregation.')
    if len(set(dimensions+metrics))!=len(dimensions+metrics): raise ValueError('Use each field once; a grouping field cannot also be a measure.')
    if not metrics or len(metrics)>8 or len(dimensions)>3: raise ValueError('Select 1–8 measures and up to 3 grouping fields.')
    if any(c not in frame for c in dimensions+metrics): raise ValueError('A selected field is unavailable in this dataset.')
    if any(not (is_numeric_dtype(frame[c]) or is_bool_dtype(frame[c])) for c in metrics): raise ValueError('Measures must be numeric or Boolean dataset fields.')
    data=frame.copy();data[metrics]=clean_numeric(data,metrics)
    for field in dimensions:
        if is_datetime64_any_dtype(data[field]):
            dates=pd.to_datetime(data[field])
            if period=='Day':data[field]=dates.dt.floor('D')
            elif period in {'Week','Month'}:data[field]=dates.dt.to_period('W-SUN' if period=='Week' else 'M').dt.start_time
            else:raise ValueError('Choose Day, Week or Month.')
    if not dimensions:
        result=pd.DataFrame({metric:[data[metric].sum(min_count=1) if operation=='Sum' else data[metric].agg(OPERATIONS[operation])] for metric in metrics})
        result['Records']=len(data)
        for metric in metrics:result[f'Valid · {metric}']=data[metric].count()
    else:
        grouped=data.groupby(dimensions,dropna=False,observed=True,sort=False)
        values=grouped[metrics].sum(min_count=1) if operation=='Sum' else grouped[metrics].agg(OPERATIONS[operation])
        result=values.join(grouped.size().rename('Records')).join(grouped[metrics].count().rename(columns=lambda c:f'Valid · {c}')).reset_index()
    result.attrs.update(frame.attrs)
    return result


def segment_labels(table, dimensions):
    if not dimensions: return pd.Series(['All selected records']*len(table),index=table.index)
    return table[dimensions].apply(lambda row:' · '.join(f'{c}: {"Missing" if pd.isna(row[c]) else str(row[c])}' for c in dimensions),axis=1)


def evidence(frame, table, dimensions, metrics, operation):
    facts=[]
    def add(title,text,metric=None,value=None,segment=None,**details):
        facts.append({'id':f'E{len(facts)+1}','title':title,'text':text,'metric':metric,'value':value,'segment':segment,**details})
    add('Analysis coverage',f'{len(frame):,} matching records across {len(table):,} comparison groups.',value=len(frame),groups=len(table))
    labels=segment_labels(table,dimensions)
    for metric in metrics:
        values=pd.to_numeric(table[metric],errors='coerce').dropna()
        valid=int(clean_numeric(frame,[metric])[metric].count());missing=len(frame)-valid
        add(f'{metric} coverage',f'{metric}: {valid:,} usable values; {missing:,} missing or non-finite values excluded.',metric,valid,missing=missing)
        if values.empty:
            add(f'{metric}: no measured values',f'No usable values for {metric} in the selected records.',metric)
            continue
        high=values.idxmax();low=values.idxmin()
        add(f'Highest {operation.lower()} {metric}',f'{labels.loc[high]} has the highest {operation.lower()} {metric}: {values.loc[high]:,.6g}, based on {int(table.loc[high,"Records"]):,} records.',metric,float(values.loc[high]),str(labels.loc[high]),records=int(table.loc[high,'Records']))
        if len(values)>1:
            add(f'{metric} spread',f'Highest minus lowest {operation.lower()} {metric} is {values.max()-values.min():,.6g}; lowest group is {labels.loc[low]} ({values.loc[low]:,.6g}).',metric,float(values.max()-values.min()),str(labels.loc[low]),lowest_value=float(values.loc[low]))
    if len(metrics)>1:
        corr=clean_numeric(frame,metrics).corr(min_periods=3)
        candidates=[(abs(corr.loc[a,b]),a,b,float(corr.loc[a,b])) for i,a in enumerate(metrics) for b in metrics[i+1:] if pd.notna(corr.loc[a,b])]
        if candidates:
            _,a,b,value=max(candidates)
            pairs=int(clean_numeric(frame,[a,b]).dropna().shape[0])
            add('Strongest selected association',f'{a} and {b}: Pearson r = {value:.3f} over {pairs:,} paired records. This is an association, not evidence of causation.',f'{a} / {b}',value,paired_records=pairs)
    return facts


def signature(frame, parameters):
    digest=sha256(pd.util.hash_pandas_object(frame,index=True).values.tobytes())
    digest.update(json.dumps(parameters,sort_keys=True,default=str).encode())
    digest.update(str(list(frame.columns)).encode())
    digest.update(json.dumps(frame.attrs,sort_keys=True,default=str).encode())
    return digest.hexdigest()


def narration_payload(facts, parameters, source):
    # Never send group labels, cohort values, raw rows, order IDs or product identifiers.
    segments={}
    safe=[]
    for fact in facts:
        segment=fact.get('segment')
        if segment is not None and segment not in segments:segments[segment]=f'Segment {len(segments)+1}'
        safe.append({'id':fact['id'],'metric':fact['metric'],'value':fact['value'],
                     'segment':segments.get(segment),'kind':fact['title'], 'details':{k:fact[k] for k in ['groups','missing','records','lowest_value','paired_records'] if k in fact}})
    return {'source':source,'grouping_fields':parameters['dimensions'],'measures':parameters['metrics'],
            'aggregation':parameters['operation'],'evidence':safe,'note':'Group labels are anonymized. Values are observational historical summaries; prediction evidence is explicitly marked when present.'}


def trained_predictions(frame, dataset):
    if not frame.attrs.get('verified_artifacts'):raise ValueError('Trained inference requires the connected verified dataset. Demo values remain illustrative.')
    if frame.empty:raise ValueError('Select matching records before running predictions.')
    if dataset=='delivery':
        from services.inference_service import input_rows,predict_delivery
        predictions=predict_delivery(input_rows(frame.Order.tolist()))
        predictions['Order']=predictions.pop('Order Id').astype(str)
        context=frame.drop(columns=['Risk Probability','Predicted Late','Risk','Correct Prediction'],errors='ignore')
        result=context.merge(predictions,on='Order',how='inner',validate='one_to_one')
        if len(result)!=len(frame):raise ValueError('Prediction order coverage does not match the selected cohort.')
        result.attrs.update(predictions.attrs,data_source='Registered Tuned XGBoost inference on selected delivery orders')
        return result
    if dataset=='demand':
        from services.demand_inference import registered,SOURCE,predict_next_day
        history=pd.read_csv(registered(SOURCE)[0]);history['DateOnly']=pd.to_datetime(history.DateOnly)
        history=history[history.Product.isin(frame.Product.unique()) & history.DateOnly.le(pd.to_datetime(frame.Date).max())]
        result=predict_next_day(history)
        result['Date']=result['Forecast Date']
        return result
    raise ValueError('Choose delivery or demand.')
