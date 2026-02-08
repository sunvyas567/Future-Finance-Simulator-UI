import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from services.api_client import calculate_projections


def render_scenarios(user_data: dict, user: dict):
    st.header("🔀 Scenario Analysis (What-If Simulation)")

    if not user["is_premium"]:
        st.info("Scenario analysis is a Premium feature.")
        return

    st.markdown(
        """
        Create a *what-if* scenario by changing only a few assumptions.
        Your **baseline data remains unchanged**.
        """
    )

    # -------------------------------------------------
    # Scenario metadata
    # -------------------------------------------------
    scenario_name = st.text_input(
        "Scenario Name",
        value="High Inflation Scenario"
    )

    st.markdown("---")

    # -------------------------------------------------
    # Scenario diff builder
    # -------------------------------------------------
    st.subheader("Assumption Changes (Delta from Baseline)")

    diff = {}

    col1, col2 = st.columns(2)

    with col1:
        diff["InflationRate"] = st.slider(
            "Inflation Change (%)",
            min_value=-5.0,
            max_value=5.0,
            value=0.0,
            step=0.5
        )

        diff["Return_EQUITY"] = st.slider(
            "Equity Return Change (%)",
            min_value=-5.0,
            max_value=5.0,
            value=0.0,
            step=0.5
        )

    with col2:
        diff["Return_DEBT"] = st.slider(
            "Debt Return Change (%)",
            min_value=-3.0,
            max_value=3.0,
            value=0.0,
            step=0.25
        )

        diff["LifeExpectancy"] = st.slider(
            "Life Expectancy Change (Years)",
            min_value=-5,
            max_value=5,
            value=0,
            step=1
        )

    st.markdown("---")

    # -------------------------------------------------
    # Run scenario
    # -------------------------------------------------
    if st.button("▶ Run Scenario"):
        with st.spinner("Running scenario simulation..."):
            # ---- Baseline ----
            baseline_result = calculate_projections(user_data, user)
            baseline_df = pd.DataFrame(baseline_result["projections"])

            # ---- Scenario payload ----
            scenario_user_data = {}
            for k, v in user_data.items():
                scenario_user_data[k] = dict(v)

            for field, delta in diff.items():
                if delta != 0:
                    if field in scenario_user_data:
                        scenario_user_data[field]["input"] += delta
                    else:
                        scenario_user_data[field] = {"input": delta}

            scenario_result = calculate_projections(scenario_user_data, user)
            scenario_df = pd.DataFrame(scenario_result["projections"])

        st.success(f"Scenario '{scenario_name}' generated")

        # -------------------------------------------------
        # Comparison chart — Corpus over time
        # -------------------------------------------------
        st.subheader("Corpus Comparison")

        corpus_cols = [
            c for c in baseline_df.columns
            if "Corpus" in c or "Balance" in c
        ]

        if corpus_cols:
            corpus_col = corpus_cols[0]

            fig = go.Figure()

            fig.add_trace(
                go.Scatter(
                    x=baseline_df["Year"],
                    y=baseline_df[corpus_col],
                    name="Baseline",
                    line=dict(width=3)
                )
            )

            fig.add_trace(
                go.Scatter(
                    x=scenario_df["Year"],
                    y=scenario_df[corpus_col],
                    name=scenario_name,
                    line=dict(dash="dash", width=3)
                )
            )

            fig.update_layout(
                title="Investment Corpus Over Time",
                xaxis_title="Year",
                yaxis_title="Corpus Value",
                legend_title="Scenario"
            )

            st.plotly_chart(fig, use_container_width=True)

        # -------------------------------------------------
        # Comparison chart — Income vs Expenses
        # -------------------------------------------------
        st.subheader("Income vs Expenses Impact")

        baseline_df["Net"] = (
            baseline_df["GLTotalIncomeOverallFDs"]
            - baseline_df["GLTotalYearlyExpensesMust"]
            - baseline_df["GLTotalYearlyExpensesOptional"]
        )

        scenario_df["Net"] = (
            scenario_df["GLTotalIncomeOverallFDs"]
            - scenario_df["GLTotalYearlyExpensesMust"]
            - scenario_df["GLTotalYearlyExpensesOptional"]
        )

        fig2 = go.Figure()

        fig2.add_trace(
            go.Scatter(
                x=baseline_df["Year"],
                y=baseline_df["Net"],
                name="Baseline Net",
                line=dict(width=3)
            )
        )

        fig2.add_trace(
            go.Scatter(
                x=scenario_df["Year"],
                y=scenario_df["Net"],
                name=f"{scenario_name} Net",
                line=dict(dash="dash", width=3)
            )
        )

        fig2.update_layout(
            title="Net Surplus / Deficit Comparison",
            xaxis_title="Year",
            yaxis_title="Net Amount"
        )

        st.plotly_chart(fig2, use_container_width=True)

        # -------------------------------------------------
        # Explanation panel (deterministic, not LLM)
        # -------------------------------------------------
        st.subheader("Scenario Impact Summary")

        delta_years = (
            scenario_df["Net"] > 0
        ).sum() - (baseline_df["Net"] > 0).sum()

        explanation = f"""
        **Scenario:** {scenario_name}

        Changes applied:
        {', '.join([f"{k}: {v:+}" for k, v in diff.items() if v != 0])}

        Result:
        • Net-positive years change: {delta_years:+} years
        """

        st.info(explanation)
