"""Comparison Studio: dataset fields -> charts -> evidence -> trained predictions."""
from html import escape
import json
import pandas as pd
import plotly.express as px
import streamlit as st
from components.charts import show
from components.section_header import section
from services.provider import get_service
from services.export_service import csv_bytes
from services import parameter_comparison as analysis
from services import ai_narration


def graph(frame, table, dimensions, metrics, kind, operation, scale, limit, ascending, key):
    if not metrics or table.empty:
        st.info('No comparison values are available. Adjust fields or filters.');return
    sampled=frame.sample(min(5000,len(frame)),random_state=42)
    if kind=='Correlation heatmap':
        if len(metrics)<2:st.info('Choose at least two measures for a correlation heatmap.');return
        matrix=analysis.clean_numeric(frame,metrics).corr(min_periods=3)
        if matrix.notna().sum().sum()<=len(metrics):st.info('No measured correlations: choose non-constant fields with at least three paired values.');return
        fig=px.imshow(matrix,text_auto='.2f',zmin=-1,zmax=1,color_continuous_scale='RdBu_r',aspect='auto')
        st.caption('Pearson correlation on matching records; missing/non-finite pairs are excluded. Association does not establish causation.')
    elif kind=='Scatter':
        if len(metrics)<2:st.info('Choose at least two measures for a scatter plot.');return
        a,b=st.columns(2)
        x=a.selectbox('Scatter X',metrics,key=key+'_scatter_x');y=b.selectbox('Scatter Y',metrics,index=1,key=key+'_scatter_y')
        clean=analysis.clean_numeric(sampled,[x,y] if x!=y else [x]);fig=px.scatter(clean,x=x,y=y,opacity=.6)
        st.caption(f'{len(sampled):,} deterministically sampled rows of {len(frame):,}; axes use the original field units.')
    elif kind=='Distribution':
        long=analysis.clean_numeric(sampled,metrics).melt(var_name='Metric',value_name='Value').dropna()
        if long.empty:st.info('These measures have no usable values in the current selection.');return
        fig=px.histogram(long,x='Value',facet_col='Metric',facet_col_wrap=1,nbins=30)
        fig.update_xaxes(matches=None);fig.update_yaxes(matches=None)
        st.caption(f'Distribution of a stable sample of {len(sampled):,} matching rows; count axis refers to that sample. Units are specific to each field.')
    else:
        if kind=='Trend' and 'Date' in dimensions:
            shown=table.sort_values('Date',kind='stable').tail(limit).copy()
        else:
            shown=table.sort_values(metrics[0],ascending=ascending,na_position='last',kind='stable').head(limit).copy()
        shown['Segment']=analysis.segment_labels(shown,dimensions)
        tidy=[]
        for metric in metrics:
            part=shown[['Segment','Records',metric,f'Valid · {metric}']].rename(columns={metric:'Value',f'Valid · {metric}':'Valid values'})
            part['Metric']=metric
            if kind=='Trend' and 'Date' in dimensions:
                part['Date']=shown['Date']
                part['Series']=analysis.segment_labels(shown,[c for c in dimensions if c!='Date'])
            tidy.append(part)
        long=pd.concat(tidy,ignore_index=True).dropna(subset=['Value'])
        if long.empty:st.info('These measures have no usable values in the selected groups. Missing values are not displayed as zeros.');return
        if scale=='Index (max absolute = 100)':
            maximum=long.groupby('Metric').Value.transform(lambda s:s.abs().max())
            long['Value']=long.Value.div(maximum.where(maximum.ne(0),1))*100
        if kind=='Trend':
            if 'Date' not in dimensions:st.info('Add Date as a grouping field to draw a time trend.');return
            long=long.sort_values('Date')
            fig=px.line(long,x='Date',y='Value',color='Series',facet_col='Metric',facet_col_wrap=1,markers=True,hover_data=['Segment','Records','Valid values'])
        else:
            fig=px.bar(long,x='Segment',y='Value',facet_col='Metric',facet_col_wrap=1,hover_data=['Records','Valid values'])
        fig.update_yaxes(matches=None)
        if kind=='Comparison bars':
            fig.update_xaxes(tickmode='auto',nticks=8,tickangle=-35,automargin=True)
        ordering='latest dates in chronological order' if kind=='Trend' else 'sorted by '+metrics[0]
        st.caption(f'Chart shows {len(shown):,} of {len(table):,} groups, {ordering}. Evidence and export use the complete comparison. {scale}.')
    fig.update_layout(showlegend=kind=='Trend' and len(dimensions)>1,legend=dict(orientation='h',y=-.3))
    for annotation in fig.layout.annotations:
        if '=' in annotation.text:annotation.text=annotation.text.split('=',1)[1]
    show(fig,key,height=max(300,260*len(metrics)) if kind in {'Comparison bars','Trend','Distribution'} else 380,category_footer=kind=='Comparison bars')


