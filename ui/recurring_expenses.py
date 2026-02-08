# ui/recurring_expenses.py

import streamlit as st
import pandas as pd
import plotly.express as px

from ui.currency import get_currency
from ui.expense_templates import EXPENSE_TEMPLATES


# =========================================================
# Helpers
# =========================================================

def _is_input_field(field: dict) -> bool:
    """
    Only render true input fields.
    """
    return (
        isinstance(field, dict)
        and field.get("Field Name")
        and field.get("Field Description")
        and "Field Default Value" in field
    )


# =========================================================
# MAIN UI
# =========================================================

def render_recurring_expenses(config, user_data, user):
    """
    Monthly Recurring Expenses (country-safe, defensive)

    Stores:
      user_data["recurring_expenses"][FIELD_NAME]["monthly"]
    """
    is_guest = user is None
    is_premium = user.get("is_premium", False) if user else False
    currency = get_currency(user_data)
    country = user_data.get("country", "IN")

    st.subheader("🔁 Recurring Monthly Expenses")

    # --------------------------------------------------
    # Storage (country-scoped)
    # --------------------------------------------------
     # -------------------------------------------------
    # Ensure country-scoped storage
    # -------------------------------------------------
    user_data.setdefault("recurring_expenses", {})
    user_data["recurring_expenses"].setdefault(country, {})
    expenses = user_data["recurring_expenses"][country]
    #user_data.setdefault("recurring_expenses", {})
    #expenses = user_data["recurring_expenses"]

    # --------------------------------------------------
    # Filter only valid input fields
    # --------------------------------------------------
    input_fields = [f for f in config if _is_input_field(f)]

    # Build field_map ONLY from valid inputs
    field_map = {f["Field Name"]: f for f in input_fields}

    # --------------------------------------------------
    # Country Templates (optional)
    # --------------------------------------------------
    templates = EXPENSE_TEMPLATES.get(country)

    if templates and not is_guest:
        st.markdown("### ⚡ Quick Setup (Templates)")

        lifestyle = st.selectbox(
            "Lifestyle",
            list(templates.keys()),
            key="recurring_template",
        )

        if st.button("Apply Template"):
            for field, value in templates[lifestyle].items():
                if field in field_map:
                    expenses[field] = {"monthly": float(value)}
            st.success("Template applied. Adjust values below.")

        st.caption("Templates are indicative.")

    st.divider()

    # --------------------------------------------------
    # Render fields
    # --------------------------------------------------
    for field in input_fields:
        name = field["Field Name"]
        label = field["Field Description"]
        default = field.get("Field Default Value", 0)

        value = expenses.get(name, {}).get("monthly", default)

        cols = st.columns([2, 1])

        with cols[0]:
            value = st.number_input(
                f"{label} ({currency} / month)",
                min_value=0.0,
                value=float(value),
                step=500.0,
                disabled=is_guest or not is_premium,
                key=f"rec_{country}_{name} ",
            )

        with cols[1]:
            st.metric("Yearly", f"{currency}{value * 12:,.0f}")

        expenses[name] = {"monthly": value}

    # --------------------------------------------------
    # Compute totals (backend truth)
    # --------------------------------------------------
    must_yearly = 0.0
    optional_yearly = 0.0

    for name, data in expenses.items():
        monthly = data.get("monthly", 0)
        annual = monthly * 12

        # Convention: Optional fields end with 'Opt'
        if name.endswith("Opt"):
            optional_yearly += annual
        else:
            must_yearly += annual

    # Store for engine / summary
    user_data["AnnualMustExpenses"] = {"input": round(must_yearly, 2)}
    user_data["AnnualOptionalExpenses"] = {"input": round(optional_yearly, 2)}

    # --------------------------------------------------
    # Snapshot
    # --------------------------------------------------
    st.divider()
    c1, c2 = st.columns(2)

    c1.metric("Annual Mandatory Expenses", f"{currency}{must_yearly:,.0f}")
    c2.metric("Annual Optional Expenses", f"{currency}{optional_yearly:,.0f}")

    # --------------------------------------------------
    # Chart (defensive)
    # --------------------------------------------------
    rows = []

    for name, data in expenses.items():
        monthly = data.get("monthly", 0)
        if monthly <= 0 or name not in field_map:
            continue

        rows.append({
            "Category": field_map[name]["Field Description"],
            "Annual": monthly * 12,
        })

    if rows:
        df = pd.DataFrame(rows)

        fig = px.pie(
            df,
            names="Category",
            values="Annual",
            title=f"Annual Recurring Expense Breakdown ({currency})",
        )

        st.plotly_chart(fig, use_container_width=True)
