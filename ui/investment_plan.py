# ui/investment_plan.py

import streamlit as st
import pandas as pd
import plotly.express as px
import copy

from services.api_client import calculate_projections
from ui import scenario
#from ui import scenario
from ui.currency import get_currency
from ui.expense_summary import render_expense_summary

from ui.allocations_engine import (
    build_allocation_model,
    normalize_allocations,
    filter_instruments_by_age
)


import copy

# =========================================================
# INVESTMENT LIMITS (INDIA)
# =========================================================
SCSS_MAX_INVESTMENT = 30_00_000   # 30 lakh per individual
POMIS_MAX_INVESTMENT = 4_50_000   # 4.5 lakh single account
SCSS_MAX = 30_00_000   # 30 lakh per individual
POMIS_MAX_SINGLE = 4_50_000   # 4.5 lakh single account
POMIS_MAX_JOINT = 9_00_000    # 9 lakh joint account

SCSS_MIN_AGE = 60

# =========================================================
# LIFE STAGE HELPER
# =========================================================
def _get_life_stage(user_data):
    age = user_data.get("GLAge", {}).get("input", 35)

    if age < 35:
        return "early"
    elif age < 55:
        return "mid"
    else:
        return "retirement"

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
                "SWP": 50,
                "FD": 30,
                "SCSS":15,
                "POMIS": 5,
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
# ELIGIBILITY & LIMIT HELPERS
# =========================================================
def get_user_age(user_data: dict):
    age = user_data.get("GLAge", {}).get("input")
    return int(age) if age else None

# =========================================================
# INVESTMENT CAP ENGINE (SINGLE SOURCE OF TRUTH)
# =========================================================

def apply_instrument_caps(
    total_corpus: float,
    allocations: dict,
    age: int | None,
    pomis_limit=POMIS_MAX_SINGLE,
):
    """
    Final enforcement engine.
    Used for BOTH UI display and backend projection safety.
    """

    capped = allocations.copy()
    surplus_pct = 0.0

    if total_corpus <= 0:
        return capped, 0.0

    # ---------- SCSS age eligibility ----------
    if age is None or age < SCSS_MIN_AGE:
        surplus_pct += capped.get("SCSS", 0)
        capped["SCSS"] = 0

    # ---------- SCSS cap ----------
    scss_pct_limit = min(100.0, (SCSS_MAX / total_corpus) * 100)
    if capped.get("SCSS", 0) > scss_pct_limit:
        surplus_pct += capped["SCSS"] - scss_pct_limit
        capped["SCSS"] = scss_pct_limit

    # ---------- POMIS cap ----------
    pomis_pct_limit = min(100.0, (pomis_limit / total_corpus) * 100)
    if capped.get("POMIS", 0) > pomis_pct_limit:
        surplus_pct += capped["POMIS"] - pomis_pct_limit
        capped["POMIS"] = pomis_pct_limit

    # ---------- redirect surplus to SWP ----------
    capped["SWP"] = capped.get("SWP", 0) + surplus_pct

    return capped, surplus_pct

def percent_from_amount(amount, corpus):
    if corpus <= 0:
        return 0
    if (amount / corpus) * 100 > 100:
        return 100.0
    return round((amount / corpus) * 100, 2)


def rebalance_to_100(alloc, locked_keys=None):
    locked_keys = locked_keys or []

    total = sum(alloc.values())
    diff = 100 - total

    adjustable = [k for k in alloc if k not in locked_keys]

    if not adjustable:
        return alloc

    share = diff / len(adjustable)

    for k in adjustable:
        alloc[k] = max(0, alloc[k] + share)

    return {k: round(v, 2) for k, v in alloc.items()}

def get_instrument_max_percent(
    instrument: str,
    total_corpus: float,
    age: int | None,
):
    """Used ONLY for UI slider max values"""

    if total_corpus <= 0:
        return 0.0

    if instrument == "SCSS":
        if age is None or age < SCSS_MIN_AGE:
            return 0.0
        return min(100.0, (SCSS_MAX / total_corpus) * 100)

    if instrument == "POMIS":
        return min(100.0, (POMIS_MAX_SINGLE / total_corpus) * 100)

    return 100.0


def get_allocation_max_pct(instrument, total_corpus, age):
    if instrument == "SCSS":
        if age is None or age < SCSS_MIN_AGE:
            return 0.0
        return min(100, (SCSS_MAX / total_corpus) * 100) if total_corpus else 0

    if instrument == "POMIS":
        return min(100, (POMIS_MAX_SINGLE / total_corpus) * 100) if total_corpus else 0

    return 100.0

