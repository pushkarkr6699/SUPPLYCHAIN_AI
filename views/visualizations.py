"""Visualization Studio: independent dataset boards with explicit field choices."""
from components.secure_actions import download_button
import json
import pandas as pd
import streamlit as st
from components.charts import show
from components.section_header import section
from services.provider import get_service
from services.export_service import csv_bytes
from services import visualization_service as viz, parameter_comparison as analysis
from services import visualization_config as saved
from services.privacy import minimize

SOURCES={'delivery':'Delivery orders','demand':'Demand forecasts','profitability':'Profitability line items','delivery_final':'Final delivery line observations'}


def board(frame,dataset,primary=False,label=None):
    frame=minimize(frame)
    prefix='viz_'+dataset
    has_dates='Date' in frame and pd.api.types.is_datetime64_any_dtype(frame['Date']) and frame['Date'].notna().any()
    section(label or SOURCES.get(dataset,'Demo workspace'),'Uploaded selection' if frame.attrs.get('uploaded') else 'Workspace filters' if primary else 'Independent source period; not joined to the primary dataset')
    if not primary and not frame.empty and has_dates:
        low,high=frame.Date.min().date(),frame.Date.max().date()
        dates=st.date_input('Additional source period',value=(low,high),min_value=low,max_value=high,key=prefix+'_period')
        if len(dates)!=2:st.info('Choose both start and end dates.');return
        frame=frame[frame.Date.ge(pd.Timestamp(dates[0])) & frame.Date.lt(pd.Timestamp(dates[1])+pd.Timedelta(days=1))].copy()
        frame.attrs['analysis_filters']=[*frame.attrs.get('analysis_filters',[]),{'field':'Date','date_bounds':[value.isoformat() for value in dates]}]
    if frame.empty:st.info('No matching records. Broaden this source period or reset workspace filters.');return
    fields,numeric=analysis.catalog(frame)
    if not numeric:st.info('This source has no numeric measures.');return
    model=frame.attrs.get('model_key',dataset)
    preferred=['Risk Probability','Actual Late','Predicted Late'] if model=='delivery_final' else ['Forecast Demand','Actual Demand','Predicted Visits'] if model=='demand' else ['Profit','Profitability Probability','Loss Probability'] if model=='profitability' else ['Risk Probability','Sales']
    defaults=list(dict.fromkeys([c for c in preferred if c in numeric]+numeric))[:2]
    group=next((c for c in ['Market','Category','Shipping Mode','Region'] if c in fields),None)
    if group is None and frame.attrs.get('uploaded'):
        group=next((c for c in fields if c not in numeric and not pd.api.types.is_datetime64_any_dtype(frame[c])),None)
    initial={'groups':[group] if group else [],'metrics':defaults,'operation':'Sum' if frame.attrs.get('generated_measure') else 'Mean','period':'Day','limit':20,'size':'Record count','charts':['Vertical bars','Line','Histogram']}
    initial.update(sort_by='Records',ascending=False)
    plan=st.session_state.get(prefix+'_plan',initial)
    plan={**initial,**plan,'groups':[c for c in plan['groups'] if c in fields],'metrics':[c for c in plan['metrics'] if c in numeric]}
    overrides=plan.get('overrides',[])
    plan['overrides']=[overrides[i] if i<len(overrides) else {} for i in range(len(plan['charts']))]
    with st.expander('Restore or reset this analysis board'):
        restore=st.file_uploader('Restore exported chart settings',type=['json'],key=prefix+'_restore',max_upload_size=1)
        if st.button('Restore settings',key=prefix+'_restore_apply',disabled=restore is None):
            try:
                st.session_state[prefix+'_plan']=saved.decode(restore.getvalue(),frame,dataset)
                _clear_builder(prefix)
                st.rerun()
            except ValueError as error:st.warning(str(error))
        if st.button('Reset analysis board',key=prefix+'_reset'):
            st.session_state[prefix+'_plan']=initial
            _clear_builder(prefix)
            st.rerun()
    period_label=f'{frame.Date.min():%d %b %Y} - {frame.Date.max():%d %b %Y}' if has_dates else 'No time axis selected'
    st.caption(f'{len(frame):,} records | '+period_label+' | '+str(frame.attrs.get('data_source','Synthetic demo workspace')))
    with st.form(prefix+'_builder'):
        a,b=st.columns(2)
        groups=a.multiselect('Grouping fields',fields,default=plan['groups'],max_selections=2,key=prefix+'_groups')
        metrics=b.multiselect('Numeric measures',numeric,default=plan['metrics'],max_selections=4,key=prefix+'_metrics')
        availability=viz.availability(frame,groups,metrics,st.session_state.get(prefix+'_operation',plan['operation']))
        reasons=dict(zip(availability.Visualization,availability.Requirement))
        enabled=[c for c in viz.CHART_TYPES if not reasons[c] or c in plan['charts']]
        charts=st.multiselect('Visualizations (25 options; up to 10 charts)',enabled,default=list(dict.fromkeys(plan['charts'])),format_func=lambda c:c+(' (requires fields/settings)' if reasons[c] else ''),max_selections=10,key=prefix+'_charts')
        a,b=st.columns(2)
        operation=a.selectbox('Calculation',list(analysis.OPERATIONS),index=list(analysis.OPERATIONS).index(plan['operation']),key=prefix+'_operation')
        period=b.selectbox('Time interval',['Day','Week','Month'],index=['Day','Week','Month'].index(plan['period']),key=prefix+'_time')
        a,b=st.columns(2)
        limit=a.slider('Visible groups',5,50,plan['limit'],step=5,key=prefix+'_limit')
        size=b.selectbox('Composition size',['Record count','First measure (sum)'],index=['Record count','First measure (sum)'].index(plan['size']),key=prefix+'_size')
        a,b=st.columns(2)
        sort_options=['Records',*metrics]
        sort_by=a.selectbox('Rank groups by',sort_options,index=sort_options.index(plan['sort_by']) if plan['sort_by'] in sort_options else 0,key=prefix+'_sort')
        ascending=b.checkbox('Ascending group order',value=plan['ascending'],key=prefix+'_ascending')
        applied=st.form_submit_button('Build visualizations',type='primary',width='stretch')
    if applied:
        plan={'groups':groups,'metrics':metrics,'charts':charts,'operation':operation,'period':period,'limit':limit,'size':size,'sort_by':sort_by,'ascending':ascending,'overrides':[{} for _ in charts]}
        st.session_state[prefix+'_plan']=plan
        from services.audit_log import record
        record('analysis_applied',rows=len(frame),charts=len(charts))
    st.caption('Charts use the applied choices above. Workspace/date filters refresh the data. X/Y use the first two selected measures; bubble size uses the third. Different measure units have separate panels. No model is trained or executed by a visualization.')
    with st.expander('Chart availability for the applied fields'):
        st.dataframe(viz.availability(frame,plan['groups'],plan['metrics'],plan['operation']),hide_index=True,width='stretch')
    if not plan['charts']:st.info('Choose one or more visualizations and click Build visualizations.');return
    try:table=viz.summary(frame,plan['groups'],plan['metrics'],plan['operation'],plan['period'],plan['limit'])
    except ValueError as error:st.warning(str(error));return
    st.caption('Measures: '+'; '.join(c+' - '+viz.units(c,frame) for c in plan['metrics']))
    for index,kind in enumerate(plan['charts']):
        with st.container(border=True,key=prefix+'_card_'+str(index)):
            st.subheader(kind)
            with st.expander('Edit, duplicate or arrange this chart'):
                edited=st.selectbox('Chart type',viz.CHART_TYPES,index=viz.CHART_TYPES.index(kind),key=prefix+'_edit_'+str(index))
                options={**{k:v for k,v in plan.items() if k not in {'charts','overrides'}},**plan['overrides'][index]}
                a,b=st.columns(2)
                edit_groups=a.multiselect('Chart grouping fields',fields,default=options['groups'],max_selections=2,key=prefix+'_edit_groups_'+str(index))
                edit_metrics=b.multiselect('Chart measures',numeric,default=options['metrics'],max_selections=4,key=prefix+'_edit_metrics_'+str(index))
                edit_operation=st.selectbox('Chart calculation',list(analysis.OPERATIONS),index=list(analysis.OPERATIONS).index(options['operation']),key=prefix+'_edit_operation_'+str(index))
                controls=st.columns(4)
                if controls[0].button('Apply changes',key=prefix+'_edit_apply_'+str(index)):
                    try:
                        viz.validate(frame,edit_groups,edit_metrics,edit_operation,options['limit'])
                        plan['charts'][index]=edited
                        plan['overrides'][index]={'groups':edit_groups,'metrics':edit_metrics,'operation':edit_operation,'sort_by':'Records'}
                        _save_card_plan(prefix,plan)
                    except ValueError as error:st.warning(str(error))
                if controls[1].button('Duplicate',disabled=len(plan['charts'])>=10,key=prefix+'_duplicate_'+str(index)):
                    plan['charts'].insert(index+1,kind);plan['overrides'].insert(index+1,dict(plan['overrides'][index]));_save_card_plan(prefix,plan)
                if controls[2].button('Move up',disabled=index==0,key=prefix+'_move_'+str(index)):
                    plan['charts'][index-1],plan['charts'][index]=plan['charts'][index],plan['charts'][index-1]
                    plan['overrides'][index-1],plan['overrides'][index]=plan['overrides'][index],plan['overrides'][index-1];_save_card_plan(prefix,plan)
                if controls[3].button('Remove',key=prefix+'_remove_'+str(index)):
                    plan['charts'].pop(index);plan['overrides'].pop(index);_save_card_plan(prefix,plan)
            try:result=viz.build(frame,kind,options['groups'],options['metrics'],options['operation'],options['period'],options['limit'],options['size'],options['sort_by'],options['ascending'])
            except ValueError as error:st.info(str(error));continue
            st.caption(result['note'])
            faceted=kind in {'Vertical bars','Horizontal bars','Line','Area','Histogram','Box plot','Violin plot','ECDF'}
            show(result['figure'],prefix+'_chart_'+str(index),height=max(320,200*len(options['metrics'])) if faceted else 380,preserve_axis_titles=True)
            st.caption('Source: '+str(frame.attrs.get('data_source','Synthetic demo workspace'))+' | '+f'{len(frame):,} selected records. Chart display limits are stated above.')
            download_button('Download this chart analysis',csv_bytes(result['table'],frame.attrs.get('data_source')),'chart_'+str(index+1)+'_analysis.csv','text/csv',key=prefix+'_card_csv_'+str(index),on_click='ignore',container=st)
    report_signature=analysis.signature(frame,{'dataset':dataset,'plan':plan})
    generated_report=st.session_state.get(prefix+'_pdf')
    current_report=bool(generated_report and generated_report['signature']==report_signature)
    with st.expander('Analysis table and downloads',expanded=current_report):
        st.caption('Complete grouped values, record counts and valid-value coverage. Chart group/sample limits do not truncate this table export.')
        st.dataframe(table.head(1000),hide_index=True,width='stretch')
        if len(table)>1000:st.caption(f'Preview: first 1,000 of {len(table):,} groups. Download includes every group.')
        download_button('Download analysis CSV',csv_bytes(table,frame.attrs.get('data_source')),dataset+'_visualization_analysis.csv','text/csv',key=prefix+'_csv',on_click='ignore', container=st)
        download_button('Download chart settings',saved.encode(frame,dataset,plan),dataset+'_chart_settings.json','application/json',key=prefix+'_settings',on_click='ignore', container=st)
        from services.access_control import can
        if st.button('Generate analysis PDF',key=prefix+'_pdf_create',disabled=not can('export') or current_report):
            from services.analysis_report import create
            try:
                with st.spinner('Creating a report from the current selection...'):
                    report=create(frame,dataset,plan)
                st.session_state[prefix+'_pdf']={'signature':report_signature,'content':report}
                st.rerun()
            except (ValueError,TypeError,OSError):st.warning('This report could not be generated. Review the selected fields and retry.')
        if current_report:
            download_button('Download analysis PDF',generated_report['content'],'analysis_brief.pdf','application/pdf',key=prefix+'_pdf_download',on_click='ignore',container=st)
            st.success('Report ready: current selection, source version, measures and limitations included.')
        elif generated_report:
            st.caption('The data or chart settings changed. Generate a new report for the current selection.')
    st.caption('Zoom, pan, autoscale, reset, fullscreen and PNG export are available in each compatible chart toolbar. Composition charts use count/area controls instead of Cartesian axis zoom.')


