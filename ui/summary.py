import streamlit as st
import pandas as pd
import plotly.express as px

from ui.pdf import generate_financial_summary_pdf_playwright
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

def compute_retirement_score(projection_df, base_context):
    if projection_df.empty:
        return 0, {}

    years = len(projection_df)
    last = projection_df.iloc[-1]
    first = projection_df.iloc[0]

    # 1️⃣ Corpus Sustainability (40 pts)
    if last["EndingCorpus"] > 0:
        corpus_score = 40
    elif last["EndingCorpus"] > -0.2 * base_context["initial_corpus"]["total"]:
        corpus_score = 25
    else:
        corpus_score = 10

    # 2️⃣ Income Coverage (25 pts)
    if first["TotalIncome"] >= first["TotalExpenses"]:
        coverage_score = 25
    else:
        ratio = first["TotalIncome"] / max(first["TotalExpenses"], 1)
        coverage_score = max(5, 25 * ratio)

    # 3️⃣ Withdrawal Safety (20 pts)
    withdrawal_rate = (
        first["TotalWithdrawal"] / base_context["initial_corpus"]["total"]
        if base_context["initial_corpus"]["total"] > 0 else 0
    )

    if withdrawal_rate <= 0.04:
        withdrawal_score = 20
    elif withdrawal_rate <= 0.06:
        withdrawal_score = 15
    else:
        withdrawal_score = 5

    # 4️⃣ Tax Efficiency (15 pts)
    tax_ratio = first["TotalTax"] / max(first["TotalIncome"], 1)
    if tax_ratio <= 0.15:
        tax_score = 15
    elif tax_ratio <= 0.25:
        tax_score = 10
    else:
        tax_score = 5

    total_score = round(
        corpus_score + coverage_score + withdrawal_score + tax_score
    )

    breakdown = {
        "Corpus Sustainability": corpus_score,
        "Income Coverage": coverage_score,
        "Withdrawal Safety": withdrawal_score,
        "Tax Efficiency": tax_score,
    }

    return total_score, breakdown

# -------------------------------------------------
# MAIN SUMMARY
# -------------------------------------------------
def render_summary(projections, user_data, user, base_context):
    st.header("📊 Your Retirement Outlook")
    #st.header("📄 Your Retirement Outlook")
    st.caption("A clear picture of your future income, expenses, and savings.")


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

    score, breakdown = compute_retirement_score(df, base_context)

    st.markdown("## 🏆 Retirement Readiness Score")

    col1, col2 = st.columns([1,2])

    with col1:
        st.metric("Overall Score", f"{score} / 100")

    with col2:
        st.progress(score / 100)

    if score >= 80:
        st.success("You are on track for a confident retirement 🎯")
    elif score >= 60:
        st.warning("You are moderately prepared. Some adjustments recommended.")
    else:
        st.error("Retirement plan needs strengthening.")

    st.markdown("### 📊 Score Breakdown")

    breakdown_df = pd.DataFrame({
        "Category": breakdown.keys(),
        "Score": breakdown.values()
    })

    fig_score = px.bar(
        breakdown_df,
        x="Category",
        y="Score",
        color="Score",
        color_continuous_scale="Blues"
    )

    st.plotly_chart(fig_score, use_container_width=True)

    # -------------------------------------------------
    # Key Numbers (Top)
    # -------------------------------------------------
    starting_corpus = safe_get(base_context, ["initial_corpus", "total"], 0)
    one_time_total = safe_get(base_context, ["one_time", "total"], 0)

    st.subheader("🔑 Your Retirement Snapshot (Year 1)")

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Starting Corpus", f"{currency}{starting_corpus:,.0f}")
    k2.metric("Yearly Essential Living Costs", f"{currency}{year1['AnnualMustExpenses']:,.0f}")
    k3.metric("Yearly Leisure Costs", f"{currency}{year1['AnnualOptionalExpenses']:,.0f}")
    k4.metric("Take-home Income (Post-Tax)", f"{currency}{year1['NetIncomeAfterTax']:,.0f}")

    st.divider()

    # -------------------------------------------------
    # Income vs Expenses
    # -------------------------------------------------
    st.subheader("📈 Will My Income Cover My Expenses? - Income vs Expenses")

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
    st.subheader("💰 How Your Savings Change Over Time - Corpus Trajectory")

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
    
    income_expense_chart_html = fig_ie.to_html(full_html=False, include_plotlyjs=False)
    corpus_chart_html = fig_corpus.to_html(full_html=False, include_plotlyjs=False)
    tax_chart_html = fig_tax.to_html(full_html=False, include_plotlyjs=False)

    #try:
    #    income_expense_png = fig_ie.to_image(format="png", scale=2)
    #    corpus_png = fig_corpus.to_image(format="png", scale=2)
    #except Exception as e:
    #    st.warning("Chart images unavailable (kaleido not installed).")
    print("Tax chart HTML length:", len(tax_chart_html))
    if user.get("is_premium"):
        if st.button("📥 Download Detailed Retirement Report (PDF"):
            #pdf_bytes = generate_financial_summary_pdf(
            #    username=user["username"],
            #     base_context=base_context,
            #    projection_df=df,
            #    currency=currency,
            #    income_expense_chart_png=income_expense_png,
            #    corpus_chart_png=corpus_png,
            #    scenario_comparison_df=cmp_df if not cmp_df.empty else None,
            #)

            pdf_bytes = generate_financial_summary_pdf_playwright(
                username=user["username"],
                base_context=base_context,
                projection_df=df,
                currency=currency,
                retirement_score=score,
                score_breakdown=breakdown,
                advisor_advice=advice,
                income_expense_chart_html=income_expense_chart_html,
                corpus_chart_html=corpus_chart_html,
                tax_chart_html=tax_chart_html,
                scenario_comparison_df=cmp_df
            )

            if isinstance(pdf_bytes, bytearray):
                pdf_bytes = bytes(pdf_bytes)

            st.download_button(
                "Download Report PDF",
                pdf_bytes,
                file_name=f"{user['username']}_{scenario_name}_summary.pdf",
                mime="application/pdf",
            )
    else:
        st.info("Upgrade to Premium to download PDF reports.")
