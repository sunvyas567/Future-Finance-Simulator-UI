import streamlit as st
from ui.currency import get_currency

# =========================================================
# Life Stage Detection
# =========================================================
def get_life_stage(age: int) -> str:
    if age < 35:
        return "early"
    elif age < 55:
        return "mid"
    else:
        return "retirement"
    
def render_stage_context(stage: str):
    if stage == "early":
        st.info(
            "🌱 **Wealth Building Stage**\n\n"
            "Capture your current savings and investments. "
            "Even small amounts matter — this helps project long-term growth."
        )

    elif stage == "mid":
        st.info(
            "📈 **Retirement Building Stage**\n\n"
            "You are actively building retirement assets. "
            "Include all long-term investments and retirement accounts."
        )

    else:
        st.success(
            "🏖 **Retirement / Pre-Retirement Stage**\n\n"
            "This represents your retirement corpus available for income planning."
        )

# =========================================================
# Defaults (single source of truth)
# =========================================================
def hydrate_initial_corpus_defaults(user_data: dict, country: str):
    DEFAULTS = {
        "IN": {
            "PF": 150000,
            "PPF": 100000,
            "NPS": 50000,
            "SUPER": 0,
            "OTHER": 0,
        },
        "US": {
            "401K": 50000,
            "IRA": 30000,
            "BROKERAGE": 20000,
            "OTHER": 0,
        },
        "UK": {
            "PENSION": 40000,
            "ISA": 20000,
            "OTHER": 0,
        },
    }

    expected = DEFAULTS.get(country, {})
    user_data.setdefault("initial_corpus", {})
    country = user_data.get("country", "IN")
    user_data["initial_corpus"].setdefault(country, {})
    country_corpus = user_data["initial_corpus"][country]
    # If country changed → reset safely - NOT required as country level scoping is implemented for corpus values    
    #if set(user_data["initial_corpus"].keys()) != set(expected.keys()):
    #    user_data["initial_corpus"] = {}

    # Apply defaults ONLY if missing
    for k, v in expected.items():
        country_corpus.setdefault(k, v)

    #print("InitialCorpus defualts", user_data["initial_corpus"])

