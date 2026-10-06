"""Native floating chat panel; no credentials or dataset rows in browser JS."""
import json
import pandas as pd
import streamlit as st
from services import sevika, ai_provider


def refresh():
    st.rerun()


def render(frame=None, route='landing', dataset='public'):
    if not st.session_state.get('copilot_enabled',True):return
    public=route in {'landing','login'}
    if route == 'uploads':
        frame = None
    context=sevika.build_context(pd.DataFrame() if public or frame is None else frame,route,dataset,
        {} if public or route == 'uploads' else st.session_state.get('filters',{}),
        None if public or route == 'uploads' else st.session_state.get('selected_order'))
    panel(context)


def panel(context):
    conversations=st.session_state.setdefault('sevika_conversations',{})
    scope=context['signature']
    if scope not in conversations:
        conversations[scope]={'history':[],'predictions':None}
        while len(conversations)>6:conversations.pop(next(iter(conversations)))
    store=conversations[scope]; history=store['history']
    with st.container(key='sevika_launcher'):
        with st.popover('Sevika',icon=':material/forum:',width='stretch'):
            with st.container(key='sevika_panel'):
                with st.container(key='sevika_heading'):
                    top,clear=st.columns([3,1])
                    top.markdown('### Sevika')
                    if clear.button('Clear',key='sevika_clear',help='Clear this context conversation and predictions'):
                        store.update(history=[],predictions=None);refresh()
                st.caption('Your supply-chain assistant - '+context['page'].replace('_',' ').title())
                state=ai_provider.status()
                choices=['Local analysis','Live AI'] if state['available'] else ['Local analysis']
                if st.session_state.get('sevika_engine') not in choices:
                    st.session_state.sevika_engine='Live AI' if state['available'] else 'Local analysis'
                engine=st.radio('Answer mode',choices,key='sevika_engine',horizontal=True)
                if engine=='Live AI':
                    st.caption('Hugging Face / '+state['routing']+' - your question is sent as written with anonymized aggregate evidence. Avoid private identifiers. Raw dataset rows stay local.')
                else:st.caption('Local calculations and workflow help. No external request; this mode is not a generative model.')
                if not state['available']:st.caption('Live AI is unavailable until HF_TOKEN is configured privately on the server.')
                if not context['public']:
                    st.caption(f"{len(context['frame']):,} selected records - {context['dataset']} - filters follow the current page.")
                    if context['frame'].empty:st.info('No matching data. I can explain the workflow; broaden filters for analysis.')
                prompts=history[-1]['answer']['follow_ups'] if history else context['suggestions']
                fields=['Current page']+[c for c in ['Market','Region','Category','Shipping Mode','Customer Segment','Department','Risk Probability','Profitability Probability','Sales','Profit','Forecast Demand','Actual Demand','Absolute Error'] if c in context['frame']]
                if not context['public'] and len(fields)>1:
                    if st.session_state.get('sevika_field') not in fields:st.session_state.sevika_field='Current page'
                    focus=st.selectbox('Explore a field',fields,key='sevika_field')
                    if focus!='Current page':
                        numeric=pd.api.types.is_numeric_dtype(context['frame'][focus])
                        prompts=[f'Explain {focus} in this dataset.',f'What is the mean {focus}?' if numeric else f'Compare the selection by {focus}.',f'What are the limitations when interpreting {focus}?']
                question=None
                with st.expander('Questions for this page',expanded=not history):
                    for index,prompt in enumerate(prompts):
                        if st.button(prompt,key=f'sevika_suggest_{index}',width='stretch'):question=prompt
                if not context['public'] and context['frame'].attrs.get('verified_artifacts') and context['dataset'] in {'delivery','demand'} and not context['frame'].empty:
                    st.caption('Trained prediction: up to 50 selected delivery orders, or next-day web visits for selected products. Historical inputs; no new model training.')
                    if st.button('Run trained prediction',key='sevika_predict',disabled=store['predictions'] is not None):
                        try:
                            with st.spinner('Running the registered model...'):store['predictions']=sevika.train(context)
                            refresh()
                        except (ValueError,RuntimeError,OSError):st.error('The registered model could not score this selection. Check its model status and required inputs in the prediction view.')
                    if store['predictions'] is not None:st.success(f"{len(store['predictions']):,} trained outputs ready to explain.")
                with st.container(height=280,key='sevika_messages'):
                    if not history:st.markdown('Hi, I am **Sevika**. Ask me to explain this page, compare its fields, review a forecast or describe the next step.')
                    for turn in history:
                        with st.chat_message('user'):st.write(turn['question'])
                        with st.chat_message('assistant',avatar=':material/psychology:'):
                            st.caption(turn['engine']);st.write(turn['answer']['answer'])
                            with st.expander('Supporting evidence'):
                                lookup={f['id']:f for f in turn['facts']}
                                for ref in turn['answer']['evidence_ids']:st.caption(ref+' - '+lookup[ref]['text'])
                with st.form('sevika_question_form',clear_on_submit=True):
                    typed=st.text_input('Ask Sevika',placeholder='Explain, compare, predict or ask how...',max_chars=1000,key='sevika_question')
                    submitted=st.form_submit_button('Ask',type='primary',width='stretch')
                if submitted and typed.strip():question=typed.strip()
                if question:
                    try:
                        with st.spinner('Sevika is reviewing the evidence...'):
                            answer,facts=sevika.answer(question,context,engine,history,store['predictions'])
                        history.append({'question':question,'answer':answer,'facts':facts,'engine':engine})
                        store['history']=history[-sevika.MAX_TURNS:]
                        refresh()
                    except (ai_provider.AIUnavailable,ValueError) as error:st.error(str(error))
                if history:
                    st.download_button('Download conversation',json.dumps({'assistant':'Sevika','page':context['page'],'dataset':context['dataset'],'turns':store['history']},default=str,indent=2).encode(),'sevika_conversation.json','application/json',key='sevika_download',on_click='ignore')
                st.caption('Historical evidence, not guarantees. Conversations stay in this session and clear on logout.')
