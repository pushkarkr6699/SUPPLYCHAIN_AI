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
    service = get_service()
    dataset = st.selectbox("Dataset", ["delivery", "demand", "profitability"], format_func=str.title, key="copilot_dataset")
    active = st.session_state.get("filters", {}) if service.demo or st.session_state.get("active_filter_dataset") == dataset else st.session_state.get("filters_by_dataset", {}).get(dataset, {})
    df = service.records(active, dataset=dataset)
    if st.session_state.get("copilot_engine") == "Live OpenAI": st.session_state.copilot_engine = "Live AI"
    engine = st.radio("Analysis engine", ["Local calculations", "Live AI"], horizontal=True, key="copilot_engine")
    if engine == "Live AI" or dataset == "profitability":
        from components.live_ai import render as live_ai
        question=st.text_area("Your analytical question", value="Explain the key patterns, reliability and review priorities.", max_chars=1000, key="copilot_live_question")
        if engine == "Live AI":
            live_ai(df,"copilot",question)
        else:
            from services.live_insights import context
            facts,_,_=context(df,question)
            st.caption("Computed profitability evidence. Choose Live AI for a written interpretation of your question.")
            for fact in facts:st.write(fact["text"])
        return
    st.caption("OFFLINE ANALYTICAL ASSISTANT · Deterministic calculations · " + df.attrs.get("data_source", "DEMO UI DATA") + " · No external AI service")
    mode = st.radio("Assistant mode", ["Explore", "Analyze", "Explain", "Simulate", "Report"], horizontal=True, key="copilot_mode")
    main, context = st.columns([2.8, 1], gap="large")
    with context:
        with st.expander("Workspace Context", expanded=True):
            context_drawer(df, active)
        if st.button("Clear conversation", icon=":material/delete_sweep:", width="stretch"):
            st.session_state.conversation = []
            st.rerun()
    with main:
        started = bool(st.session_state.conversation)
        section("Evidence-first investigation", "Responses use the selected dataset's filters and preserve evidence with each answer.")
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
        typed = st.chat_input("Ask about risk, demand, a segment or a record…", key="copilot_input")
        if typed or question:
            q = typed or question
            context = dict(active)
            response = respond(q, df, mode, st.session_state.selected_order, context)
            evidence = get_service().evidence(df, context)
            evidence["Calculated at (UTC)"] = response["evidence_context"]["calculated_at"]
            st.session_state.conversation.append({"question": q, "response": response, "evidence": evidence})
            st.session_state.conversation = st.session_state.conversation[-12:]
            st.rerun()
