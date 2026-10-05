"""An optional guided route through existing, real platform workflows."""
import streamlit as st
from components.navigation import go

STEPS = [
    ("overview", "Overview", "Review source coverage and the current decision summary."),
    ("delivery", "Delivery", "Inspect daily risk trends and the highest scored orders."),
    ("orders", "Order", "Inspect the selected order, observed outcome and score provenance."),
    ("scenarios", "Prediction", "Run the trained model explicitly; compare its estimate with the historical score."),
    ("reports", "Report", "Choose sections, generate a PDF and download the decision brief."),
]


def navigate_step(index):
    index = max(0, min(len(STEPS) - 1, index))
    st.session_state.guide_active = True
    st.session_state.guide_step = index
    if STEPS[index][0] == "reports":
        st.session_state.report_type = "Delivery"
    go(STEPS[index][0])


def stop_guide():
    st.session_state.guide_active = False
    st.toast("Guided demo closed. Your workspace remains available.")


def guide(frame):
    with st.container(key="demo_guide"):
        if not st.session_state.get("guide_active"):
            with st.popover("Guided demo", icon=":material/play_circle:", width="content"):
                st.write("Overview → Delivery → Order → Prediction → Report")
                st.caption("Uses your current filters. Each step opens an existing workspace; predictions run only when you submit them.")
                st.button("Start guided demo", key="guide_start", on_click=navigate_step, args=(0,))
            return
        index = st.session_state.get("guide_step", 0)
        route, label, instruction = STEPS[index]
        if route == "scenarios" and not frame.attrs.get("verified_artifacts"):
            instruction = "Compare shipping inputs using the illustrative demo rules. No trained model is executed in demo mode."
        st.caption(f"Guided demo · step {index + 1} of {len(STEPS)} · {label}")
        st.write(instruction)
        if route == "delivery" and "Risk Probability" in frame and len(frame):
            ranked = frame.dropna(subset=["Risk Probability"]).sort_values("Risk Probability", ascending=False)
            if len(ranked):
                st.session_state.selected_order = str(ranked.iloc[0].Order)
        previous, current, following, close = st.columns(4)
        previous.button("Back", key="guide_back", disabled=index == 0, on_click=navigate_step, args=(index - 1,), width="stretch")
        current.button("Open this step", key="guide_open", on_click=navigate_step, args=(index,), width="stretch")
        following.button("Next step", key="guide_next", disabled=index == len(STEPS) - 1, on_click=navigate_step, args=(index + 1,), width="stretch")
        close.button("Finish demo" if index == len(STEPS) - 1 else "Close guide", key="guide_close", on_click=stop_guide, width="stretch")
