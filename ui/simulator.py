import streamlit as st
import pandas as pd

from services.api_client import (
    get_config,
    get_user_data,
    save_user_data,
    get_entitlement,
    calculate_projections
)

from ui.payments import render_payments

# -------------------------------------------------------------------
# User Context Resolver (SAFE)
# -------------------------------------------------------------------
def get_user_context(is_guest: bool):
    if is_guest:
        return {
            "username": "guest",
            "is_guest": True,
            "is_premium": False
        }

    username = st.session_state.get("username")
    entitlement = get_entitlement(username)

    return {
        "username": username,
        "is_guest": False,
        "is_premium": entitlement.get("is_premium", False)
    }

def hydrate_defaults_from_config(user_data: dict, config: list):
    for field in config:
        name = field.get("Field Name")
        default = field.get("Field Default Value")

        if not name:
            continue

        if name not in user_data:
            user_data[name] = {"input": default}

def apply_defaults_from_config(
    user_data: dict,
    config: dict,
    *,
    force: bool = False
):
    """
    Safely hydrate user_data from config defaults.

    Rules:
    - Never overwrite non-empty user values (unless force=True)
    - Safe to call multiple times (idempotent)
    - Works for guest + logged-in users
    - Backward compatible with older saved users
    """
    #print("In Apply defaults from config" , config)
    # ---------------------------------------------------------
    # Helper: set value only if missing
    # ---------------------------------------------------------
    def set_default(container: dict, key: str, value):
        if force:
            container[key] = value
            return

        if key not in container:
            container[key] = value
            return

        # Handle structured values
        existing = container[key]

        #if isinstance(existing, dict) and "input" in existing:
        #    if existing["input"] in (None, "", 0):
        #        container[key] = value
        # NEVER overwrite expense inputs once created
        if isinstance(existing, dict) and "input" in existing:
            return

        elif existing in (None, "", 0):
            container[key] = value

    country = user_data.get("country", "IN")
    # ---------------------------------------------------------
    # BASE DATA (GL fields)
    # ---------------------------------------------------------
    for field in config.get("base_data", []):
        fname = field.get("Field Name")
        default = field.get("Field Default Value")
        #print("BASE DATA FNAME", fname)
        if not fname:
            continue
        if fname == "GLProjectionYears":
            continue  # 🔒 Base Data owns this field
        set_default(
            user_data,
            fname,
            {"input": default}
        )
        #print("BASE DATA FNAME VALUE", default)

    # ---------------------------------------------------------
    # ONE-TIME EXPENSES
    # ---------------------------------------------------------
    user_data.setdefault("onetime_expenses", {})

    for field in config.get("onetime_expenses", []):
        fname = field.get("Field Name")
        default = field.get("Field Default Value", 0)

        if not fname:
            continue

        set_default(
            user_data["onetime_expenses"],
            fname,
            {"input": default}
        )

    # ---------------------------------------------------------
    # RECURRING EXPENSES (monthly)
    # ---------------------------------------------------------
    user_data.setdefault("recurring_expenses", {})
    user_data["recurring_expenses"].setdefault(country, {})

    for field in config.get("recurring_expenses", []):
        fname = field.get("Field Name")
        default = field.get("Field Default Value", 0)

        if not fname:
            continue

        if force or fname not in user_data["recurring_expenses"][country]:
            user_data["recurring_expenses"][country][fname] = {
                "monthly": default
            }

    #user_data.setdefault("recurring_expenses", {})

    #for field in config.get("recurring_expenses", []):
    #    fname = field.get("Field Name")
    #    default = field.get("Field Default Value", 0)

    #    if not fname:
    #        continue

    #    set_default(
    #        user_data["recurring_expenses"],
    #        fname,
    #        {"monthly": default}
    #    )

    # ---------------------------------------------------------
    # INVESTMENT PLAN + SCENARIOS
    # ---------------------------------------------------------
    if "investment_plan" not in user_data or force:
        user_data["investment_plan"] = {}

    plan = user_data["investment_plan"]

    plan.setdefault("active_scenario", "Base")
    plan.setdefault("scenarios", {})

    # ---------------- Default Base Scenario ----------------
    if "Base" not in plan["scenarios"] or force:
        plan["scenarios"]["Base"] = {
            "allocations": {},
            "rates": {},
            "income_sources": {},
        }

    base_scenario = plan["scenarios"]["Base"]

    # Allocation defaults
    for field in config.get("investment_plan", []):
        fname = field.get("Field Name")
        default = field.get("Field Default Value")
        #print('INVEST FANME', fname)
        if not fname:
            continue

        # Allocation
        if fname.startswith("ALLOC_"):
            key = fname.replace("ALLOC_", "")
            base_scenario["allocations"].setdefault(key, default)

        # Rates
        elif fname.startswith("RATE_"):
            key = fname.replace("RATE_", "")
            base_scenario["rates"].setdefault(key, default)

        # Income sources
        elif fname.startswith("INCOME_"):
            key = fname.replace("INCOME_", "")
            base_scenario["income_sources"].setdefault(key, default)
        #print("INVEST FANME value", default)
    
        
    for sc in plan.get("scenarios", {}).values():
        sc["_engine_synced"] = False

    print("After applying defaults, user data is:", user_data)
    # ---------------------------------------------------------
    # MARK INITIALIZED (important!)
    # ---------------------------------------------------------
    user_data.setdefault("_defaults_applied", True)

