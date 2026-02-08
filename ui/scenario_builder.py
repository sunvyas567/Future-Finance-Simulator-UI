import streamlit as st
import copy
import pandas as pd

from services.api_client import calculate_projections
from ui.charts import plot_income_vs_expenses
from ui.assumption_diff import render_assumption_diff_between, extract_diffs
from ui.scenario_engine import apply_scenario_diff


SCENARIO_ASSUMPTIONS = [
    "GLInflationRate",
    "GLSWPGrowthRate",
    "GLNormalFDRate",
    "GLSrCitizenFDRate",
    "GLSCSSRate",
    "GLPOMISRate"
]

def get_scenario_fields(base_config):
    return [
        f["Field Name"]
        for f in base_config
        if f.get("scenario") is True
    ]

def render_scenario_builder(config, user_data, user):
    st.header("🧪 Scenario Builder")
    st.caption("Create and compare what-if scenarios using assumption changes")

    if not user["is_premium"]:
        st.info("Upgrade to Premium to create scenarios.")
        return

    # -----------------------------------
    # Scenario storage
    # -----------------------------------
    if "scenarios" not in user_data:
        user_data["scenarios"] = {}

    # -----------------------------------
    # Baseline snapshot
    # -----------------------------------
    baseline_data = copy.deepcopy(user_data)
    scenario_fields = get_scenario_fields(config["base_data"])

    print("DEBUG scnario fields", scenario_fields)
    # -----------------------------------
    # Scenario creation UI
    # -----------------------------------
    with st.expander("➕ Create New Scenario", expanded=True):
        scenario_name = st.text_input("Scenario Name", "High Inflation Scenario")

        scenario_diff = {}

        cols = st.columns(2)
        for i, key in enumerate(scenario_fields):
            default = user_data.get(key, {}).get("input")
            if default is None:
                continue

            with cols[i % 2]:
                new_val = st.number_input(
                    f"{key}",
                    value=float(default),
                    key=f"sc_{key}"
                )
                if new_val != default:
                    scenario_diff[key] = new_val

        if not scenario_diff:
            st.warning("No changes from baseline yet.")

        if st.button("💾 Save Scenario"):
            if not scenario_name:
                st.warning("Please provide a scenario name.")
            elif not scenario_diff:
                st.warning("No changes detected from baseline.")
            else:
                user_data["scenarios"][scenario_name] = scenario_diff
                st.session_state.user_data["scenarios"] = user_data["scenarios"]  # 🔥 force persistence
                st.success(f"Scenario '{scenario_name}' saved")
                st.rerun()

    # -----------------------------------
    # Existing Scenarios
    # -----------------------------------
    st.subheader("📁 Saved Scenarios")

    if not user_data["scenarios"]:
        st.info("No scenarios saved yet.")
        return

    selected = st.selectbox(
        "Select a scenario",
        list(user_data["scenarios"].keys())
    )

    scenario_diff = user_data["scenarios"][selected]
    scenario_data = apply_scenario_diff(baseline_data, scenario_diff)

    # -----------------------------------
    # Run comparison
    # -----------------------------------
    if st.button("▶ Run Selected Scenario"):
        with st.spinner("Running baseline vs scenario projections..."):
            baseline_result = calculate_projections(baseline_data, user)
            scenario_result = calculate_projections(scenario_data, user)

        baseline_df = pd.DataFrame(baseline_result["projections"])
        scenario_df = pd.DataFrame(scenario_result["projections"])

        st.success(f"Scenario '{selected}' calculated")

        # -----------------------------------
        # Comparison chart
        # -----------------------------------
        st.subheader("📊 Income Comparison")

        compare_df = pd.DataFrame({
            "Year": baseline_df["Year"],
            "Baseline Income": baseline_df["TotalIncome"],
            "Scenario Income": scenario_df["TotalIncome"]
        })

        fig = plot_income_vs_expenses(compare_df.rename(columns={
            "Baseline Income": "Total Income",
            "Scenario Income": "Total Expenses"  # reuse chart
        }))

        st.plotly_chart(fig, use_container_width=True)

        # -------------------------------------------------
        # Assumption Diff: Baseline vs Scenario
        # -------------------------------------------------
        render_assumption_diff_between(
            title="🔍 Assumption Changes in This Scenario",
            base_data_config=config["base_data"],
            left_data=baseline_data,
            right_data=scenario_data
        )

        # -----------------------------------
        # Delta table
        # -----------------------------------
        st.subheader("🔍 Key Differences")

        diff_rows = []
        for k, v in scenario_diff.items():
            diff_rows.append({
                "Assumption": k,
                "Baseline": baseline_data[k]["input"],
                "Scenario": v,
                "Change": v - baseline_data[k]["input"]
            })

        st.dataframe(pd.DataFrame(diff_rows), use_container_width=True)

        from ui.ai_explanation import explain_scenario

        st.subheader("🤖 AI Explanation")

        ai_text = explain_scenario(baseline_df, scenario_df, selected)
        st.info(ai_text)