# =========================================================
# UI
# =========================================================
def render_base_data(config, user_data: dict, user: dict):
    """
    FINAL Base Data UI
    - Country
    - Demographics
    - Projection Years
    - Initial Corpus (single source of truth)
    """

    is_guest = user is None
    is_premium = user.get("is_premium", False) if user else False

    # -----------------------------------------------------
    # Country
    # -----------------------------------------------------
    COUNTRIES = {
        "India": "IN",
        "United States": "US",
        "United Kingdom": "UK",
    }

    user_data.setdefault("country", "IN")

    def Reset_Active_Scenario(): # for investment plan page - resets active scenario to base on country change to prevent key errors
        # Implementation for resetting active scenario
        st.session_state["_active_scenario_loaded"] = None  # Reset the flag to allow reloading the scenario for the new country

    selected = st.selectbox(
        "🌍 Country of Residence",
        list(COUNTRIES.keys()),
        index=list(COUNTRIES.values()).index(user_data["country"]),
        on_change=Reset_Active_Scenario, #resets active scenario to base on country change to prevent key errors
        disabled=is_guest,
    )

    user_data["country"] = COUNTRIES[selected]

    # -----------------------------------------------------
    # Defaults (safe & idempotent)
    # -----------------------------------------------------
    hydrate_initial_corpus_defaults(user_data, user_data["country"])

    currency = get_currency(user_data)

    #st.header("📋 Base Information")
    st.header("👤 Define your financial identity and planning horizon.")
    st.caption("Tell us a little about yourself so that your financial plan can be personalized to your context and needs.")
    st.caption("These details remain constant across all scenarios.")

    # -----------------------------------------------------
    # Demographics
    # -----------------------------------------------------
    col1, col2 = st.columns(2)

    user_data.setdefault("GLAge", {"input": 35})
    user_data.setdefault("GLGender", {"input": "Male"})
    user_data.setdefault("GLProjectionYears", {"input": 25})

    with col1:
        st.subheader("👤 Your Profile")

        age = st.number_input(
            "Current Age",
            min_value=18,
            max_value=100,
            value=int(user_data["GLAge"]["input"]),
            disabled=is_guest or not is_premium,
        )
        if not is_guest:
            user_data["GLAge"]["input"] = age

        gender = st.selectbox(
            "Gender",
            ["Male", "Female"],
            index=0 if user_data["GLGender"]["input"] == "Male" else 1,
            disabled=is_guest or not is_premium,
        )
        if not is_guest:
            user_data["GLGender"]["input"] = gender

    with col2:
        st.subheader("🗓 How long you want to plan for?")

        max_years = 60 if is_premium else 2

        stored_years = int(user_data["GLProjectionYears"]["input"])

        # 🔥 Clamp stored value to allowed range
        safe_years = min(stored_years, max_years)

        years = st.number_input(
            "Planning Duration (Years)",
            min_value=1,
            max_value=max_years,
            value=safe_years,
            disabled=is_guest or not is_premium,
        )

        #user_data["GLProjectionYears"]["input"] = years

        #years = st.number_input(
        #    "Projection Years",
        #    min_value=1,
        ###    max_value=max_years,
        #    value=int(user_data["GLProjectionYears"]["input"]),
        #    disabled=is_guest or not is_premium,
        #)
        if not is_guest:
            user_data["GLProjectionYears"]["input"] = years

        if not is_guest and not is_premium:
            st.info("Free users are limited to 2 years. projection years can be extended with a premium subscription.")

    st.divider()

    # -----------------------------------------------------
    # Initial Corpus (REDESIGNED UI)
    # -----------------------------------------------------
    #st.subheader("💰 Initial Retirement Corpus")
    #st.caption("Your current retirement savings (include/exclude as needed)")
    #st.subheader("💰 Your Current Savings (Starting Corpus)")
    #st.caption("Savings and investments you already have for retirement. (include/exclude as needed)")

    # -----------------------------------------------------
    # Life Stage Context
    # -----------------------------------------------------
    age_val = user_data["GLAge"]["input"]
    stage = get_life_stage(age_val)

    if stage == "early":
        st.subheader("💰 Your Current Savings & Investments")
        st.caption("Everything you have saved or invested so far")

    elif stage == "mid":
        st.subheader("💰 Your Growing Retirement Corpus")
        st.caption("All assets being built for long-term retirement")

    else:
        st.subheader("💰 Your Retirement Corpus")
        st.caption("Assets available to fund retirement")

    render_stage_context(stage)


    def render_corpus_cards(corpus_config: list):
        # 1. Ensure the nested structure exists for the current country
        user_data.setdefault("initial_corpus", {})
        country = user_data.get("country", "IN")
        user_data["initial_corpus"].setdefault(country, {})
        
        # 2. Create a shortcut to the current country's corpus data
        country_corpus = user_data["initial_corpus"][country]

        total = 0
        cols = st.columns(2)

        for idx, item in enumerate(corpus_config):
            col = cols[idx % 2]
            key = item["key"]

            with col:
                with st.container(border=True):
                    st.markdown(f"### {item['icon']} {item['label']}")

                    # We include 'country' in the session_state key to prevent 
                    # values from "bleeding" over when switching countries
                    include_key = f"corpus_{country}_{key}_include"
                    value_key = f"corpus_{country}_{key}_value"

                    # Initialize include flag based on country-specific data
                    if include_key not in st.session_state:
                        st.session_state[include_key] = country_corpus.get(key, 0) > 0

                    include = st.checkbox(
                        "Include",
                        key=include_key,
                        disabled=is_guest or not is_premium
                    )

                    # Get value from the country-specific dictionary
                    current_value = float(country_corpus.get(key, 0))

                    value = st.number_input(
                        f"Amount ({currency})",
                        min_value=0.0,
                        value=current_value,
                        disabled=not include or is_guest or not is_premium,
                        key=value_key
                    )

                    if not is_guest:
                        # Save back to the country-specific dictionary
                        country_corpus[key] = value if include else 0.0

                    if include:
                        total += value
        
        return total # Optional: return total if you need it elsewhere

    def render_corpus_cards_old(corpus_config: list):
        total = 0
        cols = st.columns(2)

        for idx, item in enumerate(corpus_config):
            col = cols[idx % 2]
            key = item["key"]

            with col:
                with st.container(border=True):
                    st.markdown(f"### {item['icon']} {item['label']}")

                    include_key = f"corpus_{key}_include"
                    value_key = f"corpus_{key}_value"

                    # Initialize include flag (default = True if value > 0)
                    if include_key not in st.session_state:
                        st.session_state[include_key] = user_data["initial_corpus"].get(key, 0) > 0

                    include = st.checkbox(
                        "Include",
                        key=include_key,
                        disabled=is_guest or not is_premium
                    )

                    current_value = float(user_data["initial_corpus"].get(key, 0))

                    value = st.number_input(
                        f"Amount ({currency})",
                        min_value=0.0,
                        value=current_value,
                        disabled=not include or is_guest or not is_premium,
                        key=value_key
                    )

                    if not is_guest:
                        user_data["initial_corpus"][key] = value if include else 0.0

                    if include:
                        total += value

        return total
    # Country-specific corpus configuration
    if user_data["country"] == "IN":
        corpus_config = [
            {"key": "PF", "label": "Provident Fund (PF)", "icon": "🏦"},
            {"key": "PPF", "label": "Public Provident Fund (PPF)", "icon": "📘"},
            {"key": "NPS", "label": "National Pension Scheme (NPS)", "icon": "📊"},
            {"key": "SUPER", "label": "Superannuation", "icon": "🧾"},
            {"key": "OTHER", "label": "Other Corpus", "icon": "➕"},
        ]

    elif user_data["country"] == "US":
        corpus_config = [
            {"key": "401K", "label": "401(k)", "icon": "🏦"},
            {"key": "IRA", "label": "IRA", "icon": "📘"},
            {"key": "BROKERAGE", "label": "Brokerage Account", "icon": "📈"},
            {"key": "OTHER", "label": "Other Corpus", "icon": "➕"},
        ]

    elif user_data["country"] == "UK":
        corpus_config = [
            {"key": "PENSION", "label": "Pension Fund", "icon": "🏦"},
            {"key": "ISA", "label": "ISA", "icon": "📘"},
            {"key": "OTHER", "label": "Other Corpus", "icon": "➕"},
        ]
    
    if stage == "early":
        st.caption("💡 Tip: Include EPF, savings, mutual funds, and any investments. in Others category")

    if stage == "mid":
        st.caption("💡 Tip: Include retirement accounts, long-term investments, and pension funds. in Others category")

    total = render_corpus_cards(corpus_config)

    st.divider()

    st.metric(
        "Total Initial Corpus",
        f"{currency}{total:,.0f}"
    )

    # -----------------------------------------------------
    # Initial Corpus (ONLY source of truth) - OLD UI (for reference)
    # -----------------------------------------------------
    
    #st.subheader("💰 Initial Retirement Corpus")
    #st.caption("Your current retirement savings")

    #def corpus_field_old(key: str, label: str):
    #    value = user_data["initial_corpus"].get(key, 0.0)

    #    new_val = st.number_input(
    #        f"{label} ({currency})",
    #        min_value=0.0,
    #        value=float(value),
    #        disabled=is_guest or not is_premium,
    #        key=f"corpus_{key}",
    #    )

    #    user_data["initial_corpus"][key] = new_val
    #def corpus_field(key: str, label: str):
    #    value = user_data["initial_corpus"].get(key, 0.0)

    #    new_val = st.number_input(
    #        f"{label} ({currency})",
    #        min_value=0.0,
    #        value=float(value),
    #        disabled=is_guest or not is_premium,
    #        key=f"corpus_{key}",
    #    )

    #    if not is_guest:
    #        user_data["initial_corpus"][key] = new_val
    #    else :
    #        user_data["initial_corpus"][key] = value  # preserve existing value for guest

    # 🇮🇳 INDIA
    #if user_data["country"] == "IN":
    #    corpus_field("PF", "Provident Fund (PF)")
    #    corpus_field("PPF", "Public Provident Fund (PPF)")
    #    corpus_field("NPS", "National Pension Scheme (NPS)")
    #    corpus_field("SUPER", "Superannuation")
    #    corpus_field("OTHER", "Other Corpus")

    # 🇺🇸 US
    #elif user_data["country"] == "US":
    #    corpus_field("401K", "401(k)")
    ##    corpus_field("IRA", "IRA")
    #    corpus_field("BROKERAGE", "Brokerage Account")
    #    corpus_field("OTHER", "Other Corpus")

    # 🇬🇧 UK
    #elif user_data["country"] == "UK":
    #    corpus_field("PENSION", "Pension Fund")
    #    corpus_field("ISA", "ISA")
    #    corpus_field("OTHER", "Other Corpus")

    #print("InitialCorpus UI", user_data["initial_corpus"])
    # -----------------------------------------------------
    # Total (derived only)
    # -----------------------------------------------------
    #total = sum(user_data["initial_corpus"].values())

    #st.metric(
    #    "Total Initial Corpus",
    #    f"{currency}{total:,.0f}"
    #)

