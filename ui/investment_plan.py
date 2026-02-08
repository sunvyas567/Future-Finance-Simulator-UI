# ui/investment_plan.py

import streamlit as st
import pandas as pd
import plotly.express as px
import copy

from services.api_client import calculate_projections
from ui.currency import get_currency

import copy


def ensure_scenarios(plan: dict, country: str):
    plan.setdefault("active_scenario", "Base")
    plan.setdefault("scenarios", {})

    # ---------- Base ----------
    base = plan["scenarios"].get("Base")
    #print("Base scenario in ensure -1 :", base)
    def is_empty_scenario(sc: dict) -> bool:
        if not isinstance(sc, dict):
            return True
        if not sc:
            return True
        if not sc.get("allocations"):
            return True
        if not sc.get("rates"):
            return True
        if "income_sources" not in sc:
            return True
        return False
    
    if is_empty_scenario(base):
        plan["scenarios"]["Base"] = _default_scenario(country)
    #if not isinstance(base, dict) or not base:
        #print("Base scenario missing or invalid. Applying defaults.")
    #    plan["scenarios"]["Base"] = _default_scenario(country)

    base = plan["scenarios"]["Base"]
    #print("Base scenario in ensure -2 :", base)

    # ---------- Conservative ----------
    cons = plan["scenarios"].get("Conservative")
    if not isinstance(cons, dict) or not cons:
        cons = copy.deepcopy(base)
        for k in cons.get("rates", {}):
            cons["rates"][k] = round(cons["rates"][k] * 0.8, 2)
        plan["scenarios"]["Conservative"] = cons

    # ---------- Aggressive ----------
    agg = plan["scenarios"].get("Aggressive")
    if not isinstance(agg, dict) or not agg:
        agg = copy.deepcopy(base)
        for k in agg.get("rates", {}):
            agg["rates"][k] = round(agg["rates"][k] * 1.2, 2)
        plan["scenarios"]["Aggressive"] = agg

    # ---------- Safety ----------
    if plan["active_scenario"] not in plan["scenarios"]:
        plan["active_scenario"] = "Base"

    #print("PLAN at ensure exit UPDATED:", plan)

# =========================================================
# DEFAULT SCENARIO (SINGLE SOURCE OF TRUTH)
# =========================================================

def _default_scenario(country: str) -> dict:
    if country == "IN":
        return {
            "allocations": {
                "SWP": 40,
                "FD": 30,
                "SCSS": 20,
                "POMIS": 10,
            },
            "rates": {
                "SWP": 8.0,
                "FD": 6.5,
                "SCSS": 8.2,
                "POMIS": 7.4,
            },
            "income_sources": {
                "rental": 20000,
                "pension": 2000,
                "annuity": 1500,
                "dividends": 200000,
                "other": 50000,
            },
            "withdrawal": {"monthly": 10_000},
        }

    if country == "US":
        return {
            "allocations": {
                "SWP": 40,
                "401K": 30,
                "IRA": 20,
                "BROKERAGE": 10,
            },
            "rates": {
                "SWP": 7.5,
                "401K": 7.0,
                "IRA": 6.5,
                "BROKERAGE": 6.0,
            },
            "income_sources": {
                "social_security": 2000,
                "rental": 0,
                "pension": 0,
                "annuity": 0,
                "dividends": 0,
                "other": 0,
            },
            "withdrawal": {"monthly": 2000},
        }

    # UK
    return {
        "allocations": {
            "SWP": 40,
            "PENSION": 40,
            "ISA": 20,
        },
        "rates": {
            "SWP": 7.0,
            "PENSION": 6.5,
            "ISA": 6.0,
        },
        "income_sources": {
            "rental": 0,
            "pension": 0,
            "annuity": 0,
            "dividends": 0,
            "other": 0,
        },
        "withdrawal": {"monthly": 1000},
    }


def _derive_scenario(base: dict, mode: str) -> dict:
    """
    mode: 'conservative' | 'aggressive'
    """
    sc = copy.deepcopy(base)

    if mode == "conservative":
        rate_factor = 0.85
        withdraw_factor = 0.8
        equity_shift = -15
    else:
        rate_factor = 1.15
        withdraw_factor = 1.2
        equity_shift = 15

    # ---- Rates ----
    for k in sc["rates"]:
        sc["rates"][k] = round(sc["rates"][k] * rate_factor, 2)

    # ---- Withdrawal ----
    sc["withdrawal"]["monthly"] = round(
        sc["withdrawal"]["monthly"] * withdraw_factor, 0
    )

    # ---- Allocation shift (SWP = equity proxy) ----
    if "SWP" in sc["allocations"]:
        sc["allocations"]["SWP"] = max(
            0, min(100, sc["allocations"]["SWP"] + equity_shift)
        )

        # rebalance others
        remaining = 100 - sc["allocations"]["SWP"]
        others = [k for k in sc["allocations"] if k != "SWP"]
        total_other = sum(sc["allocations"][k] for k in others) or 1

        for k in others:
            sc["allocations"][k] = round(
                remaining * sc["allocations"][k] / total_other, 2
            )

    return sc