def default_investment_scenario(country: str) -> dict:
    """
    Country-aware base investment defaults
    """
    if country == "US":
        return {
            "allocations": {
                "401K": 40,
                "IRA": 30,
                "BROKERAGE": 30
            },
            "rates": {
                "401K": 5,
                "IRA": 4,
                "BROKERAGE": 6
            },
            "income_sources": {
                "social_security": 2000,
                "rental": 0,
                "pension": 0,
                "annuity": 0,
                "dividends": 0,
                "other": 0
            }
        }

    elif country == "UK":
        return {
            "allocations": {
                "PENSION": 70,
                "ISA": 30
            },
            "rates": {
                "PENSION": 4,
                "ISA": 3
            },
            "income_sources": {
                "rental": 0,
                "pension": 1200,
                "annuity": 0,
                "dividends": 0,
                "other": 0
            }
        }

    # INDIA (default)
    return {
        "allocations": {
            "SWP": 40,
            "FD": 25,
            "SCSS": 20,
            "POMIS": 15
        },
        "rates": {
            "SWP": 6,
            "FD": 5,
            "SCSS": 8,
            "POMIS": 7
        },
        "income_sources": {
            "rental": 0,
            "pension": 0,
            "annuity": 0,
            "dividends": 0,
            "other": 0
        }
    }


def clone_scenario(base: dict) -> dict:
    import copy
    return copy.deepcopy(base)