# =========================================================
# UI
# =========================================================
# UI (Wealthfront/Mobile Style)
# =========================================================
# =========================================================
# UI (Wealthfront/Mobile Style)
# =========================================================
import streamlit as st

def render_base_data_mobile(config, user_data: dict, user: dict):
    is_guest = user is None
    is_premium = user.get("is_premium", False) if user else False
    COUNTRIES = {"India": "IN", "United States": "US", "United Kingdom": "UK"}
    user_data.setdefault("country", "IN")

    def Reset_Active_Scenario(): 
        st.session_state["_active_scenario_loaded"] = None  

    # 1. 🚨 THE BULLETPROOF iOS CSS HACK
    st.markdown("""
    <style>
        @media screen and (max-width: 850px) {
            div[data-testid="stHorizontalBlock"] {
                flex-direction: row !important;
                flex-wrap: wrap !important;
                justify-content: space-between !important;
            }
            div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {
                width: 48% !important;
                flex: 0 0 48% !important;
                min-width: 48% !important;
                margin-bottom: 10px !important;
            }
        }
        
        .stNumberInput {
            margin-bottom: 0px !important;
        }
        
        div[data-testid="stVerticalBlockBorderWrapper"] {
            padding: 10px 8px !important; 
        }
    </style>
    """, unsafe_allow_html=True)

    # 1. Subtle Country Selector
    selected = st.selectbox(
        "🌍 Where do you live?",
        list(COUNTRIES.keys()),
        index=list(COUNTRIES.values()).index(user_data["country"]),
        on_change=Reset_Active_Scenario,
        disabled=is_guest,
    )
    user_data["country"] = COUNTRIES[selected]
    # Make sure this helper exists in your code imports!
    # hydrate_initial_corpus_defaults(user_data, user_data["country"]) 
    currency = get_currency(user_data)

    st.markdown("---")
    st.markdown("### 👤 Let's get to know you")

    # 2. Conversational Sliders (Tactile Mobile Input)
    with st.container(border=True):
        user_data.setdefault("GLAge", {"input": 35})
        user_data.setdefault("GLProjectionYears", {"input": 25})

        age = st.slider(
            "How old are you today?",
            min_value=18, max_value=80,
            value=int(user_data["GLAge"]["input"]),
            disabled=is_guest or not is_premium,
        )
        if not is_guest: user_data["GLAge"]["input"] = age

        max_years = 60 if is_premium else 2
        safe_years = min(int(user_data["GLProjectionYears"]["input"]), max_years)
        
        years = st.slider(
            "How many years into the future should we look?",
            min_value=1, max_value=max_years,
            value=safe_years,
            disabled=is_guest or not is_premium,
            help="Free users are limited to 2 years."
        )
        if not is_guest: user_data["GLProjectionYears"]["input"] = years

    # 3. Starting Corpus (Mobile Grid Layout)
    st.markdown("### 💰 Your Starting Line")
    st.caption("Enter current balances. Leave at 0 if you don't have this account.")

    # Added short "desc" to each config to match our tile design
    if user_data["country"] == "IN":
        corpus_config = [
            {"key": "PF", "label": "Provident Fund", "icon": "🏦", "desc": "Employer tied"},
            {"key": "PPF", "label": "PPF Account", "icon": "📘", "desc": "Tax free"},
            {"key": "NPS", "label": "NPS Balance", "icon": "📊", "desc": "Retirement tier"},
            {"key": "OTHER", "label": "Other Savings", "icon": "➕", "desc": "Cash & equity"},
        ]
    elif user_data["country"] == "US":
        corpus_config = [
            {"key": "401K", "label": "401(k)", "icon": "🏦", "desc": "Employer match"}, 
            {"key": "IRA", "label": "IRA", "icon": "📘", "desc": "Tax advantaged"}, 
            {"key": "BROKERAGE", "label": "Brokerage", "icon": "📈", "desc": "Taxable investing"}, 
            {"key": "OTHER", "label": "Other", "icon": "➕", "desc": "Cash & equity"}
        ]
    elif user_data["country"] == "UK":
        corpus_config = [
            {"key": "PENSION", "label": "Pension Fund", "icon": "🏦", "desc": "Workplace/SIPP"}, 
            {"key": "ISA", "label": "ISA", "icon": "📘", "desc": "Tax free wrapper"}, 
            {"key": "OTHER", "label": "Other", "icon": "➕", "desc": "Cash & equity"}
        ]

    def render_corpus_grid(corpus_config: list):
        user_data.setdefault("initial_corpus", {})
        country = user_data.get("country", "IN")
        user_data["initial_corpus"].setdefault(country, {})
        country_corpus = user_data["initial_corpus"][country]
        total = 0

        cols = st.columns(2)

        for i, item in enumerate(corpus_config):
            key = item["key"]
            value_key = f"corpus_{country}_{key}_value"
            
            stored_value = float(country_corpus.get(key, 0.0))
            col = cols[i % 2]

            with col:
                with st.container(border=True):
                    # HTML Layout: Icon + Title side-by-side, Description below
                    st.markdown(f"""
                    <div style='margin-bottom: 8px;'>
                        <div style='display: flex; align-items: center; gap: 6px; margin-bottom: 2px;'>
                            <span style='font-size: 20px;'>{item['icon']}</span>
                            <span style='font-weight: 700; font-size: 14px; color: #111827;'>{item['label']}</span>
                        </div>
                        <div style='font-size: 11px; color: #6b7280; line-height: 1.2;'>{item.get('desc', 'Current balance')}</div>
                    </div>
                    """, unsafe_allow_html=True)

                    # Hidden-label number input
                    value = st.number_input(
                        f"Amount ({currency})",
                        min_value=0.0,
                        value=stored_value,
                        step=10000.0,
                        disabled=is_guest or not is_premium,
                        key=value_key,
                        label_visibility="collapsed"
                    )
                    
                    if not is_guest: 
                        country_corpus[key] = value
                    
                    total += value

        return total

    total = render_corpus_grid(corpus_config)

    # Big, bold summary at the bottom
    st.markdown(f"""
    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 15px; border-left: 5px solid #4f46e5; margin-top: 15px;">
        <p style="margin:0; font-size: 14px; color: #6c757d;">Total Starting Wealth</p>
        <h2 style="margin:0; color: #111827;">{currency}{total:,.0f}</h2>
    </div>
    """, unsafe_allow_html=True)
    
