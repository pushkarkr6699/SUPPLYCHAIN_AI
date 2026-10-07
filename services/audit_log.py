"""Bounded session audit, excluding raw records, questions and credentials."""
from datetime import datetime,timezone
from streamlit.runtime.scriptrunner import get_script_run_ctx
import streamlit as st
EVENTS={'login_success','login_failure','logout','upload_imported','model_predicted','analysis_applied','report_generated','page_viewed','filters_changed','local_question','scenario_executed','dataset_accessed','model_selected'}


def record(event,**metadata):
    if event not in EVENTS or get_script_run_ctx(suppress_warning=True) is None:return
    safe={key:value for key,value in metadata.items() if key in {'rows','columns','charts'} and type(value) in {int,bool}}
    for key in ('route','model','role'):
        if key in metadata and isinstance(metadata[key],str) and metadata[key].replace('_','').isalnum():safe[key]=metadata[key][:40]
    st.session_state['audit_events']=[*st.session_state.get('audit_events',[]),{'event':event,'utc':datetime.now(timezone.utc).isoformat(),**safe}][-100:]