def explanation(parameters, rows, groups):
    fields=', '.join(parameters['metrics'])
    steps=[('Select',fields),('Filter',f'{rows:,} matching rows'),('Calculate',parameters['operation']),('Compare',f'{groups:,} groups'),('Explain','Cited evidence and optional AI narration')]
    st.html('<div class="comparison-flow" role="list" aria-label="Comparison calculation flow">'+''.join(f'<div role="listitem"><b>{escape(a)}</b><span>{escape(b)}</span></div>' for a,b in steps)+'</div>')
    st.caption('Measures retain their source units. Mean/median exclude missing values; sums of entirely missing groups stay missing. Boolean means are proportions. Different units use separate panels or an explicitly labeled index.')


def predictions(frame, dataset, dimensions, metrics, token):
    st.caption('Your field choices control comparison and display. Trained models use their validated training features from the registered source; arbitrary field choices do not retrain a model.')
    if not frame.attrs.get('verified_artifacts'):
        st.info('Demo mode displays synthetic data. Switch to the verified provider to run the connected trained models.');return
    if dataset=='delivery_final':
        from views.final_delivery import prediction_view
        prediction_view(frame,'comparison_final_delivery');return
    if dataset=='profitability':
        from views.profitability import prediction_view
        prediction_view(frame,'comparison_profitability');return
    if dataset=='delivery':
        from services.inference_service import status
    else:
        from services.demand_inference import status
    availability=status()
    if not availability['available']:st.warning(availability['reason']);return
    st.caption(f'Delivery: all {len(frame):,} matching orders will be scored.' if dataset=='delivery' else 'Demand: forecasts are per selected product; cohort and measure filters select products, while the model uses their complete registered history. Forecasts use the selected products and at least 15 consecutive historical days ending on or before the selected period end. Earlier days are retained to construct model lags.')
    key='comparison_prediction_'+dataset
    saved=st.session_state.get(key)
    if st.button('Run trained predictions',key='comparison_run_prediction',type='primary',disabled=bool(saved and saved['token']==token)):
        try:
            with st.spinner('Running the validated trained model…'):
                result=analysis.trained_predictions(frame,dataset)
            st.session_state[key]={'token':token,'data':result}
            st.toast('Trained predictions generated for this selection.')
        except (ValueError,RuntimeError,OSError,KeyError) as exc:
            st.error(str(exc));return
    saved=st.session_state.get(key)
    if saved and saved['token']==token:
        result=saved['data'];metric='Risk Probability' if dataset=='delivery' else 'Predicted Visits'
        dims=[c for c in dimensions if c in result]
        grouped=analysis.comparison(result,dims,[metric],'Mean')
        graph(result,grouped,dims,[metric],'Comparison bars','Mean','Original units',20,False,'comparison_prediction_graph')
        columns=list(dict.fromkeys([c for c in ['Order','Product','Base Date','Forecast Date']+dims+metrics+[metric,'Predicted Late','Risk'] if c in result]))
        st.dataframe(result[columns],hide_index=True,width='stretch')
        st.download_button('Download trained predictions',csv_bytes(result[columns],result.attrs.get('data_source')),'comparison_predictions.csv','text/csv',key='comparison_prediction_export',on_click='ignore')
        st.success(f'{len(result):,} trained-model outputs · '+('Tuned XGBoost delivery probabilities' if dataset=='delivery' else 'XGBoost point forecasts in web visits'))
        st.caption('Historical inference on registered observations. These outputs are not a refreshed operational feed; retrospective training/test limitations still apply.')
    elif saved:
        st.info('The selection changed. Run predictions again to use the current comparison.')