# =========================================================
# FIELD DEFINITIONS
# =========================================================

def _allocation_fields(country):
    return {
        "IN": [
            ("SWP", "SWP / Market Linked"),
            ("FD", "Fixed Deposits"),
            ("SCSS", "Senior Citizen Savings"),
            ("POMIS", "Post Office MIS"),
        ],
        "US": [
            ("SWP", "SWP / Market Linked"),
            ("401K", "401(k)"),
            ("IRA", "IRA"),
            ("BROKERAGE", "Brokerage"),
        ],
        "UK": [
            ("SWP", "SWP / Market Linked"),
            ("PENSION", "Pension"),
            ("ISA", "ISA"),
        ],
    }[country]


# =========================================================
# MAIN UI
# =========================================================

def render_investment_plan(user_data: dict, user: dict):
    st.header("📊 Income & Investment Strategy")

    is_guest = user.get("is_guest", False)
    is_premium = user.get("is_premium", False)
    #editable = (not is_guest) and (is_premium or active == "Base")
    #print("USER DATA IN INVESTMENT PLAN:")

    country = user_data.get("country", "IN")
    currency = get_currency(user_data)

    # ---------------------------------------------------------
    # Ensure investment_plan structure (SAFE & PERSISTENT)
    # ---------------------------------------------------------
    user_data.setdefault("investment_plan", {})
    plan = user_data["investment_plan"]

    ensure_scenarios(plan, country)
    #plan.setdefault("active_scenario", "Base")
    #plan.setdefault("scenarios", {})

    # Ensure Base exists
    #if "Base" not in plan["scenarios"]:
    #    plan["scenarios"]["Base"] = _default_scenario(country)

    # Hydrate all scenarios safely (NO overwrite)
    default = _default_scenario(country)
    #print("PLAN SCENARIO:", plan["scenarios"])
    for sc in plan["scenarios"].values():
        for section in ["allocations", "rates", "income_sources", "withdrawal"]:
            sc.setdefault(section, {})
            for k, v in default[section].items():
                sc[section].setdefault(k, v)

    # ---------------------------------------------------------
    # AUTO-CREATE CONSERVATIVE & AGGRESSIVE (ONCE)
    # ---------------------------------------------------------
    if not is_guest:
        base = plan["scenarios"]["Base"]

        if "Conservative" not in plan["scenarios"]:
            plan["scenarios"]["Conservative"] = _derive_scenario(
                base, "conservative"
            )

        if "Aggressive" not in plan["scenarios"]:
            plan["scenarios"]["Aggressive"] = _derive_scenario(
                base, "aggressive"
            )

    # =========================================================
    # SCENARIO SELECTOR
    # =========================================================
    st.subheader("🧪 Scenario")

    scenario_names = list(plan["scenarios"].keys())

    active = st.selectbox(
        "Active Scenario",
        scenario_names,
        index=scenario_names.index(plan["active_scenario"]),
        disabled=False,
    )

    plan["active_scenario"] = active
    scenario = plan["scenarios"][active]

    # ---- Scenario actions (non-guest only) ----
    if not is_guest:
        c1, c2 = st.columns(2)

        with c1:
            if st.button(
                "➕ Clone Scenario",
                disabled=len(scenario_names) >= 3,
            ):
                new_name = f"Scenario {len(scenario_names)}"
                plan["scenarios"][new_name] = copy.deepcopy(scenario)
                plan["active_scenario"] = new_name
                st.rerun()

        with c2:
            if active != "Base":
                if st.button("🗑 Delete Scenario"):
                    del plan["scenarios"][active]
                    plan["active_scenario"] = "Base"
                    st.rerun()

    st.divider()

    editable = not is_guest

    # =========================================================
    # SECTION A — STARTING CORPUS (READ ONLY)
    # =========================================================
    st.subheader("A️⃣ Starting Corpus")

    corpus = user_data.get("initial_corpus", {})
    #print("CORPUS", corpus)
    total_corpus = round(sum(corpus.values()), 2)

    st.metric("Total Starting Corpus", f"{currency}{total_corpus:,.0f}")

    if corpus:
        st.dataframe(
            pd.DataFrame(
                [{"Component": k, "Amount": v} for k, v in corpus.items()]
            ),
            use_container_width=True,
        )

    if total_corpus == 0:
        st.warning("Starting corpus is zero. Update Base Data.")

    st.divider()

    # =========================================================
    # SECTION B — ALLOCATION + RETURNS
    # =========================================================
    st.subheader("B️⃣ Allocation & Expected Returns")

    rows = []
    alloc_total = 0.0

    for key, label in _allocation_fields(country):
        alloc = float(scenario["allocations"][key])
        rate = float(scenario["rates"][key])

        allocated_amt = round(total_corpus * alloc / 100, 2)
        annual_income = round(allocated_amt * rate / 100, 2)

        rows.append({
            "Instrument": label,
            "Allocation %": alloc,
            "Rate %": rate,
            "Allocated Amount": allocated_amt,
            "Annual Income (est.)": annual_income,
        })

        alloc_total += alloc

    st.dataframe(pd.DataFrame(rows), use_container_width=True)

    if alloc_total != 100:
        st.warning(f"Allocation totals {alloc_total}%. Recommended: 100%.")

    st.markdown("### ✏️ Edit Allocation & Rates")

    for key, label in _allocation_fields(country):
        c1, c2 = st.columns(2)

        with c1:
            scenario["allocations"][key] = st.number_input(
                f"{label} Allocation %",
                0.0, 100.0,
                step=5.0,
                value=float(scenario["allocations"][key]),
                disabled=not editable,
            )

        with c2:
            scenario["rates"][key] = st.number_input(
                f"{label} Rate %",
                0.0, 20.0,
                step=0.25,
                value=float(scenario["rates"][key]),
                disabled=not editable,
            )

    st.divider()

    # =========================================================
    # SECTION C — EXTERNAL INCOME & WITHDRAWAL
    # =========================================================
    st.subheader("C️⃣ External Income & Withdrawal")

    for k in scenario["income_sources"]:
        scenario["income_sources"][k] = st.number_input(
            k.replace("_", " ").title(),
            min_value=0.0,
            value=float(scenario["income_sources"][k]),
            disabled=not editable,
        )

    scenario["withdrawal"]["monthly"] = st.number_input(
        "Monthly Withdrawal (SWP)",
        min_value=0.0,
        step=1000.0,
        value=float(scenario["withdrawal"]["monthly"]),
        disabled=not editable,
    )

    st.divider()

    # =========================================================
    # SECTION D — PROJECTIONS (ACTIVE SCENARIO)
    # =========================================================
    st.subheader("D️⃣ Projections")
    #print("Calculing prrojections")
    result = calculate_projections(user_data, user)

    active = result.get("active_result", {})
    projections = active.get("projections", [])
    #print("active", active)
    if not projections:
        st.info("Complete inputs to view projections.")
        return

    df = pd.DataFrame(projections)
    st.dataframe(df, use_container_width=True)

    # ---- Ending Corpus chart ----
    if "EndingCorpus" in df.columns:
        st.plotly_chart(
            px.line(
                df,
                x="Year",
                y="EndingCorpus",
                markers=True,
                title=f"Ending Corpus — {active.get('scenario', 'Base')} Scenario",
            ),
            use_container_width=True,
        )

    # ---- Income vs Expenses ----
    cols = [
        c for c in ["TotalIncome", "TotalExpenses", "NetIncomeAfterTax"]
        if c in df.columns
    ]
    if cols:
        st.plotly_chart(
            px.line(
                df,
                x="Year",
                y=cols,
                markers=True,
                title="Income vs Expenses",
            ),
            use_container_width=True,
        )

    # =========================================================
    # SECTION E — SCENARIO COMPARISON (NO RECOMPUTE)
    # =========================================================
    st.subheader("E️⃣ Scenario Comparison")

    results_by_scenario = result.get("results_by_scenario", {})

    comparison_rows = []
    #print("Results by scenario: INVESTMENT PLAN ", results_by_scenario)
    for name, sc_result in results_by_scenario.items():
        projections = sc_result.get("projections", [])
        if not projections:
            continue

        first = projections[0]
        last = projections[-1]

        comparison_rows.append({
            "Scenario": name,
            "Ending Corpus": last.get("EndingCorpus", 0),
            "Total Income (Y1)": first.get("TotalIncome", 0),
            "Total Expenses (Y1)": first.get("TotalExpenses", 0),
            "Net Income After Tax (Y1)": first.get("NetIncomeAfterTax", 0),
        })

    if comparison_rows:
        df_cmp = pd.DataFrame(comparison_rows)

        st.dataframe(df_cmp, use_container_width=True)

        st.plotly_chart(
            px.bar(
                df_cmp,
                x="Scenario",
                y="Ending Corpus",
                title="Ending Corpus Comparison Across Scenarios",
                text_auto=".2s",
                color="Scenario",
                color_discrete_sequence=["#6366f1", "#22c55e", "#ef4444"],
            ),
            use_container_width=True,
        )


