RETIREMENT_PROFILES = {
    "IN": {
        "income_sources": [
            ("FD Interest", "GLFDInterestIncome", 0.10),
            ("SWP Withdrawals", "GLSWPWithdrawal", 0.05),
            ("Rental Income", "GLCurrentMonthlyRental", 0.10),
        ]
    },
    "US": {
        "income_sources": [
            ("401k Withdrawals", "GLSWPWithdrawal", 0.15),
            ("Social Security", "GLPensionEPS", 0.10),
            ("Dividends", "GLDividendIncome", 0.15),
        ]
    },
    "UK": {
        "income_sources": [
            ("Pension Drawdown", "GLSWPWithdrawal", 0.12),
            ("State Pension", "GLPensionEPS", 0.08),
            ("Dividends", "GLDividendIncome", 0.15),
        ]
    }
}