# -------------------------------------------------------------------
# MAIN SIMULATOR
# -------------------------------------------------------------------
def run_simulator(is_guest: bool = False):
    # ==========================================================
    # 1. USER CONTEXT
    # ==========================================================
    user = get_user_context(is_guest)

    # ---------------- Sidebar ----------------
    if user["is_guest"]:
        st.sidebar.title("Demo Mode")
        st.sidebar.info("Sample data only. Nothing is saved.")
    else:
        st.sidebar.title(f"Welcome, {user['username']}")

    if user["is_premium"]:
        st.sidebar.success("Premium Member ✨")
    elif not user["is_guest"]:
        if st.sidebar.button("Upgrade to Premium 🚀"):
            st.session_state.page = "Upgrade"
            st.rerun()

    # ==========================================================
    # 2. LOAD USER DATA (ONCE)
    # ==========================================================
    if "user_data" not in st.session_state:
        if user["is_guest"]:
            st.session_state.user_data = {}
        else:
            st.session_state.user_data = get_user_data(user["username"]) or {}

    user_data = st.session_state.user_data

    # ----------------------------------------------------------
    # Country safety (MUST be before config)
    # ----------------------------------------------------------
    user_data.setdefault("country", "IN")
    country = user_data["country"]

    # ==========================================================
    # 3. LOAD CONFIG (country-aware)
    # ==========================================================
    config = get_config(country)
    #print("COMFIG ",config["investment_plan"])

    #def prune_by_config(container: dict, valid_keys: set):
    #    return {k: v for k, v in container.items() if k in valid_keys}

    # ---- COUNTRY-SAFE PRUNING (CRITICAL) ----
    #valid_onetime = {
    #    f["Field Name"]
    #    for f in config["onetime_expenses"]
    #    if isinstance(f, dict) and "Field Name" in f and "Field Default Value" in f
    #}

    #valid_recurring = {
    #    f["Field Name"]
    #    for f in config["recurring_expenses"]
    #    if isinstance(f, dict) and "Field Name" in f and "Field Default Value" in f
    #}

    #user_data["onetime_expenses"] = prune_by_config(
    #    user_data.get("onetime_expenses", {}),
    #    valid_onetime,
    #)

    #user_data["recurring_expenses"] = prune_by_config(
    #    user_data.get("recurring_expenses", {}),
    #    valid_recurring,
    #)

    # After loading new config
    #user_data["onetime_expenses"] = prune_by_config(
    #    user_data.get("onetime_expenses", {}),
    #    {f["Field Name"] for f in config["onetime_expenses"] if "Field Name" in f}
    #)

    #user_data["recurring_expenses"] = prune_by_config(
    #    user_data.get("recurring_expenses", {}),
    #    {f["Field Name"] for f in config["recurring_expenses"] if "Field Name" in f}
    #)

    #prev_country = user_data.get("_prev_country")

    #if prev_country != user_data["country"]:
    #    # Mark country switch
    #    user_data["_prev_country"] = user_data["country"]

        # Country-sensitive resets
    #    user_data.pop("initial_corpus", None)
    #    user_data.pop("investment_plan", None)
    #    user_data.pop("recurring_expenses", None)
    #    user_data.pop("onetime_expenses", None)

        # Important: allow defaults to reapply
    #    user_data.pop("_defaults_applied", None)

    #if user["is_guest"]:
    #    # 🔥 Country switch must reset country-dependent data
    #    user_data.clear()
    #    user_data["country"] = country

    #    apply_defaults_from_config(
    #        user_data,
    #        {
    #            "base_data": config["base_data"],
    #            "onetime_expenses": config["onetime_expenses"],
    #            "recurring_expenses": config["recurring_expenses"],
    #            "investment_plan": config["investment_plan"],
    #        },
    #        force=True
    #   )

    # ==========================================================
    # 4. APPLY DEFAULTS (EARLY, ONCE, IDENTITY-SAFE)
    # ==========================================================
    if user["is_guest"]:
        #print("I am here in gust")
        # 🔥 Country switch must reset country-dependent data
    #    user_data.clear()
        user_data.setdefault("country", country)
        #user_data["country"] = country
        # Guest: always deterministic fresh state
        apply_defaults_from_config(
            user_data,
            {
                "base_data": config["base_data"],
                "onetime_expenses": config["onetime_expenses"],
                "recurring_expenses": config["recurring_expenses"],
                "investment_plan": config["investment_plan"],
            },
            force=True
        )
        user_data.setdefault("GLProjectionYears", {"input": 2})
        user_data["GLProjectionYears"]["input"] = min(
            user_data["GLProjectionYears"]["input"], 2
        )
    else:
        # Logged-in user: hydrate only once per DB record
        #print("I am here")
        if not user_data.get("_defaults_applied"):
            #print("I am here applying defaults")
            apply_defaults_from_config(
                user_data,
                {
                    "base_data": config["base_data"],
                    "onetime_expenses": config["onetime_expenses"],
                    "recurring_expenses": config["recurring_expenses"],
                    "investment_plan": config["investment_plan"],
                }
            )
            user_data["_defaults_applied"] = True

    
    # --------------------------------------------------
    # GLOBAL initial corpus hydration (CRITICAL)
    # --------------------------------------------------
    from ui.base_data import hydrate_initial_corpus_defaults

    hydrate_initial_corpus_defaults(
        user_data,
        user_data["country"]
    )
    # ==========================================================
    # 5. NAVIGATION
    # ==========================================================
    pages = [
        "Welcome",
        "Your Financial Profile",
        "Your Financial Commitments & Expenses",
        "Your Income Sources & Investment Strategy",
        "Your Financial Outlook Report",
    ]

    if not user["is_guest"] and not user["is_premium"]:
        pages.append("Upgrade")

    if "page" not in st.session_state or st.session_state.page not in pages:
        st.session_state.page = pages[0]

    with st.sidebar:
        selected = st.radio(
            "Navigate",
            pages,
            index=pages.index(st.session_state.page),
        )
        if selected != st.session_state.page:
            st.session_state.page = selected
            st.rerun()

    page = st.session_state.page

    # ==========================================================
    # 6. PROJECTIONS (ONLY FOR SUMMARY)
    # ==========================================================
    projections = None
    base_context = None

    if page == "Your Financial Outlook Report":
        try:
            from ui.investment_plan import ensure_scenarios
            # -------------------------------------------------
            # ENSURE SCENARIOS EXIST (CRITICAL – SINGLE PLACE)
            # -------------------------------------------------
            plan = user_data.setdefault("investment_plan", {})
            ensure_scenarios(plan, user_data.get("country", "IN"))

            result = calculate_projections(user_data, user)

            active = result.get("active_result", {})
            projections = active.get("projections", [])

            base_context = result.get("base_context", {})

            # store full result for comparison charts
            st.session_state.projection_result = result

            #projections = result.get("projections", [])
            #base_context = result.get("base_context", {})

            if not isinstance(base_context, dict):
                raise ValueError("Invalid base_context")

            #st.session_state.projection_result = result

        except Exception as e:
            st.error(f"Projection calculation failed: {e}")
            return
    else:
        cached = st.session_state.get("projection_result")
        if isinstance(cached, dict):
            projections = cached.get("projections")
            base_context = cached.get("base_context")
            life_stage = cached.get("life_stage")
            stage_metrics = cached.get("stage_metrics")

    # ==========================================================
    # 7. CURRENCY (DERIVED)
    # ==========================================================
    if base_context and "_meta" in base_context:
        st.session_state.currency = base_context["_meta"].get("currency", "₹")
    else:
        st.session_state.currency = "₹"

    # ==========================================================
    # 8. PAGE RENDERING (PURE UI)
    # ==========================================================
    if page == "Welcome":
        #st.header("About the App")
        st.title("Plan Your Financial Future With Confidence")
        st.subheader("A simple, powerful tool to understand your future income, expenses, and savings.")
        
        st.markdown("""
        ## 👋 Welcome to Your Smart Financial Planner

        Plan smarter. Invest better. Retire with confidence.

        """)

        st.markdown("### 🎯 What you can do here")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("""
            ### 💰 Money & Expenses
            - Track lifestyle costs  
            - Plan major life goals  
            - Estimate yearly spending  
            """)

        with col2:
            st.markdown("""
            ### 📈 Investments & Growth
            - Choose investment mix  
            - Compare strategies  
            - See long-term projections  
            """)

        with col3:
            st.markdown("""
            ### 🏖 Finance Readiness
            - Check income sustainability  
            - Estimate corpus longevity  
            - Visualize future wealth  
            """)

        st.markdown("---")


        st.markdown("### 🔮 Explore Different Financial Futures")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("""
            🟢 **Base Scenario**  
            Balanced growth with realistic assumptions.
            """)

        with col2:
            st.markdown("""
            🟡 **Conservative Scenario**  
            Stability first. Lower risk approach.
            """)

        with col3:
            st.markdown("""
            🔴 **Aggressive Scenario**  
            Higher growth with higher risk.
            """)

        st.markdown("---")


        st.markdown("""
        ### 🚀 Why people love this simulator

        ✔ Simple and intuitive  
        ✔ Adapts to your life stage  
        ✔ Visual projections — not guesswork  
        ✔ Multi-scenario planning in seconds  

        """)

        st.success("💡 In just a few minutes, see if your future lifestyle is financially secure.")

        
        st.info(
            "Designed for everyday individuals — no financial background required."
        )
        st.success(
            "👉 Start by entering your details in 'Your Profile' to see your personalized retirement outlook."
        )

    #    st.markdown(config["about"])

    elif page == "Your Financial Profile":
        from ui.base_data import render_base_data
        render_base_data(config["base_data"], user_data, user)

    elif page == "Your Financial Commitments & Expenses":
        from ui.expenses import render_expenses
        render_expenses(config=config, user_data=user_data, user=user)

    elif page == "Your Income Sources & Investment Strategy":
        from ui.investment_plan import render_investment_plan
        render_investment_plan(user_data=user_data, user=user)

    elif page == "Your Financial Outlook Report":
        from ui.summary import render_summary
        if not projections or not base_context:
            st.warning("Please complete inputs to view summary.")
            return
        render_summary(
            projections=projections,
            user_data=user_data,
            user=user,
            base_context=base_context,
            life_stage=result["life_stage"],
            stage_metrics=result["life_stage_metrics"]
        )

    elif page == "Upgrade":
        render_payments(user["username"])

    # ==========================================================
    # 9. SAVE USER DATA (ONLY AFTER FULL HYDRATION)
    # ==========================================================
    if not user["is_guest"]:
        #print(f"Saving user data for '{user['username']}' with keys: {list(user_data.keys())}")
        #print("session states user data : ", st.session_state.user_data)
        save_user_data(user["username"], st.session_state.user_data)
