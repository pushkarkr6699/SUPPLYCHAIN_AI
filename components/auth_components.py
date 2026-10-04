import streamlit as st
from components.navigation import go
from services.auth_service import enter_demo, sign_in_form


def toggle_password():
    st.session_state.show_password = not st.session_state.show_password


def show_recovery_copy():
    st.session_state.recovery_notice = True
    st.session_state.login_error = ""


def login_card():
    with st.container(key="login_card"):
        st.html('<div class="login-eyebrow">WELCOME BACK</div><h2>Sign in to continue.</h2><p class="login-intro">Enter the workspace for a guided demo session.</p>')
        st.html('<div class="demo-auth-note"><span>i</span><p><b>Demo authentication is enabled for this preview.</b><br>Entries are not validated or transmitted. The password is cleared after submit. Use sample values or continue without credentials.</p></div>')

        st.text_input("Email or username", key="login_username", placeholder="Your name or demo email", autocomplete="off")
        password_label, toggle = st.columns([3, 1], vertical_alignment="bottom")
        with password_label:
            st.text_input("Password", key="login_password", type="default" if st.session_state.show_password else "password", placeholder="Sample value only", autocomplete="off")
        with toggle:
            st.button("Hide" if st.session_state.show_password else "Show", key="toggle_password", on_click=toggle_password, type="tertiary", help="Show or hide the sample password", width="stretch")

        st.checkbox("Remember me for this session", key="remember_me", help="Stores only a demo display preference until logout")
        if st.session_state.get("login_error"):
            st.error(st.session_state.login_error, icon=":material/info:")
        if st.session_state.get("recovery_notice"):
            st.info("Password recovery will be available when an authentication provider is connected.")

        st.button("Sign In", key="login_submit", on_click=sign_in_form, type="primary", icon=":material/arrow_forward:", width="stretch")
        left, middle, right = st.columns([1, 1.2, 1])
        with left:
            st.html('<div class="login-divider"></div>')
        with middle:
            st.html('<div class="login-or">OR</div>')
        with right:
            st.html('<div class="login-divider"></div>')
        st.button("Continue in Demo Mode", key="login_demo", on_click=enter_demo, width="stretch")
        st.button("Forgot password?", key="forgot_password", on_click=show_recovery_copy, type="tertiary", width="stretch")
        st.html('<div class="login-privacy"><span>◈</span> This UI preview has no connected identity provider.</div>')
        st.button("← Return to website", key="login_back", on_click=go, args=("landing",), type="tertiary")
