import streamlit as st
import requests
from ui.auth import get_authenticator
from services.api_client import BACKEND_BASE_URL


# ================================
# LOGIN PAGE
# ================================
def render_login():

    st.title("Login")

    st.info("👉 Username is your email ID without '@domain'\n\nExample: testuser@gmail.com → username = testuser")

    authenticator = get_authenticator()
    #print("Authenticator instance in login:", authenticator)  # Debug print
    authenticator.login(location="main")

    if st.session_state.authentication_status is True:
        st.session_state.view = "app"
        st.rerun()

    elif st.session_state.authentication_status is False:
        st.error("Invalid username or password")

    if st.button("Create account"):
        st.session_state.view = "register"
        st.rerun()


# ================================
# REGISTER PAGE
# ================================
def render_register():

    st.title("Create Account")

    name = st.text_input("Full name")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Register"):

        if not name or not email or not password:
            st.error("All fields required")
            return

        resp = requests.post(
            f"{BACKEND_BASE_URL}/auth/register",
            json={
                "name": name,
                "email": email,
                "password": password
            }
        )

        if resp.status_code != 200:
            st.error(resp.text)
            return

        st.success("Account created. Please login.")
        #import auth  # your auth.py module

        #auth._authenticator = None   # reset cached authenticator
        #st.session_state.authentication_status = None

        st.session_state.view = "login"
        st.rerun()

        #st.session_state.view = "login"
        #st.rerun()

    if st.button("Back to login"):
        st.session_state.view = "login"
        st.rerun()
