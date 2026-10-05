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
