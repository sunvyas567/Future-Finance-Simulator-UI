import streamlit as st
from ui.simulator import run_simulator
from ui.auth import get_authenticator

import streamlit as st

import subprocess, os

if not os.path.exists("/home/appuser/.cache/ms-playwright"):
    subprocess.run(["playwright", "install", "chromium"], check=True)

# --------------------------------------------------
# GLOBAL session initialization (MUST BE FIRST)
# --------------------------------------------------
DEFAULT_SESSION_KEYS = {
    "view": "landing",
    "authentication_status": None,
    "username": None,
    "logout": False,
}

for k, v in DEFAULT_SESSION_KEYS.items():
    if k not in st.session_state:
        st.session_state[k] = v

# -------------------------------------------------------------------
# Session initialization (CRITICAL)
# -------------------------------------------------------------------
if "view" not in st.session_state:
    st.session_state.view = "landing"

if "authentication_status" not in st.session_state:
    st.session_state.authentication_status = None

if "username" not in st.session_state:
    st.session_state.username = None

# -------------------------------------------------------------------
# UI RENDERERS
# -------------------------------------------------------------------
def render_landing():
    st.title("Visualize Your Financial Future in Minutes")
    st.markdown(
        "Plan smarter, account for inflation, and stress-test your retirement "
        "with multi-year projections."
    )
    st.markdown("---")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader("📊 Live Demo")
        st.markdown("Try the simulator with sample data. No sign-up required.")
        if st.button("Try Demo"):
            st.session_state.view = "demo"
            st.rerun()

    with col2:
        st.subheader("🚀 Get Started Free")
        st.markdown("Create an account to save plans and unlock features.")
        if st.button("Create Account"):
            st.session_state.view = "register"
            st.rerun()

    with col3:
        st.subheader("👤 Login")
        st.markdown("Access your saved plans and premium features.")
        if st.button("Login"):
            st.session_state.view = "login"
            st.rerun()


def render_demo():
    st.info("You are using Demo Mode with sample data.")

    if st.button("⬅ Back to Home"):
        st.session_state.view = "landing"
        st.rerun()

    # 🔥 DEMO MUST ALWAYS RENDER SIMULATOR
    run_simulator(is_guest=True)

from datetime import datetime

def save_user_to_firebase(
    username: str,
    email: str,
    name: str,
    password_hash: str,
):
    """
    Creates / initializes a user record in Firebase.
    Called ONLY at registration time.
    """

    user_ref = db.collection("users").document(username)

    existing = user_ref.get()

    # -----------------------------
    # If user already exists → do nothing
    # -----------------------------
    if existing.exists:
        print(f"User '{username}' already exists in Firebase")
        return {"status": "exists"}

    # -----------------------------
    # Create new user record
    # -----------------------------
    user_doc = {
        "username": username,
        "email": email,
        "name": name,
        "password_hash": password_hash,   # 🔐 store hashed password only
        "created_at": datetime.utcnow(),
        "app_data": {},                   # optional initial empty data
    }

    user_ref.set(user_doc)

    print(f"Created Firebase user document for '{username}'")

    return {"status": "created"}

from ui.auth_pages import render_login, render_register

def render_auth():
    if st.session_state.view == "login":
        render_login()
    elif st.session_state.view == "register":
        render_register()

    st.markdown("---")
    if st.button("⬅ Back to Home"):
        st.session_state.view = "landing"
        st.rerun()

#def render_auth():
#    authenticator = get_authenticator()

#    if st.session_state.view == "login":
#        st.title("Login")
#        authenticator.login(location="main")

#        if st.session_state.authentication_status is True:
#            st.session_state.view = "app"
#            st.rerun()
#        elif st.session_state.authentication_status is False:
#            st.error("Invalid username or password")

#    elif st.session_state.view == "register":
#        st.title("Create an Account")
#        email, username, name = authenticator.register_user(location="main")

#        if email:
#            st.success("Account created successfully. Please login.")
#            password_hash = config["credentials"]["usernames"][username]["password"]
#            #authenticator.credentials["usernames"][username]["password"]

#            save_user_to_firebase(
#                username=username,
#                email=email,
#                name=name,
#                password_hash=password_hash
#            )
#            st.session_state.view = "login"
#            st.rerun()

#    st.markdown("---")
#    if st.button("⬅ Back to Home"):
#        st.session_state.view = "landing"
#        st.rerun()


def render_app():
    # 🔥 DO NOT RETURN EARLY — EVER
    auth_status = st.session_state.get("authentication_status")

    if auth_status is None:
        st.info("Please login to continue.")
        if st.button("Login"):
            st.session_state.view = "login"
            st.rerun()
        return

    if auth_status is False:
        st.error("Authentication failed.")
        return

    username = st.session_state.get("username")
    st.sidebar.success(f"Logged in as {username}")

    authenticator = get_authenticator()

    # Logout
    if authenticator.logout("Logout", "sidebar"):
        # Clear only auth-related state
        for k in ["authentication_status", "username"]:
            st.session_state[k] = None

        # Reset navigation
        st.session_state.view = "landing"
        st.session_state.logout = False

        st.rerun()

        #st.session_state.clear()
        #st.session_state.view = "landing"
        #st.rerun()

    run_simulator(is_guest=False)


# -------------------------------------------------------------------
# MAIN ROUTER
# -------------------------------------------------------------------
view = st.session_state.view

if view == "landing":
    render_landing()
elif view == "demo":
    render_demo()
elif view in ("login", "register"):
    render_auth()
else:
    render_app()
