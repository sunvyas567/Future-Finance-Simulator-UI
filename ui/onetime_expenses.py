# ui/onetime_expenses.py

import streamlit as st
import pandas as pd
import plotly.express as px
from ui.currency import get_currency

# -------------------------------------------------
# Life stage helper
# -------------------------------------------------
def _get_life_stage(user_data):
    age = user_data.get("GLAge", {}).get("input", 35)

    if age < 35:
        return "early"
    elif age < 55:
        return "mid"
    else:
        return "retirement"
def _apply_stage_rules(stage, key, label):
    rules = STAGE_EXPENSE_RULES.get(stage, {})

    if key in rules.get("hide", []):
        return None  # hidden

    label = rules.get("rename", {}).get(key, label)
    return label

# -------------------------------------------------
# Stage visibility rules (UI only — data preserved)
# -------------------------------------------------
STAGE_EXPENSE_RULES = {

    "early": {
        # hide things that don’t make sense yet
        "hide": [
            "OTMarriage"
        ],
        # rename if needed
        "rename": {
            "OTHouseRenovation": "Future Education Planning"
        }
    },

    "mid": {
        "hide": [],
        "rename": {}
    },

    "retirement": {
        "hide": [],
        "rename": {}
    }
}

FIELD_ICONS = {
    "LocalKidsEducation": "🎓",
    "LocalHouseRenovation": "🏡",
    "LocalVehicleRenewal": "🚗",
    "LocalJewelry": "💎",
    "LocalTravelForeign": "✈️",
    "LocalOthers": "🛍️",
    "LocalMarriages": "💍",
    "LocalProperty": "🏘️",
}


# -------------------------------------------------
# Formula evaluator (UI-only)
# -------------------------------------------------
def _eval_formula(expr: str, data: dict):
    """
    Evaluates formulas like:
    ={A}+{B}
    Uses ONLY current country data
    """
    import re, math

    expr = expr[1:]

    def repl(m):
        key = m.group(1)
        return str(float(data.get(key, {}).get("input", 0)))

    expr = re.sub(r"\{([^}]+)\}", repl, expr)

    try:
        return eval(expr, {"__builtins__": {"min": min, "max": max, "math": math}})
    except Exception:
        return 0


