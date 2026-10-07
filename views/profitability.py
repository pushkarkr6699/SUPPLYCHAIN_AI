"""Profitability UI: source-grain analytics, model diagnostics and gated trained inputs."""
from components.secure_actions import download_button
from hashlib import sha256
import pandas as pd
import numpy as np
import plotly.express as px
import streamlit as st
from services import profitability_data as data,profitability_inference as inference
from services.export_service import csv_bytes
from components.charts import show
from components.kpi_cards import kpis
from components.section_header import section


def feature_view(key):
    features=data.artifact('DataCo_Feature_Importance.csv').sort_values('Importance',ascending=False)
    section('Profitability feature importance','Supplied global ranking of 238 transformed features; this is not SHAP or a causal explanation.')
    show(px.bar(features.head(20).sort_values('Importance'),x='Importance',y='Feature',orientation='h'),key+'_importance',height=540)
    st.dataframe(features,hide_index=True,width='stretch')
    download_button('Download profitability feature importance',csv_bytes(features),'profitability_importance.csv','text/csv',key=key+'_importance_csv', container=st)


def drift_view(key):
    section('Profitability train/test drift','Supplied historical feature-mean comparison, not current operational monitoring.')
    drift=data.artifact('DataCo_Train_Test_Drift.csv')
    st.caption('Relative changes are absolute shifts. Constant-zero features have an undefined relative change. Identifier means require caution and do not establish distribution drift by themselves.')
    shown=drift.dropna(subset=['Relative_Change']).sort_values('Relative_Change',ascending=False)
    show(px.bar(shown,x='Relative_Change',y='Feature',orientation='h'),key+'_drift',height=440)
    st.dataframe(drift,hide_index=True,width='stretch')
    download_button('Download profitability drift reference',csv_bytes(drift),'profitability_train_test_drift.csv','text/csv',key=key+'_drift_csv', container=st)


def threshold_view(df,key):
    section('Profitability threshold analysis','Exploratory test-set calculations; the saved threshold stays 0.20.')
    threshold=st.slider('Profitability analysis threshold',0.,1.,.2,.01,key=key+'_threshold')
    if df.empty:st.info('No matching profitability rows.');return
    scores=data.evaluation(df,threshold)
    kpis([(name,scores[name],'percent','Selected line-item test rows') for name in ['Accuracy','Precision','Recall','F1']])
    points=[{'Threshold':float(t),**data.evaluation(df,float(t))} for t in np.linspace(0,1,51)]
    show(px.line(pd.DataFrame(points),x='Threshold',y=['Precision','Recall','F1']),key+'_threshold_plot',height=320)
    st.caption('Actual profitable rate is the always-profitable baseline. Raising a threshold here does not alter stored predictions or prove future performance.')
    with st.expander('Supplied threshold reference · separate evaluation context'):
        st.dataframe(data.artifact('DataCo_Threshold_Analysis.csv'),hide_index=True,width='stretch')


def model_diagnostics(df,key):
    st.warning(data.NOTE)
    scores=data.evaluation(df)
    if scores:st.dataframe(pd.DataFrame({'Metric':list(scores),'Selected test-row value':list(scores.values())}),hide_index=True,width='stretch')
    summary,comparison,calibration,features,drift=st.tabs(['Project summary','Model comparison','Calibration','Feature importance','Train/test drift'])
    with summary:
        st.dataframe(data.artifact('DataCo_Final_Project_Summary.csv'),hide_index=True,width='stretch')
        st.caption('The project summary reports test ROC-AUC 0.4978, train ROC-AUC 0.7538 and an AUC gap of 0.256. Accuracy largely reflects the profitable-class prevalence.')
    with comparison:
        reference=data.artifact('DataCo_Model_Comparison.csv');show(px.bar(reference,x='Model',y='ROC_AUC'),key+'_model_comparison',height=320)
        st.dataframe(reference,hide_index=True,width='stretch')
        st.caption('Supplied model comparison and tuning results are separate evaluation references. Their values differ from the final scored test rows; no notebook was supplied to independently establish the split procedure.')
        with st.expander('CatBoost tuning reference'):st.dataframe(data.artifact('DataCo_CatBoost_Tuning.csv'),hide_index=True,width='stretch')
    with calibration:
        reference=data.artifact('DataCo_Calibration_Check.csv');usable=reference[reference.Records.gt(0)]
        show(px.scatter(usable,x='Average_Predicted_Probability',y='Actual_Profitability',size='Records',hover_name='Probability_Band'),key+'_calibration',height=320)
        st.dataframe(reference,hide_index=True,width='stretch')
        st.caption('This supplied calibration table describes all 27,078 source rows, independently of workspace filters. Empty bins retain missing measurements.')
    with features:feature_view(key)
    with drift:drift_view(key)


