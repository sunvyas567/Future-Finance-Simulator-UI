# ui/onetime_expenses.py

import streamlit as st
import pandas as pd
import plotly.express as px
from ui.currency import get_currency


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

    st.subheader("🏷 One-Time Expenses")

    # -------------------------------------------------
    # Ensure country-scoped storage
    # -------------------------------------------------
    user_data.setdefault("onetime_expenses", {})
    user_data["onetime_expenses"].setdefault(country, {})
    expenses = user_data["onetime_expenses"][country]

    #print("One-time expenses UI: - 1", expenses)

    # -------------------------------------------------
    # Input fields only
    # -------------------------------------------------
    input_fields = [
        f for f in config
        if "Field Default Value" in f and "Field Description" in f
    ]

    for field in input_fields:
        key = field["Field Name"]
        label = field["Field Description"]
        default = field.get("Field Default Value", 0)

        value = expenses.get(key, {}).get("input", default)

        value = st.number_input(
            f"{FIELD_ICONS.get(key, '💸')} {label} ({currency})",
            min_value=0.0,
            value=float(value),
            step=1000.0,
            disabled=is_guest or not is_premium,
            key=f"onetime_{country}_{key}",
        )

        expenses[key] = {"input": value}

    
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
        st.dataframe(df, use_container_width=True)

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

    for field in input_fields:
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
        st.plotly_chart(fig, use_container_width=True)
