import streamlit as st
from ui.currency import get_currency


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

    # If country changed → reset safely
    if set(user_data["initial_corpus"].keys()) != set(expected.keys()):
        user_data["initial_corpus"] = {}

    # Apply defaults ONLY if missing
    for k, v in expected.items():
        user_data["initial_corpus"].setdefault(k, v)

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

    selected = st.selectbox(
        "🌍 Country of Residence",
        list(COUNTRIES.keys()),
        index=list(COUNTRIES.values()).index(user_data["country"]),
        disabled=is_guest,
    )

    user_data["country"] = COUNTRIES[selected]

    # -----------------------------------------------------
    # Defaults (safe & idempotent)
    # -----------------------------------------------------
    hydrate_initial_corpus_defaults(user_data, user_data["country"])

    currency = get_currency(user_data)

    st.header("📋 Base Information")
    st.caption("These details remain constant across all scenarios.")

    # -----------------------------------------------------
    # Demographics
    # -----------------------------------------------------
    col1, col2 = st.columns(2)

    user_data.setdefault("GLAge", {"input": 35})
    user_data.setdefault("GLGender", {"input": "Male"})
    user_data.setdefault("GLProjectionYears", {"input": 25})

    with col1:
        st.subheader("👤 Personal Details")

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
        st.subheader("🗓 Projection Horizon")

        max_years = 60 if is_premium else 2

        stored_years = int(user_data["GLProjectionYears"]["input"])

        # 🔥 Clamp stored value to allowed range
        safe_years = min(stored_years, max_years)

        years = st.number_input(
            "Projection Years",
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
            st.info("Free users are limited to 2 years.")

    st.divider()

    # -----------------------------------------------------
    # Initial Corpus (ONLY source of truth)
    # -----------------------------------------------------
    st.subheader("💰 Initial Retirement Corpus")
    st.caption("Your current retirement savings")

    def corpus_field_old(key: str, label: str):
        value = user_data["initial_corpus"].get(key, 0.0)

        new_val = st.number_input(
            f"{label} ({currency})",
            min_value=0.0,
            value=float(value),
            disabled=is_guest or not is_premium,
            key=f"corpus_{key}",
        )

        user_data["initial_corpus"][key] = new_val
    def corpus_field(key: str, label: str):
        value = user_data["initial_corpus"].get(key, 0.0)

        new_val = st.number_input(
            f"{label} ({currency})",
            min_value=0.0,
            value=float(value),
            disabled=is_guest or not is_premium,
            key=f"corpus_{key}",
        )

        if not is_guest:
            user_data["initial_corpus"][key] = new_val
        else :
            user_data["initial_corpus"][key] = value  # preserve existing value for guest

    # 🇮🇳 INDIA
    if user_data["country"] == "IN":
        corpus_field("PF", "Provident Fund (PF)")
        corpus_field("PPF", "Public Provident Fund (PPF)")
        corpus_field("NPS", "National Pension Scheme (NPS)")
        corpus_field("SUPER", "Superannuation")
        corpus_field("OTHER", "Other Corpus")

    # 🇺🇸 US
    elif user_data["country"] == "US":
        corpus_field("401K", "401(k)")
        corpus_field("IRA", "IRA")
        corpus_field("BROKERAGE", "Brokerage Account")
        corpus_field("OTHER", "Other Corpus")

    # 🇬🇧 UK
    elif user_data["country"] == "UK":
        corpus_field("PENSION", "Pension Fund")
        corpus_field("ISA", "ISA")
        corpus_field("OTHER", "Other Corpus")

    #print("InitialCorpus UI", user_data["initial_corpus"])
    # -----------------------------------------------------
    # Total (derived only)
    # -----------------------------------------------------
    total = sum(user_data["initial_corpus"].values())

    st.metric(
        "Total Initial Corpus",
        f"{currency}{total:,.0f}"
    )
