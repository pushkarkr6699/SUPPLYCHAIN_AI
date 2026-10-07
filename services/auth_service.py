"""Labelled demo access or optional private hashed local accounts."""
import streamlit as st
from time import time
from services.access_control import mode,authenticate
from services.audit_log import record


class DemoAuthService:
    def sign_in(self, username="Demo Analyst", remember_me=False):
        return {
            "authenticated": True,
            "user_name": username.strip() or "Demo Analyst",
            "remember_me": bool(remember_me),
            "route": "overview",
            "auth_kind": "demo", "user_role": "Analyst",
        }


def enter_demo():
    st.session_state["login_password"] = ""
    st.session_state.update(DemoAuthService().sign_in())
    record('login_success',role='Analyst')


def sign_in_form():
    username = st.session_state.get("login_username", "").strip()
    password = st.session_state.get("login_password", "")
    st.session_state["login_password"] = ""
    if mode()=='invalid':
        st.session_state['login_error']='Invalid server authentication configuration. Set SUPPLYCHAIN_AUTH_MODE to demo or accounts.';return
    if mode() == 'accounts':
        if time() < st.session_state.get('login_block_until',0):
            st.session_state['login_error']='Too many attempts. Wait one minute before retrying.';return
        account=authenticate(username,password) if len(username)<=128 and len(password)<=512 else None
        if account is None:
            attempts=st.session_state.get('login_attempts',0)+1
            st.session_state['login_attempts']=attempts
            if attempts>=5:
                st.session_state['login_block_until']=time()+60;st.session_state['login_attempts']=0
            st.session_state['login_error']='Sign-in failed. Check your account or contact the local administrator.'
            record('login_failure');return
        st.session_state.pop('login_error',None);st.session_state['login_attempts']=0
        st.session_state.update(account);record('login_success',role=account['user_role']);return
    if not username or not password:
        st.session_state["login_error"] = "Enter a demo username and password, or continue in Demo Mode."
        return
    st.session_state.pop("login_error", None)
    st.session_state.update(DemoAuthService().sign_in(username, st.session_state.get("remember_me", False)))
    record('login_success',role='Analyst')


def logout():
    record('logout')
    # Session retention ends here; the event is intentionally not persisted.
    for key in list(st.session_state):
        del st.session_state[key]
    # Explicit values reset a reused browser widget as well as the server session.
    st.session_state["login_username"] = ""
    st.session_state["login_password"] = ""
    st.query_params.clear()
    st.session_state["route"] = "login"