def render(df):
    dataset=st.session_state.get('comparison_dataset','delivery');prefix='comparison_'+dataset
    section('Build your comparison','Choose only the dataset fields and factors relevant to your question.')
    if df.empty:st.info('No records match the workspace filters. Reset or broaden filters to start a comparison.');return
    dimensions,numeric=analysis.catalog(df)
    if not numeric:st.info('This dataset has no numeric measures to compare.');return
    frame=df.copy()
    with st.expander('Additional parameter filters'):
        selected=st.multiselect('Filter fields',list(df.columns),max_selections=4,key=prefix+'_filter_fields')
        for field in selected:
            if field in numeric and not pd.api.types.is_bool_dtype(df[field]):
                values=pd.to_numeric(df[field],errors='coerce').dropna()
                values=values[values.abs().ne(float('inf'))]
                if values.empty:st.caption(f'{field}: no measured values to filter.');continue
                low,high=float(values.min()),float(values.max())
                if low==high:st.caption(f'{field}: constant at {low:,.6g}');continue
                bound_key=prefix+'_bounds_'+field
                saved_bounds=st.session_state.get(bound_key)
                if saved_bounds and (saved_bounds[0]<low or saved_bounds[1]>high):
                    del st.session_state[bound_key]
                bounds=st.slider(field,min_value=low,max_value=high,value=(low,high),key=bound_key)
                frame=analysis.filter_field(frame,field,bounds=bounds)
            else:
                options=sorted(df[field].dropna().unique().tolist(),key=str)
                values=st.multiselect(field,options,key=prefix+'_values_'+field)
                frame=analysis.filter_field(frame,field,selection=values)
    if frame.empty:st.info('No rows match these parameter filters. Clear a selection or broaden a numeric range.');return
    mode=st.radio('Comparison factors',['Segments','Two cohorts'],horizontal=True,key=prefix+'_mode')
    cohort_meta={}
    if mode=='Two cohorts':
        categorical=[c for c in dimensions if c not in numeric or pd.api.types.is_bool_dtype(frame[c])]
        categorical=[c for c in categorical if c!='Date']
        if not categorical:st.info('This dataset has no categorical cohort fields. Use segment comparisons.');return
        field=st.selectbox('Cohort field',categorical,key=prefix+'_cohort_field')
        choices=sorted(frame[field].dropna().unique().tolist(),key=str)
        a,b=st.columns(2)
        left=a.multiselect('Cohort A values',choices,default=choices[:1],key=prefix+'_a_'+field)
        right=b.multiselect('Cohort B values',choices,default=choices[1:2],key=prefix+'_b_'+field)
        try:frame=analysis.cohorts(frame,field,left,right)
        except ValueError as exc:st.info(str(exc));return
        cohort_meta={'field':field,'A':left,'B':right}
    preferred=['Risk Probability','Actual Late'] if dataset=='delivery_final' else ['Risk Probability','Sales'] if dataset=='delivery' else ['Forecast Demand','Actual Demand']
    if dataset=='profitability':preferred=['Profitability Probability','Profit']
    defaults=[c for c in preferred if c in numeric] or numeric[:2]
    default_dimension=next((c for c in (['Market'] if dataset=='delivery' else ['Category','Product']) if c in dimensions),dimensions[0] if dimensions else None)
    group_key=prefix+'_groups'
    if mode=='Two cohorts' and len(st.session_state.get(group_key,[]))>2:
        st.session_state[group_key]=st.session_state[group_key][:2]
    with st.form('comparison_builder_'+dataset):
        a,b=st.columns(2)
        groups=a.multiselect('Group by dataset fields',dimensions,default=[default_dimension] if default_dimension else [],max_selections=2 if mode=='Two cohorts' else 3,key=prefix+'_groups')
        metrics=b.multiselect('Measures to compare',numeric,default=defaults,max_selections=8,key=prefix+'_metrics')
        a,b,c=st.columns(3)
        operation=a.selectbox('Comparison calculation',list(analysis.OPERATIONS),key=prefix+'_operation')
        kind=b.selectbox('Graph type',['Comparison bars','Trend','Scatter','Correlation heatmap','Distribution'],key=prefix+'_graph')
        period=c.selectbox('Date grouping',['Day','Week','Month'],key=prefix+'_period')
        a,b,c=st.columns(3)
        scale=a.selectbox('Scale',['Original units','Index (max absolute = 100)'],key=prefix+'_scale')
        limit=b.slider('Groups displayed',5,50,20,key=prefix+'_limit')
        ascending=c.checkbox('Show lowest values first',key=prefix+'_ascending')
        focus=st.selectbox('Analysis focus',['Explain differences','Find high values','Find low values','Find relationships','Planning priorities'],key=prefix+'_focus')
        st.form_submit_button('Apply comparison',type='primary',width='stretch')
    groups=(['Cohort'] if mode=='Two cohorts' else [])+groups
    parameters={'dimensions':groups,'metrics':metrics,'operation':operation,'period':period,'cohorts':cohort_meta,'focus':focus}
    try:table=analysis.comparison(frame,groups,metrics,operation,period)
    except ValueError as exc:st.info(str(exc));return
    token=analysis.signature(frame,parameters)
    facts=analysis.evidence(frame,table,groups,metrics,operation)
    st.caption(f'{len(frame):,} matching records · {len(table):,} complete comparison groups · {len(metrics)} selected measures · '+get_service().data_source_label(dataset))
    explanation(parameters,len(frame),len(table))
    charts,insights,prediction,export=st.tabs(['Graphs','Key insights','Predictions','Evidence & export'])
    with charts:
        graph(frame,table,groups,metrics,kind,operation,scale,limit,ascending,'comparison_main_graph')
    with insights:
        section('Evidence-based findings','Computed from your current fields, filters and comparison calculation.')
        for fact in facts:
            st.write(f"**{fact['id']} · {fact['title']}**")
            st.write(fact['text'])
        section('OpenAI analyst narrative','An interpretation of aggregate evidence with references to the calculations above.')
        state=ai_narration.status()
        st.caption('Only computed values and anonymized segment labels are sent to OpenAI. Raw records, order IDs, product names and cohort value selections stay local.')
        payload=analysis.narration_payload(facts,parameters,'Verified historical data' if frame.attrs.get('verified_artifacts') else 'Synthetic demonstration data');payload['focus']=focus;payload['limitations']=frame.attrs.get('evaluation_note','Historical data');payload['grain']=frame.attrs.get('grain','Dataset observations')
        if not state['available']:
            st.info(state['reason'])
            with st.expander('Configure AI narration'):
                st.code('OPENAI_API_KEY=your_key_here\nOPENAI_MODEL=gpt-4o-mini',language='bash')
                st.caption('Add these settings to the ignored project .env or your process environment. Never put the real key in a committed file. Retry when configured.')
        saved=st.session_state.get('comparison_narration')
        current=saved and saved['token']==token
        if st.button('Generate AI insights',key='comparison_generate_ai',disabled=not state['available'] or bool(current),type='primary'):
            try:
                with st.spinner('Interpreting the selected comparison evidence…'):
                    answer=ai_narration.narrate(payload)
                saved={'token':token,'answer':answer,'model':state['model']};st.session_state.comparison_narration=saved;current=True
            except ai_narration.NarrationUnavailable as exc:st.error(str(exc))
        if current:
            answer=saved['answer'];st.write(answer['summary'])
            lookup={f['id']:f for f in facts}
            for item in answer['insights']:
                st.write('**'+item['title']+'**');st.write(item['observation']);st.write('Suggested review: '+item['next_step'])
                for ref in item['evidence_ids']:st.caption(ref+' · '+lookup[ref]['text'])
            st.caption('AI interpretation · '+saved['model']+' · Verify the cited evidence before acting.')
        elif saved:st.caption('Previous AI narration belongs to another selection. Generate insights for the current comparison.')
    with prediction:
        predictions(frame,dataset,groups,metrics,token)
    with export:
        section('Complete comparison','All groups are included here; chart display limits do not change the analysis.')
        st.dataframe(table,hide_index=True,width='stretch')
        st.download_button('Download comparison CSV',csv_bytes(table,frame.attrs.get('data_source')),'parameter_comparison.csv','text/csv',key='comparison_csv',on_click='ignore')
        manifest={'parameters':parameters,'records':len(frame),'groups':len(table),'source':frame.attrs.get('data_source','Synthetic demo data'),'workspace_filters':st.session_state.get('filters',{}),'evidence':facts,'note':'Historical observations; association is not causation. No delivery-to-demand join.'}
        saved_narration=st.session_state.get('comparison_narration')
        if saved_narration and saved_narration['token']==token:
            manifest['ai_narration']={'model':saved_narration['model'],'answer':saved_narration['answer']}
        st.download_button('Download evidence brief',json.dumps(manifest,default=str,indent=2).encode(),'comparison_evidence.json','application/json',key='comparison_brief',on_click='ignore')
        st.dataframe(pd.DataFrame(facts)[['id','title','text']],hide_index=True,width='stretch')
        if 'Risk Probability' in metrics:st.caption('Unscored delivery orders keep missing probabilities; they are excluded from probability statistics and retained in row coverage.')
