from html import escape
import streamlit as st
from components.copilot_ui import context_drawer, response_card
from components.section_header import section
from services.copilot_service import respond
from services.copilot.prompts import SUGGESTED_QUESTIONS
from services.provider import get_service


def render(df):
    if not st.session_state.copilot_enabled:
        st.info("Copilot is disabled in Settings. Enable it to explore the offline preview.")
        return
    st.caption("OFFLINE ANALYTICAL PREVIEW · Deterministic demo responses · No external AI service")
    mode = st.radio("Assistant mode", ["Explore", "Analyze", "Explain", "Simulate", "Report"], horizontal=True, key="copilot_mode")
    main, context = st.columns([2.8, 1], gap="large")
    with context:
        with st.expander("Workspace Context", expanded=True):
            context_drawer()
        if st.button("Clear conversation", icon=":material/delete_sweep:", width="stretch"):
            st.session_state.conversation = []
            st.rerun()
    with main:
        started = bool(st.session_state.conversation)
        section("Evidence-first investigation", "Responses use the current demo filters and preserve evidence with each answer.")
        question = None
        if not started:
            cols = st.columns(2)
            for i, prompt in enumerate(SUGGESTED_QUESTIONS):
                if cols[i % 2].button(prompt, key=f"prompt_{i}", width="stretch"):
                    question = prompt
        for index, entry in enumerate(st.session_state.conversation):
            st.html(f'<div class="copilot-user-message"><span class="eyebrow">YOU ASKED</span><p>{escape(entry["question"])}</p></div>')
            with st.container(key=f"copilot_answer_{index}"):
                response_card(entry["response"], entry["evidence"], index)
        typed = st.chat_input("Ask about risk, demand, a segment or a demo record…", key="copilot_input")
        if typed or question:
            q = typed or question
            context = dict(st.session_state.filters)
            response = respond(q, df, mode, st.session_state.selected_order, context)
            evidence = get_service().evidence(df, context)
            evidence["Calculated at (UTC)"] = response["evidence_context"]["calculated_at"]
            st.session_state.conversation.append({"question": q, "response": response, "evidence": evidence})
            st.session_state.conversation = st.session_state.conversation[-12:]
            st.rerun()
