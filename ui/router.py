import streamlit as st
from services.api_client import get
from ui.auth import auth_block
from ui.forms import render_forms
from ui.summary import render_summary

def run_app():
    user = auth_block()
    st.warning(f"User in router :{user}")
    if not user:
        return

    configs = get("/config/")
    st.warning("Rendering Forms 1")
    render_forms(configs, user)
    st.warning("Rendering Summary")
    render_summary(user)
