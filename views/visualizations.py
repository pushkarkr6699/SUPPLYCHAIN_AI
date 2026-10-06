"""Visualization Studio: independent dataset boards with explicit field choices."""
import json
import pandas as pd
import streamlit as st
from components.charts import show
from components.section_header import section
from services.provider import get_service
from services.export_service import csv_bytes
from services import visualization_service as viz, parameter_comparison as analysis

SOURCES={'delivery':'Delivery orders','demand':'Demand forecasts','profitability':'Profitability line items','delivery_final':'Final delivery line observations'}


def board(frame,dataset,primary=False):
    prefix='viz_'+dataset
    section(SOURCES.get(dataset,'Demo workspace'),'Workspace filters' if primary else 'Independent source period; not joined to the primary dataset')
    if not primary and not frame.empty:
        low,high=frame.Date.min().date(),frame.Date.max().date()
        dates=st.date_input('Additional source period',value=(low,high),min_value=low,max_value=high,key=prefix+'_period')
        if len(dates)!=2:st.info('Choose both start and end dates.');return
        frame=frame[frame.Date.ge(pd.Timestamp(dates[0])) & frame.Date.lt(pd.Timestamp(dates[1])+pd.Timedelta(days=1))].copy()
    if frame.empty:st.info('No matching records. Broaden this source period or reset workspace filters.');return
    fields,numeric=analysis.catalog(frame)
    if not numeric:st.info('This source has no numeric measures.');return
    preferred=['Risk Probability','Actual Late'] if dataset=='delivery_final' else ['Forecast Demand','Actual Demand'] if dataset=='demand' else ['Profit','Profitability Probability'] if dataset=='profitability' else ['Risk Probability','Sales']
    defaults=list(dict.fromkeys([c for c in preferred if c in numeric]+numeric))[:2]
    group=next((c for c in ['Market','Category','Shipping Mode','Region'] if c in fields),None)
    initial={'groups':[group] if group else [],'metrics':defaults,'operation':'Mean','period':'Day','limit':20,'size':'Record count','charts':['Vertical bars','Line','Histogram']}
    plan=st.session_state.get(prefix+'_plan',initial)
    plan={**initial,**plan,'groups':[c for c in plan['groups'] if c in fields],'metrics':[c for c in plan['metrics'] if c in numeric]}
    st.caption(f'{len(frame):,} records | {frame.Date.min():%d %b %Y} - {frame.Date.max():%d %b %Y} | '+str(frame.attrs.get('data_source','Synthetic demo workspace')))
    with st.form(prefix+'_builder'):
        a,b=st.columns(2)
        groups=a.multiselect('Grouping fields',fields,default=plan['groups'],max_selections=2,key=prefix+'_groups')
        metrics=b.multiselect('Numeric measures',numeric,default=plan['metrics'],max_selections=4,key=prefix+'_metrics')
        charts=st.multiselect('Visualizations (18 options)',viz.CHART_TYPES,default=plan['charts'],max_selections=8,key=prefix+'_charts')
        a,b=st.columns(2)
        operation=a.selectbox('Calculation',list(analysis.OPERATIONS),index=list(analysis.OPERATIONS).index(plan['operation']),key=prefix+'_operation')
        period=b.selectbox('Time interval',['Day','Week','Month'],index=['Day','Week','Month'].index(plan['period']),key=prefix+'_time')
        a,b=st.columns(2)
        limit=a.slider('Visible groups',5,50,plan['limit'],step=5,key=prefix+'_limit')
        size=b.selectbox('Composition size',['Record count','First measure (sum)'],index=['Record count','First measure (sum)'].index(plan['size']),key=prefix+'_size')
        applied=st.form_submit_button('Build visualizations',type='primary',width='stretch')
    if applied:
        plan={'groups':groups,'metrics':metrics,'charts':charts,'operation':operation,'period':period,'limit':limit,'size':size}
        st.session_state[prefix+'_plan']=plan
    st.caption('Charts use the applied choices above. Workspace/date filters refresh the data. X/Y use the first two selected measures; bubble size uses the third. Different measure units have separate panels. No model is trained or executed by a visualization.')
    if not plan['charts']:st.info('Choose one or more visualizations and click Build visualizations.');return
    try:table=viz.summary(frame,plan['groups'],plan['metrics'],plan['operation'],plan['period'],plan['limit'])
    except ValueError as error:st.warning(str(error));return
    st.caption('Measures: '+'; '.join(c+' - '+viz.units(c,frame) for c in plan['metrics']))
    for index,kind in enumerate(plan['charts']):
        with st.container(border=True,key=prefix+'_card_'+str(index)):
            st.subheader(kind)
            try:result=viz.build(frame,kind,plan['groups'],plan['metrics'],plan['operation'],plan['period'],plan['limit'],plan['size'])
            except ValueError as error:st.info(str(error));continue
            st.caption(result['note'])
            faceted=kind in {'Vertical bars','Horizontal bars','Line','Area','Histogram','Box plot','Violin plot','ECDF'}
            show(result['figure'],prefix+'_chart_'+str(index),height=max(320,200*len(plan['metrics'])) if faceted else 380,preserve_axis_titles=True)
            st.caption('Source: '+str(frame.attrs.get('data_source','Synthetic demo workspace'))+' | '+f'{len(frame):,} selected records. Chart display limits are stated above.')
    with st.expander('Analysis table and downloads'):
        st.caption('Complete grouped values, record counts and valid-value coverage. Chart group/sample limits do not truncate this table export.')
        st.dataframe(table.head(1000),hide_index=True,width='stretch')
        if len(table)>1000:st.caption(f'Preview: first 1,000 of {len(table):,} groups. Download includes every group.')
        st.download_button('Download analysis CSV',csv_bytes(table,frame.attrs.get('data_source')),dataset+'_visualization_analysis.csv','text/csv',key=prefix+'_csv',on_click='ignore')
        st.download_button('Download chart settings',json.dumps({'dataset':dataset,'records':len(frame),'period':[str(frame.Date.min()),str(frame.Date.max())],'source':frame.attrs.get('data_source'),**plan},indent=2).encode(),dataset+'_chart_settings.json','application/json',key=prefix+'_settings',on_click='ignore')
    st.caption('Zoom, pan, autoscale, reset, fullscreen and PNG export are available in each compatible chart toolbar. Composition charts use count/area controls instead of Cartesian axis zoom.')


def render(df):
    service=get_service();primary='demo' if service.demo else st.session_state.get('visualizations_dataset','delivery')
    section('Build a visual analysis board','Pick the source above, choose multiple graphs, and inspect relationships without changing your data.')
    choices=[] if service.demo else [c for c in SOURCES if c!=primary]
    if st.session_state.get('visualization_extra_sources'):
        st.session_state.visualization_extra_sources=[c for c in st.session_state.visualization_extra_sources if c in choices]
    extras=st.multiselect('Additional datasets (optional)',choices,format_func=lambda c:SOURCES[c],key='visualization_extra_sources')
    st.caption('The primary source follows workspace filters and Sevika. Additional sources have separate date ranges and field choices, start with their full history, and are never joined or treated as matching observations.')
    board(df,primary,True)
    for dataset in extras:
        with st.expander(SOURCES[dataset]+' - additional board',expanded=True):
            try:frame=service.records(dataset=dataset)
            except (RuntimeError,ValueError,OSError):st.warning('This source could not be loaded. Check Data Quality and retry the source selection.');continue
            board(frame,dataset)
