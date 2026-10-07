"""Shared local questions and explicit cross-source investigation controls."""
from components.secure_actions import download_button
import pandas as pd
import streamlit as st
from services import data_questions, relationships, parameter_comparison as analysis
from services.dataset_catalog import catalog, load
from services.visualization_service import build
from services.export_service import csv_bytes
from components.charts import show


def questions(frame,prefix):
    with st.expander('Ask Sevika a local question about these fields', expanded=bool(st.session_state.get(prefix+'_question_result'))):
        st.caption('Active context: '+str(frame.attrs.get('data_source','Current selection'))+'. Uses allowlisted local calculations; no question or rows are sent to an AI provider.')
        st.caption('Examples: top 10 Market by Sales; trend Sales monthly; distribution Sales; correlation Sales and Profit; anomalies Sales. Use your exact field names. Model runs use the separate validated prediction workflow.')
        with st.form(prefix+'_question_form'):
            question=st.text_input('Local data question',max_chars=1000,key=prefix+'_local_question')
            submitted=st.form_submit_button('Analyze question',key=prefix+'_question_run')
        signature=analysis.signature(frame,{'question':question})
        if submitted:
            st.session_state.pop(prefix+'_question_result',None)
            try:
                st.session_state[prefix+'_question_result']={'signature':signature,'answer':data_questions.answer(frame,question)}
                st.rerun()
            except ValueError as error:st.info(str(error))
        saved=st.session_state.get(prefix+'_question_result')
        if saved and saved['signature']==signature:
            result=saved['answer']
            st.write('Computed method: '+result['intent']);st.caption(result['note'])
            st.dataframe(result['table'].head(200),hide_index=True,width='stretch')
            try:
                chart=build(frame,result['chart'],result['groups'],result['metrics'],result['operation'],result['period'])
                st.caption(chart['note']);show(chart['figure'],prefix+'_question_chart',preserve_axis_titles=True)
            except ValueError as error:st.caption(str(error))
            download_button('Download question result',csv_bytes(result['table'],frame.attrs.get('data_source')),'local_question.csv','text/csv',key=prefix+'_question_csv',on_click='ignore', container=st)


def joins(frame,prefix):
    from services.access_control import can
    if not can('project_data'):
        st.caption('Sign in with a local account to compare against connected project files.');return
    with st.expander('Explicit comparison with another registered dataset'):
        st.caption('No automatic merge occurs. Validate common keys first. A direct join must be one-to-one; repeated child records require an explicit aggregation to protect parent totals.')
        ready={e['id']:e for e in catalog() if e['Status'] in {'READY','WARNING'}}
        choice=st.selectbox('Right-hand source',['[Choose source]',*ready],format_func=lambda k:ready[k]['Name'] if k in ready else k,key=prefix+'_join_source')
        if choice=='[Choose source]':return
        try:right=load(choice)
        except (OSError,ValueError):st.warning('Source unavailable. Choose another registered dataset.');return
        a,b=st.columns(2)
        left_key=a.selectbox('Left join key',list(frame.columns),key=prefix+'_left_key')
        right_key=b.selectbox('Right join key',list(right.columns),key=prefix+'_right_key')
        try:
            evidence=relationships.inspect(frame,right,left_key,right_key)
            st.json(evidence,expanded=False)
        except ValueError as error:st.info(str(error));return
        if evidence['cardinality']=='one-to-many':
            numeric=[c for c in right if pd.api.types.is_numeric_dtype(right[c]) and c!=right_key]
            selected=st.multiselect('Child measures to aggregate before joining',numeric,max_selections=4,key=prefix+'_child_metrics')
            operation=st.selectbox('Child calculation',['Mean','Sum'],key=prefix+'_child_operation')
            if selected:
                try:
                    right=relationships.aggregate_child(right,right_key,selected,operation)
                    evidence=relationships.inspect(frame,right,left_key,right_key)
                    st.caption('Child aggregation selected explicitly: '+operation+'. The resulting join uses one row per child key.')
                except ValueError as error:st.info(str(error));return
        if evidence['cardinality'] in {'many-to-many','many-to-one'}:
            st.warning('Direct join blocked because parent records repeat. Use a unique-key left dataset or aggregate to a justified analytical grain first.')
        if evidence['shared_keys'] and evidence['left_matched_records']/max(1,len(frame))<.5:
            st.warning('Less than 50% of left records match. The joined selection is not representative of the full source.')
        signature=analysis.signature(frame,{'right':analysis.signature(right,{}),'left_key':left_key,'right_key':right_key})
        if st.button('Create validated matched-record analysis',disabled=not evidence['safe_direct_join'],key=prefix+'_join_run'):
            st.session_state.pop(prefix+'_join_result',None)
            try:st.session_state[prefix+'_join_result']={'signature':signature,'frame':relationships.join(frame,right,left_key,right_key)}
            except ValueError as error:st.warning(str(error))
        saved=st.session_state.get(prefix+'_join_result')
        if saved and saved['signature']==signature:
            result=saved['frame']
            st.success(f'{len(result):,} reconciled matched unique keys. Null and unmatched keys are excluded.')
            st.dataframe(result.head(100),hide_index=True,width='stretch')
            download_button('Download validated join',csv_bytes(result),'validated_join.csv','text/csv',key=prefix+'_join_csv',on_click='ignore', container=st)
            from views.visualizations import board
            board(result,prefix+'_matched',True,'Validated cross-source analysis')
