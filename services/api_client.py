import os
import requests
import streamlit as st
import pandas as pd

# -------------------------------------------------------------------
# Backend configuration
# -------------------------------------------------------------------
BACKEND_BASE_URL = os.getenv(
    "BACKEND_BASE_URL",
    "http://127.0.0.1:8000"
)


# -------------------------------------------------------------------
# Low-level HTTP helpers
# -------------------------------------------------------------------
def _get(path: str):
    url = f"{BACKEND_BASE_URL}{path}"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        st.error(f"Backend GET failed: {url}")
        st.exception(e)
        st.stop()


def _post(path: str, payload: dict):
    url = f"{BACKEND_BASE_URL}{path}"
    try:
        resp = requests.post(url, json=payload, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        st.error(f"Backend POST failed: {url}")
        st.exception(e)
        st.stop()


# -------------------------------------------------------------------
# Config (shared, public)
# -------------------------------------------------------------------
def get_config():
    """
    Fetch static configuration:
    - about text
    - base data config
    - expense configs
    - investment plan config
    """
    #def get_config():
    raw = _get("/config")

    return {
    "about": raw["about"],
    "base_data": raw["base_data"],
    "onetime_expenses": raw["onetime_expenses"],
    "recurring_expenses": raw["recurring_expenses"],
    "investment_plan": raw["investment_plan"],
    }

    #return _get("/config/")

def get_config(country="IN"):
    resp = requests.get(f"{BACKEND_BASE_URL}/config/", params={"country": country})
    resp.raise_for_status()
    return resp.json()

# -------------------------------------------------------------------
# Authentication (Streamlit Authenticator)
# -------------------------------------------------------------------
def get_users_for_auth():
    """
    Returns user credentials in streamlit-authenticator format
    """
    return _get("/users/auth/")


# -------------------------------------------------------------------
# User data persistence
# -------------------------------------------------------------------
def get_user_data(username: str):
    """
    Load saved simulator inputs for a user
    """
    #print("IN get user data for",username)
    return _get(f"/user-data/{username}")


def save_user_data(username: str, data: dict):
    """
    Persist simulator inputs for a user
    """
    if not data or data == {}:
        print("Not saving null user data ")
        return   # do nothing
    payload = {
        "username": username,
        "data": data
    }
    return _post("/user-data/save", payload)


# -------------------------------------------------------------------
# Entitlements / Plans
# -------------------------------------------------------------------
def get_entitlement(username: str):
    """
    Returns:
    {
      "plan": "free" | "monthly" | "lifetime",
      "is_premium": bool
    }
    """
    return _get(f"/entitlements/{username}")


# -------------------------------------------------------------------
# Payments
# -------------------------------------------------------------------
#def create_payment_order(username: str, plan: str):
#   """
#    plan = monthly | lifetime
#    """
#    payload = {
#        "username": username,
#        "plan": plan
#    }
#    return _post("/payments/create-order", payload)

#import requests

#BASE_URL = "http://127.0.0.1:8000"

def create_payment_order(user_id: str, plan: str):
    payload = {
        "user_id": user_id,
        "plan": plan
    }

    resp = requests.post(
        f"{BACKEND_BASE_URL}/payments/create-order",
        json=payload
    )

    resp.raise_for_status()
    return resp.json()

def calculate_projections(user_data: dict, user: dict):
    payload = {
        "user_data": user_data,
        "user": user
    }
    #print("Payload inside cal porjections",payload)
    resp = requests.post(
        f"{BACKEND_BASE_URL}/projections/",
        json=payload
    )
    resp.raise_for_status()
    return resp.json()


def get_advisor_recommendations(
    projections: list,
    user_data: dict,
    base_context: dict,
    scenario: dict,
):
    payload = {
        "projections": projections,
        "user_data": user_data,
        "base_context": base_context,
        "scenario": scenario,
    }

    resp = requests.post(
        f"{BACKEND_BASE_URL}/advisor",
        json=payload,
        timeout=15
    )
    resp.raise_for_status()
    return resp.json()
