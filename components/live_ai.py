"""Explicit live narration requests backed by local aggregate evidence."""
import json
import streamlit as st
from services import ai_narration,live_insights


def render(frame,key,question='Explain the key findings, model limitations and useful review steps.'):
    st.subheader('Live AI insights')
    st.caption('Your question and computed aggregate evidence are sent to OpenAI on request. Dataset rows and their group identifiers stay local; segment labels are anonymized.')
    if frame.empty:st.info('Broaden filters to generate insights.');return
    facts,payload,token=live_insights.context(frame,question)
    state=ai_narration.status();store='live_ai_'+key
    saved=st.session_state.get(store);current=bool(saved and saved['token']==token)
    if not state['available']:
        st.info(state['reason'])
        st.caption('Configure OPENAI_API_KEY in the ignored local .env, refresh, then generate. Never paste the key into chat.')
    if st.button('Generate live AI insights',key=store+'_generate',type='primary',disabled=not state['available'] or current):
        try:
            with st.spinner('Generating insights from the computed evidence…'):
                result=ai_narration.narrate(payload)
            saved={'token':token,'answer':result,'model':state['model']};st.session_state[store]=saved;current=True
        except ai_narration.NarrationUnavailable as exc:st.error(str(exc))
    if current:
        st.write(saved['answer']['summary']);lookup={f['id']:f for f in facts}
        for item in saved['answer']['insights']:
            st.write('**'+item['title']+'**');st.write(item['observation']);st.write('Suggested review: '+item['next_step'])
            for ref in item['evidence_ids']:st.caption(ref+' · '+lookup[ref]['text'])
        st.caption('OpenAI interpretation · '+saved['model']+' · Check the cited evidence before acting.')
        brief={'model':saved['model'],'answer':saved['answer'],'source':frame.attrs.get('data_source'),'question':question,'evidence':facts}
        st.download_button('Download AI insight brief',json.dumps(brief,indent=2,default=str).encode(),'ai_insights.json','application/json',key=store+'_download',on_click='ignore')
    elif saved:st.caption('Filters or the question changed. Generate a new answer for this selection.')
    with st.expander('Local evidence available without an API key'):
        for fact in facts:st.write(f"**{fact['id']} · {fact['title']}** — {fact['text']}")
