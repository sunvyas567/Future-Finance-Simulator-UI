import streamlit as st
import pandas as pd
import plotly.express as px

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
    st.header("💸 Your Living Expenses")

    # Ensure containers exist
    user_data.setdefault("onetime_expenses", {})
    user_data.setdefault("recurring_expenses", {})

    is_mobile = st.session_state.get("is_mobile", False)

    # -------------------------------
    # One-Time Expenses Section
    # -------------------------------
    #with st.expander("🏷 Big One-Time Costs", expanded=True):
    with st.expander("I🏷 Big One-Time Costs", expanded=not is_mobile):

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
    #with st.expander("🔁 Monthly Living Costs", expanded=True):
    with st.expander("🔁 Monthly Living Costs", expanded=not is_mobile):

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
    c1.metric("Yearly Living Costs - Must", f"{annual_recurring_must:,.0f}")
    c2.metric("Yearly Living Coss - Optional", f"{annual_recurring_optional:,.0f}")
    c3.metric("Total One-Time Costs", f"{one_tome_total:,.0f}")
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
    # =========================================================
    # SECTION — Expense Growth Over Time
    # =========================================================
    st.subheader("📈 How Your Expenses Grow Over Time")

    try:
        from services.api_client import calculate_projections
        from ui.investment_plan import ensure_scenarios

        # 🔥 Ensure scenarios exist before projection call
        
        plan = user_data.setdefault("investment_plan", {})
        #from ui.investment_plan import ensure_scenarios

        #plan = user_data.setdefault("investment_plan", {})
        if plan.get("active_scenario") not in plan["scenarios"]:
            plan["active_scenario"] = "Base"

        # 🔥 ALWAYS ensure scenarios before running engine
        ensure_scenarios(plan, user_data.get("country"))

        #scenarios = plan.get("scenarios", {})
        #active = plan.get("active_scenario", "Base")

        #ensure_scenarios(plan, user_data.get("country"))
        #print("UI scenarios before projection:", plan["scenarios"].keys())


        result = calculate_projections(user_data, user)

        #print("Projection result in expenses.py:", result)  # Debug print
        # Handle new multi-scenario engine


        active_result = result.get("active_result")

        #print("Projection ACTIVE result in expenses.py:", active_result)  # Debug print

        if not active_result:
            st.info("Projection data not available yet.")
            return
        #active_result = result.get("active_result", {})
        projections = active_result.get("projections", [])

        #print("Projection POST ACTIVE result in expenses.py:", projections)  # Debug print

        if projections:
            df_proj = pd.DataFrame(projections)

            expense_cols = [
                "AnnualMustExpenses",
                "AnnualOptionalExpenses",
                "TotalExpenses",
            ]

            available_cols = [c for c in expense_cols if c in df_proj.columns]

            if available_cols:
                fig_expense_growth = px.line(
                    df_proj,
                    x="Year",
                    y=available_cols,
                    markers=True,
                    title="Inflation Impact on Annual Expenses",
                    labels={"value": "Amount", "variable": "Expense Type"},
                )

                fig_expense_growth.update_layout(
                    template="plotly_white",
                    legend_title="Expense Type",
                )
                height = 320 if is_mobile else 500
                fig_expense_growth.update_layout(height=height)
                #st.plotly_chart(fig, use_container_width=True)

                st.plotly_chart(fig_expense_growth, use_container_width=True)

        else:
            st.info("Complete inputs to visualize expense growth.")

    except Exception:
        st.info("Projection data unavailable.")

