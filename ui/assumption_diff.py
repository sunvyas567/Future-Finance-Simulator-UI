import streamlit as st
import pandas as pd


def build_assumption_diff(config_base_data: list, user_data: dict):
    """
    Compare default assumptions vs user-modified assumptions
    """
    rows = []

    for item in config_base_data:
        key = item["Field Name"]
        label = item["Field Description"]
        default = item.get("Field Default Value")

        # Only numeric defaults
        if not isinstance(default, (int, float)):
            continue

        current = user_data.get(key, {}).get("input", default)

        if current != default:
            delta = current - default
            pct = (delta / default * 100) if default != 0 else None

            rows.append({
                "Assumption": label,
                "Default": default,
                "Current": current,
                "Change": delta,
                "Change %": pct
            })

    return pd.DataFrame(rows)

def render_assumption_diff_panel(base_data_config: list, user_data: dict):
    st.subheader("🧮 Assumption Changes")

    df = build_assumption_diff(
        config_base_data=base_data_config,
        user_data=user_data
    )

    if df.empty:
        st.success("You are using all default assumptions 👍")
        return

    with st.container(border=True):
        st.caption(
            "These assumptions differ from the default values used by the simulator."
        )

        def highlight(row):
            return (
                ["background-color: #e0f7fa"] * len(row)
                if row["Change"] > 0
                else ["background-color: #fdecea"] * len(row)
            )

        styled = (
            df.style
            .apply(highlight, axis=1)
            .format({
                "Default": "{:,.2f}",
                "Current": "{:,.2f}",
                "Change": "{:+,.2f}",
                "Change %": lambda x: f"{x:+.1f}%" if x is not None else "—"
            })
        )

        st.dataframe(styled, use_container_width=True)

def build_assumption_diff_between(
    base_data_config: list,
    left_data: dict,
    right_data: dict
):
    rows = []

    for item in base_data_config:
        key = item["Field Name"]
        label = item["Field Description"]
        default = item.get("Field Default Value")

        left_val = left_data.get(key, {}).get("input", default)
        right_val = right_data.get(key, {}).get("input", default)

        if left_val != right_val:
            delta = right_val - left_val
            pct = (delta / left_val * 100) if left_val not in (0, None) else None

            rows.append({
                "Assumption": label,
                "Baseline": left_val,
                "Scenario": right_val,
                "Change": delta,
                "Change %": pct
            })

    return pd.DataFrame(rows)

def render_assumption_diff_between(
    title: str,
    base_data_config: list,
    left_data: dict,
    right_data: dict
):
    st.subheader(title)

    df = build_assumption_diff_between(
        base_data_config,
        left_data,
        right_data
    )

    if df.empty:
        st.success("No assumption differences detected.")
        return

    with st.container(border=True):
        styled = (
            df.style
            .format({
                "Baseline": "{:,.2f}",
                "Scenario": "{:,.2f}",
                "Change": "{:+,.2f}",
                "Change %": lambda x: f"{x:+.1f}%" if x is not None else "—"
            })
        )

        st.dataframe(styled, use_container_width=True)