def is_scss_eligible(user_data: dict) -> bool:
    return get_user_age(user_data) >= SCSS_MIN_AGE

def redistribute_remaining(alloc, changed_key):
    """
    Keeps changed_key fixed.
    Redistributes remaining % across other instruments proportionally.
    """

    fixed_value = alloc[changed_key]
    remaining_target = 100 - fixed_value

    other_keys = [k for k in alloc if k != changed_key]
    other_total = sum(alloc[k] for k in other_keys)

    if other_total <= 0:
        return alloc

    scale = remaining_target / other_total

    for k in other_keys:
        alloc[k] *= scale

    return alloc

def rebalance_allocations_to_100(allocations: dict, total_corpus: float, age: int):
    """
    Ensures allocations sum to 100%.
    Respects SCSS / POMIS limits.
    Distributes remaining % to eligible instruments.
    """

    total = sum(allocations.values())

    if round(total, 2) == 100:
        return allocations

    remaining = 100 - total

    # eligible instruments that can receive extra allocation
    eligible = []
    for inst in allocations:
        max_pct = get_allocation_max_pct(inst, total_corpus, age)
        if allocations[inst] < max_pct:
            eligible.append(inst)

    if not eligible:
        return allocations

    add_each = remaining / len(eligible)

    for inst in eligible:
        max_pct = get_allocation_max_pct(inst, total_corpus, age)
        allocations[inst] = min(max_pct, allocations[inst] + add_each)

    return allocations

def apply_age_based_default_allocation(scenario, total_corpus, age):
    if age is None or age >= 60:
        return scenario

    alloc = scenario["allocations"]

    # remove SCSS
    alloc["SCSS"] = 0

    # set POMIS to max
    pomis_max = get_allocation_max_pct("POMIS", total_corpus, age)
    alloc["POMIS"] = pomis_max

    remaining = 100 - pomis_max

    others = [k for k in alloc if k not in ("SCSS", "POMIS")]
    total_other = sum(alloc[k] for k in others) or 1

    for k in others:
        alloc[k] = remaining * alloc[k] / total_other

    return scenario

def enforce_stage_investment_rules(scenario, stage, age):
    alloc = scenario["allocations"]

    # ---- SCSS hard disable below 60 ----
    if age is None or age < SCSS_MIN_AGE:
        alloc["SCSS"] = 0

    # ---- Early stage rules ----
    if stage == "early":
        alloc["SCSS"] = 0  # safety

    # ---- Mid stage rules ----
    if stage == "mid":
        alloc["SCSS"] = 0  # safety

    return scenario

def get_visible_income_sources(stage, country):
    base = {
        "IN": ["rental", "pension", "annuity", "dividends", "other"],
        "US": ["social_security", "rental", "pension", "annuity", "dividends", "other"],
        "UK": ["rental", "pension", "annuity", "dividends", "other"],
    }[country]

    if stage == "early":
        return [k for k in base if k not in ("pension", "annuity")]

    if stage == "mid":
        return [k for k in base if k != "pension"]

    return base

def get_current_monthly_expense(user_data):
    recurring = user_data.get("expenses_recurring", [])
    total = 0
    for row in recurring:
        total += float(row.get("Monthly", 0))
    return total

def ui_section(title, icon="📊"):
    st.markdown(f"## {icon} {title}")
    return st.container(border=True)

# =========================================================
# MAIN UI
# =========================================================