def prediction_view(df,key):
    from services.access_control import can
    if not can('predict'):st.info('Model execution requires an Analyst or Admin account.');return
    state=inference.status()
    st.caption(state['reason'])
    st.info('The scored dataset does not contain all 23 trained inputs. Existing records use their supplied scores. To run new trained predictions, provide complete feature rows using the template below.')
    if not state['available']:return
    with st.expander('Required trained feature columns'):st.write(state['features'])
    download_button('Download profitability input template',pd.DataFrame(columns=state['features']).to_csv(index=False).encode(),'profitability_input_template.csv','text/csv',key=key+'_template', container=st)
    uploaded=st.file_uploader('Profitability feature CSV',type=['csv'],key=key+'_upload',max_upload_size=20)
    if uploaded is None:return
    raw=uploaded.getvalue();token=sha256(raw).hexdigest();saved=st.session_state.get(key+'_result')
    current=bool(saved and saved['token']==token)
    if len(raw)>20*1024*1024:st.error('Use a CSV smaller than 20 MB.');return
    if st.button('Run profitability trained model',type='primary',key=key+'_run',disabled=current):
        try:
            from services import upload_service as uploads
            inputs=uploads.parse(raw,uploaded.name)
            with st.spinner('Validating inputs and running the registered profitability model…'):result=uploads.predict(inputs,'profitability',{c:c for c in state['features']})
            saved={'token':token,'data':result};st.session_state[key+'_result']=saved;current=True
        except (ValueError,OSError,KeyError) as exc:st.error(str(exc))
    if current:
        result=saved['data'];st.success(f'{len(result):,} trained profitability predictions generated.')
        st.dataframe(result,hide_index=True,width='stretch')
        download_button('Download trained profitability predictions',csv_bytes(result),'profitability_predictions.csv','text/csv',key=key+'_prediction_csv', container=st)
    elif saved:st.caption('Input file changed. Generate predictions for this file.')


def render(df):
    if not df.attrs.get('verified_artifacts'):
        from views.unavailable import profitability
        profitability(df);return
    if df.empty:st.info('No profitability line items match these filters. Reset or broaden the selected period.');return
    kpis([('Scored line items',len(df),'number','Each row is one supplied observation'),('Unique orders',df.Order.nunique(),'number','An order may contain multiple rows'),('Mean profit probability',df['Profitability Probability'].mean(),'percent','Supplied model probability'),('Observed losing lines',int((~df['Actual Profitable']).sum()),'number','Recorded profit is zero or negative')])
    st.caption('Profit is the recorded source field per line item. Aggregates describe supplied rows and must not be presented as complete order totals.')
    overview,diagnostics,threshold,prediction,insights,records=st.tabs(['Overview','Model diagnostics','Threshold','Trained prediction','AI insights','Records & export'])
    with overview:
        group=st.selectbox('Compare profitability by',['Market','Category','Department','Shipping Mode','Customer Segment','Region'],key='profitability_dimension')
        grouped=df.groupby(group,dropna=False).agg(**{'Line items':('Profitability Row','size'),'Unique orders':('Order','nunique'),'Mean profitability probability':('Profitability Probability','mean'),'Observed profitable rate':('Actual Profitable','mean'),'Mean recorded profit':('Profit','mean')}).reset_index()
        shown=grouped.sort_values('Mean profitability probability',ascending=False).head(20)
        show(px.bar(shown,x=group,y=['Mean profitability probability','Observed profitable rate'],barmode='group'),'profitability_groups',height=360,category_footer=True)
        st.dataframe(grouped,hide_index=True,width='stretch')
        daily=df.assign(Day=df.Date.dt.normalize()).groupby('Day')[['Profitability Probability','Actual Profitable']].mean().reset_index()
        show(px.line(daily,x='Day',y=['Profitability Probability','Actual Profitable']),'profitability_trend',height=320)
        counts=df['Profitability Risk'].value_counts().rename_axis('Probability band').reset_index(name='Line items')
        st.dataframe(counts,hide_index=True,width='stretch')
        st.caption('High Loss Risk means profitability probability below 0.40; Moderate means 0.40–0.70; High Profit Probability means at least 0.70. These bands do not replace the 0.20 classification threshold.')
        with st.expander('Supplied summaries · complete source scope'):
            for name in ['Market','Category','Shipping']:
                st.write('**'+name+' reference**');st.dataframe(data.artifact('DataCo_'+name+'_Summary.csv'),hide_index=True,width='stretch')
            st.caption('The source summaries label row counts as Orders. Here those counts are explicitly interpreted as line-item records.')
    with diagnostics:model_diagnostics(df,'profit_main')
    with threshold:threshold_view(df,'profit_main')
    with prediction:prediction_view(df,'profit_main')
    with insights:
        from components.live_ai import render as live_ai
        live_ai(df,'profitability')
    with records:
        st.dataframe(df,hide_index=True,width='stretch')
        choice=st.selectbox('Inspect a profitability row',df['Profitability Row'].tolist(),key='profitability_row')
        selected=df[df['Profitability Row'].eq(choice)].iloc[0]
        st.dataframe(pd.DataFrame({'Field':selected.index,'Value':[str(v) for v in selected.values]}),hide_index=True,width='stretch')
        download_button('Download selected profitability data',csv_bytes(df),'profitability_selected.csv','text/csv',key='profitability_selected_csv', container=st)
        with st.expander('Supplied high-loss shortlist · five source rows'):
            st.dataframe(data.artifact('DataCo_High_Loss_Risk_Orders.csv'),hide_index=True,width='stretch')
