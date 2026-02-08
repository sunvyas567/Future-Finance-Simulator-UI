import streamlit as st
import pandas as pd
import plotly.express as px

from ui.pdf import generate_financial_summary_pdf
from ui.retirement_profiles import RETIREMENT_PROFILES
from services.api_client import get_advisor_recommendations
from ui.advisor_panel import render_advisor_panel


# -------------------------------------------------
# Safe nested getter
# -------------------------------------------------
def safe_get(d: dict, path: list, default=0):
    cur = d
    for key in path:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(key)
        if cur is None:
            return default
    return cur


# -------------------------------------------------
# MAIN SUMMARY
# -------------------------------------------------
def render_summary(projections, user_data, user, base_context):
    st.header("📊 Retirement Outlook")

    # -------------------------------------------------
    # Safety
    # -------------------------------------------------
    if not projections or not isinstance(base_context, dict):
        st.warning("Complete inputs to view summary.")
        return

    meta = base_context["_meta"]
    currency = meta.get("currency", "₹")
    scenario_name = meta.get("scenario", "Base")

    st.caption(
        f"🌍 {meta.get('country_label')} | "
        f"📌 Scenario: **{scenario_name}** | "
        f"💱 Currency: {currency}"
    )

    df = pd.DataFrame(projections)
    year1 = df.iloc[0]

    # -------------------------------------------------
    # Key Numbers (Top)
    # -------------------------------------------------
    starting_corpus = safe_get(base_context, ["initial_corpus", "total"], 0)
    one_time_total = safe_get(base_context, ["one_time", "total"], 0)

    st.subheader("🔑 Key Numbers (Year 1)")

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Starting Corpus", f"{currency}{starting_corpus:,.0f}")
    k2.metric("Annual Mandatory", f"{currency}{year1['AnnualMustExpenses']:,.0f}")
    k3.metric("Annual Optional", f"{currency}{year1['AnnualOptionalExpenses']:,.0f}")
    k4.metric("Net Income (Post-Tax)", f"{currency}{year1['NetIncomeAfterTax']:,.0f}")

    st.divider()

    # -------------------------------------------------
    # Income vs Expenses
    # -------------------------------------------------
    st.subheader("📈 Income vs Expenses")

    fig_ie = px.line(
        df,
        x="Year",
        y=["TotalIncome", "TotalExpenses"],
        markers=True,
        color_discrete_sequence=["#22c55e", "#ef4444"],
    )
    st.plotly_chart(fig_ie, use_container_width=True)

    # -------------------------------------------------
    # Corpus Growth
    # -------------------------------------------------
    st.subheader("💰 Corpus Trajectory")

    fig_corpus = px.area(
        df,
        x="Year",
        y="EndingCorpus",
        color_discrete_sequence=["#6366f1"],
    )
    st.plotly_chart(fig_corpus, use_container_width=True)

    # -------------------------------------------------
    # Tax Impact
    # -------------------------------------------------
    st.subheader("🧾 Tax Impact")

    fig_tax = px.line(
        df,
        x="Year",
        y=["TotalTax", "NetIncomeAfterTax"],
        markers=True,
        color_discrete_sequence=["#f59e0b", "#22c55e"],
    )
    st.plotly_chart(fig_tax, use_container_width=True)

    # -------------------------------------------------
    # Scenario Comparison
    # -------------------------------------------------
    #--print("BASE CONTEXT IN SUMMARY", base_context)
    scenario_results = base_context.get("scenario_results", {})
    #scenario_results = base_context.get("scenario_results", {})


    rows = []
    for name, proj in scenario_results.items():
        df_s = pd.DataFrame(proj)
        last = df_s.iloc[-1]

        rows.append({
            "Scenario": name,
            "Ending Corpus": last["EndingCorpus"],
            "Year-1 Income": df_s.iloc[0]["TotalIncome"],
            "Year-1 Expenses": df_s.iloc[0]["TotalExpenses"],
            "Year-1 Net Income": df_s.iloc[0]["NetIncomeAfterTax"],
        })

    cmp_df = pd.DataFrame(rows)

    st.dataframe(cmp_df, use_container_width=True)

    fig = px.bar(
        cmp_df,
        x="Scenario",
        y="Ending Corpus",
        color="Scenario",
        color_discrete_sequence=["#6366f1", "#22c55e", "#ef4444"],
    )
    st.plotly_chart(fig, use_container_width=True)

    #st.subheader("🔀 Scenario Comparison")

    #comparison_rows = []

    #for name, scenario in user_data["investment_plan"]["scenarios"].items():
    #    res = scenario.get("_projection")
    #    print("RES",res)
    #    if not res:
    #        continue

    #    proj = pd.DataFrame(res)
    #    last = proj.iloc[-1]

    #    comparison_rows.append({
    #        "Scenario": name,
    #        "Ending Corpus": last["EndingCorpus"],
    #        "Year-1 Income": proj.iloc[0]["TotalIncome"],
    #        "Year-1 Expenses": proj.iloc[0]["TotalExpenses"],
    #    })

    #if comparison_rows:
    #    cmp_df = pd.DataFrame(comparison_rows)#

    #    st.dataframe(cmp_df, use_container_width=True)

    #    fig_cmp = px.bar(
    #        cmp_df,
    #        x="Scenario",
    #        y="Ending Corpus",
    #        color="Scenario",
    #        color_discrete_sequence=["#6366f1", "#22c55e", "#ef4444"],
    #        title="Ending Corpus by Scenario",
    #    )
    #    st.plotly_chart(fig_cmp, use_container_width=True)

    st.divider()

    # -------------------------------------------------
    # Advisor Insights
    # -------------------------------------------------
    try:
        advice = get_advisor_recommendations(
            projections=projections,
            base_context=base_context,
            scenario=user_data["investment_plan"]["scenarios"][scenario_name],
            user_data=user_data,
        )
        render_advisor_panel(advice)
    except Exception:
        st.info("Advisor insights unavailable.")

    st.divider()

    # -------------------------------------------------
    # PDF Export
    # -------------------------------------------------
    
    # Try to generate chart images for PDF; gracefully skip if kaleido unavailable
    income_expense_png = None
    corpus_png = None
    
    try:
        income_expense_png = fig_ie.to_image(format="png", scale=2)
        corpus_png = fig_corpus.to_image(format="png", scale=2)
    except Exception as e:
        st.warning("Chart images unavailable (kaleido not installed). PDF will be generated without charts.")

    if user.get("is_premium"):
        if st.button("📥 Download Detailed PDF"):
            pdf_bytes = generate_financial_summary_pdf(
                username=user["username"],
                base_context=base_context,
                projection_df=df,
                currency=currency,
                income_expense_chart_png=income_expense_png,
                corpus_chart_png=corpus_png,
                scenario_comparison_df=cmp_df if not cmp_df.empty else None,
            )

            if isinstance(pdf_bytes, bytearray):
                pdf_bytes = bytes(pdf_bytes)

            st.download_button(
                "Download PDF",
                pdf_bytes,
                file_name=f"{user['username']}_{scenario_name}_summary.pdf",
                mime="application/pdf",
            )
    else:
        st.info("Upgrade to Premium to download PDF reports.")
