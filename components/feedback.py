import streamlit as st


def download_feedback(label="Download"):
    st.toast(f"{label} requested. Your browser handles the file download.", icon=":material/download:")
