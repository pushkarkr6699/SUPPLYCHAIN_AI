from html import escape
import streamlit as st
from services.decision_context import coverage_context, decision_summary


def coverage_strip(frame):
    context = coverage_context(frame)
    coverage = f"{context['scored']:,} scored · {context['unscored']:,} unscored" if "scored" in context else f"{context['rows']:,} observations"
    st.html('<div class="coverage-strip" aria-label="Data coverage">' + ''.join(
        f'<div><span>{escape(label)}</span><strong>{escape(value)}</strong></div>' for label, value in [
            ("Selected records", context["period"]), ("Coverage", coverage), ("Source freshness", context["freshness"])]) + '</div>')


def decision_brief(frame):
    dataset = "demand" if st.session_state.route == "demand" else None
    st.html(f'<div class="decision-brief"><h2>Focus for this view</h2><p>{escape(decision_summary(frame, dataset))}</p></div>')
    from services.decision_intelligence import momentum,priorities,opportunities,anomalies
    with st.expander('Momentum, investigation priority and observed opportunities'):
        measures=[c for c in ['Risk Probability','Actual Demand','Forecast Demand','Profit'] if c in frame]
        if not measures:st.info('No supported measured signals in this selection.');return
        a,b=st.columns(2)
        measure=a.selectbox('Signal',measures,key='decision_signal_'+str(dataset))
        period=b.selectbox('Observed interval',['Day','Week','Month'],key='decision_interval_'+str(dataset))
        try:
            result=momentum(frame,measure,'Mean' if 'Probability' in measure else 'Sum',period)
            a,b,c=st.columns(3)
            a.metric('Observed level',f"{result['level']:.4g}")
            b.metric('Momentum',f"{result['momentum']:+.4g}",help=result['change_units'])
            c.metric('Acceleration',f"{result['acceleration']:+.4g}",help='Change in momentum, '+result['change_units'])
            st.caption(result['state']+' | '+result['change_units']+' | '+result['note'])
            st.dataframe(result['series'].tail(12),hide_index=True,width='stretch')
        except ValueError as error:st.info(str(error))
        dimension=next((c for c in ['Market','Category','Region','Product'] if c in frame),None)
        if dimension and 'Risk Probability' in frame:
            try:
                ranking,method=priorities(frame,dimension)
                st.markdown('**Investigation queue by '+dimension+'**')
                st.caption(method['formula']);st.caption(method['components']);st.caption(method['limitation'])
                st.dataframe(ranking.head(10),hide_index=True,width='stretch')
            except ValueError as error:st.info(str(error))
        if dimension and {'Sales','Profit'}.issubset(frame):
            st.markdown('**Favorable observed segments**')
            st.caption('Positive observed profit and sales only; sorted by observed profit. This is not a guarantee of future performance.')
            st.dataframe(opportunities(frame,dimension).head(10),hide_index=True,width='stretch')
    with st.expander('Observed anomalies and their reference'):
        measures=['Record volume',*[c for c in ['Sales','Profit','Risk Probability','Actual Demand','Forecast Demand'] if c in frame]]
        if {'Actual Demand','Forecast Demand'}.issubset(frame):measures.append('Forecast error')
        metric=st.selectbox('Anomaly measure',measures,key='anomaly_measure_'+str(dataset))
        interval=st.selectbox('Anomaly interval',['Day','Week','Month'],key='anomaly_interval_'+str(dataset))
        try:
            observations,method=anomalies(frame,metric,interval)
            st.caption(method['method']+' | '+method['limitation'])
            st.caption(f"Reference Q1 {method['q1']:.6g}; Q3 {method['q3']:.6g}; IQR {method['iqr']:.6g}. UNUSUAL: outside 1.5 x IQR fences; HIGHLY UNUSUAL: outside 3 x IQR fences.")
            st.dataframe(observations,hide_index=True,width='stretch')
        except ValueError as error:st.info(str(error))
