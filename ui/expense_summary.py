import streamlit as st
import pandas as pd


# =========================================================
# SAFE DATA HELPERS
# =========================================================

def _to_float(v):
    try:
        return float(v)
    except:
        return 0.0

def _sum_column(data, value_key):
    """
    Safely sum values from different structures.

    Supports:
    - list of dicts
    - dict of dicts
    - ignores invalid rows
    """

    total = 0.0

    # ----------------------------
    # Case 1: dict of dicts
    # ----------------------------
    if isinstance(data, dict):
        for v in data.values():
            if isinstance(v, dict):
                # detect known keys automatically
                val = (
                    v.get(value_key)
                    or v.get("input")
                    or v.get("monthly")
                    or 0
                )
                total += _to_float(val)
        return total

    # ----------------------------
    # Case 2: list of dict rows
    # ----------------------------
    if isinstance(data, list):
        for r in data:
            if isinstance(r, dict):
                total += _to_float(r.get(value_key, 0))
        return total

    # ----------------------------
    # Fallback
    # ----------------------------
    return 0.0

def _sum_column_old(rows, key):
    return sum(_to_float(r.get(key, 0)) for r in rows)


def _group_by_category(rows, amount_key):
    df = pd.DataFrame(rows)
    if "Category" not in df.columns:
        return None

    grouped = (
        df.groupby("Category")[amount_key]
        .sum()
        .reset_index()
        .sort_values(amount_key, ascending=False)
    )
    return grouped


# =========================================================
# MAIN RENDER FUNCTION
# =========================================================

def render_expense_summary(user_data: dict, currency: str = "₹"):
    """
    Shows:
    - One-time expense summary
    - Monthly recurring expense
    - Yearly recurring expense
    - Tables
    - Category totals (if available)
    """

    country = user_data.get("country")

    is_mobile = st.session_state.get("is_mobile", False)

    one_time = user_data.get("onetime_expenses", {}).get(country, {})
    recurring = user_data.get("recurring_expenses", {}).get(country, {})

    total_one_time = _sum_column(one_time, "input")

    total_recurring = 0.0
    if isinstance(recurring, dict):
        for v in recurring.values():
            if isinstance(v, dict):
                total_recurring += _to_float(v.get("monthly", 0)) * 12

    #one_time = user_data.get("onetime_expenses", [])
    #recurring = user_data.get("recurring_expenses", [])

    total_one_time = _sum_column(one_time, "Amount")
    total_monthly = _sum_column(recurring, "Monthly")
    total_yearly = total_monthly * 12

    # =====================================================
    # METRICS
    # =====================================================
    c1, c2, c3 = st.columns(3)

    c1.metric("One-Time Expenses", f"{currency}{total_one_time:,.0f}")
    c2.metric("Monthly Lifestyle Cost", f"{currency}{total_monthly:,.0f}")
    c3.metric("Yearly Lifestyle Cost", f"{currency}{total_yearly:,.0f}")

    # =====================================================
    # ONE TIME TABLE
    # =====================================================
    if one_time:
        #with st.expander("View One-Time Expenses", expanded=False):
        with st.expander("View One-Time Expenses", expanded=not is_mobile):
            df = pd.DataFrame(one_time)
            st.dataframe(df, use_container_width=True)

            grouped = _group_by_category(one_time, "Amount")
            if grouped is not None:
                st.caption("Category totals")
                st.dataframe(grouped, use_container_width=True)

    # =====================================================
    # RECURRING TABLE
    # =====================================================
    if recurring:
        #with st.expander("View Recurring Expenses", expanded=False):
        with st.expander("View Recurring Expenses", expanded=not is_mobile):
            df = pd.DataFrame(recurring)
            st.dataframe(df, use_container_width=True)

            grouped = _group_by_category(recurring, "Monthly")
            if grouped is not None:
                st.caption("Monthly category totals")
                st.dataframe(grouped, use_container_width=True)

    # =====================================================
    # RETURN VALUES (IMPORTANT for summary.py)
    # =====================================================
    return {
        "one_time_total": total_one_time,
        "monthly_total": total_monthly,
        "yearly_total": total_yearly,
    }