def render_investment_plan(user_data: dict, user: dict):
    #st.header("📊 Income & Investment Strategy")
    st.header("📊 Income & Investment Strategy - How Your Money Works for You")
    st.caption("See how your savings generate income and support your lifestyle.")

    # ---------------------------------------------------------
    # LIFE STAGE CONTEXT
    # ---------------------------------------------------------
    stage = _get_life_stage(user_data)

    age = get_user_age(user_data)
    

    if stage == "early":
        st.info("🌱 Wealth accumulation phase — focus on growth and contributions.")
        st.caption("💡 Salary growth, investments, low withdrawals")

    elif stage == "mid":
        st.info("👨‍👩‍👧 Income + responsibility balance phase.")
        st.caption("💡 Education costs, EMIs, long-term retirement planning")

    else:
        st.success("🏖 Income distribution phase — retirement cashflow planning.")
        st.caption("💡 Pension, withdrawals, income sustainability")


    is_guest = user.get("is_guest", False)
    is_premium = user.get("is_premium", False)
    #editable = (not is_guest) and (is_premium or active == "Base")
    #print("USER DATA IN INVESTMENT PLAN:")

    country = user_data.get("country", "IN")
    currency = get_currency(user_data)

    # -------------------------------------------------
    # Resolve active scenario (ALWAYS define early)
    # -------------------------------------------------

    investment_plan = user_data.setdefault("investment_plan", {})
    scenarios = investment_plan.setdefault("scenarios", {})

    # active scenario name
    #active = investment_plan.get("selected_scenario", "Base")

    # ---------------------------------------------------------
    # Ensure investment_plan structure (SAFE & PERSISTENT)
    # ---------------------------------------------------------
    #user_data.setdefault("investment_plan", {})
    #plan = user_data["investment_plan"]

    #active = plan.get("active_scenario", "Base")


    # ensure exists
    #if active not in scenarios:
    #    scenarios[active] = {}

    # active scenario object
    #scenario = scenarios[active]

    #print("scenario at start of render:", scenario)
    # Default scenario name
    #scenario_name = investment_plan.get("selected_scenario", "Base")

    # Ensure scenario exists
    #if scenario_name not in scenarios:
    #    scenarios[scenario_name] = {}

    # FINAL scenario object used everywhere
    #scenario = scenarios[scenario_name]


    #ensure_scenarios(plan, country)
    #plan.setdefault("active_scenario", "Base")
    #plan.setdefault("scenarios", {})

    user_data.setdefault("investment_plan", {})
    plan = user_data["investment_plan"]

    ensure_scenarios(plan, country)

    active = plan.get("active_scenario", "Base")
    scenario = plan["scenarios"][active]

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
    else:
        print("Iam in guest mode, skipping auto-creation of Conservative and Aggressive scenarios")
        base = plan["scenarios"]["Base"] # Fix for Guest login ket error withdrawal


    editable = not is_guest

    # =========================================================
    # SECTION A — STARTING CORPUS (READ ONLY)
    # =========================================================
    with ui_section("Financial Foundation", "💼"):
        st.subheader("💰  Your Current Savings - Starting Corpus")

        corpus = user_data.get("initial_corpus", {})
        #print("CORPUS", corpus)
        total_corpus = round(sum(corpus.values()), 2)

        age = get_user_age(user_data)

        # ---------------------------------------------------------
        # BUILD ALLOCATION ENGINE MODEL (NEW)
        # ---------------------------------------------------------
        allocation_model = build_allocation_model(
            country=country,
            age=age,
            corpus=total_corpus
        )

        engine_default_alloc = allocation_model["allocations"]
        engine_rates = allocation_model["rates"]

        #print("Allocation model built: 5", allocation_model)
        #print("scenario before engine sync:", scenario)
        #scenario = apply_age_based_default_allocation(
        #    scenario,
        #    total_corpus,
        #    age

        # --------------------------------------------------
        # SYNC SCENARIO WITH ENGINE MODEL (PRODUCTION SAFE)
        # --------------------------------------------------

        # ensure dicts exist
        #scenario.setdefault("allocations", {})
        #scenario.setdefault("rates", {})

        #existing_alloc = scenario["allocations"]
        #existing_rates = scenario["rates"]

        # --------------------------------------------------
        # 1️⃣ rebuild allocations from engine structure
        #    preserve user values if instrument still valid
        # --------------------------------------------------
        #scenario["allocations"] = {
        #    inst: existing_alloc.get(inst, default_pct)
        #    for inst, default_pct in engine_default_alloc.items()
        #}

        # --------------------------------------------------
        # 2️⃣ normalize to 100%
        # --------------------------------------------------
        #from core.allocation_engine import normalize_allocations

        #scenario["allocations"] = normalize_allocations(
        #    scenario["allocations"]
        #)

        # --------------------------------------------------
        # 3️⃣ sync rates (preserve user override if exists)
        # --------------------------------------------------
        #scenario["rates"] = {
        #    inst: existing_rates.get(inst, default_rate)
        #   for inst, default_rate in engine_rates.items()
        #}
        #print("Scenario after syncing with engine defaults: 3", scenario)
        # ---------------------------------------------------------
        # SYNC SCENARIO WITH ENGINE DEFAULTS (ONLY IF EMPTY)
        # ---------------------------------------------------------
        #if not scenario.get("allocations"):
        #    print("I am her 1")
        #    scenario["allocations"] = engine_default_alloc.copy()

        # ensure all instruments exist
        #for inst, pct in engine_default_alloc.items():
        #    print("inst:", inst, "pct:", pct)
        #    scenario["allocations"].setdefault(inst, pct)

        #print("Engine default allocations:", engine_default_alloc)
        # ensure rates synced
        #for inst, rate in engine_rates.items():
        #    print("I am her 3")
        #    scenario["rates"].setdefault(inst, rate)

        # --------------------------------------------------
        # ENGINE SYNC — RUN ONLY ONCE PER SCENARIO
        # --------------------------------------------------
        if not scenario.get("_engine_synced"):

            scenario.setdefault("allocations", {})
            scenario.setdefault("rates", {})

            existing_alloc = scenario["allocations"]
            existing_rates = scenario["rates"]

            # FIRST TIME ONLY → full engine defaults
            #print("Existing allocations before engine sync 123:", existing_alloc)
            if not existing_alloc:
                scenario["allocations"] = engine_default_alloc.copy()
                #print("Applied engine default allocations")

            else:
                # preserve user values but sync structure
                #print("REPPLY Applied engine default allocations")
                #Force engine allocations to take care of existing user valeues
                scenario["allocations"] = engine_default_alloc.copy()
                #scenario["allocations"] = {
                #    inst: existing_alloc.get(inst, engine_default_alloc[inst])
                #    for inst in engine_default_alloc
                #}

                # remove obsolete instruments
                scenario["allocations"] = {
                    k: v for k, v in scenario["allocations"].items()
                    if k in engine_default_alloc
                }
                #print("Removed obsolete instruments from allocations", scenario["allocations"])
            # normalize
            scenario["allocations"] = normalize_allocations(
                scenario["allocations"]
            )

            # sync rates
            scenario["rates"] = {
                inst: existing_rates.get(inst, engine_rates[inst])
                for inst in engine_rates
            }

            scenario["_engine_synced"] = True

        #if not scenario.get("_engine_synced"):

        #    scenario.setdefault("allocations", {})
        #    scenario.setdefault("rates", {})

        #    existing_alloc = scenario["allocations"]
        #    existing_rates = scenario["rates"]

            # rebuild structure from engine (preserve user values)
        #    scenario["allocations"] = {
        #        inst: existing_alloc.get(inst, pct)
        #        for inst, pct in engine_default_alloc.items()
        #    }
        #    print("Scenario after rebuilding with engine structure:", scenario)
        #    scenario["allocations"] = normalize_allocations(
        #        scenario["allocations"]
        #    )
        #    print("Scenario after normalizing allocations:", scenario)
        #    scenario["rates"] = {
        #        inst: existing_rates.get(inst, rate)
        #        for inst, rate in engine_rates.items()
        #    }

        #    scenario["_engine_synced"] = True

        #    print("Engine synced once for scenario")

        #print("Scenario after syncing with engine defaults:", scenario)
        # ---------------------------------------------------------
        # ENFORCE GOVT INVESTMENT LIMITS
        # ---------------------------------------------------------
        #enforce_investment_caps(scenario, total_corpus, user_data)

        st.metric("Total Starting Corpus ", f"{currency}{total_corpus:,.0f}")

        if corpus:
            st.dataframe(
                pd.DataFrame(
                    [{"Component": k, "Amount": v} for k, v in corpus.items()]
                ),
                use_container_width=True,
            )

        if total_corpus == 0:
            st.warning("Starting corpus is zero. Update Base Data.")

        if stage == "early":
            st.caption("📈 Corpus will grow mainly through new investments.")

        elif stage == "mid":
            st.caption("⚖ Corpus supports both growth and financial goals.")

        else:
            st.caption("💸 Corpus now supports retirement income withdrawals.")

        st.divider()

            # =========================================================
        # SECTION C — EXTERNAL INCOME & WITHDRAWAL (REDESIGNED)
        # =========================================================

        # Income frequency configuration
        INCOME_FREQUENCY = {
            "rental": "monthly",
            "pension": "monthly",
            "annuity": "monthly",
            "social_security": "monthly",
            "dividends": "yearly",
            "other": "yearly",
        }

        st.subheader("💰 Other Income & Withdrawal")

        # ---------------------------------------------------------
        # STAGE INCOME CONTEXT
        # ---------------------------------------------------------
        if stage == "early":
            st.info("Most income comes from work. Passive income optional.")

        elif stage == "mid":
            st.info("Multiple income streams strengthen financial stability.")

        else:
            st.success("Passive and retirement income become primary cashflow.")

        # -----------------------------
        # External Income Sources
        # -----------------------------
        st.markdown("### 💸 Other Income Sources")

        INCOME_ICONS = {
            "rental": "🏠",
            "pension": "🧓",
            "annuity": "📜",
            "dividends": "📈",
            "social_security": "🏛️",
            "other": "➕",
        }

        INCOME_FREQUENCY = {
            "rental": "monthly",
            "pension": "monthly",
            "annuity": "monthly",
            "social_security": "monthly",
            "dividends": "yearly",
            "other": "yearly",
        }

        income_cols = st.columns(2)

        #for idx, (key, value) in enumerate(scenario["income_sources"].items()):
        visible_sources = get_visible_income_sources(stage, country)

        for idx, key in enumerate(visible_sources):
            value = scenario["income_sources"].get(key, 0)

            col = income_cols[idx % 2]

            label = key.replace("_", " ").title()
            icon = INCOME_ICONS.get(key, "💰")
            frequency = INCOME_FREQUENCY.get(key, "monthly")

            include_key = f"income_{active}_{key}_include"
            value_key = f"income_{active}_{key}_value"

            if include_key not in st.session_state:
                st.session_state[include_key] = value > 0

            with col:
                with st.container(border=True):

                    st.markdown(f"### {icon} {label}")

                    include = st.checkbox(
                        "Include",
                        key=include_key,
                        disabled=not editable,
                    )

                    # 🔹 Label shows Monthly or Yearly
                    label_text = (
                        f"Monthly Amount ({currency})"
                        if frequency == "monthly"
                        else f"Yearly Amount ({currency})"
                    )

                    amount = st.number_input(
                        label_text,
                        min_value=0.0,
                        step=1000.0,
                        value=float(value),
                        disabled=not include or not editable,
                        key=value_key,
                    )

                    # 🔹 Show annual equivalent for monthly items
                    if include:
                        if frequency == "monthly":
                            annual_value = amount * 12
                            st.caption(f"💡 Annual Equivalent: {currency}{annual_value:,.0f}")
                        else:
                            st.caption(f"💡 Annual Income: {currency}{amount:,.0f}")

                    # 🔹 Store consistently (store raw user input)
                    scenario["income_sources"][key] = amount if include else 0.0
        # remove hidden incomes from model
        for k in scenario["income_sources"].keys():
            if k not in visible_sources:
                scenario["income_sources"][k] = 0
            
        # -----------------------------
        # SWP Withdrawal
        # -----------------------------
        st.divider()
        st.markdown("### 🔄 Systematic Withdrawal (SWP)")

        with st.container(border=True):
            st.markdown("### 💳 Monthly Withdrawal")

            if stage == "early":
                st.caption("⚠ Withdrawals reduce long-term growth.")

            elif stage == "mid":
                st.caption("⚖ Withdraw only if needed for major goals.")

            else:
                st.caption("💰 Primary retirement income source.")

            scenario["withdrawal"]["monthly"] = st.number_input(
                f"Withdrawal Amount ({currency} / month)",
                min_value=0.0,
                step=1000.0,
                value=float(scenario["withdrawal"]["monthly"]),
                disabled=not editable,
                key=f"withdrawal_{active}",
            )

            st.caption(
                f"📅 Yearly: {currency}{scenario['withdrawal']['monthly'] * 12:,.0f}"
            )

        st.divider()

    with ui_section("Lifestyle Cost Context", "🏡"):

        expense_totals = render_expense_summary(
            user_data,
            currency=currency
        )

    with ui_section("Planning Scenario", "🎯"):

        # =========================================================
        # SCENARIO SELECTOR
        # =========================================================
        st.subheader("🧪 Your Future Plans (Scenarios)")
    # st.subheader("🧪 Your Future Plans")
        st.caption("Compare different approaches to managing your retirement income.")


        scenario_names = list(plan["scenarios"].keys())

        selected = st.selectbox(
            "Active Scenario",
            scenario_names,
            index=scenario_names.index(plan["active_scenario"]),
            disabled=False,
        )

        plan["active_scenario"] = selected
        scenario = plan["scenarios"][selected]

        #print("Selected scenario:", selected)
        #st.session_state.alloc_state = scenario["allocations"].copy()
        #for k, v in scenario["allocations"].items():
        #    st.session_state[f"alloc_{k}"] = float(v)

        # --------------------------------------------------
        # LOAD SESSION ONLY WHEN SCENARIO CHANGES
        # --------------------------------------------------
        #if st.session_state.get("_active_scenario_loaded") != selected:

        #    st.session_state.alloc_state = scenario["allocations"].copy()

        #    for k, v in scenario["allocations"].items():
        #        st.session_state[f"alloc_{k}"] = float(v)

        #    st.session_state["_active_scenario_loaded"] = selected
        if st.session_state.get("_active_scenario_loaded") != selected:

            # 1️⃣ apply engine rules ONCE when scenario selected
            scenario_alloc = filter_instruments_by_age(
                allocations=scenario["allocations"],
                age=age
            )

            scenario_alloc = normalize_allocations(scenario_alloc)

            scenario["allocations"] = scenario_alloc

            # 2️⃣ load into session UI state
            st.session_state.alloc_state = scenario_alloc.copy()

            for k, v in scenario_alloc.items():
                st.session_state[f"alloc_{k}"] = float(v)

            st.session_state["_active_scenario_loaded"] = selected

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
        #print("Scenario after selection:", scenario)
        st.divider()

    with ui_section("Investment Allocation Strategy", "📈"):

        # =========================================================
        # 💰 PROFESSIONAL ALLOCATION UI
        # =========================================================
        st.subheader("💰 Where Your Money Is Invested")

        # ---------------------------------------------------------
        # STAGE ALLOCATION GUIDANCE
        # ---------------------------------------------------------
        if stage == "early":
            st.info("Higher growth allocation usually appropriate.")

        elif stage == "mid":
            st.info("Balanced allocation between growth and stability.")

        else:
            st.info("Income stability and capital preservation focus.")

        #total_corpus = sum(user_data.get("initial_corpus", {}).values())
        #age = user_data.get("age")

        #scenario = enforce_stage_investment_rules(scenario, stage, age)
        #display_alloc = enforce_stage_investment_rules(
        #    {"allocations": st.session_state.alloc_state.copy()},
        #    stage,
        #    age
        #)["allocations"]

        display_alloc = st.session_state.alloc_state.copy()



        #print("Scenario after enforcing stage rules:", scenario)
        # ---------------------------------------------------------
        # ENGINE ELIGIBILITY FILTER (NEW)
        # ---------------------------------------------------------
        #scenario_alloc = filter_instruments_by_age(
        #    allocations=scenario["allocations"],
        #    age=age
        #)

        # normalize after eligibility
        #scenario_alloc = normalize_allocations(scenario_alloc)

        #scenario["allocations"] = scenario_alloc

        #print("Scenario allocations after age-based filtering:", scenario_alloc)
        #scenario = enforce_stage_investment_rules(scenario, stage, age)

        #scenario_alloc = scenario["allocations"]

        # -------------------------------------------------
        # FORCE SESSION STATE TO MATCH ENFORCED SCENARIO
        # -------------------------------------------------
        #for k, v in scenario_alloc.items():
        #    st.session_state[f"alloc_{k}"] = float(v)

        #st.session_state.alloc_state = scenario_alloc.copy()


        #print("Scenario allocations 11111 after stage rule enforcement:", scenario_alloc)
        # ---------- session state init ----------
        #if "alloc_state" not in st.session_state:
        #    st.session_state.alloc_state = scenario_alloc.copy()
        #if "alloc_state" not in st.session_state:
        #    st.session_state.alloc_state = {
        #        k: float(v) for k, v in scenario_alloc.items()
        #    }

        # ---------- POMIS joint ----------
        if "pomis_joint" not in st.session_state:
            st.session_state.pomis_joint = False

        pomis_limit = POMIS_MAX_JOINT if st.session_state.pomis_joint else POMIS_MAX_SINGLE

        scss_pct_cap = percent_from_amount(SCSS_MAX_INVESTMENT, total_corpus)
        pomis_pct_cap = percent_from_amount(pomis_limit, total_corpus)

        # =========================================================
        # CAP INFO PANEL
        # =========================================================
        with st.container(border=True):
            st.markdown("### 🛡 Investment Limits")
            #print(f"User age: {age}")
            if age and age < SCSS_MIN_AGE:
                st.info("SCSS not available below age 60")

            else:
                st.info(f"SCSS max allowed: {scss_pct_cap:.2f}%")

            st.checkbox(
                "Joint POMIS account",
                key="pomis_joint",
            )

            st.info(f"POMIS max allowed: {pomis_pct_cap:.2f}%")

        # =========================================================
        # CHANGE HANDLER
        # =========================================================
        def allocation_changed(inst):

            st.session_state.alloc_state[inst] = st.session_state[f"alloc_{inst}"]

            alloc = st.session_state.alloc_state.copy()

            # ---------- SCSS eligibility ----------
            if age is None or age < SCSS_MIN_AGE:
                #alloc["SWP"] += alloc.get("SCSS", 0)
                alloc["SCSS"] = 0

            # ---------- SCSS cap ----------
            if alloc.get("SCSS", 0) > scss_pct_cap:
                surplus = alloc["SCSS"] - scss_pct_cap
                alloc["SCSS"] = scss_pct_cap
                alloc["SWP"] += surplus

            # ---------- POMIS cap ----------
            if alloc.get("POMIS", 0) > pomis_pct_cap:
                surplus = alloc["POMIS"] - pomis_pct_cap
                alloc["POMIS"] = pomis_pct_cap
                alloc["SWP"] += surplus

            # ---------- rebalance ----------
            #alloc = rebalance_to_100(alloc)

            # ---------- rebalance only remaining ----------
            alloc = redistribute_remaining(alloc, inst) 
            # hard enforce again after rebalance
            if age is None or age < SCSS_MIN_AGE:
                alloc["SCSS"] = 0

            # final safety
            alloc["SCSS"] = min(alloc["SCSS"], scss_pct_cap)
            alloc["POMIS"] = min(alloc["POMIS"], pomis_pct_cap)
            #print("Alloc after change and cap enforcement:", alloc)
            # ---------- write back ----------
            st.session_state.alloc_state = alloc

            for k, v in alloc.items():
                st.session_state[f"alloc_{k}"] = v

            scenario["allocations"] = alloc

            #st.rerun()

        # =========================================================
        # INPUT GRID
        # =========================================================
        st.markdown("### ✏️ Edit Allocation")

        #STAGE_PRIORITY_ALLOC = {
        #    "early": ["SWP"],
        #    "mid": ["FD", "SWP"],
        #    "retirement": ["SCSS", "POMIS", "FD"]
        #}
        STAGE_PRIORITY_ALLOC = {
            "early": ["SWP"],
            "mid": ["FD", "SWP"],
            "retirement": ["POMIS", "FD"] + (["SCSS"] if age and age >= 60 else [])
        }
        #print("In Edit Allocation - User age:", age)
        priority_instruments = STAGE_PRIORITY_ALLOC.get(stage, [])

        for key, label in _allocation_fields(country):

            disabled = False

            if key == "SCSS" and (age is None or age < SCSS_MIN_AGE):
                disabled = True

            if key == "SCSS":
                label = f"{label} (max {scss_pct_cap:.1f}%)"

            if key == "POMIS":
                label = f"{label} (max {pomis_pct_cap:.1f}%)"

            #st.number_input(
            #    label,
            #    min_value=0.0,
            #    max_value=100.0,
            #    key=f"alloc_{key}",
            #    value=st.session_state.alloc_state.get(key, 0),
            #    disabled=disabled,
            #    on_change=allocation_changed,
            #    args=(key,)
            #)
            if key in priority_instruments:
                label = f"⭐ {label}"

            st.number_input(
                label,
                min_value=float(0),
                max_value=float(100),
                value=float(st.session_state.alloc_state.get(key, 0.0)),
                step=float(1),
                key=f"alloc_{key}",
                disabled=disabled,
                on_change=allocation_changed,
                args=(key,)
            )


        # =========================================================
        # VALIDATION
        # =========================================================
        total_alloc = sum(st.session_state.alloc_state.values())

        if round(total_alloc, 2) != 100:
            st.warning(f"Total allocation = {total_alloc:.2f}% (auto balanced to 100%)")
        else:
            st.success("Allocation balanced at 100%")

        # =========================================================
        # PIE CHART
        # =========================================================
        #import plotly.express as px
        #import pandas as pd

        df_alloc = pd.DataFrame(
            list(st.session_state.alloc_state.items()),
            columns=["Instrument", "Allocation"]
        )

        fig = px.pie(
            df_alloc,
            values="Allocation",
            names="Instrument",
            hole=0.45,
            title="Allocation Mix"
        )

        st.plotly_chart(fig, use_container_width=True)
        
        #scenario["allocations"] = st.session_state.alloc_state.copy()

        #final_alloc = normalize_allocations(
        #    st.session_state.alloc_state.copy()
        #)

        #scenario["allocations"] = final_alloc
        #st.session_state.alloc_state = final_alloc

        scenario["allocations"] = normalize_allocations(
            st.session_state.alloc_state.copy()
        )

        rows = []
        alloc_total = 0.0

    
        for key, label in _allocation_fields(country):
            alloc = float(scenario["allocations"].get(key, 0))
            rate = float(scenario["rates"][key])

            allocated_amt = round(total_corpus * alloc / 100, 2)
            annual_income = round(allocated_amt * rate / 100, 2)

            rows.append({
                "Instrument": label,
                "Allocation %": round(alloc, 2),
                "Rate %": rate,
                "Allocated Amount": allocated_amt,
                "Estimated Yearly Income": annual_income,
            })

            alloc_total += alloc
        
        
        st.dataframe(pd.DataFrame(rows), use_container_width=True)

        if alloc_total != 100:
            st.warning(f"Allocation totals {alloc_total}%. Recommended: 100%.")
        
    
        st.divider()

    with ui_section("Projected Financial Growth", "📊"):

        # =========================================================
        # SECTION D — PROJECTIONS (ACTIVE SCENARIO)
        # =========================================================
        st.subheader("💰  Projections")

        if stage == "retirement":
            st.caption("Monitor corpus sustainability carefully.")

        st.metric("Number of Planning Years - ",user_data["GLProjectionYears"]["input"])
        #print("Calculing prrojections")
        # ensure legal allocation before simulation
        scenario["allocations"], _ = apply_instrument_caps(
            total_corpus,
            scenario["allocations"],
            age
        )
        
        #scenario["allocations"] = normalize_allocations(
        #    scenario["allocations"]
        #)

        #scenario["allocations"] = normalize_allocations(
        #    st.session_state.alloc_state.copy()
        #)
        scenario["allocations"] = apply_instrument_caps(
            total_corpus,
            scenario["allocations"],
            age
        )[0]


        #scenario = enforce_stage_investment_rules(scenario, stage, age)
        display_alloc = enforce_stage_investment_rules(
            {"allocations": st.session_state.alloc_state.copy()},
            stage,
            age
        )["allocations"]

        #scenario = enforce_stage_investment_rules(scenario, stage, age)
        scenario["allocations"]["SCSS"] = 0 if age is None or age < SCSS_MIN_AGE else scenario["allocations"]["SCSS"]


        result = calculate_projections(user_data, user)

        #result = calculate_projections(user_data, user)

        active = result.get("active_result", {})
        projections = active.get("projections", [])
        #print("active", active)
        if not projections:
            st.info("Complete inputs to view projections.")
            return

        df = pd.DataFrame(projections)
        st.dataframe(df, use_container_width=True)

    with ui_section("Growth Visualisation", "📉"):

        # =========================================================
        # SECTION — Instrument Income Over Time
        # =========================================================
        st.subheader("📈 Income Contribution by Instrument")

        if not projections:
            st.info("Complete inputs to view projections.")
        else:
            df = pd.DataFrame(projections)

            # Detect income columns dynamically
            income_cols = [
                c for c in df.columns
                if c.endswith("Income") and c != "TotalIncome"
            ]

            if income_cols:
                fig_income_sources = px.line(
                    df,
                    x="Year",
                    y=income_cols,
                    markers=True,
                    title="Annual Income by Instrument",
                    labels={"value": "Annual Income", "variable": "Instrument"},
                )

                fig_income_sources.update_layout(
                    template="plotly_white",
                    legend_title="Income Source",
                )

                st.plotly_chart(fig_income_sources, use_container_width=True)

                # Optional stacked version (uncomment if desired)
                """
                fig_stacked = px.area(
                    df,
                    x="Year",
                    y=income_cols,
                    title="Stacked Income Sources Over Time",
                )
                fig_stacked.update_layout(template="plotly_white")
                st.plotly_chart(fig_stacked, use_container_width=True)
                """
            else:
                st.info("No instrument-level income data available.")

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
        st.subheader("💰  Scenario Comparison")

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
        st.caption(
            "These charts illustrate how your financial position evolves "
            "based on income, expenses, inflation and investment returns."
        )

