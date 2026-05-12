import streamlit as st
from ui.simulator import run_simulator
from ui.auth import get_authenticator

import streamlit as st

import subprocess, os

#import streamlit as st

# Simple mobile detection using query params fallback
is_mobile = st.session_state.get("is_mobile", False)

st.markdown("""
<script>
const isMobile = window.innerWidth < 768;
window.parent.postMessage({
  type: "streamlit:setComponentValue",
  key: "is_mobile",
  value: isMobile
}, "*");
</script>
""", unsafe_allow_html=True)


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
   
#    st.markdown("""
#    ### 💡 What This Tool Helps You Do

#    - Understand your financial future across different life stages  
#    - Plan major expenses like education, housing, travel, and retirement  
#    - Model income, investments, and lifestyle choices  
#    - Compare scenarios and see long-term impact instantly  
#    - Stay financially prepared through life transitions  
#    - Plan smarter, account for inflation, and stress-test your financial future with multi-year projections  #

#    ---

    ### 🔄 Life-Stage Intelligent Planning

#    This simulator automatically adjusts planning logic based on your life stage:

#    🌱 **Early Stage** — build income, assets, and financial stability  
#    🏡 **Mid Stage** — manage family, major goals, and wealth growth  
#    🏖 **Retirement Stage** — preserve wealth and manage income streams  

#    ---

#    ### 📊 What Makes This Different?

#    - Scenario-based financial projections  
#    - Stage-aware expenses and investment logic  
#    - Country-specific retirement structures  
#    - Integrated income, expense, and investment modeling  
#    - Visual financial trajectory forecasting  

#    ---

    ### 📈 Three Scenarios, One Click

#    🟢 **Base Scenario — Balanced Planning**  
#    A realistic and moderate financial strategy based on stable growth assumptions and disciplined spending.#

#    🟡 **Conservative Scenario — Safety First**  
#    A cautious approach focused on capital protection, lower risk, and higher financial resilience.

#    🔴 **Aggressive Scenario — Growth Focused**  
#    A higher-growth strategy that assumes stronger investment performance and a more growth-oriented allocation.
#    """)

        # ----------

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

    st.markdown("---")

    #import streamlit as st

    st.set_page_config(layout="wide")

    st.markdown("""
    <style>
    .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
        padding-left: 1rem;
        padding-right: 1rem;
    }
    /* NEW: Hide the default Streamlit top bar and menu */
    [data-testid="stHeader"] {
        display: none !important;
    }
    
    /* NEW: Hide the "Deploy" button (just in case Streamlit forces it) */
    .stDeployButton {
        display: none !important;
    }
    /* NEW: Hide the sidebar completely on mobile screens */
    @media (max-width: 768px) {
        [data-testid="collapsedControl"] {
            display: none !important;
        }
        section[data-testid="stSidebar"] {
            display: none !important;
        }
    }
    </style>
    """, unsafe_allow_html=True)

    is_mobile = st.session_state.get("is_mobile", False)

    if is_mobile:
        st.markdown("""
        <style>
        html, body {
            font-size: 14px;
        }
        </style>
        """, unsafe_allow_html=True)

    st.title("Financial Life Planner")

    # ---------- 2 x 2 GRID ----------
    row1_col1, row1_col2 = st.columns(2)
    row2_col1, row2_col2 = st.columns(2)

    # ---- Section 1 ----
    with row1_col1:
        st.markdown("""
        ### 💡 What This Tool Helps You Do
        - Understand financial future across life stages
        - Plan major expenses and goals
        - Model income and investments
        - Compare long-term scenarios
        """)

    # ---- Section 2 ----
    with row1_col2:
        st.markdown("""
        ### 🔄 Life-Stage Intelligent Planning
        🌱 Early — Build income & assets  
        🏡 Mid — Manage family & wealth  
        🏖 Retirement — Preserve & draw income
        """)

    # ---- Section 3 ----
    with row2_col1:
        st.markdown("""
        ### 📊 What Makes This Different?
        - Scenario-based projections
        - Stage-aware planning logic
        - Integrated income + expense modeling
        - Financial trajectory forecasting
        """)

    # ---- Section 4 ----
    with row2_col2:
        st.markdown("""
        ### 📈 Three Scenarios
        🟢 Base — Balanced strategy  
        🟡 Conservative — Safety focused  
        🔴 Aggressive — Growth focused
        """)

    st.markdown("---")



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
