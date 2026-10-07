"""Register downloadable data only for authorized session roles."""
import streamlit as st
from services.access_control import can


def download_button(*args,container=None,**kwargs):
    target=container if container is not None else st
    if not can('export'):
        target.caption('Downloads require an Analyst, Executive or Admin account.')
        return False
    return target.download_button(*args,**kwargs)
