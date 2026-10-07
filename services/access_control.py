"""Optional private local accounts; server-side permissions and demo isolation."""
import os
import json
import hmac
from hashlib import pbkdf2_hmac
from config import ROOT

ROLES={'Admin','Analyst','Executive','Viewer'}
PERMISSIONS={'view':ROLES,'export':{'Admin','Analyst','Executive'},'predict':{'Admin','Analyst'},'admin':{'Admin'},'project_data':ROLES,'audit':{'Admin'}}


def mode():
    configured=os.getenv('SUPPLYCHAIN_AUTH_MODE','demo').strip().lower()
    return configured if configured in {'demo','accounts'} else 'invalid'


def password_hash(password,salt):
    return pbkdf2_hmac('sha256',password.encode('utf-8'),bytes.fromhex(salt),310000).hex()


def authenticate(username,password):
    try:
        accounts=json.loads((ROOT/'.streamlit/accounts.json').read_text(encoding='utf-8'))
        row=accounts.get(username.strip().casefold())
        salt=row.get('salt','') if isinstance(row,dict) else '0'*32
        expected=row.get('password_hash','') if isinstance(row,dict) else '0'*64
        calculated=password_hash(password,salt)
        if row and row.get('role') in ROLES and len(salt)==32 and len(expected)==64 and hmac.compare_digest(calculated,expected):
            return {'user_name':username.strip(),'user_role':row['role'],'auth_kind':'account','authenticated':True,'route':'overview'}
    except (OSError,ValueError,TypeError,AttributeError):pass
    return None


def allowed(permission,role,auth_kind='account'):
    return role in PERMISSIONS.get(permission,set()) and (permission!='project_data' or auth_kind!='demo')


def can(permission):
    if mode()=='demo':return True
    if mode()=='invalid':return False
    import streamlit as st
    return bool(st.session_state.get('authenticated')) and allowed(permission,st.session_state.get('user_role','Viewer'),st.session_state.get('auth_kind','demo'))


def require(permission):
    from streamlit.runtime.scriptrunner import get_script_run_ctx
    if get_script_run_ctx(suppress_warning=True) is not None and not can(permission):
        raise PermissionError('Your current session role does not allow this action.')