def render_base_data_mobile_old2(config, user_data: dict, user: dict):
    is_guest = user is None
    is_premium = user.get("is_premium", False) if user else False
    COUNTRIES = {"India": "IN", "United States": "US", "United Kingdom": "UK"}
    user_data.setdefault("country", "IN")

    def Reset_Active_Scenario(): 
        st.session_state["_active_scenario_loaded"] = None  

    # 1. Subtle Country Selector
    selected = st.selectbox(
        "🌍 Where do you live?",
        list(COUNTRIES.keys()),
        index=list(COUNTRIES.values()).index(user_data["country"]),
        on_change=Reset_Active_Scenario,
        disabled=is_guest,
    )
    user_data["country"] = COUNTRIES[selected]
    hydrate_initial_corpus_defaults(user_data, user_data["country"])
    currency = get_currency(user_data)

    st.markdown("---")
    st.markdown("### 👤 Let's get to know you")

    # 2. Conversational Sliders (Tactile Mobile Input)
    with st.container(border=True):
        user_data.setdefault("GLAge", {"input": 35})
        user_data.setdefault("GLProjectionYears", {"input": 25})

        age = st.slider(
            "How old are you today?",
            min_value=18, max_value=80,
            value=int(user_data["GLAge"]["input"]),
            disabled=is_guest or not is_premium,
        )
        if not is_guest: user_data["GLAge"]["input"] = age

        max_years = 60 if is_premium else 2
        safe_years = min(int(user_data["GLProjectionYears"]["input"]), max_years)
        
        years = st.slider(
            "How many years into the future should we look?",
            min_value=1, max_value=max_years,
            value=safe_years,
            disabled=is_guest or not is_premium,
            help="Free users are limited to 2 years."
        )
        if not is_guest: user_data["GLProjectionYears"]["input"] = years

    # 3. Starting Corpus (Clean Toggle Cards)
    st.markdown("### 💰 Your Starting Line")
    st.caption("Tap to include savings you already have.")

    def render_corpus_cards(corpus_config: list):
        user_data.setdefault("initial_corpus", {})
        country = user_data.get("country", "IN")
        user_data["initial_corpus"].setdefault(country, {})
        country_corpus = user_data["initial_corpus"][country]
        total = 0

        for item in corpus_config:
            key = item["key"]
            with st.container(border=True):
                include_key = f"corpus_{country}_{key}_include"
                value_key = f"corpus_{country}_{key}_value"

                if include_key not in st.session_state:
                    st.session_state[include_key] = country_corpus.get(key, 0) > 0

                # Sleek Toggle
                include = st.toggle(f"{item['icon']} **{item['label']}**", key=include_key, disabled=is_guest or not is_premium)

                if include:
                    current_value = float(country_corpus.get(key, 0))
                    value = st.number_input(
                        f"Current Balance ({currency})",
                        min_value=0.0,
                        value=current_value if current_value > 0 else 50000.0,
                        step=10000.0,
                        disabled=is_guest or not is_premium,
                        key=value_key,
                        label_visibility="collapsed"
                    )
                    if not is_guest: country_corpus[key] = value
                    total += value
                else:
                    if not is_guest: country_corpus[key] = 0.0
        return total

    if user_data["country"] == "IN":
        corpus_config = [
            {"key": "PF", "label": "Provident Fund", "icon": "🏦"},
            {"key": "PPF", "label": "Public Provident Fund", "icon": "📘"},
            {"key": "NPS", "label": "NPS Balance", "icon": "📊"},
            {"key": "OTHER", "label": "Other Savings", "icon": "➕"},
        ]
    # (Keep your existing US/UK config lists here)
    elif user_data["country"] == "US":
        corpus_config = [{"key": "401K", "label": "401(k)", "icon": "🏦"}, {"key": "IRA", "label": "IRA", "icon": "📘"}, {"key": "BROKERAGE", "label": "Brokerage", "icon": "📈"}, {"key": "OTHER", "label": "Other", "icon": "➕"}]
    elif user_data["country"] == "UK":
        corpus_config = [{"key": "PENSION", "label": "Pension Fund", "icon": "🏦"}, {"key": "ISA", "label": "ISA", "icon": "📘"}, {"key": "OTHER", "label": "Other", "icon": "➕"}]

    total = render_corpus_cards(corpus_config)

    # Big, bold summary at the bottom
    st.markdown(f"""
    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 15px; border-left: 5px solid #4f46e5; margin-top: 20px;">
        <p style="margin:0; font-size: 14px; color: #6c757d;">Total Starting Wealth</p>
        <h2 style="margin:0; color: #111827;">{currency}{total:,.0f}</h2>
    </div>
    """, unsafe_allow_html=True)
    
