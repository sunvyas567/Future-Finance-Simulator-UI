# allocation_engine.py

from typing import Dict
#from allocation_rules import COUNTRY_RULES

# allocation_rules.py

from dataclasses import dataclass
from typing import Optional


@dataclass
class InstrumentRule:
    name: str
    min_age: Optional[int] = None
    max_age: Optional[int] = None
    max_allocation_pct: Optional[float] = None
    max_investment_amount: Optional[float] = None
    enabled: bool = True


INDIA_RULES = {
    "SWP": InstrumentRule("SWP", max_allocation_pct=100),

    "FD": InstrumentRule("FD", max_allocation_pct=100),

    "SCSS": InstrumentRule(
        "SCSS",
        min_age=60,
        max_allocation_pct=100,
        max_investment_amount=30_00_000  # ₹30 lakh govt cap
    ),

    "POMIS": InstrumentRule(
        "POMIS",
        max_allocation_pct=100,
        max_investment_amount=4_50_000  # single holder cap
    )
}


US_RULES = {
    "SWP": InstrumentRule("SWP"),
    "401K": InstrumentRule("401K"),
    "IRA": InstrumentRule("IRA"),
    "BROKERAGE": InstrumentRule("BROKERAGE"),
}


UK_RULES = {
    "SWP": InstrumentRule("SWP"),
    "PENSION": InstrumentRule("PENSION"),
    "ISA": InstrumentRule("ISA"),
}


COUNTRY_RULES = {
    "IN": INDIA_RULES,
    "US": US_RULES,
    "UK": UK_RULES,
}


class AllocationEngine:

    def __init__(self, country: str, age: int, investable_amount: float):
        self.country = country
        self.age = age
        self.amount = investable_amount
        self.rules = COUNTRY_RULES[country]

    # ---------------------------------------------------
    # STEP 1 — Remove ineligible instruments
    # ---------------------------------------------------
    def filter_eligible(self, allocations: Dict[str, float]):

        valid = {}

        for instrument, pct in allocations.items():

            rule = self.rules.get(instrument)

            if not rule or not rule.enabled:
                continue

            if rule.min_age and self.age < rule.min_age:
                continue

            if rule.max_age and self.age > rule.max_age:
                continue

            valid[instrument] = pct

        return valid

    # ---------------------------------------------------
    # STEP 2 — Normalize to 100%
    # ---------------------------------------------------
    def normalize(self, allocations: Dict[str, float]):

        total = sum(allocations.values())

        if total == 0:
            return allocations

        return {
            k: v * 100 / total
            for k, v in allocations.items()
        }

    # ---------------------------------------------------
    # STEP 3 — Apply investment caps
    # ---------------------------------------------------
    def apply_caps(self, allocations: Dict[str, float]):

        final = {}
        leftover_pct = 0

        for inst, pct in allocations.items():

            rule = self.rules[inst]
            amount = self.amount * pct / 100

            if rule.max_investment_amount and amount > rule.max_investment_amount:
                capped_pct = rule.max_investment_amount * 100 / self.amount
                final[inst] = capped_pct
                leftover_pct += pct - capped_pct
            else:
                final[inst] = pct

        # redistribute leftover
        if leftover_pct > 0:
            eligible = [k for k in final if final[k] > 0]
            if eligible:
                add = leftover_pct / len(eligible)
                for k in eligible:
                    final[k] += add

        return self.normalize(final)

    # ---------------------------------------------------
    # STEP 4 — Convert % → money
    # ---------------------------------------------------
    def to_amounts(self, allocations):

        return {
            k: round(self.amount * v / 100, 2)
            for k, v in allocations.items()
        }

    # ---------------------------------------------------
    # MASTER FUNCTION
    # ---------------------------------------------------
    def build(self, raw_allocations):

        step1 = self.filter_eligible(raw_allocations)
        step2 = self.normalize(step1)
        step3 = self.apply_caps(step2)
        amounts = self.to_amounts(step3)

        return {
            "final_percentages": step3,
            "final_amounts": amounts
        }

# =========================================================
# ALLOCATION ENGINE — PRODUCTION SAFE
# =========================================================

SCSS_MIN_AGE = 60

# India investment limits
SCSS_MAX = 30_00_000
POMIS_MAX_SINGLE = 4_50_000


# ---------------------------------------------------------
# DEFAULT ALLOCATION MODELS BY COUNTRY
# ---------------------------------------------------------
def _india_model(age: int, corpus: float):
    """
    Age aware default allocation model for India
    """

    # retirement
    if age and age >= 60:
        alloc = {
            "SWP": 35,
            "FD": 25,
            "SCSS": 25,
            "POMIS": 15,
        }

    # pre-retirement
    elif age and age >= 45:
        alloc = {
            "SWP": 55,
            "FD": 30,
            "SCSS": 0,
            "POMIS": 15,
        }

    # growth stage
    else:
        alloc = {
            "SWP": 70,
            "FD": 20,
            "SCSS": 0,
            "POMIS": 10,
        }

    rates = {
        "SWP": 8.0,
        "FD": 6.5,
        "SCSS": 8.2,
        "POMIS": 7.4,
    }

    return alloc, rates


def _us_model(age, corpus):
    alloc = {
        "SWP": 50,
        "401K": 25,
        "IRA": 15,
        "BROKERAGE": 10,
    }

    rates = {
        "SWP": 7.5,
        "401K": 7.0,
        "IRA": 6.5,
        "BROKERAGE": 6.0,
    }

    return alloc, rates


def _uk_model(age, corpus):
    alloc = {
        "SWP": 45,
        "PENSION": 35,
        "ISA": 20,
    }

    rates = {
        "SWP": 7.0,
        "PENSION": 6.5,
        "ISA": 6.0,
    }

    return alloc, rates


# ---------------------------------------------------------
# PUBLIC ENGINE — BUILD MODEL
# ---------------------------------------------------------
def build_allocation_model(country: str, age: int, corpus: float):

    if country == "IN":
        alloc, rates = _india_model(age, corpus)
    elif country == "US":
        alloc, rates = _us_model(age, corpus)
    else:
        alloc, rates = _uk_model(age, corpus)

    alloc = filter_instruments_by_age(alloc, age)
    alloc = normalize_allocations(alloc)

    return {
        "allocations": alloc,
        "rates": rates
    }


# ---------------------------------------------------------
# AGE ELIGIBILITY FILTER
# ---------------------------------------------------------
def filter_instruments_by_age(allocations: dict, age: int):

    alloc = allocations.copy()

    if age is None or age < SCSS_MIN_AGE:
        alloc["SCSS"] = 0

    return alloc


# ---------------------------------------------------------
# NORMALIZATION ENGINE
# ---------------------------------------------------------
def normalize_allocations(allocations: dict):
    """
    Ensures total = 100%
    Preserves proportions.
    """

    total = sum(allocations.values())

    if total <= 0:
        return allocations

    factor = 100 / total

    return {
        k: round(v * factor, 2)
        for k, v in allocations.items()
    }
