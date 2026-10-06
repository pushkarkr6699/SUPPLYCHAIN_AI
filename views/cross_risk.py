import streamlit as st
import plotly.express as px
from services.profitability_data import cross_risk
from services.export_service import csv_bytes
from components.kpi_cards import kpis
from components.charts import show


def render(df):
    if not df.attrs.get('verified_artifacts'):
        from views.unavailable import cross_risk as demo
        demo(df);return
    frame=cross_risk(df)
    matched=frame['Profitability rows'].notna();both=matched & frame['Risk Probability'].notna()
    kpis([('Delivery orders',len(frame),'number','Current delivery filters'),('Profitability matched',int(matched.sum()),'number','Order ID, date, market and country verified'),('Both signals available',int(both.sum()),'number','Only these rows can be compared')])
    st.caption('Profitability line items are aggregated once per order before joining. Mean/max line probabilities are descriptive statistics, not a combined-risk model or an order-profitability probability. Demand is not joined.')
    if both.any():
        show(px.scatter(frame[both],x='Risk Probability',y='Maximum line loss probability',hover_data=['Order','Profitability rows','Observed losing lines']),'cross_risk_scatter',height=380)
    else:st.info('No orders in this period have both supplied signals. Broaden the date range to include scored delivery records.')
    st.dataframe(frame[[c for c in ['Order','Date','Market','Risk Probability','Risk','Profitability rows','Mean line profitability','Maximum line loss probability','Observed losing lines','High loss risk lines'] if c in frame]],hide_index=True,width='stretch')
    st.download_button('Download joined risk evidence',csv_bytes(frame),'cross_risk_evidence.csv','text/csv',key='cross_risk_csv')
