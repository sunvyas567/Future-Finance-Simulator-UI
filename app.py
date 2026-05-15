import streamlit as st
from ui.simulator import run_simulator
from ui.auth import get_authenticator
import pandas as pd
import subprocess, os
from streamlit_javascript import st_javascript
from ui.auth_pages import render_login, render_register

# 1. THIS MUST BE THE VERY FIRST STREAMLIT COMMAND
st.set_page_config(layout="wide", initial_sidebar_state="collapsed")

# ==========================================================
    # GLOBAL MOBILE CSS HACKS
    # ==========================
# 2. INJECT GLOBAL CSS (This nukes the header across all pages)
st.markdown("""
    <style>
        /* Hide the entire Streamlit top header */
        header {visibility: hidden;}
        
        /* Specifically target the container to free up screen space */
        [data-testid="stHeader"] {
            display: none !important;
        }
        
        /* Hide the Deploy button */
        .stDeployButton {
            display: none !important;
        }
        
        /* Hide the Main Menu hamburger */
        #MainMenu {
            visibility: hidden;
        }
        
        /* Hide the 'Made with Streamlit' footer */
        footer {
            visibility: hidden;
        }

        /* Compress the main container padding for mobile */
        .block-container {
            padding-top: 1rem;
            padding-bottom: 1rem;
            padding-left: 1rem;
            padding-right: 1rem;
        }

        /* Hide the sidebar completely on mobile screens */
        @media (max-width: 768px) {
            [data-testid="collapsedControl"] {
                display: none !important;
            }
            section[data-testid="stSidebar"] {
                display: none !important;
            }
        }
        /* Compress the vertical space between input widgets */
        .stTextInput, .stNumberInput, .stSelectbox {
            margin-bottom: -1rem !important;
        }
        
        /* Make the labels smaller and closer to the inputs */
        .stTextInput label, .stNumberInput label, .stSelectbox label {
            font-size: 12px !important;
            padding-bottom: 0px !important;
        }

        /* ---------------------------------------------------
           1. NUKE THE MASSIVE TOP GAP (THE ULTIMATE VERSION)
        --------------------------------------------------- */
        /* Target every possible wrapper Streamlit uses for the main page */
        .block-container, 
        div[data-testid="stAppViewBlockContainer"], 
        div[data-testid="stAppViewContainer"] > section > div {
            padding-top: 0rem !important; 
            margin-top: 0rem !important;
        }
        
        /* Completely destroy the header and any ghost space it leaves */
        header[data-testid="stHeader"] {
            display: none !important; 
            height: 0px !important;
            min-height: 0px !important;
            margin: 0px !important;
            padding: 0px !important;
        }    
        

        /* ---------------------------------------------------
           2. THE NUCLEAR 2-COLUMN MOBILE GRID
           Targets both old and new Streamlit class names to 
           guarantee it works on Chrome/Safari iOS.
        --------------------------------------------------- */
        @media screen and (max-width: 1000px) {
            div[data-testid="stHorizontalBlock"] {
                display: flex !important;
                flex-direction: row !important;
                flex-wrap: wrap !important;
                gap: 2% !important; /* Clean gap instead of margins */
            }
            
            div[data-testid="stHorizontalBlock"] > div[data-testid="column"],
            div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"] {
                width: 49% !important;
                min-width: 49% !important;
                max-width: 49% !important;
                flex: 0 0 49% !important;
                display: block !important;
            }
        }

        /* ---------------------------------------------------
           3. TILE PADDING COMPRESSION
        --------------------------------------------------- */
        .stNumberInput {
            margin-bottom: 0px !important;
        }
        
        div[data-testid="stVerticalBlockBorderWrapper"] {
            padding: 10px 8px !important; 
        }
    </style>
""", unsafe_allow_html=True)

# ... Rest of your GLOBAL session initialization starts here ...



# 1. Fetch the window width from the browser synchronously
window_width = st_javascript("window.innerWidth")

# 2. Safely initialize the session state variable
if "is_mobile" not in st.session_state:
    st.session_state.is_mobile = False

# 3. If we successfully got the width, evaluate and store it globally
if window_width > 0:
    st.session_state.is_mobile = (window_width < 768)

# Now you can use it locally in app.py if needed
#is_mobile = st.session_state.is_mobile
#import streamlit as st

# Simple mobile detection using query params fallback
is_mobile = st.session_state.get("is_mobile", False)

#st.markdown("""
#<script>
#const isMobile = window.innerWidth < 768;
#window.parent.postMessage({
###  type: "streamlit:setComponentValue",
#  key: "is_mobile",
#  value: isMobile
#}, "*");
#</script>
#""", unsafe_allow_html=True)


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
def render_landing_old():
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

    #st.set_page_config(layout="wide")

    #st.markdown("""
    #<style>
    #.block-container {
    #    padding-top: 1rem;
    #    padding-bottom: 1rem;
    #    padding-left: 1rem;
    #    padding-right: 1rem;
    #}
    #/* NEW: Hide the default Streamlit top bar and menu */
    #[data-testid="stHeader"] {
    #    display: none !important;
    #}
    
    #/* NEW: Hide the "Deploy" button (just in case Streamlit forces it) */
    #.stDeployButton {
    #    display: none !important;
    #}
    #/* NEW: Hide the sidebar completely on mobile screens */
    #@media (max-width: 768px) {
    #    [data-testid="collapsedControl"] {
    #        display: none !important;
    #    }
    #    section[data-testid="stSidebar"] {
    #        display: none !important;
    #    }
    #}
    #</style>
    #""", unsafe_allow_html=True)

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

