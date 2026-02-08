import streamlit as st
import pandas as pd

from ui.onetime_expenses import render_onetime_expenses
from ui.recurring_expenses import render_recurring_expenses

# -------------------------------------------------
# Recurring Expenses (COUNTRY-SCOPED)
# -------------------------------------------------
def compute_yearly_recurring_expenses_UI(user_data: dict, inflation: float, year: int):
    country = user_data.get("country")
    expenses = user_data.get("recurring_expenses", {}).get(country, {})

    #expenses = user_data.get("recurring_expenses", {})

    must_monthly = 0.0
    optional_monthly = 0.0

    for k, v in expenses.items():
        monthly = v.get("monthly", 0)
        if k.endswith("Opt"):
            optional_monthly += monthly
        else:
            must_monthly += monthly

    factor = (1 + inflation) ** (year - 1)

    return (
        round(must_monthly * 12 * factor, 2),
        round(optional_monthly * 12 * factor, 2),
    )


# -------------------------------------------------
# One-time expenses (COUNTRY-SCOPED)
# -------------------------------------------------
def compute_grand_total_onetime_UI(user_data: dict) -> float:
    country = user_data.get("country")
    expenses = user_data.get("onetime_expenses", {}).get(country, {})
    return round(sum(v.get("input", 0) for v in expenses.values()), 2)


def render_expenses(config, user_data, user):
    st.header("💸 Expenses")

    # Ensure containers exist
    user_data.setdefault("onetime_expenses", {})
    user_data.setdefault("recurring_expenses", {})

    # -------------------------------
    # One-Time Expenses Section
    # -------------------------------
    with st.expander("🏷 One-Time Expenses", expanded=True):
        render_onetime_expenses(
            config=config["onetime_expenses"],
            user_data=user_data,
            user=user
        )

    st.divider()

    # -------------------------------
    # Recurring Expenses Section
    # -------------------------------
    #print("user data passed to recurring expenses: KKKK", user_data)
    with st.expander("🔁 Recurring Expenses", expanded=True):
        render_recurring_expenses(
            config=config["recurring_expenses"],
            user_data=user_data,
            user=user
        )

    st.divider()

    # -------------------------------
    # Expense Snapshot (UI-only)
    # -------------------------------
    # -------------------------------
    # Expense Snapshot (COUNTRY SAFE)
    # -------------------------------

    # Build valid field sets from config
    #valid_onetime_fields = {
    #    f["Field Name"]
    #    for f in config["onetime_expenses"]
    #    if isinstance(f, dict) and "Field Name" in f and "Field Default Value" in f
    #}

    #valid_recurring_fields = {
    #    f["Field Name"]
    #    for f in config["recurring_expenses"]
    #    if isinstance(f, dict) and "Field Name" in f and "Field Default Value" in f
    #}
    #print("user data recurring expenses: before VALID print", user_data["recurring_expenses"])
    # Country-safe totals
    #annual_recurring = sum(
    #    user_data["recurring_expenses"].get(k, {}).get("monthly", 0) * 12
    #    for k in valid_recurring_fields
    #)

    #print("user data one time expenses: before VALID print", user_data["onetime_expenses"])
    #one_time_total = sum(
    #    user_data["onetime_expenses"].get(k, {}).get("input", 0)
    #    for k in valid_onetime_fields
    #)
    #country = user_data.get("country", "IN")

    #one_time_total = sum(
    #    user_data["onetime_expenses"]
    ##        .get(country, {})
    #        .get(k, {})
    #        .get("input", 0)
    #    for k in valid_onetime_fields
    #)

    #country = user_data.get("country", "IN")

    #annual_recurring = sum(
    #        user_data["recurring_expenses"]
    #            .get(country, {})
    #            .get(k, {})
    ##            .get("monthly", 0) * 12
    #        for k in valid_recurring_fields
    #    )

    #print("VALID one-time fields:", valid_onetime_fields)
    #print("VALID recurring fields:", valid_recurring_fields)
    one_tome_total = compute_grand_total_onetime_UI(user_data)
    annual_recurring_must, annual_recurring_optional = compute_yearly_recurring_expenses_UI(user_data, inflation=0.0, year=1)
    c1, c2, c3 = st.columns(3)
    c1.metric("Annual Recurring Expenses - Must", f"{annual_recurring_must:,.0f}")
    c2.metric("Annual Recurring Expenses - Optional", f"{annual_recurring_optional:,.0f}")
    c3.metric("One-Time Expenses", f"{one_tome_total:,.0f}")
    #    v.get("monthly", 0) * 12
    #    for v in user_data["recurring_expenses"].values()
    #)

    #one_time_total = sum(
    #    v.get("input", 0)
    #    for v in user_data["onetime_expenses"].values()
    #)

    #print("One time values:", user_data["onetime_expenses"])
    #print("recuriing values:", user_data["recurring_expenses"])


    #c1, c2 = st.columns(2)
    #c1.metric("Annual Recurring Expenses", f"₹{annual_recurring:,.0f}")
    #c2.metric("One-Time Expenses", f"₹{one_time_total:,.0f}")

    # -------------------------------
    # Simple Visual
    # -------------------------------
    #df = pd.DataFrame({
    #    "Category": ["Recurring (Annual)", "One-Time"],
    #    "Amount": [annual_recurring, one_time_total]
    #})

    #st.bar_chart(df.set_index("Category"))
