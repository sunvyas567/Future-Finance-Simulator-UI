import streamlit as st
import pandas as pd
from services.api_client import calculate_projections
from ui.scenario_engine import apply_scenario_diff
from ui.charts import plot_income_vs_expenses
from ui.currency import get_currency


def render_scenario_dashboard(config, user_data, user):
    st.header("📊 Scenario Comparison Dashboard")

    if not user["is_premium"]:
        st.info("Upgrade to Premium to access scenario comparison.")
        return

    if "scenarios" not in user_data or not user_data["scenarios"]:
        st.info("No saved scenarios to compare.")
        return

    baseline = user_data.copy()
    currency = get_currency(user_data)

    selected = st.multiselect(
        "Select scenarios to compare",
        list(user_data["scenarios"].keys())
    )

    if not selected:
        st.warning("Select at least one scenario.")
        return

    with st.spinner("Running scenario projections..."):
        baseline_result = calculate_projections(baseline, user)
        baseline_df = pd.DataFrame(baseline_result["projections"])

        all_frames = []

        # Baseline
        baseline_df["Scenario"] = "Baseline"
        all_frames.append(baseline_df[["Year", "GLTotalIncomeOverallFDs", "Scenario"]])

        for name in selected:
            diff = user_data["scenarios"][name]
            scenario_data = apply_scenario_diff(baseline, diff)
            result = calculate_projections(scenario_data, user)
            df = pd.DataFrame(result["projections"])
            df["Scenario"] = name
            all_frames.append(df[["Year", "GLTotalIncomeOverallFDs", "Scenario"]])

    compare_df = pd.concat(all_frames, ignore_index=True)

    st.subheader("📈 Income Comparison Across Scenarios")

    import plotly.express as px

    fig = px.line(
        compare_df,
        x="Year",
        y="GLTotalIncomeOverallFDs",
        color="Scenario",
        markers=True,
        title="Income Comparison Across Scenarios"
    )

    fig.update_layout(
        yaxis_title="Income",
        xaxis_title="Year"
    )

    st.plotly_chart(fig, use_container_width=True)

    
    # Summary table
    st.subheader("📋 Summary (Year 1)")

    summary_rows = []
    for scenario, group in compare_df.groupby("Scenario"):
        y1 = group[group["Year"] == 1].iloc[0]
        summary_rows.append({
            "Scenario": scenario,
            "Income Year 1": y1["GLTotalIncomeOverallFDs"]
        })

    st.dataframe(pd.DataFrame(summary_rows))

    from ui.pdf import generate_scenario_comparison_pdf

    if st.button("📥 Export Scenario Comparison PDF"):
        scenario_results = {}

        scenario_results["Baseline"] = baseline_df

        for name in selected:
            diff = user_data["scenarios"][name]
            scenario_data = apply_scenario_diff(baseline, diff)
            result = calculate_projections(scenario_data, user)
            scenario_results[name] = pd.DataFrame(result["projections"])

        pdf = generate_scenario_comparison_pdf(
            username=user["username"],
            scenario_results=scenario_results,
            currency=currency
        )

        st.download_button(
            "Download Scenario Comparison PDF",
            data=pdf,
            file_name="scenario_comparison.pdf",
            mime="application/pdf"
        )
