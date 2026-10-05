"""Temporary UI access. No password is checked or passed to the service."""
import streamlit as st


class DemoAuthService:
    def sign_in(self, username="Demo Analyst", remember_me=False):
        return {
            "authenticated": True,
            "user_name": username.strip() or "Demo Analyst",
            "remember_me": bool(remember_me),
            "route": "overview",
        }


def enter_demo():
    st.session_state["login_password"] = ""
    st.session_state.update(DemoAuthService().sign_in())


def sign_in_form():
    username = st.session_state.get("login_username", "").strip()
    password = st.session_state.get("login_password", "")
    st.session_state["login_password"] = ""
    if not username or not password:
        st.session_state["login_error"] = "Enter a demo username and password, or continue in Demo Mode."
        return
    st.session_state.pop("login_error", None)
    st.session_state.update(DemoAuthService().sign_in(username, st.session_state.get("remember_me", False)))


def logout():
    for key in list(st.session_state):
        del st.session_state[key]
    # Explicit values reset a reused browser widget as well as the server session.
    st.session_state["login_username"] = ""
    st.session_state["login_password"] = ""
    st.query_params.clear()
    st.session_state["route"] = "login"

