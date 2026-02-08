import streamlit as st

# -------------------------------------------------
# Country-based expense templates
# -------------------------------------------------
EXPENSE_TEMPLATES = {
    "IN": {
        "Housing": 0.30,
        "Food": 0.25,
        "Transport": 0.10,
        "Healthcare": 0.10,
        "Education / Family": 0.10,
        "Discretionary": 0.15,
    },
    "US": {
        "Housing": 0.35,
        "Healthcare": 0.20,
        "Transport": 0.15,
        "Insurance": 0.10,
        "Discretionary": 0.20,
    },
    "UK": {
        "Housing": 0.30,
        "Council Tax": 0.10,
        "Utilities": 0.10,
        "Transport": 0.15,
        "Healthcare": 0.05,
        "Discretionary": 0.30,
    },
}


def render_expense_auto_distribution(
    user_data: dict,
    expense_bucket: str = "recurring"
):
    """
    expense_bucket:
        - "recurring"  → GLRecurringExpenses
        - "optional"   → Optional recurring expenses
    """

    st.subheader("⚡ Smart Expense Setup (Auto-Distribution)")

    country = user_data.get("country", "IN")
    template = EXPENSE_TEMPLATES.get(country, EXPENSE_TEMPLATES["IN"])

    st.caption(
        f"Using {country} household expense structure. "
        "You can modify values anytime."
    )

    # -------------------------------------------------
    # Total monthly expense input
    # -------------------------------------------------
    total_monthly = st.number_input(
        "Total Monthly Household Expense",
        min_value=0.0,
        value=0.0,
        step=1000.0
    )

    if total_monthly <= 0:
        st.info("Enter total monthly expense to auto-distribute.")
        return

    # -------------------------------------------------
    # Auto-distribute button
    # -------------------------------------------------
    if st.button("🔁 Auto-distribute by Country"):
        expenses = {}

        for label, pct in template.items():
            expenses[label] = round(total_monthly * pct, 2)

        # -------------------------------------------------
        # Persist into user_data (non-destructive)
        # -------------------------------------------------
        if "RecurringExpenses" not in user_data:
            user_data["RecurringExpenses"] = {}

        for label, value in expenses.items():
            if label not in user_data["RecurringExpenses"]:
                user_data["RecurringExpenses"][label] = {
                    "input": value
                }

        st.success("Expenses auto-distributed. You can fine-tune below.")

    st.markdown("---")

    # -------------------------------------------------
    # Editable breakdown
    # -------------------------------------------------
    st.subheader("Monthly Expense Breakdown")

    if "RecurringExpenses" not in user_data:
        st.info("No expenses yet.")
        return

    total = 0.0

    for label, entry in user_data["RecurringExpenses"].items():
        val = st.number_input(
            label,
            value=float(entry.get("input", 0)),
            min_value=0.0,
            step=500.0
        )
        user_data["RecurringExpenses"][label]["input"] = val
        total += val

    st.markdown("---")
    st.metric("Total Monthly Expenses", f"{total:,.0f}")