def render_landing():
    # 1. Edge-to-Edge Mobile Hero Banner
    # The negative margins pull the banner flush to the edges of the phone screen
    #st.markdown("""
    #<div style="background: linear-gradient(135deg, #1e3a8a 0%, #4f46e5 100%); 
    #            padding: 50px 20px 40px 20px; 
    ##            margin: -1rem -1rem 20px -1rem; 
    #            border-radius: 0 0 30px 30px; 
    #            text-align: center; 
    #            color: white; 
    #            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);">
    #    <div style="font-size: 50px; margin-bottom: 10px;">📊</div>
    #    <h1 style="color: white; font-size: 32px; font-weight: 800; margin-bottom: 5px; padding-top: 0;">FinPlan</h1>
    #    <p style="font-size: 16px; opacity: 0.9; margin: 0;">Your Financial Future, Visualized.</p>
    #</div>
    #""", unsafe_allow_html=True)
    # 1. Edge-to-Edge Mobile Hero Banner (Slimmer Version)
    st.markdown("""
    <div style="background: linear-gradient(135deg, #1e3a8a 0%, #4f46e5 100%); 
                padding: 25px 20px 20px 20px; /* Cut padding in half */
                margin: -1rem -1rem 20px -1rem; 
                border-radius: 0 0 20px 20px; /* Slightly softer curve */
                text-align: center; 
                color: white; 
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);">
        <div style="font-size: 30px; margin-bottom: 5px;">📊</div> <h1 style="color: white; font-size: 24px; font-weight: 800; margin-bottom: 2px; padding-top: 0;">FinPlan</h1>
        <p style="font-size: 14px; opacity: 0.9; margin: 0;">Your Financial Future, Visualized.</p>
    </div>
    """, unsafe_allow_html=True)
    # 2. Primary Call to Actions (Thumb-friendly stack)
    # We use empty columns to center the text slightly or just rely on native center alignment
    st.markdown("<br>", unsafe_allow_html=True)
    
    if st.button("🚀 Try the Demo (No Sign-up)", use_container_width=True, type="primary"):
        st.session_state.view = "demo"
        st.rerun()

    if st.button("✨ Create Free Account", use_container_width=True):
        st.session_state.view = "register"
        st.rerun()

    # Subtle login prompt below the main actions
    st.markdown("<p style='text-align: center; font-size: 14px; color: #6b7280; margin-top: 15px; margin-bottom: 5px;'>Already have an account?</p>", unsafe_allow_html=True)
    if st.button("Log In", use_container_width=True):
        st.session_state.view = "login"
        st.rerun()

    st.divider()

    # 3. Mobile-Friendly Feature Highlights (Stacked Cards)
    st.markdown("### 💡 Why use this planner?")
    
    with st.container(border=True):
        st.markdown("#### 🔄 Stage-Intelligent")
        st.caption("Adapts automatically whether you are building wealth in your 30s or planning withdrawals in your 60s.")

    with st.container(border=True):
        st.markdown("#### 📈 Multi-Scenario")
        st.caption("Compare Base, Conservative, and Aggressive market scenarios with a single tap.")

    with st.container(border=True):
        st.markdown("#### 🛡️ Tax & Rule Aware")
        st.caption("Built-in logic for country-specific accounts like SCSS, POMIS, 401(k), and ISAs.")
        
    st.markdown("<br><br>", unsafe_allow_html=True) # Bottom padding for easy scrolling

def render_landing_old1():
    st.title("Financial Life Planner")
    st.subheader("Visualize Your Financial Future in Minutes")
    
    st.markdown("---")

    # Mobile-Friendly Button Stack (No columns!)
    with st.container(border=True):
        st.markdown("### 📊 Try it out")
        st.caption("Try the simulator with sample data. No sign-up required.")
        if st.button("Try Demo", use_container_width=True, type="primary"):
            st.session_state.view = "demo"
            st.rerun()

    with st.container(border=True):
        st.markdown("### 🚀 Get Started Free")
        st.caption("Create an account to save plans and unlock features.")
        if st.button("Create Account", use_container_width=True):
            st.session_state.view = "register"
            st.rerun()

    with st.container(border=True):
        st.markdown("### 👤 Welcome Back")
        st.caption("Access your saved plans and premium features.")
        if st.button("Login", use_container_width=True):
            st.session_state.view = "login"
            st.rerun()

    st.markdown("---")

    # Mobile-Friendly Feature List (Stacked Cards)
    st.markdown("### 💡 What This Tool Helps You Do")
    
    with st.container(border=True):
        st.markdown("**🔄 Life-Stage Intelligent Planning**")
        st.markdown("🌱 Early — Build income & assets\n\n🏡 Mid — Manage family & wealth\n\n🏖 Retirement — Preserve & draw income")

    with st.container(border=True):
        st.markdown("**📊 What Makes This Different?**")
        st.markdown("- Scenario-based projections\n- Stage-aware planning logic\n- Integrated income + expense modeling\n- Financial trajectory forecasting")

    with st.container(border=True):
        st.markdown("**📈 Three Scenarios**")
        st.markdown("🟢 Base — Balanced strategy\n\n🟡 Conservative — Safety focused\n\n🔴 Aggressive — Growth focused")

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
    if is_mobile:
        render_landing()
    else:
        render_landing_old()
elif view == "demo":
    render_demo()
elif view in ("login", "register"):
    render_auth()
else:
    render_app()
