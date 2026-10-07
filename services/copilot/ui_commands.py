"""Bounded natural-language UI commands with validated, fixed actions."""
import re
import pandas as pd
from components.navigation import ROUTES
from services.provider import FILTER_COLUMNS
from services.copilot.intent import unsafe_request
from services.privacy import minimize

TYPES={'OPEN_PAGE','APPLY_FILTER','CLEAR_FILTER','SELECT_RECORD','SELECT_SEGMENT','SHOW_CHART','SHOW_TABLE','SHOW_MAP','RUN_ANALYSIS','RUN_SCENARIO','OPEN_REPORT','DOWNLOAD_RESULT'}


def parse(question,frame,selected_order=None):
    text=str(question).strip();query=text.casefold()
    if len(text)>1000 or unsafe_request(text):return None
    action=None
    if query in {'clear filters','reset filters'}:action={'type':'CLEAR_FILTER'}
    elif query in {'open report','open reports'}:action={'type':'OPEN_REPORT','route':'reports'}
    elif query=='download result':action={'type':'DOWNLOAD_RESULT'}
    elif query in {'show chart','show table','show map'}:action={'type':{'show chart':'SHOW_CHART','show table':'SHOW_TABLE','show map':'SHOW_MAP'}[query]}
    elif query.startswith('open '):
        value=query[5:]
        route=next((r for r,details in ROUTES.items() if value in {r,details[0].casefold()}),None)
        if route is None:raise ValueError('Choose a page from the existing sidebar.')
        action={'type':'OPEN_PAGE','route':route}
    elif query.startswith(('select order ','select record ')):
        value=text.split(' ',2)[2]
        if 'Order' not in frame:raise ValueError('This source has no validated order identifier.')
        matched=frame.loc[frame.Order.astype(str).str.casefold().eq(value.casefold()),'Order']
        if matched.empty:raise ValueError('That record is outside the selected data.')
        action={'type':'SELECT_RECORD','record':matched.iloc[0],'route':'orders'}
    elif query.startswith(('filter ','select segment ')):
        match=re.fullmatch(r'(?:filter|select segment) (.+?) (?:to|=) (.+)',text,flags=re.I)
        if not match:raise ValueError('Use filter Market to Europe or select segment Market = Europe.')
        field=next((c for c in FILTER_COLUMNS if c in frame and c.casefold()==match[1].casefold()),None)
        if field is None:raise ValueError('Choose an available categorical workspace filter.')
        matched=frame.loc[frame[field].astype(str).str.casefold().eq(match[2].casefold()),field]
        if matched.empty:raise ValueError('The filter value is outside the current selection.')
        action={'type':'SELECT_SEGMENT' if query.startswith('select segment') else 'APPLY_FILTER','field':field,'values':[matched.iloc[0]]}
    elif query.startswith(('analyze ','analyse ')):action={'type':'RUN_ANALYSIS','question':text.split(' ',1)[1]}
    elif query.startswith('simulate shipping mode '):
        if frame.attrs.get('dataset') not in {'delivery',None} or not frame.attrs.get('verified_artifacts') or not {'Order','Shipping Mode'}.issubset(frame):
            raise ValueError('This scenario requires registered order-level delivery data.')
        value=text[len('simulate shipping mode '):]
        matched=frame.loc[frame['Shipping Mode'].astype(str).str.casefold().eq(value.casefold()),'Shipping Mode']
        if matched.empty:raise ValueError('Choose a shipping mode observed in this selection.')
        record=selected_order if selected_order in set(frame.Order) else frame.Order.iloc[0]
        action={'type':'RUN_SCENARIO','record':record,'shipping':matched.iloc[0]}
    return action