def _clear_builder(prefix):
    for key in list(st.session_state):
        if key.startswith(prefix+'_edit_') or key in [prefix+s for s in ('_groups','_metrics','_charts','_operation','_time','_limit','_size','_sort','_ascending')]:
            del st.session_state[key]


def _save_card_plan(prefix,plan):
    st.session_state[prefix+'_plan']=plan
    _clear_builder(prefix)
    st.rerun()


def render(df):
    service=get_service();primary='demo' if service.demo else st.session_state.get('visualizations_dataset','delivery')
    section('Build a visual analysis board','Pick the source above, choose multiple graphs, and inspect relationships without changing your data.')
    choices=[] if service.demo else [c for c in SOURCES if c!=primary]
    if st.session_state.get('visualization_extra_sources'):
        st.session_state.visualization_extra_sources=[c for c in st.session_state.visualization_extra_sources if c in choices]
    extras=st.multiselect('Additional datasets (optional)',choices,format_func=lambda c:SOURCES[c],key='visualization_extra_sources')
    st.caption('The primary source follows workspace filters and Sevika. Additional sources have separate date ranges and field choices, start with their full history, and are never joined or treated as matching observations.')
    board(df,primary,True)
    from views.data_tools import questions, joins
    questions(df,'viz_primary')
    if not service.demo:joins(df,'viz_primary')
    for dataset in extras:
        with st.expander(SOURCES[dataset]+' - additional board',expanded=True):
            try:frame=service.records(dataset=dataset)
            except (RuntimeError,ValueError,OSError):st.warning('This source could not be loaded. Check Data Quality and retry the source selection.');continue
            board(frame,dataset)
    if not service.demo:
        _registered_sources()


def _registered_sources():
    from services.dataset_catalog import catalog, load
    entries=catalog()
    with st.expander('All registered source files and evaluation datasets'):
        st.caption('Validated project files only. Evaluation tables and legacy outputs retain their source roles; they are not substituted for current operational datasets.')
        st.dataframe(pd.DataFrame([{k:v for k,v in e.items() if k in {'Name','Role','Rows','Columns','Period','Status'}} for e in entries]),hide_index=True,width='stretch')
        ready={e['id']:e for e in entries if e['Status'] in {'READY','WARNING'}}
        selected=st.multiselect('Registered source boards',list(ready),format_func=lambda key:ready[key]['Name'],max_selections=3,key='registered_viz_sources')
    for key in selected:
        with st.expander(ready[key]['Name'],expanded=True):
            try:
                frame=load(key)
                board(frame,'registered_'+str(entries.index(ready[key])),True,ready[key]['Name'])
            except (ValueError,OSError):st.warning('This registered source is unavailable or changed. Check its registry and retry.')
