import streamlit as st
import pandas as pd
import plotly.express as px

from ui.pdf import generate_financial_summary_pdf_playwright
from ui.retirement_profiles import RETIREMENT_PROFILES
from services.api_client import get_advisor_recommendations
from ui.advisor_panel import render_advisor_panel


def section(title, subtitle=None):
    st.markdown("### " + title)
    if subtitle:
        st.caption(subtitle)
    return st.container(border=True)

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


def style_chart_for_pdf(fig):
    fig.update_layout(
        width=700,          # fits A4
        height=420,         # compact
        margin=dict(l=40, r=40, t=60, b=80),
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.20,        # move legend below chart
            xanchor="center",
            x=0.5,
            font=dict(size=10)
        ),
        font=dict(size=11),
        autosize=False
    )
    return fig
# -------------------------------------------------
# MAIN SUMMARY
# -------------------------------------------------
def render_summary(projections, user_data, user, base_context,life_stage=None,stage_metrics=None):
    st.title("📊 Financial Outcome Summary")

    is_mobile = st.session_state.get("is_mobile", False)
    with section(
        "Scenario Overview",
        "Your financial outcome based on current inputs"
    ):
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


    
    #st.header("📊 Your Future Financial Outlook")
    #st.header("📄 Your Retirement Outlook")
    #st.caption("A clear picture of your future income, expenses, and savings.")


   
    # ======================================================
    # 👤 LIFE STAGE INSIGHTS
    # ======================================================
    print("Life stage:", life_stage)

    
    if life_stage and stage_metrics:

        with section("👤 Life Stage Profile", "Your current financial phase"):
            stage_labels = {
                "fire": "🟢 FIRE Builder",
                "wealth": "🟡 Wealth Builder",
                "pre_retire": "🟠 Pre-Retirement Planner",
                "retired": "🔵 Retirement Income Mode"
            }
            st.success(stage_labels.get(life_stage, life_stage))

            cols = st.columns(len(stage_metrics))
            for i, (label, value) in enumerate(stage_metrics.items()):
                cols[i].metric(label, value)

    #if life_stage and stage_metrics:
    #    st.markdown("---")
    #    st.markdown("## 👤 Life Stage Profile")

    #    stage_labels = {
    #        "fire": "🟢 FIRE Builder",
    #        "wealth": "🟡 Wealth Builder",
    #        "pre_retire": "🟠 Pre-Retirement Planner",
    #        "retired": "🔵 Retirement Income Mode"
    #    }

    #    st.success(stage_labels.get(life_stage, life_stage))

    #    st.markdown("### 📊 Stage Insights")#

    #    cols = st.columns(len(stage_metrics))

    #    for i, (label, value) in enumerate(stage_metrics.items()):
    #        cols[i].metric(label, value)
    with section("🏆 Retirement Readiness", "Overall health of your plan"):

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
        height = 320 if is_mobile else 500
        fig_score.update_layout(height=height)
        st.plotly_chart(fig_score, use_container_width=True)

    #metrics = projections[0]["life_stage_metrics"]

    #st.subheader("📊 Life Stage Insights")

    #for k, v in stage_metrics.items():
    #    st.write(f"{k.replace('_',' ').title()} : {v}")

    # -------------------------------------------------
    # Key Numbers (Top)
    # -------------------------------------------------
    starting_corpus = safe_get(base_context, ["initial_corpus", "total"], 0)
    one_time_total = safe_get(base_context, ["one_time", "total"], 0)

    #st.subheader("🔑 Your Financial Snapshot (Year 1)")
    with section("🔑 Year-1 Financial Snapshot"):


        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Starting Corpus", f"{currency}{starting_corpus:,.0f}")
        k2.metric("Yearly Essential Living Costs", f"{currency}{year1['AnnualMustExpenses']:,.0f}")
        k3.metric("Yearly Leisure Costs", f"{currency}{year1['AnnualOptionalExpenses']:,.0f}")
        k4.metric("Take-home Income (Post-Tax)", f"{currency}{year1['NetIncomeAfterTax']:,.0f}")

        st.divider()

    with section("📈 Financial Trajectory", "Income, savings and tax evolution"):
    
        st.markdown("**📈 Will My Income Cover My Expenses? - Income vs Expenses*")
        fig_ie = px.line(
            df,
            x="Year",
            y=["TotalIncome", "TotalExpenses"],
            markers=True,
            color_discrete_sequence=["#22c55e", "#ef4444"],
        )
        height = 320 if is_mobile else 500
        fig_ie.update_layout(height=height)
        st.plotly_chart(fig_ie, use_container_width=True)

        st.markdown("**Corpus Growth 💰 - How Your Savings Change Over Time**")
        fig_corpus = px.area(
            df,
            x="Year",
            y="EndingCorpus",
            color_discrete_sequence=["#6366f1"],
        )
        height = 320 if is_mobile else 500
        fig_corpus.update_layout(height=height)
        st.plotly_chart(fig_corpus, use_container_width=True)

        st.markdown("**Tax Impact**")
        fig_tax = px.line(
            df,
            x="Year",
            y=["TotalTax", "NetIncomeAfterTax"],
            markers=True,
            color_discrete_sequence=["#f59e0b", "#22c55e"],
        )
        height = 320 if is_mobile else 500
        fig_tax.update_layout(height=height)
        st.plotly_chart(fig_tax, use_container_width=True)

    # -------------------------------------------------
    # Income vs Expenses
    # -------------------------------------------------
    #st.subheader("📈 Will My Income Cover My Expenses? - Income vs Expenses")

    
    #st.plotly_chart(fig_ie, use_container_width=True)

    # -------------------------------------------------
    # Corpus Growth
    # -------------------------------------------------
    #st.subheader("💰 How Your Savings Change Over Time - Corpus Trajectory")

    
    #st.plotly_chart(fig_corpus, use_container_width=True)

    # -------------------------------------------------
    # Tax Impact
    # -------------------------------------------------
    #st.subheader("🧾 Tax Impact")

   
    #st.plotly_chart(fig_tax, use_container_width=True)

    # -------------------------------------------------
    # Scenario Comparison
    # -------------------------------------------------
    #--print("BASE CONTEXT IN SUMMARY", base_context)

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


    st.divider()

 
    # -------------------------------------------------
    # PDF Export
    # -------------------------------------------------
    
    # Try to generate chart images for PDF; gracefully skip if kaleido unavailable
    income_expense_png = None
    corpus_png = None
    country = user_data.get("country")

    onetime = user_data.get("onetime_expenses", {}).get(country, {})
    onetime_rows = [
        {"Category": k, "Amount": v.get("input", 0)}
        for k, v in onetime.items()
        if v.get("input", 0) > 0
    ]

    onetime_chart_html = ""
    if onetime_rows:
        df_ot = pd.DataFrame(onetime_rows)
        fig_ot = px.pie(df_ot, names="Category", values="Amount", title="One-Time Expenses")
        #fig_ot.update_traces(
        #    textinfo="label+percent",
        #    textposition="inside",   # or "outside"
        #    insidetextorientation="radial",
        #    showlegend=True
        #)
        fig_ot.update_layout(
            showlegend=True,
            legend=dict(
                font=dict(color="black"),
                orientation="h",
                yanchor="bottom",
                y=-0.1,
                xanchor="center",
                x=0.5
            ),
            font=dict(color="#111827"),   # force visible text
            paper_bgcolor="white",
            plot_bgcolor="white",
            
            template="plotly_white",
        )
        #fig_ot.update_layout(
        #            template="plotly_white",
        #            legend_title="One Time Expense Category",
        #            showlegend=True,
        #            legend=dict(
        #                orientation="v",
        #                font=dict(size=12)
        #            ),
        #        )
        
    
    recurring = user_data.get("recurring_expenses", {}).get(country, {})

    recurring_rows = []
    for k, v in recurring.items():
        yearly = v.get("monthly", 0) * 12
        if yearly > 0:
            recurring_rows.append({"Category": k, "Amount": yearly})

    recurring_chart_html = ""
    if recurring_rows:
        df_rec = pd.DataFrame(recurring_rows)
        fig_rec = px.pie(df_rec, names="Category", values="Amount", title="Recurring Expenses (Year 1)")
        fig_rec.update_traces(
            textinfo="label+percent",
            textposition="inside",   # or "outside"
            insidetextorientation="radial",
            showlegend=True
        )
        fig_rec.update_layout(
            showlegend=True,
            legend=dict(
                orientation="v",
                font=dict(color="black"),
                #yanchor="bottom",
                #y=-0.2,
                #xanchor="center",
                #x=0.5
            ),
            font=dict(color="#111827"),   # force visible text
            paper_bgcolor="white",
            plot_bgcolor="white",
            template="plotly_white",
        )
        #fig_rec.update_layout(
        #            template="plotly_white",
        #            legend_title="Recurring Expense Category",
        #            showlegend=True,
        #            legend=dict(
        #                orientation="v",
        #                font=dict(size=12)
        #            ),
        #        )
        

    expense_growth_chart_html = ""

    if not df.empty:
        fig_exp_growth = px.line(
            df,
            x="Year",
            y=["AnnualMustExpenses", "AnnualOptionalExpenses", "TotalExpenses"],
            markers=True,
            color_discrete_sequence=[
                "#6366f1",
                "#22c55e",
                "#f59e0b",
                "#ef4444",
            ],
            title="Expense Growth Over Time"
        )
        fig_exp_growth.update_layout(
                    template="plotly_white",
                    legend_title="Expense Growth Over Time",
                )
        
       # Expense breakdown charts (country-safe)
    fig_ot = style_chart_for_pdf(fig_ot)
    onetime_chart_html = fig_ot.to_html(full_html=False, include_plotlyjs=False)
    fig_rec = style_chart_for_pdf(fig_rec)
    recurring_chart_html = fig_rec.to_html(full_html=False, include_plotlyjs=False)
    fig_exp_growth = style_chart_for_pdf(fig_exp_growth)
    fig_ie = style_chart_for_pdf(fig_ie)
    fig_corpus = style_chart_for_pdf(fig_corpus)
    fig_tax = style_chart_for_pdf(fig_tax)
    income_expense_chart_html = fig_ie.to_html(full_html=False, include_plotlyjs=False)
    corpus_chart_html = fig_corpus.to_html(full_html=False, include_plotlyjs=False)
    tax_chart_html = fig_tax.to_html(full_html=False, include_plotlyjs=False)

    with section("💸 Expense Structure", "Where your money goes"):
    
        col1, col2 = st.columns(2)

        with col1:
            if onetime_rows:
                height = 320 if is_mobile else 500
                fig_ot.update_layout(height=height)
                st.plotly_chart(fig_ot, use_container_width=True)

        with col2:
            if recurring_rows:
                height = 320 if is_mobile else 500
                fig_rec.update_layout(height=height)
                st.plotly_chart(fig_rec, use_container_width=True)

        if not df.empty:
            height = 320 if is_mobile else 500
            fig_exp_growth.update_layout(height=height)
            st.plotly_chart(fig_exp_growth, use_container_width=True)

   

    with section("🔀 Scenario Comparison", "Compare financial outcomes"):

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
        height = 320 if is_mobile else 500
        fig.update_layout(height=height)
        st.plotly_chart(fig, use_container_width=True)

        #st.dataframe(cmp_df, use_container_width=True)
        #st.plotly_chart(fig, use_container_width=True)

    with section("🧠 Advisor Insights"):

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
        #try:
        #    advice = get_advisor_recommendations(...)
        #    render_advisor_panel(advice)
        #except:
        #    st.info("Advisor insights unavailable")

    with section("📄 Report Export"):


        if user.get("is_premium"):
            if st.button("📥 Download Detailed Financial Report (PDF)"):
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
                    scenario_comparison_df=cmp_df,
                    onetime_chart_html=onetime_chart_html,
                    recurring_chart_html=recurring_chart_html,
                    expense_growth_chart_html=expense_growth_chart_html,
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