# -------------------------------------------------
# MAIN UI
# -------------------------------------------------
def render_onetime_expenses(config, user_data, user):
    """
    ✅ Country-scoped one-time expenses
    ✅ Raw inputs only stored
    ✅ Totals derived (never stored)
    """
    is_guest = user.get("is_guest", False)
    is_premium = user.get("is_premium", False) if user else False
    currency = get_currency(user_data)
    country = user_data.get("country", "IN")

    st.subheader("🏷 Big One-Time Costs")

    # -------------------------------------------------
    # Life stage context
    # -------------------------------------------------
    stage = _get_life_stage(user_data)

    if stage == "early":
        st.info(
            "🌱 Plan major life milestones like education, vehicle purchase, or travel."
        )
        st.caption("💡 Common: higher education, vehicle purchase, travel, career upgrade")

    elif stage == "mid":
        st.info(
            "👨‍👩‍👧 Plan family goals like children education, home purchase, or life events."
        )
        st.caption("💡 Common: children education, home renovation, marriage")

    else:
        st.success(
            "🏖 Plan retirement lifestyle goals like travel, healthcare, or legacy gifting."
        )
        st.caption("💡 Common: medical reserve, bucket-list travel, wealth transfer")

    # -------------------------------------------------
    # Ensure country-scoped storage
    # -------------------------------------------------
    user_data.setdefault("onetime_expenses", {})
    user_data["onetime_expenses"].setdefault(country, {})
    expenses = user_data["onetime_expenses"][country]

    #print("One-time expenses UI: - 1", expenses)

    STAGE_PRIORITY = {
        "early": ["Education", "Vehicle", "Travel"],
        "mid": ["Children", "House", "Marriage", "Property"],
        "retirement": ["Medical", "Healthcare", "Travel"]
    }
    priority_keywords = STAGE_PRIORITY.get(stage, [])

    # -------------------------------------------------
    # Input fields (REDESIGNED CARD UI)
    # -------------------------------------------------
    input_fields = [
        f for f in config
        if "Field Default Value" in f and "Field Description" in f
    ]

    #cols = st.columns(2)
    visible_fields = []

    for field in input_fields:
        key = field["Field Name"]
        label = field["Field Description"]

        stage_label = _apply_stage_rules(stage, key, label)
        if stage_label is None:
            expenses[key] = {"input": 0.0}
            continue

        field["__stage_label"] = stage_label
        visible_fields.append(field)

    cols = st.columns(2)
    #print("Visible fields for one-time expenses:", [f["Field Name"] for f in visible_fields])
    for idx, field in enumerate(visible_fields):
    #for idx, field in enumerate(input_fields):
        col = cols[idx % 2]

        key = field["Field Name"]
        #label = field["__stage_label"]
        #label = field["Field Description"]
        label = field.get("__stage_label", field["Field Description"])
        default = float(field.get("Field Default Value", 0))
        icon = FIELD_ICONS.get(key, "💸")

        stored_value = float(expenses.get(key, {}).get("input", default))

        include_key = f"onetime_{country}_{key}_include"
        value_key = f"onetime_{country}_{key}_value"

        # Default include = True if value > 0
        if include_key not in st.session_state:
            st.session_state[include_key] = stored_value > 0

        with col:
            with st.container(border=True):
                base_label = field["Field Description"]

                if any(k.lower() in base_label.lower() for k in priority_keywords):
                #if any(k.lower() in label.lower() for k in priority_keywords):
                    st.markdown(f"### ⭐ {icon} {label}")
                else:
                    st.markdown(f"### {icon} {label}")

                #st.markdown(f"### {icon} {label}")

                include = st.checkbox(
                    "Include",
                    key=include_key,
                    disabled=is_guest or not is_premium
                )

                value = st.number_input(
                    f"Amount ({currency})",
                    min_value=0.0,
                    value=stored_value,
                    step=1000.0,
                    disabled=not include or is_guest or not is_premium,
                    key=value_key
                )

                if not is_guest:
                    expenses[key] = {
                        "input": value if include else 0.0
                    }

        #expenses[key] = {"input": value} #commented for above country level scoping

    
    #print("One-time expenses UI: - 2", expenses)
    # -------------------------------------------------
    # Derived (formula) fields — UI ONLY
    # -------------------------------------------------
    formula_fields = [
        f for f in config
        if isinstance(f.get("Field Input"), str)
        and f["Field Input"].startswith("=")
    ]

    derived_rows = []
    for field in formula_fields:
        key = field["Field Name"]
        label = field.get("Field Description")
        if not label:
            continue
        #label = field["Field Description"]
        value = _eval_formula(field["Field Input"], expenses)

        derived_rows.append({
            "Category": label,
            "Amount": value,
        })

    if derived_rows:
        st.divider()
        st.markdown("### 📊 Derived One-Time Costs")
        df = pd.DataFrame(derived_rows)
        st.dataframe(df, width='stretch')

    # -------------------------------------------------
    # Total (derived, single source of truth)
    # -------------------------------------------------
    total = sum(v.get("input", 0) for v in expenses.values())

    st.divider()
    st.metric(
        "Total One-Time Expenses",
        f"{currency}{total:,.0f}",
    )

    # -------------------------------------------------
    # Chart (country-safe)
    # -------------------------------------------------
    #rows = [
    #    {
    #        "Category": field["Field Description"],
    #        "Amount": expenses.get(field["Field Name"], {}).get("input", 0),
    #    }
    #    for field in input_fields
    #    if expenses.get(field["Field Name"], {}).get("input", 0) > 0
    #]

    rows = []

    for field in visible_fields:
        name = field.get("Field Name")
        label = field.get("Field Description")

        if not name or not label:
            continue

        value = expenses.get(name, {}).get("input", 0)
        if value > 0:
            rows.append({
                "Category": label,
                "Amount": value,
            })


    if rows:
        df = pd.DataFrame(rows)
        fig = px.bar(
            df,
            x="Category",
            y="Amount",
            text_auto=".2s",
            title=f"One-Time Expense Breakdown ({currency})",
        )
        fig.update_traces(textposition="outside")
        is_mobile = st.session_state.get("is_mobile", False)
        height = 320 if is_mobile else 500
        fig.update_layout(height=height)
        st.plotly_chart(fig, use_container_width=True)

