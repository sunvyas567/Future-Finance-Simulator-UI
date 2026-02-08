import streamlit as st
from services.api_client import get, post

def render_forms(configs, username):
    user_data = get(f"/user-data/{username}")

    for item in configs["base"]:
        key = item["Field Name"]
        val = user_data.get(key, {}).get("input", item["Field Default Value"])
        user_data[key] = {"input": st.number_input(item["Field Description"], value=float(val))}

    post(f"/user-data/{username}", user_data)
