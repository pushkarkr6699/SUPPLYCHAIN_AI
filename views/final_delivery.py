"""Source-grain views for the separately trained final delivery experiment."""
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
from services import final_delivery_data as data
from services.export_service import csv_bytes
from components.charts import show
from components.kpi_cards import kpis
from components.section_header import section


def render(filters=None,key='final_delivery'):
    frame=data.records()
    for name,values in (filters or {}).items():
        if name=='Date' and len(values)==2:
            frame=frame[frame.Date.ge(pd.Timestamp(values[0])) & frame.Date.lt(pd.Timestamp(values[1])+pd.Timedelta(days=1))]
        elif name in frame and values:frame=frame[frame[name].isin(values)]
    section('Final delivery line-item model','Independent XGBoost experiment · saved threshold 0.56')
    st.info(data.NOTE)
    st.caption("Saved risk bands use threshold ? 0.15: Low ? 0.41, Medium ? 0.71, High > 0.71. These differ from the main delivery model bands.")
    if frame.empty:st.info('No final delivery observations match the selected filters.');return
    kpis([('Scored line observations',len(frame),'number','Original exported rows retained'),
        ('Unique orders',frame.Order.nunique(),'number','Multiple observations per order'),
        ('Mean late probability',frame['Risk Probability'].mean(),'percent','Supplied probabilities'),
        ('Observed late rate',frame['Actual Late'].mean(),'percent','Supplied outcome labels')])
    overview,diagnostics,threshold,prediction,insights,exports=st.tabs(['Final scores','Final diagnostics','Final threshold','Final trained prediction','Final AI insights','Final records & exports'])
    with overview:
        group=st.selectbox('Compare final delivery by',['Market','Category','Shipping Mode','Customer Segment','Region'],key=key+'_group')
        grouped=frame.groupby(group,dropna=False).agg(**{'Line observations':('Delivery Row','size'),'Mean late probability':('Risk Probability','mean'),'Observed late rate':('Actual Late','mean')}).reset_index()
        show(px.bar(grouped.head(20),x=group,y=['Mean late probability','Observed late rate'],barmode='group'),key+'_groups',height=360)
        st.dataframe(grouped,hide_index=True,width='stretch')
    with diagnostics:
        scores=data.evaluation(frame)
        st.dataframe(pd.DataFrame({'Metric':list(scores),'Current selected rows':list(scores.values())}),hide_index=True,width='stretch')
        for name in ['Late_Delivery_Final_Summary.csv','Late_Delivery_Model_Comparison.csv']:
            st.caption(name+' · supplied reference scope, independently of filters')
            st.dataframe(data.artifact(name),hide_index=True,width='stretch')
        features=data.artifact('Late_Delivery_Feature_Importance.csv').sort_values('Importance',ascending=False)
        st.caption('Global transformed-feature importances from the supplied final model. These are not SHAP or causal effects.')
        show(px.bar(features.head(15).sort_values('Importance'),x='Importance',y='Feature',orientation='h'),key+'_features',height=440)
        st.dataframe(features,hide_index=True,width='stretch')
    with threshold:
        chosen=st.slider('Final delivery analysis threshold',0.,1.,.56,.01,key=key+'_threshold')
        st.write(data.evaluation(frame,chosen))
        points=[{'Threshold':float(t),**data.evaluation(frame,float(t))} for t in np.linspace(0,1,41)]
        show(px.line(pd.DataFrame(points),x='Threshold',y=['Precision','Recall','F1']),key+'_curve',height=320)
        st.caption('Analysis does not change either saved model threshold. Source reference values may describe a different evaluation split.')
        with st.expander('Supplied final threshold reference'):st.dataframe(data.artifact('Late_Delivery_Threshold_Analysis.csv'),hide_index=True,width='stretch')
    with prediction:prediction_view(frame,key)
    with insights:
        from components.live_ai import render as live_ai
        live_ai(frame,key)
    with exports:
        st.dataframe(frame,hide_index=True,width='stretch')
        st.download_button('Download final delivery observations',csv_bytes(frame),'final_delivery_line_observations.csv','text/csv',key=key+'_csv')
        from services.export_service import report_pdf
        st.download_button('Download final delivery report',report_pdf(frame,'Delivery',filters or {},['KPIs','Charts','Insights','Records']),'final_delivery_report.pdf','application/pdf',key=key+'_pdf')
        for name in sorted(data.FILES):
            path,_=data.registered(name)
            st.download_button('Download '+name,path.read_bytes(),name,'text/csv' if name.endswith('.csv') else 'text/plain',key=key+'_'+name)


def prediction_view(df,key):
    from services import final_delivery_inference as inference
    from hashlib import sha256
    state=inference.status()
    st.caption(state['reason'])
    st.info('The scored dataset does not contain all 31 trained inputs. Existing records use their supplied scores. To run new trained predictions, provide complete feature rows using the template below.')
    if not state['available']:return
    with st.expander('Required trained feature columns'):st.write(state['features'])
    st.download_button('Download final delivery input template',pd.DataFrame(columns=state['features']).to_csv(index=False).encode(),'final_delivery_input_template.csv','text/csv',key=key+'_template')
    uploaded=st.file_uploader('Final delivery feature CSV',type=['csv'],key=key+'_upload')
    if uploaded is None:return
    raw=uploaded.getvalue();token=sha256(raw).hexdigest();saved=st.session_state.get(key+'_result')
    current=bool(saved and saved['token']==token)
    if len(raw)>20*1024*1024:st.error('Use a CSV smaller than 20 MB.');return
    if st.button('Run final delivery trained model',type='primary',key=key+'_run',disabled=current):
        try:
            from io import BytesIO
            inputs=pd.read_csv(BytesIO(raw))
            if len(inputs)>50000:raise ValueError('Limit each request to 50,000 rows.')
            with st.spinner('Validating inputs and running the registered final delivery model…'):result=inference.predict(inputs)
            saved={'token':token,'data':result};st.session_state[key+'_result']=saved;current=True
        except (ValueError,OSError,KeyError) as exc:st.error(str(exc))
    if current:
        result=saved['data'];st.success(f'{len(result):,} trained final delivery predictions generated.')
        st.dataframe(result,hide_index=True,width='stretch')
        st.download_button('Download trained final delivery predictions',csv_bytes(result),'final_delivery_predictions.csv','text/csv',key=key+'_prediction_csv')
    elif saved:st.caption('Input file changed. Generate predictions for this file.')