# -------------------------------------------------
# MAIN UI
# -------------------------------------------------
# =========================================================
# MAIN UI (Monarch-Style Mobile)
# =========================================================
def render_onetime_expenses_mobile(config, user_data, user):
    is_guest = user.get("is_guest", False)
    is_premium = user.get("is_premium", False) if user else False
    currency = get_currency(user_data)
    country = user_data.get("country", "IN")

    st.markdown("### 🎯 Big Life Milestones")
    st.caption("Tap the goals you are planning for in the future.")

    stage = _get_life_stage(user_data)
    user_data.setdefault("onetime_expenses", {})
    user_data["onetime_expenses"].setdefault(country, {})
    expenses = user_data["onetime_expenses"][country]

    input_fields = [f for f in config if "Field Default Value" in f and "Field Description" in f]
    visible_fields = []

    for field in input_fields:
        key = field["Field Name"]
        label = field["Field Description"]
        stage_label = _apply_stage_rules(stage, key, label)
        if stage_label is None:
            expenses[key] = {"input": 0.0}
            continue
        field["__stage_label"] = stage_label
        visible_fields.append(field)

    # Conversational prompts to make inputs feel human
    FRIENDLY_PROMPTS = {
        "Education": "Planning for higher education?",
        "Vehicle": "Buying or upgrading a car?",
        "House": "Renovating or buying a home?",
        "Marriage": "Funding a wedding?",
        "Travel": "Taking a dream vacation?",
        "Medical": "Setting aside a medical reserve?",
        "Property": "Investing in real estate?"
    }

    # -------------------------------------------------
    # Input fields (Conversational Cards)
    # -------------------------------------------------
    for field in visible_fields:
        key = field["Field Name"]
        label = field.get("__stage_label", field["Field Description"])
        default = float(field.get("Field Default Value", 0))
        icon = FIELD_ICONS.get(key, "💸")
        stored_value = float(expenses.get(key, {}).get("input", default))

        include_key = f"onetime_{country}_{key}_include"
        value_key = f"onetime_{country}_{key}_value"

        if include_key not in st.session_state:
            st.session_state[include_key] = stored_value > 0

        # Try to find a friendly prompt, fallback to standard label
        prompt_text = label
        for keyword, friendly in FRIENDLY_PROMPTS.items():
            if keyword.lower() in label.lower():
                prompt_text = friendly
                break

        with st.container(border=True):
            include = st.toggle(
                f"{icon} **{prompt_text}**",
                key=include_key,
                disabled=is_guest or not is_premium
            )

            if include:
                value = st.number_input(
                    f"Estimated Cost ({currency})",
                    min_value=0.0,
                    value=stored_value if stored_value > 0 else 50000.0,
                    step=10000.0,
                    disabled=is_guest or not is_premium,
                    key=value_key,
                    label_visibility="collapsed"
                )
                if not is_guest:
                    expenses[key] = {"input": value}
            else:
                if not is_guest:
                    expenses[key] = {"input": 0.0}

    # -------------------------------------------------
    # Summary & Total (App Style)
    # -------------------------------------------------
    total = sum(v.get("input", 0) for v in expenses.values())

    st.markdown(f"""
    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 15px; border-left: 5px solid #ec4899; margin-top: 20px;">
        <p style="margin:0; font-size: 14px; color: #6c757d;">Total Planned Milestones</p>
        <h2 style="margin:0; color: #111827;">{currency}{total:,.0f}</h2>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    
def render_onetime_expenses_mobile_old(config, user_data, user):
    is_guest = user.get("is_guest", False)
    is_premium = user.get("is_premium", False) if user else False
    currency = get_currency(user_data)
    country = user_data.get("country", "IN")

    st.subheader("🏷 Big One-Time Costs")

    # -------------------------------------------------
    # Life stage context
    # -------------------------------------------------
    stage = _get_life_stage(user_data)

    if stage == "early":
        st.info("🌱 Plan major life milestones like education, vehicle purchase, or travel.")
        st.caption("💡 Common: higher education, vehicle purchase, travel, career upgrade")
    elif stage == "mid":
        st.info("👨‍👩‍👧 Plan family goals like children education, home purchase, or life events.")
        st.caption("💡 Common: children education, home renovation, marriage")
    else:
        st.success("🏖 Plan retirement lifestyle goals like travel, healthcare, or legacy gifting.")
        st.caption("💡 Common: medical reserve, bucket-list travel, wealth transfer")

    # Ensure country-scoped storage
    user_data.setdefault("onetime_expenses", {})
    user_data["onetime_expenses"].setdefault(country, {})
    expenses = user_data["onetime_expenses"][country]

    STAGE_PRIORITY = {
        "early": ["Education", "Vehicle", "Travel"],
        "mid": ["Children", "House", "Marriage", "Property"],
        "retirement": ["Medical", "Healthcare", "Travel"]
    }
    priority_keywords = STAGE_PRIORITY.get(stage, [])

    # Filter visible fields based on stage rules
    input_fields = [f for f in config if "Field Default Value" in f and "Field Description" in f]
    visible_fields = []

    for field in input_fields:
        key = field["Field Name"]
        label = field["Field Description"]
        stage_label = _apply_stage_rules(stage, key, label)
        if stage_label is None:
            expenses[key] = {"input": 0.0}
            continue

        field["__stage_label"] = stage_label
        visible_fields.append(field)

    # -------------------------------------------------
    # Input fields (MOBILE OPTIMIZED CARD UI)
    # -------------------------------------------------
    for field in visible_fields:
        key = field["Field Name"]
        label = field.get("__stage_label", field["Field Description"])
        default = float(field.get("Field Default Value", 0))
        icon = FIELD_ICONS.get(key, "💸")
        stored_value = float(expenses.get(key, {}).get("input", default))

        include_key = f"onetime_{country}_{key}_include"
        value_key = f"onetime_{country}_{key}_value"

        if include_key not in st.session_state:
            st.session_state[include_key] = stored_value > 0

        # Full-width stacked card
        with st.container(border=True):
            base_label = field["Field Description"]
            is_priority = any(k.lower() in base_label.lower() for k in priority_keywords)
            
            title_text = f"⭐ {icon} **{label}**" if is_priority else f"{icon} **{label}**"

            # Combine title and checkbox into a clean native toggle
            include = st.toggle(
                title_text,
                key=include_key,
                disabled=is_guest or not is_premium
            )

            # Conditionally render the number input
            if include:
                value = st.number_input(
                    f"Amount ({currency})",
                    min_value=0.0,
                    value=stored_value if stored_value > 0 else 50000.0, # Better starter value
                    step=1000.0,
                    disabled=is_guest or not is_premium,
                    key=value_key,
                    label_visibility="collapsed" # Hides the redundant label
                )
                if not is_guest:
                    expenses[key] = {"input": value}
            else:
                if not is_guest:
                    expenses[key] = {"input": 0.0}

    # -------------------------------------------------
    # Derived (formula) fields — MOBILE CARDS
    # -------------------------------------------------
    formula_fields = [f for f in config if isinstance(f.get("Field Input"), str) and f["Field Input"].startswith("=")]

    derived_rows = []
    for field in formula_fields:
        key = field["Field Name"]
        label = field.get("Field Description")
        if not label:
            continue
        value = _eval_formula(field["Field Input"], expenses)
        derived_rows.append({"Category": label, "Amount": value})

    if derived_rows:
        st.divider()
        st.markdown("### 📊 Derived One-Time Costs")
        
        # Replace dataframe with stacked cards
        for row in derived_rows:
            with st.container(border=True):
                # Very tight columns inside a card just for aligning Text left and Number right
                col1, col2 = st.columns([2, 1]) 
                with col1:
                    st.write(f"**{row['Category']}**")
                with col2:
                    st.write(f"**{currency}{row['Amount']:,.0f}**")

    # -------------------------------------------------
    # Total (derived, single source of truth)
    # -------------------------------------------------
    total = sum(v.get("input", 0) for v in expenses.values())

    st.divider()
    with st.container(border=True):
        st.metric("Total One-Time Expenses", f"{currency}{total:,.0f}")

    # -------------------------------------------------
    # Chart (country-safe)
    # -------------------------------------------------
    rows = []
    for field in visible_fields:
        name = field.get("Field Name")
        label = field.get("Field Description")
        if not name or not label:
            continue
        value = expenses.get(name, {}).get("input", 0)
        if value > 0:
            rows.append({"Category": label, "Amount": value})

    if rows:
        df = pd.DataFrame(rows)
        fig = px.bar(
            df, x="Category", y="Amount", text_auto=".2s",
            title=f"Expense Breakdown ({currency})",
        )
        fig.update_traces(textposition="outside")
        
        # Pull global mobile state for chart height
        is_mobile = st.session_state.get("is_mobile", False)
        fig.update_layout(height=320 if is_mobile else 500, margin=dict(l=0, r=0, t=40, b=0))
        st.plotly_chart(fig, use_container_width=True)