def render_base_data_mobile_old(config, user_data: dict, user: dict):
    is_guest = user is None
    is_premium = user.get("is_premium", False) if user else False

    COUNTRIES = {
        "India": "IN",
        "United States": "US",
        "United Kingdom": "UK",
    }

    user_data.setdefault("country", "IN")

    def Reset_Active_Scenario(): 
        st.session_state["_active_scenario_loaded"] = None  

    # 1. Country Selection (Standalone)
    selected = st.selectbox(
        "🌍 Country of Residence",
        list(COUNTRIES.keys()),
        index=list(COUNTRIES.values()).index(user_data["country"]),
        on_change=Reset_Active_Scenario,
        disabled=is_guest,
    )
    user_data["country"] = COUNTRIES[selected]
    hydrate_initial_corpus_defaults(user_data, user_data["country"])
    currency = get_currency(user_data)

    st.header("👤 Your Profile")
    st.caption("These details remain constant across all scenarios.")

    # 2. Demographics (Stacked in a single mobile-friendly card)
    with st.container(border=True):
        user_data.setdefault("GLAge", {"input": 35})
        user_data.setdefault("GLGender", {"input": "Male"})
        user_data.setdefault("GLProjectionYears", {"input": 25})

        age = st.number_input(
            "Current Age",
            min_value=18, max_value=100,
            value=int(user_data["GLAge"]["input"]),
            disabled=is_guest or not is_premium,
        )
        if not is_guest: user_data["GLAge"]["input"] = age

        gender = st.selectbox(
            "Gender", ["Male", "Female"],
            index=0 if user_data["GLGender"]["input"] == "Male" else 1,
            disabled=is_guest or not is_premium,
        )
        if not is_guest: user_data["GLGender"]["input"] = gender

        max_years = 60 if is_premium else 2
        safe_years = min(int(user_data["GLProjectionYears"]["input"]), max_years)
        
        years = st.number_input(
            "Planning Duration (Years)",
            min_value=1, max_value=max_years,
            value=safe_years,
            disabled=is_guest or not is_premium,
        )
        if not is_guest: user_data["GLProjectionYears"]["input"] = years
        
        if not is_guest and not is_premium:
            st.caption("🔒 Free users are limited to 2 years. Upgrade to extend.")

    # 3. Life Stage Context
    age_val = user_data["GLAge"]["input"]
    stage = get_life_stage(age_val)
    
    st.header("💰 Starting Savings")
    render_stage_context(stage)

    def render_corpus_cards(corpus_config: list):
        user_data.setdefault("initial_corpus", {})
        country = user_data.get("country", "IN")
        user_data["initial_corpus"].setdefault(country, {})
        country_corpus = user_data["initial_corpus"][country]

        total = 0

        # No more columns! Stacked cards with Conditional Inputs
        for item in corpus_config:
            key = item["key"]
            with st.container(border=True):
                # Put the label and checkbox on the same visual block
                include_key = f"corpus_{country}_{key}_include"
                value_key = f"corpus_{country}_{key}_value"

                if include_key not in st.session_state:
                    st.session_state[include_key] = country_corpus.get(key, 0) > 0

                include = st.toggle(
                    f"{item['icon']} **{item['label']}**", 
                    key=include_key, 
                    disabled=is_guest or not is_premium
                )

                # ONLY render the number input if the toggle is ON (Saves massive screen space)
                current_value = float(country_corpus.get(key, 0))
                if include:
                    value = st.number_input(
                        f"Amount ({currency})",
                        min_value=0.0,
                        value=current_value if current_value > 0 else 10000.0, # Suggest a starter value
                        disabled=is_guest or not is_premium,
                        key=value_key,
                        label_visibility="collapsed" # Hide redundant label
                    )
                    if not is_guest:
                        country_corpus[key] = value
                    total += value
                else:
                    if not is_guest:
                        country_corpus[key] = 0.0

        return total

    # Country-specific config remains the same
    if user_data["country"] == "IN":
        corpus_config = [
            {"key": "PF", "label": "Provident Fund", "icon": "🏦"},
            {"key": "PPF", "label": "Public Provident Fund", "icon": "📘"},
            {"key": "NPS", "label": "National Pension Scheme", "icon": "📊"},
            {"key": "SUPER", "label": "Superannuation", "icon": "🧾"},
            {"key": "OTHER", "label": "Other Investments", "icon": "➕"},
        ]
    elif user_data["country"] == "US":
        corpus_config = [
            {"key": "401K", "label": "401(k)", "icon": "🏦"},
            {"key": "IRA", "label": "IRA", "icon": "📘"},
            {"key": "BROKERAGE", "label": "Brokerage", "icon": "📈"},
            {"key": "OTHER", "label": "Other", "icon": "➕"},
        ]
    elif user_data["country"] == "UK":
        corpus_config = [
            {"key": "PENSION", "label": "Pension Fund", "icon": "🏦"},
            {"key": "ISA", "label": "ISA", "icon": "📘"},
            {"key": "OTHER", "label": "Other", "icon": "➕"},
        ]

    total = render_corpus_cards(corpus_config)

    # Highlight the final metric
    with st.container(border=True):
        st.metric("Total Starting Corpus", f"{currency}{total:,.0f}")