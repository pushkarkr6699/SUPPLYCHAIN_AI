"""SupplyChain AI entrypoint. Run: streamlit run app.py"""
import streamlit as st
from components.app_shell import initialize, load_styles, render
from views import landing, login

st.set_page_config(page_title="SupplyChain AI · Decision Intelligence", page_icon="◈", layout="wide", initial_sidebar_state="expanded")
initialize()
load_styles()

context = None
route = st.session_state.route
if route == "landing":
    landing.render()
elif route == "login" or not st.session_state.authenticated:
    login.render()
else:
    context = render()

from components.sevika import render as sevika
# Keep one assistant host across public and authenticated navigation.
if context is None:
    sevika(route='landing' if route=='landing' else 'login')
else:
    sevika(*context)