def present(action,frame):
    """Read-only presentation; state/model actions require an explicit UI click."""
    table=minimize(frame).head(500).copy() if action['type'] in {'SHOW_TABLE','DOWNLOAD_RESULT'} else frame.head(0).copy()
    result={'table':table,'figure':None,'note':'Requested action: '+action['type'].replace('_',' ').lower()+'.'}
    if action['type'] in {'SHOW_TABLE','DOWNLOAD_RESULT'}:result['note']='Current filtered result, limited to the first 500 records; privacy exclusions apply. Use Downloads for the complete dataset export.'
    if action['type']=='RUN_ANALYSIS':
        from services.data_questions import answer
        value=answer(frame,action['question']);result.update(table=value['table'],figure=value.get('figure'),note=value['note'])
    if action['type'] in {'SHOW_CHART','SHOW_MAP'}:
        from services import visualization_service as viz
        numeric=[c for c in ['Risk Probability','Forecast Demand','Sales','Profit'] if c in frame and pd.api.types.is_numeric_dtype(frame[c])]
        numeric=numeric or [c for c in frame if pd.api.types.is_numeric_dtype(frame[c]) and 'id' not in c.casefold()][:1]
        if not numeric:raise ValueError('Select a dataset with an actual numeric measure for this chart.')
        group=next((c for c in ['Market','Category','Region','Product'] if c in frame),None)
        value=viz.build(frame,'Coordinate map' if action['type']=='SHOW_MAP' else 'Horizontal bars',[group] if group else [],numeric[:1],'Mean')
        result.update(table=value['table'],figure=value['figure'],note=value['note'])
    return result


def apply(action,frame):
    """Revalidate against the current frame before changing session state."""
    import streamlit as st
    from services.access_control import require
    from components.navigation import go
    from services.audit_log import record
    if not isinstance(action,dict) or action.get('type') not in TYPES:raise ValueError('Unsupported command.')
    require('view');kind=action['type']
    if kind in {'OPEN_PAGE','OPEN_REPORT'}:
        if action.get('route') not in ROUTES:raise ValueError('Unknown workspace page.')
        go(action['route'])
    elif kind in {'APPLY_FILTER','SELECT_SEGMENT'}:
        from services.copilot.validation import validate_filter
        field,values=validate_filter(frame,action['field'],action['values'])
        if field not in FILTER_COLUMNS:raise ValueError('Unsupported workspace filter.')
        filters=dict(st.session_state.get('filters',{}));filters[field]=values
        _filters(filters,field)
    elif kind=='CLEAR_FILTER':_filters({})
    elif kind=='SELECT_RECORD':
        if 'Order' not in frame or action.get('record') not in set(frame.Order):raise ValueError('The record is no longer selected.')
        go('orders',selected_order=action['record'])
    elif kind=='RUN_SCENARIO':
        require('predict')
        if not frame.attrs.get('verified_artifacts') or frame.attrs.get('dataset') not in {None,'delivery'} or 'Order' not in frame or action.get('record') not in set(frame.Order):raise ValueError('The baseline is no longer an eligible delivery order.')
        if action.get('shipping') not in set(frame['Shipping Mode']):raise ValueError('The shipping mode is no longer available.')
        from services.inference_service import input_rows,predict_delivery
        base=input_rows([action['record']]);alternative=base.copy();alternative['Shipping Mode']=action['shipping']
        before=float(predict_delivery(base)['Risk Probability'].iloc[0]);after=float(predict_delivery(alternative)['Risk Probability'].iloc[0])
        record('scenario_executed',model='delivery',rows=1)
        return {'Baseline Risk':before,'Scenario Risk':after,'Difference pp':100*(after-before)}
    else:raise ValueError('This read-only command is presented directly; no state action is needed.')
    return None


def _filters(filters,field=None):
    import streamlit as st
    from services.audit_log import record
    dataset=st.session_state.get('active_filter_dataset','delivery')
    st.session_state.filters=filters
    st.session_state.setdefault('filters_by_dataset',{})[dataset]=dict(filters)
    for key in list(st.session_state):
        if key.startswith('filter_') and (field is None or key in {'filter_'+field,'filter_'+field+'_'+dataset}):del st.session_state[key]
    record('filters_changed')
